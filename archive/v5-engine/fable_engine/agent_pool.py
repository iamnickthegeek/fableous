"""Agent pool for parallel stage execution using Hermes subprocess spawning."""

import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class AgentPool:
    """Manages parallel execution of subagents via subprocess."""

    def __init__(self, max_concurrent: int = 3, timeout: int = 300):
        self.max_concurrent = max_concurrent
        self.timeout = timeout

    def summarize_file(self, path: Path, max_lines: int = 100) -> str:
        if not path.exists():
            return f"[File not found: {path}]"
        lines = path.read_text().splitlines()
        total = len(lines)
        if total <= max_lines:
            return path.read_text()
        head = "\n".join(lines[:30])
        tail = "\n".join(lines[-30:])
        return f"{head}\n\n... [{total - 60} lines omitted] ...\n\n{tail}"

    def build_prompt(self, stage: Dict[str, Any], task: str, output_dir: Path, dependencies: Dict[str, Any]) -> str:
        stage_id = stage["id"]
        stage_name = stage.get("stage_name", stage.get("name", stage_id))
        guardrails = dependencies.get("guardrails", "")
        output_file = output_dir / stage.get("output", stage.get("output_file", f"{stage_id}.md"))

        context_parts = [f"Base task: {task}"]
        for dep_id in stage.get("depends_on", []):
            dep_file = output_dir / dependencies.get(dep_id, {}).get("output", f"{dep_id}.md")
            context_parts.append(f"\n--- {dep_id} summary ---\n{self.summarize_file(dep_file)}")
        context = "\n".join(context_parts)

        full_prompt = f"""[FABLE STAGE: {stage_name}]

{context}

{guardrails}

INSTRUCTIONS:
- This is stage {stage_id} of a fable execution.
- Produce a concrete, verifiable output.
- Save your complete output to the file: {output_file}
- Return only a brief status message.
"""
        return full_prompt

    def execute_parallel(self, stages: List[Dict[str, Any]], task: str, output_dir: Path, planner: Any) -> List[Dict[str, Any]]:
        """Execute a batch of stages in parallel, respecting max_concurrent."""
        results = []
        for i in range(0, len(stages), self.max_concurrent):
            batch = stages[i:i + self.max_concurrent]
            batch_results = self._execute_batch(batch, task, output_dir, planner)
            results.extend(batch_results)
        return results

    def _execute_batch(self, stages: List[Dict[str, Any]], task: str, output_dir: Path, planner: Any) -> List[Dict[str, Any]]:
        threads = []
        thread_results: Dict[str, Any] = {}
        lock = threading.Lock()

        def run_stage(stage):
            sid = stage["id"]
            model, provider = planner.get_model_for_stage(sid)
            output_file = output_dir / stage.get("output", f"{sid}.md")
            prompt = self.build_prompt(stage, task, output_dir, {"guardrails": planner.get_guardrails(sid)})
            escaped = prompt.replace("'", "'\"'\"'")
            cmd = f"hermes chat -q '{escaped}' -m {model} --provider {provider} -Q -t web,terminal,file"

            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=self.timeout)
                file_ready = self._wait_for_file(output_file, timeout=60)
                with lock:
                    thread_results[sid] = {
                        "stage": sid,
                        "model": model,
                        "provider": provider,
                        "output_file": str(output_file),
                        "status": "completed" if file_ready else "failed",
                        "stdout_preview": result.stdout[:500],
                        "stderr": result.stderr[:500],
                        "exit_code": result.returncode,
                    }
            except Exception as e:
                with lock:
                    thread_results[sid] = {
                        "stage": sid,
                        "model": model,
                        "provider": provider,
                        "output_file": str(output_file),
                        "status": "failed",
                        "error": str(e),
                    }

        for stage in stages:
            t = threading.Thread(target=run_stage, args=(stage,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=self.timeout + 10)

        return list(thread_results.values())

    def retry_stage(self, stage, task, output_dir, planner, attempt=1):
        """Retry a failed stage with a fallback model."""
        sid = stage["id"]
        model, provider = planner.get_model_for_stage(sid, attempt=attempt)
        output_file = output_dir / stage.get("output", stage.get("output_file", f"{sid}.md"))
        prompt = self.build_prompt(stage, task, output_dir, {"guardrails": planner.get_guardrails(sid)})
        escaped = prompt.replace("'", "'\"'\"'")
        cmd = f"hermes chat -q '{escaped}' -m {model} --provider {provider} -Q -t web,terminal,file"

        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=self.timeout)
            file_ready = self._wait_for_file(output_file, timeout=60)
            return {
                "stage": sid,
                "model": model,
                "provider": provider,
                "output_file": str(output_file),
                "status": "completed" if file_ready else "failed",
                "stdout_preview": result.stdout[:500],
                "stderr": result.stderr[:500],
                "exit_code": result.returncode,
                "retry": True,
            }
        except Exception as e:
            return {
                "stage": sid,
                "model": model,
                "provider": provider,
                "output_file": str(output_file),
                "status": "failed",
                "error": str(e),
                "retry": True,
            }

    def _wait_for_file(self, path: Path, timeout: int = 60, poll_interval: int = 2) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            if path.exists() and path.stat().st_size > 0:
                return True
            time.sleep(poll_interval)
        return False
