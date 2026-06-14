"""SQLite state manager for Fable Engine. Provides persistent task/stage/subagent state."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class StateManager:
    """Persistent SQLite-backed state for tasks, stages, and checkpoints."""

    def __init__(self, db_path: str = "~/.hermes/fable_state.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    clarified_description TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    config TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    completed_at TEXT,
                    final_output_path TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stages (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    stage_name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    depends_on TEXT,
                    parallel INTEGER DEFAULT 0,
                    output_file TEXT,
                    model_used TEXT,
                    provider_used TEXT,
                    result_summary TEXT,
                    error_log TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subagents (
                    id TEXT PRIMARY KEY,
                    stage_id TEXT NOT NULL,
                    pid INTEGER,
                    model TEXT,
                    provider TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    output_file TEXT,
                    stdout TEXT,
                    stderr TEXT,
                    exit_code INTEGER,
                    started_at TEXT,
                    completed_at TEXT,
                    FOREIGN KEY (stage_id) REFERENCES stages(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    stage_id TEXT,
                    checkpoint_data TEXT NOT NULL,
                    created_at TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS work_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    session_date TEXT,
                    decisions TEXT,
                    failures TEXT,
                    open_items TEXT,
                    created_at TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)
            conn.commit()

    def create_task(self, description: str, clarified: str, dag: Dict[str, Any], config: Optional[Dict] = None) -> str:
        task_id = f"task_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO tasks (id, description, clarified_description, status, config, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (task_id, description, clarified, "running", json.dumps(config or {}), now, now)
            )
            for stage in dag.get("stages", []):
                stage_name = stage.get("name", stage.get("stage_name", stage["id"]))
                conn.execute(
                    "INSERT INTO stages (id, task_id, stage_name, status, depends_on, parallel, output_file) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (stage["id"], task_id, stage_name, "pending", json.dumps(stage.get("depends_on", [])), 1 if stage.get("parallel", False) else 0, stage.get("output"))
                )
            conn.commit()
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not row:
                return None
            return dict(row)

    def get_stages(self, task_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM stages WHERE task_id = ?", (task_id,)).fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d["depends_on"] = json.loads(d["depends_on"] or "[]")
                d["parallel"] = bool(d["parallel"])
                result.append(d)
            return result

    def get_ready_stages(self, task_id: str) -> List[Dict[str, Any]]:
        stages = self.get_stages(task_id)
        completed = {s["id"] for s in stages if s["status"] == "completed"}
        return [s for s in stages if s["status"] == "pending" and all(d in completed for d in s["depends_on"])]

    def update_stage_status(self, stage_id: str, status: str, model: str = "", provider: str = "", error: str = "", summary: str = "") -> None:
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "UPDATE stages SET status = ?, model_used = ?, provider_used = ?, error_log = ?, result_summary = ?, completed_at = ? WHERE id = ?",
                (status, model, provider, error, summary, now if status in ("completed", "failed") else None, stage_id)
            )
            conn.commit()

    def save_checkpoint(self, task_id: str, stage_id: str, data: Dict[str, Any]) -> None:
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO checkpoints (task_id, stage_id, checkpoint_data, created_at) VALUES (?, ?, ?, ?)",
                (task_id, stage_id, json.dumps(data), now)
            )
            conn.commit()

    def load_latest_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute(
                "SELECT checkpoint_data FROM checkpoints WHERE task_id = ? ORDER BY id DESC LIMIT 1",
                (task_id,)
            ).fetchone()
            if row:
                return json.loads(row[0])
            return None

    def add_work_log(self, task_id: str, decisions: str = "", failures: str = "", open_items: str = "") -> None:
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO work_logs (task_id, session_date, decisions, failures, open_items, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (task_id, now[:10], decisions, failures, open_items, now)
            )
            conn.commit()

    def get_work_logs(self, task_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM work_logs WHERE task_id = ? ORDER BY id DESC", (task_id,)).fetchall()
            return [dict(r) for r in rows]

    def mark_task_complete(self, task_id: str, final_output_path: str) -> None:
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "UPDATE tasks SET status = ?, completed_at = ?, updated_at = ?, final_output_path = ? WHERE id = ?",
                ("completed", now, now, final_output_path, task_id)
            )
            conn.commit()

    def update_task_status(self, task_id: str, status: str) -> None:
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?", (status, now, task_id))
            conn.commit()

    def get_running_tasks(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM tasks WHERE status = 'running' ORDER BY updated_at DESC").fetchall()
            return [dict(r) for r in rows]

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]
