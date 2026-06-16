#!/usr/bin/env python3
"""
Fable Orchestrator v3 — Portable Custom Tool

Programmatic fable-mode with built-in guardrails:
- Stage 6 consolidation (propagates verification fixes)
- Anti-hallucination prompts
- Audience-segmentation enforcement
- Bias-check and pricing-volatility flags

Usage:
    python3 fable_orchestrator.py --task "Your task" --output-dir ./output

Author: Hermes Agent / Nick Smith (Point Clear Advisory)
License: MIT
"""

import argparse
import json
import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

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

STAGES = [
    {"id": "research",    "name": "Research",         "description": "Gather sources, extract facts, identify competitors"},
    {"id": "plan",        "name": "Plan",             "description": "Structure the work, define comparison dimensions"},
    {"id": "implement",   "name": "Implementation",   "description": "Draft the deliverable (code, copy, analysis)"},
    {"id": "verify",      "name": "Verification",     "description": "Run failable checks: trace claims, verify URLs, test builds"},
    {"id": "critique",    "name": "Critique",         "description": "Independent review by a different model family"},
    {"id": "consolidate", "name": "Consolidation",    "description": "Produce final corrected version incorporating all fixes"},
]

# =============================================================================
# PROMPT GUARDRAILS — generic, applied to every run
# =============================================================================

RESEARCH_GUARDRAILS = """
GUARDRAILS:
- If you cite percentages, rates, or benchmarks, label the exact source and date.
- Lead with caveats before specific numbers. If data is contested, say so.
- Do not present vendor claims as verified facts unless independently corroborated.
- Note pricing volatility: AI tool prices change frequently; flag promotional vs. stable rates.
"""

PLAN_GUARDRAILS = """
GUARDRAILS:
- Segment the audience into at least 3 tiers (solo/freelance, small agency, in-house team).
- Map every recommendation to a specific tier or use-case.
- Include a "Methodology & Caveats" section in the plan.
- Flag any predetermined conclusions; the plan must remain neutral.
"""

IMPLEMENT_GUARDRAILS = """
GUARDRAILS:
- Write the deliverable as if the reader will make purchasing decisions from it.
- Every claim must trace to a source; unsupported claims must be flagged as unverified.
- If a feature was not hands-on tested, explicitly state "described by vendor, not independently verified."
- The final line must not reveal a predetermined conclusion unless the analysis genuinely arrived there.
"""

VERIFY_GUARDRAILS = """
GUARDRAILS:
- Check for internal consistency across all prior stages.
- Flag any hallucination data that shifts between stages or uses different benchmarks.
- Verify URLs are live (HTTP 200) and pricing matches current vendor pages.
- Flag pricing volatility and promotional vs. stable rates.
- List all factual errors with exact corrections.
- Output a "Corrections to apply" section.
"""

CRITIQUE_GUARDRAILS = """
GUARDRAILS:
- Check for confirmation bias: was the conclusion predetermined?
- Verify competitor selection is justified; flag unexplained exclusions.
- Assess whether the audience segmentation is adequate.
- Check if verification errors were propagated back or ignored.
- Identify 3+ concrete weaknesses.
- Output a "Priority fixes" ranked list.
"""

CONSOLIDATE_GUARDRAILS = """
GUARDRAILS:
- Read all prior stage outputs (research, plan, implement, verify, critique).
- Produce a single, canonical final deliverable.
- Apply every correction from the verification stage.
- Address every priority fix from the critique stage.
- Remove any predetermined conclusions unless independently justified.
- Add a "Version & Caveats" header stating: (a) what was desk-researched, (b) what was hands-on tested, (c) pricing recheck date.
- This is the ONLY published version; all prior stages are working drafts.
"""

STAGE_GUARDRAILS = {
    "research":    RESEARCH_GUARDRAILS,
    "plan":        PLAN_GUARDRAILS,
    "implement":   IMPLEMENT_GUARDRAILS,
    "verify":      VERIFY_GUARDRAILS,
    "critique":    CRITIQUE_GUARDRAILS,
    "consolidate": CONSOLIDATE_GUARDRAILS,
}

# =============================================================================
# ORCHESTRATOR
# =============================================================================

class FableOrchestrator:
    def __init__(self, output_dir: str, work_log: str = "WORK_LOG.md"):
        self.output_dir = Path(output_dir).expanduser()
        self.work_log_path = self.output_dir / work_log
        self.session_log = []
        self.output_dir.mkdir(parents=True, exist_ok=True)

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
        self.session_log.append(entry)
        print(entry, flush=True)

    def run_shell(self, cmd: str, timeout: int = 300) -> dict:
        if self._terminal:
            self.log(f"Executing: {cmd[:100]}...")
            result = self._terminal(cmd, timeout=timeout)
            return {
                "stdout": result.get("output", ""),
                "exit_code": result.get("exit_code", -1),
                "error": result.get("error", None),
            }
        else:
            self.log(f"Subprocess: {cmd[:100]}...")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            return {
                "stdout": result.stdout,
                "exit_code": result.returncode,
                "error": result.stderr if result.returncode != 0 else None,
            }

    def wait_for_file(self, path: Path, timeout: int = 300) -> bool:
        self.log(f"Waiting for: {path}")
        start = time.time()
        while time.time() - start < timeout:
            if path.exists() and path.stat().st_size > 0:
                self.log(f"File ready: {path} ({path.stat().st_size} bytes)")
                return True
            time.sleep(2)
        self.log(f"TIMEOUT: File not found after {timeout}s: {path}")
        return False

    def get_model_for_stage(self, stage_id: str, attempt: int = 0):
        config = ROUTING_TABLE.get(stage_id, ROUTING_TABLE["implement"])
        keys = ["primary", "secondary", "tertiary"]
        key = keys[min(attempt, len(keys) - 1)]
        selected = config[key]
        self.log(f"Stage '{stage_id}' -> {selected['provider']}/{selected['model']} (tier={key})")
        return selected["model"], selected["provider"]

    def run_stage(self, stage_id: str, prompt: str, model: str, provider: str, output_file: Path) -> dict:
        stage_name = next(s["name"] for s in STAGES if s["id"] == stage_id)
        guardrails = STAGE_GUARDRAILS.get(stage_id, "")

        full_prompt = f"""[FABLE STAGE: {stage_name}]

{prompt}

{guardrails}

INSTRUCTIONS:
- This is stage {stage_id} of a 6-stage fable execution.
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
        self.log(f"{'='*60}")

        result = self.run_shell(cmd, timeout=300)
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

    def execute(self, task: str, domain: str = "research") -> dict:
        self.log(f"FABLE ORCHESTRATOR v3 START")
        self.log(f"Task: {task}")
        self.log(f"Domain: {domain}")
        self.log(f"Output: {self.output_dir}")

        results = []
        out = self.output_dir

        # Stage 1: Research
        self.log("\n--- STAGE 1: RESEARCH ---")
        model, provider = self.get_model_for_stage("research")
        results.append(self.run_stage("research", task, model, provider, out / "stage1_research.md"))

        # Stage 2: Plan
        self.log("\n--- STAGE 2: PLAN ---")
        model, provider = self.get_model_for_stage("plan")
        context = f"Base task: {task}\nRead {out}/stage1_research.md for research findings."
        results.append(self.run_stage("plan", context, model, provider, out / "stage2_plan.md"))

        # Stage 3: Implementation
        self.log("\n--- STAGE 3: IMPLEMENTATION ---")
        model, provider = self.get_model_for_stage("implement")
        context = f"Base task: {task}\nRead {out}/stage2_plan.md for the plan. Write the deliverable."
        results.append(self.run_stage("implement", context, model, provider, out / "stage3_implement.md"))

        # Stage 4: Verification
        self.log("\n--- STAGE 4: VERIFICATION ---")
        model, provider = self.get_model_for_stage("verify")
        context = f"Verify all claims in {out}/stage3_implement.md. Trace facts to sources. Verify URLs."
        results.append(self.run_stage("verify", context, model, provider, out / "stage4_verify.md"))

        # Stage 5: Critique
        self.log("\n--- STAGE 5: CRITIQUE ---")
        model, provider = self.get_model_for_stage("critique")
        context = f"Read all stage outputs in {out} and provide skeptical critique. Identify 3+ weaknesses."
        results.append(self.run_stage("critique", context, model, provider, out / "stage5_critique.md"))

        # Stage 6: Consolidation — produce final corrected version
        self.log("\n--- STAGE 6: CONSOLIDATION ---")
        model, provider = self.get_model_for_stage("consolidate")
        context = f"""Read ALL stage outputs in {out}.
- Research: {out}/stage1_research.md
- Plan: {out}/stage2_plan.md
- Implement: {out}/stage3_implement.md
- Verify: {out}/stage4_verify.md
- Critique: {out}/stage5_critique.md

Produce a single final deliverable that:
1. Applies every correction from Stage 4
2. Addresses every priority fix from Stage 5
3. Removes predetermined conclusions
4. Adds a 'Version & Caveats' header

Save the final deliverable to {out}/FINAL.md"""
        results.append(self.run_stage("consolidate", context, model, provider, out / "FINAL.md"))

        self.log("\nFABLE ORCHESTRATOR v3 COMPLETE")

        header = f"# Fable Orchestrator v3 Work Log\n\nSession: {datetime.utcnow().isoformat()}\n\n"
        body = "\n".join(self.session_log)
        self.work_log_path.write_text(header + body + "\n")

        return {
            "status": "complete",
            "task": task,
            "domain": domain,
            "output_dir": str(self.output_dir),
            "stages": results,
            "work_log": str(self.work_log_path),
            "final_deliverable": str(out / "FINAL.md"),
        }

# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Fable Orchestrator v3 — Programmatic staged execution")
    parser.add_argument("--task", required=True, help="The task to execute")
    parser.add_argument("--domain", default="research", choices=["software", "research", "data", "writing", "long-running"])
    parser.add_argument("--output-dir", default="~/.hermes/fable-outputs", help="Directory for outputs")

    args = parser.parse_args()
    orchestrator = FableOrchestrator(output_dir=args.output_dir)
    result = orchestrator.execute(task=args.task, domain=args.domain)

    print("\n\n=== FINAL RESULT ===")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
