"""Tests for the SQLite state manager."""

import tempfile
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from fable_engine.state import StateManager


def test_create_and_get_task():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    sm = StateManager(db_path)
    plan = {
        "stages": [
            {"id": "research", "stage_name": "Research", "parallel": False, "depends_on": [], "output": "stage1_research.md"},
            {"id": "implement", "stage_name": "Implementation", "parallel": False, "depends_on": ["research"], "output": "stage2_implement.md"},
        ]
    }
    tid = sm.create_task("Test task", "Test clarified", plan)
    assert tid.startswith("task_")
    task = sm.get_task(tid)
    assert task["id"] == tid
    assert task["status"] == "running"
    assert task["description"] == "Test task"
    assert task["clarified_description"] == "Test clarified"
    stages = sm.get_stages(tid)
    assert len(stages) == 2
    assert stages[0]["id"] == "research"
    assert stages[1]["id"] == "implement"
    Path(db_path).unlink()


def test_stage_status_update():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    sm = StateManager(db_path)
    plan = {"stages": [{"id": "test", "stage_name": "Test", "parallel": False, "depends_on": [], "output": "test.md"}]}
    tid = sm.create_task("Test", "Test", plan)
    sm.update_stage_status("test", "completed", "gemini", "google", "", "Done")
    stages = sm.get_stages(tid)
    assert stages[0]["status"] == "completed"
    assert stages[0]["model_used"] == "gemini"
    Path(db_path).unlink()


def test_work_log():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    sm = StateManager(db_path)
    plan = {"stages": []}
    tid = sm.create_task("Test", "Test", plan)
    sm.add_work_log(tid, decisions="Started", failures="", open_items="Wait")
    logs = sm.get_work_logs(tid)
    assert len(logs) == 1
    assert logs[0]["decisions"] == "Started"
    assert logs[0]["open_items"] == "Wait"
    Path(db_path).unlink()


def test_task_status_lifecycle():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    sm = StateManager(db_path)
    plan = {"stages": []}
    tid = sm.create_task("Test", "Test", plan)
    sm.update_task_status(tid, "paused")
    task = sm.get_task(tid)
    assert task["status"] == "paused"
    sm.update_task_status(tid, "running")
    task = sm.get_task(tid)
    assert task["status"] == "running"
    sm.mark_task_complete(tid, "/tmp/final.md")
    task = sm.get_task(tid)
    assert task["status"] == "completed"
    assert task["final_output_path"] == "/tmp/final.md"
    Path(db_path).unlink()
