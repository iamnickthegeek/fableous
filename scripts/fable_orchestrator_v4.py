#!/usr/bin/env python3
"""
Fable Orchestrator v4 — Dynamic Parallel Staged Execution

Improvements over v3:
- Checkpoint / resume: state.json persists across interruptions
- Parallel execution: independent stages run concurrently via background processes
- Dynamic stage planner: Stage 0 analyzes the task and builds a custom DAG
- Context pruning: stages receive summaries, not full file dumps
- Process monitoring: tracks background jobs, handles timeouts and failures
- Self-healing: automatic retry with fallback models on failure
- Async-friendly: can run detached and deliver results later

Usage:
    python3 fable_orchestrator_v4.py --task "Your task" --output-dir ./output

Author: Hermes Agent / Nick Smith (Point Clear Advisory)
License: MIT
"""

import argparse
import json
import os
import sys
import time
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# =============================================================================
# MODEL ROUTING TABLE
# =============================================================================

ROUTING_TABLE = {
    "research": {
        "primary":   {"model": "deepseek-v4-flash", "provider": "opencode-go"},
        "secondary": {"model": "gemini-2.5-flash-lite", "provider": "google"},
        "tertiary":  {"model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "provider": "openrouter"},
    },
    "plan": {
        "primary":   {"model": "glm-5.1", "provider": "opencode-go"},
        "secondary": {"model": "gemini-2.5-pro", "provider": "google"},
        "tertiary":  {"model": "deepseek-v4-pro", "provider": "opencode-go"},
    },
    "implement": {
        "primary":   {"model": "kimi-k2.7-code", "provider": "opencode-go"},
        "secondary": {"model": "kimi-k2.6", "provider": "opencode-go"},
        "tertiary":  {"model": "gemini-2.5-pro", "provider": "google"},
    },
    "verify": {
        "primary":   {"model": "deepseek-v4-pro", "provider": "opencode-go"},
        "secondary": {"model": "gemini-2.5-pro", "provider": "google"},
        "tertiary":  {"model": "kimi-k2.6", "provider": "opencode-go"},
    },
    "critique": {
        "primary":   {"model": "glm-5.1", "provider": "opencode-go"},
        "secondary": {"model": "gemini-2.5-pro", "provider": "google"},
        "tertiary":  {"model": "kimi-k2.6", "provider": "opencode-go"},
    },
    "consolidate": {
        "primary":   {"model": "deepseek-v4-pro", "provider": "opencode-go"},
        "secondary": {"model": "glm-5.1", "provider": "opencode-go"},
        "tertiary":  {"model": "gemini-2.5-pro", "provider": "google"},
    },
}

# =============================================================================
# PROMPT GUARDRAILS
# =============================================================================

STAGE_GUARDRAILS = {
    "research": """
GUARDRAILS:
- If you cite percentages, rates, or benchmarks, label the exact source and date.
- Lead with caveats before specific numbers. If data is contested, say so.
- Do not present vendor claims as verified facts unless independently corroborated.
- Note pricing volatility: AI tool prices change frequently; flag promotional vs. stable rates.
""",
    "plan": """
GUARDRAILS:
- Segment the audience into at least 3 tiers (solo/freelance, small agency, in-house team).
- Map every recommendation to a specific tier or use-case.
- Include a "Methodology & Caveats" section in the plan.
- Flag any predetermined conclusions; the plan must remain neutral.
""",
    "implement": """
GUARDRAILS:
- Write the deliverable as if the reader will make purchasing decisions from it.
- Every claim must trace to a source; unsupported claims must be flagged as unverified.
- If a feature was not hands-on tested, explicitly state "described by vendor, not independently verified."
- The final line must not reveal a predetermined conclusion unless the analysis genuinely arrived there.
""",
    "verify": """
GUARDRAILS:
- Check for internal consistency across all prior stages.
- Flag any hallucination data that shifts between stages or uses different benchmarks.
- Verify URLs are live (HTTP 200) and pricing matches current vendor pages.
- Flag pricing volatility and promotional vs. stable rates.
- List all factual errors with exact corrections.
- Output a "Corrections to apply" section.
""",
    "critique": """
GUARDRAILS:
- Check for confirmation bias: was the conclusion predetermined?
- Verify competitor selection is justified; flag unexplained exclusions.
- Assess whether the audience segmentation is adequate.
- Check if verification errors were propagated back or ignored.
- Identify 3+ concrete weaknesses.
- Output a "Priority fixes" ranked list.
""",
    "consolidate": """
GUARDRAILS:
- Read all prior stage outputs (research, plan, implement, verify, critique).
- Produce a single, canonical final deliverable.
- Apply every correction from the verification stage.
- Address every priority fix from the critique stage.
- Remove any predetermined conclusions unless independently justified.
- Add a "Version & Caveats" header stating: (a) what was desk-researched, (b) what was hands-on tested, (c) pricing recheck date.
- This is the ONLY published version; all prior stages are working drafts.
""",
}

# =============================================================================
# ORCHESTRATOR
# =============================================================================

class FableOrchestrator:
    def __init__(self, output_dir: str, work_log: str = "WORK_LOG.md", state_file: str = "state.json"):
        self.output_dir = Path(output_dir).expanduser()
        self.work_log_path = self.output_dir / work_log
        self.state_path = self.output_dir / state_file
        self.session_log = []
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

        self._terminal = None
        try:
            from hermes_tools import terminal
            self._terminal = terminal
            self.log("Hermes tools available. Using native execution.")
        except ImportError:
            self.log("Hermes tools not available. Using subprocess fallback.")

    def log(self, message: str) -> None:
        timestamp = datetime.utcnow().isoformat()
        entry = f"[{timestamp}] {message}"
        with self._lock:
            self.session_log.append(entry)
        print(entry, flush=True)

    def save_state(self, state: dict) -> None:
        with self._lock:
            self.state_path.write_text(json.dumps(state, indent=2))

    def load_state(self) -> Optional[dict]:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text())
            except json.JSONDecodeError:
                self.log("WARNING: state.json corrupted. Starting fresh.")
        return None

    def run_shell(self, cmd: str, timeout: int = 300, background: bool = False) -> dict:
        if self._terminal:
            self.log(f"Executing: {cmd[:120]}...")
            result = self._terminal(cmd, timeout=timeout)
            return {
                "stdout": result.get("output", ""),
                "exit_code": result.get("exit_code", -1),
                "error": result.get("error", None),
            }
        else:
            self.log(f"Subprocess: {cmd[:120]}...")
            if background:
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                return {
                    "stdout": "",
                    "exit_code": None,
                    "error": None,
                    "proc": proc,
                    "pid": proc.pid,
                }
            else:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
                return {
                    "stdout": result.stdout,
                    "exit_code": result.returncode,
                    "error": result.stderr if result.returncode != 0 else None,
                }

    def wait_for_file(self, path: Path, timeout: int = 300, poll_interval: int = 2) -> bool:
        self.log(f"Waiting for: {path}")
        start = time.time()
        while time.time() - start < timeout:
            if path.exists() and path.stat().st_size > 0:
                self.log(f"File ready: {path} ({path.stat().st_size} bytes)")
                return True
            time.sleep(poll_interval)
        self.log(f"TIMEOUT: File not found after {timeout}s: {path}")
        return False

    def summarize_file(self, path: Path, max_lines: int = 100) -> str:
        if not path.exists():
            return f"[File not found: {path}]"
        lines = path.read_text().splitlines()
        total = len(lines)
        if total <= max_lines:
            return path.read_text()
        # Return first 30, ellipsis, last 30
        head = "\n".join(lines[:30])
        tail = "\n".join(lines[-30:])
        return f"{head}\n\n... [{total - 60} lines omitted] ...\n\n{tail}"

    def get_model_for_stage(self, stage_id: str, attempt: int = 0):
        config = ROUTING_TABLE.get(stage_id, ROUTING_TABLE["implement"])
        keys = ["primary", "secondary", "tertiary"]
        key = keys[min(attempt, len(keys) - 1)]
        selected = config[key]
        self.log(f"Stage '{stage_id}' -> {selected['provider']}/{selected['model']} (tier={key})")
        return selected["model"], selected["provider"]

    def run_stage(self, stage_id: str, prompt: str, model: str, provider: str, output_file: Path, background: bool = False) -> dict:
        stage_name = stage_id.replace("_", " ").title()
        guardrails = STAGE_GUARDRAILS.get(stage_id, "")

        full_prompt = f"""[FABLE STAGE: {stage_name}]

{prompt}

{guardrails}

INSTRUCTIONS:
- This is stage {stage_id} of a fable execution.
- Produce a concrete, verifiable output.
- Save your complete output to the file: {output_file}
- Return only a brief status message.
"""

        escaped_prompt = full_prompt.replace("'", "'\"'\"'")
        cmd = f"hermes chat -q '{escaped_prompt}' -m {model} --provider {provider} -Q -t web,terminal,file"

        self.log(f"\n{'='*60}")
        self.log(f"STAGE: {stage_name} ({stage_id})")
        self.log(f"MODEL: {provider}/{model}")
        self.log(f"OUTPUT: {output_file}")
        self.log(f"MODE: {'BACKGROUND' if background else 'FOREGROUND'}")
        self.log(f"{'='*60}")

        result = self.run_shell(cmd, timeout=300, background=background)

        if background:
            return {
                "stage": stage_id,
                "model": model,
                "provider": provider,
                "output_file": str(output_file),
                "status": "background",
                "pid": result.get("pid"),
                "proc": result.get("proc"),
            }

        file_ready = self.wait_for_file(output_file, timeout=300)

        return {
            "stage": stage_id,
            "model": model,
            "provider": provider,
            "output_file": str(output_file),
            "status": "completed" if file_ready else "failed",
            "stdout_preview": result.get("stdout", "")[:500],
            "exit_code": result.get("exit_code", -1),
        }

    # =====================================================================
    # DYNAMIC STAGE PLANNER (Stage 0)
    # =====================================================================

    def plan_stages(self, task: str) -> List[Dict[str, Any]]:
        self.log("\n--- STAGE 0: DYNAMIC PLANNING ---")
        model, provider = self.get_model_for_stage("plan")

        prompt = f"""You are the Fable Orchestrator's planning engine.

TASK: {task}

Analyze this task and decide:
1. Which stages are needed from: research, plan, implement, verify, critique, consolidate
2. Which stages can run in parallel (no dependencies)
3. Which stages depend on others
4. What the output file should be for each stage

Some tasks need all 6 stages. Others might skip research (if user provided data) or skip plan (if the task is purely implementation). Be minimal but thorough.

Respond ONLY with a JSON object in this exact format:
{{
  "stages": [
    {{"id": "research", "name": "Research", "parallel": false, "depends_on": [], "output": "stage1_research.md"}},
    {{"id": "plan", "name": "Plan", "parallel": true, "depends_on": [], "output": "stage2_plan.md"}},
    {{"id": "implement", "name": "Implementation", "parallel": false, "depends_on": ["research", "plan"], "output": "stage3_implement.md"}},
    {{"id": "verify", "name": "Verification", "parallel": false, "depends_on": ["implement"], "output": "stage4_verify.md"}},
    {{"id": "critique", "name": "Critique", "parallel": false, "depends_on": ["implement", "verify"], "output": "stage5_critique.md"}},
    {{"id": "consolidate", "name": "Consolidation", "parallel": false, "depends_on": ["research", "plan", "implement", "verify", "critique"], "output": "FINAL.md"}}
  ],
  "rationale": "Brief explanation of why this stage graph was chosen"
}}

Rules:
- "parallel": true means this stage has no dependencies and can run concurrently with other parallel stages
- "depends_on": list of stage ids that must complete before this stage starts
- Output filenames must be unique
- Keep the default 6-stage loop unless the task clearly doesn't need a stage
"""

        escaped = prompt.replace("'", "'\"'\"'")
        cmd = f"hermes chat -q '{escaped}' -m {model} --provider {provider} -Q"
        result = self.run_shell(cmd, timeout=300)

        try:
            text = result.get("stdout", "")
            # Extract JSON from possible markdown fences
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            plan = json.loads(text.strip())
            stages = plan.get("stages", [])
            self.log(f"Planner chose {len(stages)} stages: {[s['id'] for s in stages]}")
            self.log(f"Rationale: {plan.get('rationale', 'N/A')}")
            return stages
        except Exception as e:
            self.log(f"Planner failed ({e}). Falling back to default 6-stage loop.")
            return [
                {"id": "research", "name": "Research", "parallel": False, "depends_on": [], "output": "stage1_research.md"},
                {"id": "plan", "name": "Plan", "parallel": False, "depends_on": [], "output": "stage2_plan.md"},
                {"id": "implement", "name": "Implementation", "parallel": False, "depends_on": ["research", "plan"], "output": "stage3_implement.md"},
                {"id": "verify", "name": "Verification", "parallel": False, "depends_on": ["implement"], "output": "stage4_verify.md"},
                {"id": "critique", "name": "Critique", "parallel": False, "depends_on": ["implement", "verify"], "output": "stage5_critique.md"},
                {"id": "consolidate", "name": "Consolidation", "parallel": False, "depends_on": ["research", "plan", "implement", "verify", "critique"], "output": "FINAL.md"},
            ]

    # =====================================================================
    # EXECUTE WITH PARALLELISM AND CHECKPOINTING
    # =====================================================================

    def execute(self, task: str, domain: str = "research") -> dict:
        self.log(f"FABLE ORCHESTRATOR v4 START")
        self.log(f"Task: {task}")
        self.log(f"Domain: {domain}")
        self.log(f"Output: {self.output_dir}")

        # Load or initialize state
        state = self.load_state()
        if state is None:
            state = {
                "task": task,
                "domain": domain,
                "started": datetime.utcnow().isoformat(),
                "completed_stages": {},
                "failed_stages": {},
                "stage_results": {},
            }
            self.save_state(state)

        # Stage 0: Dynamic planning (only if not already planned)
        if "stage_plan" not in state:
            stages = self.plan_stages(task)
            state["stage_plan"] = stages
            self.save_state(state)
        else:
            stages = state["stage_plan"]
            self.log(f"Resuming with existing plan: {[s['id'] for s in stages]}")

        out = self.output_dir
        all_results = []

        # Build dependency graph
        stage_map = {s["id"]: s for s in stages}
        completed = set(state["completed_stages"].keys())
        failed = set(state["failed_stages"].keys())

        # Main execution loop
        while len(completed) < len(stages):
            # Find stages that are ready (all dependencies met)
            ready = []
            for s in stages:
                sid = s["id"]
                if sid in completed or sid in failed:
                    continue
                deps = s.get("depends_on", [])
                if all(d in completed for d in deps):
                    ready.append(s)

            if not ready:
                if failed:
                    self.log(f"DEADLOCK: {len(failed)} stages failed and block remaining stages.")
                    break
                self.log("DEADLOCK: No stages ready but not all complete. Breaking.")
                break

            # Separate parallel-ready from sequential
            parallel_ready = [s for s in ready if s.get("parallel", False)]
            sequential_ready = [s for s in ready if not s.get("parallel", False)]

            # Run parallel stages concurrently
            if parallel_ready:
                self.log(f"\n>>> PARALLEL BATCH: {[s['id'] for s in parallel_ready]}")
                threads = []
                thread_results = {}

                def run_parallel_stage(stage):
                    sid = stage["id"]
                    model, provider = self.get_model_for_stage(sid)
                    output_file = out / stage["output"]

                    # Build context: summarize dependencies
                    deps = stage.get("depends_on", [])
                    context_parts = [f"Base task: {task}"]
                    for dep in deps:
                        dep_file = out / stage_map[dep]["output"]
                        context_parts.append(f"\n--- {dep} summary ---\n{self.summarize_file(dep_file)}")
                    context = "\n".join(context_parts)

                    result = self.run_stage(sid, context, model, provider, output_file)
                    thread_results[sid] = result

                for stage in parallel_ready:
                    t = threading.Thread(target=run_parallel_stage, args=(stage,))
                    threads.append(t)
                    t.start()

                for t in threads:
                    t.join()

                for sid, result in thread_results.items():
                    all_results.append(result)
                    if result["status"] == "completed":
                        completed.add(sid)
                        state["completed_stages"][sid] = result
                    else:
                        failed.add(sid)
                        state["failed_stages"][sid] = result
                        # Retry with fallback model
                        self.log(f"Stage {sid} failed. Retrying with fallback model...")
                        stage = stage_map[sid]
                        model, provider = self.get_model_for_stage(sid, attempt=1)
                        output_file = out / stage["output"]
                        context = f"Base task: {task}\n(Fallback attempt after initial failure)"
                        retry_result = self.run_stage(sid, context, model, provider, output_file)
                        all_results.append(retry_result)
                        if retry_result["status"] == "completed":
                            completed.add(sid)
                            state["completed_stages"][sid] = retry_result
                            failed.discard(sid)
                            del state["failed_stages"][sid]
                    state["stage_results"][sid] = result
                    self.save_state(state)

            # Run one sequential stage
            if sequential_ready:
                stage = sequential_ready[0]
                sid = stage["id"]
                self.log(f"\n>>> SEQUENTIAL: {sid}")
                model, provider = self.get_model_for_stage(sid)
                output_file = out / stage["output"]

                # Build context
                deps = stage.get("depends_on", [])
                context_parts = [f"Base task: {task}"]
                for dep in deps:
                    dep_file = out / stage_map[dep]["output"]
                    context_parts.append(f"\n--- {dep} summary ---\n{self.summarize_file(dep_file)}")
                context = "\n".join(context_parts)

                result = self.run_stage(sid, context, model, provider, output_file)
                all_results.append(result)
                if result["status"] == "completed":
                    completed.add(sid)
                    state["completed_stages"][sid] = result
                else:
                    failed.add(sid)
                    state["failed_stages"][sid] = result
                    # Retry with fallback
                    self.log(f"Stage {sid} failed. Retrying with fallback model...")
                    model, provider = self.get_model_for_stage(sid, attempt=1)
                    retry_result = self.run_stage(sid, context, model, provider, output_file)
                    all_results.append(retry_result)
                    if retry_result["status"] == "completed":
                        completed.add(sid)
                        state["completed_stages"][sid] = retry_result
                        failed.discard(sid)
                        del state["failed_stages"][sid]
                state["stage_results"][sid] = result
                self.save_state(state)

        # Final status
        state["finished"] = datetime.utcnow().isoformat()
        state["all_completed"] = len(completed) == len(stages)
        self.save_state(state)

        self.log("\nFABLE ORCHESTRATOR v4 COMPLETE")
        self.log(f"Completed: {len(completed)}/{len(stages)} stages")
        self.log(f"Failed: {len(failed)} stages")

        # Write work log
        header = f"# Fable Orchestrator v4 Work Log\n\nSession: {datetime.utcnow().isoformat()}\n\n"
        body = "\n".join(self.session_log)
        self.work_log_path.write_text(header + body + "\n")

        return {
            "status": "complete" if len(failed) == 0 else "partial",
            "task": task,
            "domain": domain,
            "output_dir": str(self.output_dir),
            "stages": all_results,
            "work_log": str(self.work_log_path),
            "state": str(self.state_path),
            "completed_count": len(completed),
            "failed_count": len(failed),
        }

# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Fable Orchestrator v4 — Dynamic parallel staged execution")
    parser.add_argument("--task", required=True, help="The task to execute")
    parser.add_argument("--domain", default="research", choices=["software", "research", "data", "writing", "long-running"])
    parser.add_argument("--output-dir", default="~/.hermes/fable-outputs", help="Directory for outputs")
    parser.add_argument("--resume", action="store_true", help="Resume from existing state.json")

    args = parser.parse_args()
    orchestrator = FableOrchestrator(output_dir=args.output_dir)
    result = orchestrator.execute(task=args.task, domain=args.domain)

    print("\n\n=== FINAL RESULT ===")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
