"""Core Fable Engine — orchestrates the full staged execution pipeline."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .state import StateManager
from .planner import StagePlanner
from .agent_pool import AgentPool
from .verification import VerificationEngine
from .context import ContextCompressor
from .questioner import ProactiveQuestioner


class FableEngine:
    """Main orchestrator: plans, executes, verifies, and consolidates tasks."""

    def __init__(self, state_db: str = "~/.hermes/fable_state.db", output_root: str = "~/.hermes/fable-outputs", max_parallel: int = 3):
        self.state = StateManager(state_db)
        self.planner = StagePlanner(max_parallel=max_parallel)
        self.pool = AgentPool(max_concurrent=max_parallel)
        self.verifier = VerificationEngine()
        self.compressor = ContextCompressor()
        self.questioner = ProactiveQuestioner()
        self.output_root = Path(output_root).expanduser()
        self.output_root.mkdir(parents=True, exist_ok=True)

    def start_task(self, task_description: str, config: Optional[Dict[str, Any]] = None) -> str:
        """Intake a new task, ask clarifying questions, plan stages, and save to state."""
        # Step 1: Proactive questioning
        clarified = self.questioner.clarify(task_description)
        enriched = clarified.get("clarified_task", task_description)

        # Step 2: Dynamic planning
        plan = self.planner.plan_stages(enriched)

        # Step 3: Save to state
        task_id = self.state.create_task(task_description, enriched, plan, config)
        self.state.add_work_log(task_id, decisions=f"Planned {len(plan.get('stages', []))} stages", open_items="Awaiting execution")

        return task_id

    def execute_tick(self, task_id: str) -> Dict[str, Any]:
        """Execute one tick of a running task: all currently ready stages."""
        task = self.state.get_task(task_id)
        if not task:
            return {"error": "Task not found"}
        if task["status"] != "running":
            return {"status": task["status"], "task_id": task_id}

        stages = self.state.get_stages(task_id)
        if not stages:
            return {"error": "No stages found"}

        output_dir = self.output_root / task_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Find ready stages
        completed = {s["id"] for s in stages if s["status"] == "completed"}
        ready = self.planner.get_ready_stages(stages, completed)

        if not ready:
            if self.planner.is_complete(stages):
                self._finalize(task_id, output_dir)
                return {"status": "completed", "task_id": task_id}
            return {"status": "waiting", "task_id": task_id, "message": "No stages ready, dependencies pending"}

        # Separate parallel vs sequential
        parallel = [s for s in ready if s.get("parallel", False)]
        sequential = [s for s in ready if not s.get("parallel", False)]

        results = []

        # Execute parallel batch
        if parallel:
            self.state.add_work_log(task_id, decisions=f"Executing parallel batch: {[s['id'] for s in parallel]}")
            batch_results = self.pool.execute_parallel(parallel, task["clarified_description"], output_dir, self.planner)
            for r in batch_results:
                self._handle_result(task_id, r, output_dir)
            results.extend(batch_results)

        # Execute one sequential stage
        if sequential:
            stage = sequential[0]
            self.state.add_work_log(task_id, decisions=f"Executing sequential stage: {stage['id']}")
            batch_results = self.pool.execute_parallel([stage], task["clarified_description"], output_dir, self.planner)
            for r in batch_results:
                self._handle_result(task_id, r, output_dir)
            results.extend(batch_results)

        # Check if complete
        stages = self.state.get_stages(task_id)
        if self.planner.is_complete(stages):
            self._finalize(task_id, output_dir)
            return {"status": "completed", "task_id": task_id, "results": results}

        return {"status": "running", "task_id": task_id, "results": results}

    def _handle_result(self, task_id: str, result: Dict[str, Any], output_dir: Path) -> None:
        sid = result["stage"]
        status = result["status"]
        model = result.get("model", "")
        provider = result.get("provider", "")
        error = result.get("error", "") or result.get("stderr", "")
        summary = result.get("stdout_preview", "")

        if status == "completed":
            self.state.update_stage_status(sid, "completed", model, provider, error, summary)
            # Run verification
            output_file = Path(result.get("output_file", output_dir / f"{sid}.md"))
            v = self.verifier.verify_stage(sid, output_file)
            if not v["passed"]:
                self.state.add_work_log(task_id, failures=f"Verification failed for {sid}: {v['errors']}")
        else:
            self.state.update_stage_status(sid, "failed", model, provider, error, summary)
            # Retry with fallback model
            if not result.get("retry"):
                self.state.add_work_log(task_id, open_items=f"Retrying {sid} with fallback model")
                stage = self._get_stage_from_state(task_id, sid)
                if stage:
                    retry_result = self.pool.retry_stage(stage, self.state.get_task(task_id)["clarified_description"], output_dir, self.planner, attempt=1)
                    self._handle_result(task_id, retry_result, output_dir)
            else:
                self.state.add_work_log(task_id, failures=f"Stage {sid} failed after retry")

    def _get_stage_from_state(self, task_id: str, stage_id: str) -> Optional[Dict[str, Any]]:
        stages = self.state.get_stages(task_id)
        for s in stages:
            if s["id"] == stage_id:
                return s
        return None

    def _finalize(self, task_id: str, output_dir: Path) -> None:
        """Run consolidation and mark task complete."""
        self.state.update_task_status(task_id, "consolidating")
        task = self.state.get_task(task_id)
        final_file = output_dir / "FINAL.md"

        # Build consolidation prompt
        stage_files = {}
        for s in self.state.get_stages(task_id):
            stage_files[s["id"]] = output_dir / s.get("output", f"{s['id']}.md")

        context = self.compressor.create_context_packet(task["clarified_description"], stage_files)
        guardrails = self.planner.get_guardrails("consolidate")

        prompt = f"""[FABLE STAGE: Consolidation]

{context}

{guardrails}

INSTRUCTIONS:
- Produce a single, canonical final deliverable.
- Save to {final_file}
- Return only a brief status message.
"""
        model, provider = self.planner.get_model_for_stage("consolidate")
        escaped = prompt.replace("'", "'\"'\"'")
        cmd = f"hermes chat -q '{escaped}' -m {model} --provider {provider} -Q -t web,terminal,file"
        import subprocess
        try:
            subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        except Exception:
            pass

        if final_file.exists():
            self.state.mark_task_complete(task_id, str(final_file))
            self.state.add_work_log(task_id, decisions="Consolidation complete", open_items="")
        else:
            self.state.update_task_status(task_id, "failed")
            self.state.add_work_log(task_id, failures="Consolidation failed: FINAL.md not produced")

    def process_all_running_tasks(self) -> List[Dict[str, Any]]:
        """Cron-friendly: process one tick of every running task."""
        tasks = self.state.get_running_tasks()
        results = []
        for task in tasks:
            result = self.execute_tick(task["id"])
            results.append(result)
        return results

    def resume_task(self, task_id: str) -> Dict[str, Any]:
        """Resume a task from its last checkpoint."""
        task = self.state.get_task(task_id)
        if not task:
            return {"error": "Task not found"}
        self.state.update_task_status(task_id, "running")
        return self.execute_tick(task_id)

    def show_status(self) -> Dict[str, Any]:
        """Show status of all tasks."""
        tasks = self.state.get_all_tasks()
        return {
            "total": len(tasks),
            "running": len([t for t in tasks if t["status"] == "running"]),
            "completed": len([t for t in tasks if t["status"] == "completed"]),
            "failed": len([t for t in tasks if t["status"] == "failed"]),
            "tasks": tasks,
        }
