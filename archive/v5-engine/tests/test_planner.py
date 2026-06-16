"""Tests for the dynamic stage planner."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fable_engine.planner import StagePlanner


def test_get_model_for_stage():
    planner = StagePlanner(max_parallel=3)
    model, provider = planner.get_model_for_stage("research")
    assert model in ["deepseek-v4-flash", "gemini-2.5-flash-lite", "nemotron"]
    assert provider in ["opencode-go", "google", "openrouter"]


def test_get_model_fallback():
    planner = StagePlanner(max_parallel=3)
    model, provider = planner.get_model_for_stage("research", attempt=1)
    assert "gemini" in model
    model, provider = planner.get_model_for_stage("research", attempt=2)
    assert "nemotron" in model


def test_plan_stages_small_task():
    planner = StagePlanner(max_parallel=3)
    result = planner.plan_stages("Write a one sentence summary of Fable mode")
    stages = result.get("stages", [])
    ids = [s["id"] for s in stages]
    # The planner returns whatever stages it determines appropriate
    assert len(ids) > 0
    assert "consolidate" in ids or "implement" in ids


def test_plan_stages_complex_task():
    planner = StagePlanner(max_parallel=3)
    result = planner.plan_stages("Build a full-stack web application with user authentication, payment processing, and real-time chat")
    stages = result.get("stages", [])
    ids = [s["id"] for s in stages]
    # Complex tasks should have all stages
    assert "plan" in ids
    assert "critique" in ids


def test_get_ready_stages():
    planner = StagePlanner(max_parallel=3)
    stages = [
        {"id": "a", "parallel": False, "depends_on": [], "status": "pending"},
        {"id": "b", "parallel": False, "depends_on": ["a"], "status": "pending"},
        {"id": "c", "parallel": True, "depends_on": [], "status": "pending"},
    ]
    ready = planner.get_ready_stages(stages, completed=set())
    assert len(ready) == 2
    assert ready[0]["id"] in ["a", "c"]


def test_is_complete():
    planner = StagePlanner(max_parallel=3)
    stages = [
        {"id": "a", "status": "completed"},
        {"id": "b", "status": "completed"},
    ]
    assert planner.is_complete(stages) is True
    stages = [
        {"id": "a", "status": "completed"},
        {"id": "b", "status": "pending"},
    ]
    assert planner.is_complete(stages) is False
