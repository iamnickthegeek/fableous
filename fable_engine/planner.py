"""Dynamic stage planner and DAG executor for Fable Engine."""

import json
import subprocess
from typing import Any, Dict, List, Optional

DEFAULT_STAGES = [
    {"id": "research", "name": "Research", "parallel": True, "depends_on": [], "output": "stage1_research.md"},
    {"id": "plan", "name": "Plan", "parallel": True, "depends_on": [], "output": "stage2_plan.md"},
    {"id": "implement", "name": "Implementation", "parallel": False, "depends_on": ["research", "plan"], "output": "stage3_implement.md"},
    {"id": "verify", "name": "Verification", "parallel": False, "depends_on": ["implement"], "output": "stage4_verify.md"},
    {"id": "critique", "name": "Critique", "parallel": False, "depends_on": ["implement", "verify"], "output": "stage5_critique.md"},
    {"id": "consolidate", "name": "Consolidation", "parallel": False, "depends_on": ["research", "plan", "implement", "verify", "critique"], "output": "FINAL.md"},
]

ROUTING_TABLE = {
    "research": {"primary": {"model": "deepseek-v4-flash", "provider": "opencode-go"}, "secondary": {"model": "gemini-2.5-flash-lite", "provider": "google"}, "tertiary": {"model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "provider": "openrouter"}},
    "plan": {"primary": {"model": "glm-5.1", "provider": "opencode-go"}, "secondary": {"model": "gemini-2.5-pro", "provider": "google"}, "tertiary": {"model": "deepseek-v4-pro", "provider": "opencode-go"}},
    "implement": {"primary": {"model": "kimi-k2.7-code", "provider": "opencode-go"}, "secondary": {"model": "kimi-k2.6", "provider": "opencode-go"}, "tertiary": {"model": "gemini-2.5-pro", "provider": "google"}},
    "verify": {"primary": {"model": "deepseek-v4-pro", "provider": "opencode-go"}, "secondary": {"model": "gemini-2.5-pro", "provider": "google"}, "tertiary": {"model": "kimi-k2.6", "provider": "opencode-go"}},
    "critique": {"primary": {"model": "glm-5.1", "provider": "opencode-go"}, "secondary": {"model": "gemini-2.5-pro", "provider": "google"}, "tertiary": {"model": "kimi-k2.6", "provider": "opencode-go"}},
    "consolidate": {"primary": {"model": "deepseek-v4-pro", "provider": "opencode-go"}, "secondary": {"model": "glm-5.1", "provider": "opencode-go"}, "tertiary": {"model": "gemini-2.5-pro", "provider": "google"}},
}

STAGE_GUARDRAILS = {
    "research": "GUARDRAILS:\n- Cite exact source and date for percentages/benchmarks.\n- Lead with caveats.\n- Do not present vendor claims as verified facts.\n- Flag pricing volatility.",
    "plan": "GUARDRAILS:\n- Segment audience into at least 3 tiers.\n- Map every recommendation to a tier.\n- Include 'Methodology & Caveats'.\n- Flag predetermined conclusions.",
    "implement": "GUARDRAILS:\n- Every claim traces to a source.\n- Unsupported claims flagged as unverified.\n- State 'described by vendor, not independently verified' where applicable.\n- No predetermined conclusion in the final line.",
    "verify": "GUARDRAILS:\n- Check internal consistency across stages.\n- Flag hallucination data.\n- Verify URLs are live.\n- Flag pricing volatility.\n- List factual errors with corrections.\n- Output 'Corrections to apply'.",
    "critique": "GUARDRAILS:\n- Check for confirmation bias.\n- Verify competitor selection is justified.\n- Assess audience segmentation.\n- Check if verification errors were propagated.\n- Identify 3+ concrete weaknesses.\n- Output 'Priority fixes' ranked list.",
    "consolidate": "GUARDRAILS:\n- Read all prior stages.\n- Apply every verification correction.\n- Address every critique fix.\n- Remove predetermined conclusions.\n- Add 'Version & Caveats' header.\n- This is the ONLY published version.",
}


class StagePlanner:
    """Plans stages and executes them respecting a dependency DAG."""

    def __init__(self, max_parallel: int = 3):
        self.max_parallel = max_parallel

    def plan_stages(self, task: str, model: str = "glm-5.1", provider: str = "opencode-go") -> Dict[str, Any]:
        """Use an LLM to dynamically plan the stage DAG for a task."""
        prompt = f"""You are the Fable Orchestrator planning engine.

TASK: {task}

Analyze this task and decide which stages are needed from: research, plan, implement, verify, critique, consolidate.
Some tasks need all 6. Others skip research (user provided data) or skip plan (pure implementation). Be minimal but thorough.

Respond ONLY with JSON:
{{
  "stages": [
    {{"id": "research", "name": "Research", "parallel": true, "depends_on": [], "output": "stage1_research.md"}},
    {{"id": "plan", "name": "Plan", "parallel": true, "depends_on": [], "output": "stage2_plan.md"}},
    {{"id": "implement", "name": "Implementation", "parallel": false, "depends_on": ["research", "plan"], "output": "stage3_implement.md"}},
    {{"id": "verify", "name": "Verification", "parallel": false, "depends_on": ["implement"], "output": "stage4_verify.md"}},
    {{"id": "critique", "name": "Critique", "parallel": false, "depends_on": ["implement", "verify"], "output": "stage5_critique.md"}},
    {{"id": "consolidate", "name": "Consolidation", "parallel": false, "depends_on": ["research", "plan", "implement", "verify", "critique"], "output": "FINAL.md"}}
  ],
  "rationale": "Brief explanation"
}}

Rules:
- parallel: true means no dependencies and can run concurrently
- depends_on: list of stage ids that must complete first
- Output filenames must be unique
- Keep default 6-stage loop unless task clearly doesn't need a stage
"""
        escaped = prompt.replace("'", "'\"'\"'")
        cmd = f"hermes chat -q '{escaped}' -m {model} --provider {provider} -Q"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            text = result.stdout
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            plan = json.loads(text.strip())
            return plan
        except Exception:
            return {"stages": DEFAULT_STAGES, "rationale": "Fallback to default 6-stage loop due to planner failure"}

    def get_ready_stages(self, stages: List[Dict[str, Any]], completed: set) -> List[Dict[str, Any]]:
        return [s for s in stages if s["status"] == "pending" and all(d in completed for d in s.get("depends_on", []))]

    def is_complete(self, stages: List[Dict[str, Any]]) -> bool:
        return all(s["status"] == "completed" for s in stages)

    def get_model_for_stage(self, stage_id: str, attempt: int = 0) -> tuple:
        config = ROUTING_TABLE.get(stage_id, ROUTING_TABLE["implement"])
        keys = ["primary", "secondary", "tertiary"]
        key = keys[min(attempt, len(keys) - 1)]
        selected = config[key]
        return selected["model"], selected["provider"]

    def get_guardrails(self, stage_id: str) -> str:
        return STAGE_GUARDRAILS.get(stage_id, "")
