"""Proactive questioner that asks clarifying questions before starting a task."""

import json
import subprocess
from typing import Any, Dict


class ProactiveQuestioner:
    """Asks clarifying questions before task decomposition."""

    def __init__(self, model: str = "glm-5.1", provider: str = "opencode-go"):
        self.model = model
        self.provider = provider

    def clarify(self, task: str) -> Dict[str, Any]:
        """Ask clarifying questions and return the enriched task description."""
        prompt = f"""You are the Fable Orchestrator intake system.

A user has submitted this task:
"{task}"

Before we decompose and execute this task, ask 3-5 clarifying questions that would significantly improve the result. Then answer them with sensible defaults based on common professional standards.

Respond ONLY with JSON:
{{
  "questions": [
    "Question 1?",
    "Question 2?",
    "Question 3?"
  ],
  "answers": [
    "Answer 1 with default",
    "Answer 2 with default",
    "Answer 3 with default"
  ],
  "clarified_task": "Original task with answers incorporated into a single enriched description",
  "audience_tiers": ["tier 1", "tier 2", "tier 3"],
  "output_format": "markdown|code|analysis|other",
  "estimated_complexity": "low|medium|high"
}}
"""
        escaped = prompt.replace("'", "'\"'\"'")
        cmd = f"hermes chat -q '{escaped}' -m {self.model} --provider {self.provider} -Q"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            text = result.stdout
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            data = json.loads(text.strip())
            return data
        except Exception:
            return {
                "questions": [],
                "answers": [],
                "clarified_task": task,
                "audience_tiers": ["general"],
                "output_format": "markdown",
                "estimated_complexity": "medium",
            }
