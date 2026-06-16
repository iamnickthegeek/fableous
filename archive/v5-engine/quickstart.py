#!/usr/bin/env python3
"""
Fable Orchestrator Quickstart

This script automates the setup for non-coders.
Run it once and it will:
1. Check prerequisites (Python, Hermes, API keys)
2. Make scripts executable
3. Run a test task
4. Set up the cron job for async execution
"""

import os
import subprocess
import sys
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def print_step(n, msg):
    print(f"\n{GREEN}[Step {n}]{RESET} {msg}")

def print_ok(msg):
    print(f"  {GREEN}✓{RESET} {msg}")

def print_warn(msg):
    print(f"  {YELLOW}⚠{RESET} {msg}")

def print_error(msg):
    print(f"  {RED}✗{RESET} {msg}")

def run(cmd, capture=True):
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
    return result

def main():
    print("=" * 60)
    print("Fable Orchestrator Quickstart")
    print("=" * 60)
    print("This script will set everything up automatically.")
    print("You only need to copy and paste commands.")
    print("=" * 60)

    # Step 1: Check Python version
    print_step(1, "Checking Python version")
    result = run("python3 --version")
    if result.returncode == 0:
        version = result.stdout.strip()
        print_ok(f"Python found: {version}")
        # Check if >= 3.10
        v = version.split()[1]
        major, minor = map(int, v.split(".")[:2])
        if major < 3 or (major == 3 and minor < 10):
            print_error("Python 3.10+ required. Please upgrade.")
            sys.exit(1)
    else:
        print_error("Python 3 not found. Please install Python 3.10+")
        sys.exit(1)

    # Step 2: Check Hermes
    print_step(2, "Checking Hermes Agent")
    result = run("which hermes")
    if result.returncode == 0:
        print_ok(f"Hermes found: {result.stdout.strip()}")
    else:
        print_warn("Hermes CLI not found in PATH. Make sure it's installed.")

    # Step 3: Check API keys
    print_step(3, "Checking API keys")
    home = Path.home()
    env_file = home / ".env"
    if env_file.exists():
        print_ok(".env file found")
    else:
        print_warn("No .env file found. Make sure your API keys are configured.")

    # Step 4: Check fable-orchestrator files
    print_step(4, "Checking Fable Orchestrator files")
    skill_dir = home / ".hermes" / "skills" / "fable-orchestrator"
    if skill_dir.exists():
        print_ok(f"Skill directory found: {skill_dir}")
    else:
        print_error(f"Skill directory not found: {skill_dir}")
        print("  Please clone the repo first:")
        print("  git clone https://github.com/iamnickthegeek/fable-orchestrator.git ~/.hermes/skills/fable-orchestrator")
        sys.exit(1)

    # Step 5: Make scripts executable
    print_step(5, "Making scripts executable")
    daemon_script = skill_dir / "scripts" / "fable_daemon.py"
    if daemon_script.exists():
        os.chmod(daemon_script, 0o755)
        print_ok(f"Made executable: {daemon_script}")
    else:
        print_error(f"Daemon script not found: {daemon_script}")
        sys.exit(1)

    # Step 6: Test the daemon
    print_step(6, "Testing the daemon")
    result = run(f"python3 {daemon_script} --help")
    if result.returncode == 0:
        print_ok("Daemon is working correctly")
        print("\n  Help output:")
        for line in result.stdout.strip().split("\n")[:5]:
            print(f"    {line}")
    else:
        print_error("Daemon test failed")
        print(result.stderr)
        sys.exit(1)

    # Step 7: Create output directory
    print_step(7, "Creating output directory")
    output_dir = home / "fable-outputs"
    output_dir.mkdir(exist_ok=True)
    print_ok(f"Output directory: {output_dir}")

    # Step 8: Create state database directory
    print_step(8, "Creating state database")
    state_db = home / ".hermes" / "fable_state.db"
    print_ok(f"State database will be: {state_db}")

    # Step 9: Ask about cron setup
    print_step(9, "Set up automatic execution?")
    print("  This will add a cron job that runs every 15 minutes.")
    print("  It allows Fable tasks to run while you sleep.")
    answer = input("  Set up now? (y/n): ").strip().lower()
    if answer == "y":
        cron_line = f"*/15 * * * * python3 {daemon_script} --tick --output-dir {output_dir} --state-db {state_db}\n"
        # Check if already exists
        result = run("crontab -l")
        current_crontab = result.stdout if result.returncode == 0 else ""
        if cron_line.strip() in current_crontab:
            print_ok("Cron job already exists")
        else:
            new_crontab = current_crontab + cron_line
            run(f"echo '{new_crontab}' | crontab -", capture=False)
            print_ok("Cron job added successfully")
            print(f"\n  Cron line: {cron_line.strip()}")
    else:
        print_warn("Skipped cron setup. You can add it later manually.")
        print(f"\n  To add later, run:")
        print(f"  crontab -e")
        print(f"  And add this line:")
        print(f"  */15 * * * * python3 {daemon_script} --tick --output-dir {output_dir} --state-db {state_db}")

    # Step 10: Run a test task
    print_step(10, "Run a test task?")
    print("  This will run a simple task to verify everything works.")
    answer = input("  Run test now? (y/n): ").strip().lower()
    if answer == "y":
        print("\n  Starting test task: 'Write a one sentence summary of Fable mode'")
        print("  This will take 2-3 minutes...")
        result = run(f"python3 {daemon_script} --start --task 'Write a one sentence summary of Fable mode' --output-dir {output_dir} --state-db {state_db}")
        if result.returncode == 0:
            print_ok("Test task started successfully")
            print(f"\n  Output: {result.stdout.strip()}")
            print("\n  Run this to check progress:")
            print(f"  python3 {daemon_script} --status --state-db {state_db}")
        else:
            print_error("Test task failed")
            print(result.stderr)
    else:
        print_warn("Skipped test task")

    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print("\nQuick commands:")
    print(f"  Start a task:    python3 {daemon_script} --start --task 'Your task' --output-dir {output_dir} --state-db {state_db}")
    print(f"  Run next tick:   python3 {daemon_script} --tick --output-dir {output_dir} --state-db {state_db}")
    print(f"  Check status:    python3 {daemon_script} --status --state-db {state_db}")
    print(f"  Resume task:     python3 {daemon_script} --resume TASK_ID --output-dir {output_dir} --state-db {state_db}")
    print("\nFor more help, see:")
    print("  - INSTALL.md (step-by-step guide)")
    print("  - examples/ (sample tasks)")
    print("  - README.md (full documentation)")
    print("\nHappy automating!")

if __name__ == "__main__":
    main()
