#!/usr/bin/env python3
"""
Fable Daemon — Long-horizon async execution for Hermes Agent.

Run as a cron job for true asynchronous execution:
    */15 * * * * python3 /path/to/fable_daemon.py --tick

Commands:
    --start --task "Your task"    Start a new task and run first tick
    --tick                        Process one tick of all running tasks
    --status                      Show all tasks
    --resume <task_id>            Resume a specific task
    --tail <task_id>              Follow a task's work log
"""

import argparse
import sys
from pathlib import Path

# Add fable_engine parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fable_engine.core import FableEngine


def main():
    parser = argparse.ArgumentParser(description="Fable Daemon v1.0")
    parser.add_argument("--task", help="Task description")
    parser.add_argument("--start", action="store_true", help="Start a new task")
    parser.add_argument("--tick", action="store_true", help="Process one tick of all running tasks")
    parser.add_argument("--status", action="store_true", help="Show status of all tasks")
    parser.add_argument("--resume", help="Resume a specific task ID")
    parser.add_argument("--tail", help="Follow a task's work log")
    parser.add_argument("--output-dir", default="~/.hermes/fable-outputs", help="Output directory")
    parser.add_argument("--state-db", default="~/.hermes/fable_state.db", help="State database path")
    parser.add_argument("--max-parallel", type=int, default=3, help="Max parallel stages")
    args = parser.parse_args()

    engine = FableEngine(
        state_db=args.state_db,
        output_root=args.output_dir,
        max_parallel=args.max_parallel,
    )

    if args.start and args.task:
        task_id = engine.start_task(args.task)
        print(f"[FABLE] Task started: {task_id}")
        result = engine.execute_tick(task_id)
        print(f"[FABLE] Tick result: {result['status']}")
    elif args.tick:
        results = engine.process_all_running_tasks()
        print(f"[FABLE] Processed {len(results)} running tasks")
        for r in results:
            tid = r.get("task_id", "?")
            status = r.get("status", "?")
            print(f"  - {tid}: {status}")
    elif args.status:
        status = engine.show_status()
        print(f"[FABLE] Tasks: {status['total']} total, {status['running']} running, {status['completed']} completed, {status['failed']} failed")
        for t in status["tasks"][:10]:
            print(f"  {t['id']}: {t['status']} | {t['description'][:60]}...")
    elif args.resume:
        result = engine.resume_task(args.resume)
        print(f"[FABLE] Resume {args.resume}: {result.get('status', result.get('error', 'unknown'))}")
    elif args.tail:
        logs = engine.state.get_work_logs(args.tail)
        for log in logs[:5]:
            print(f"[{log['session_date']}] Decisions: {log['decisions'][:80]}")
            if log['failures']:
                print(f"  Failures: {log['failures'][:80]}")
            if log['open_items']:
                print(f"  Open: {log['open_items'][:80]}")
    else:
        print("Use --start, --tick, --status, --resume, or --tail")
        sys.exit(1)


if __name__ == "__main__":
    main()
