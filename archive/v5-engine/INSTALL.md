# Fable Orchestrator — Non-Coder Installation Guide

This guide is written for people who don't know how to code. If you can copy and paste, you can use this.

## What This Is

Fable Orchestrator is a tool that lets you give complex tasks to AI and have it work on them autonomously — even while you sleep. It breaks big tasks into smaller stages, runs them in parallel, checks its own work, and produces a final result.

## Prerequisites (What You Need Before You Start)

1. **Hermes Agent** installed on your computer (you already have this)
2. **API keys** set up (Opencode Go, Google, OpenRouter — you already have these)
3. **Python 3.10 or higher** (your Hermes machine already has this)

If you're unsure about any of these, ask your Hermes agent: *"Do I have Python 3.10+ installed?"* and *"Are my API keys configured?"*

## Step 1: Copy the Files Into Place

You have two options. Pick whichever feels easier.

### Option A: Copy the skill directory (Easiest)

You already have the files in your Hermes skills directory. Just verify they're there:

```bash
ls ~/.hermes/skills/fable-orchestrator/
```

You should see folders like `fable_engine/`, `scripts/`, `examples/`, etc. If you do, you're done with this step.

### Option B: Clone from GitHub (When you publish the repo)

When the repo is live at `github.com/iamnickthegeek/fable-orchestrator`:

```bash
git clone https://github.com/iamnickthegeek/fable-orchestrator.git ~/.hermes/skills/fable-orchestrator
```

## Step 2: Make the Scripts Executable

Copy and paste this one line into your terminal:

```bash
chmod +x ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py
```

This just tells your computer "this file is allowed to run."

## Step 3: Test That Everything Works

Copy and paste this:

```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --help
```

You should see something like:

```
usage: fable_daemon.py [-h] [--task TASK] [--start] [--tick] [--status]
                       [--resume RESUME] [--tail TAIL]
                       ...

Fable Daemon v1.0
```

If you see that, everything is working. If you see errors, scroll down to the **Troubleshooting** section.

## Step 4: Run Your First Task

This is the fun part. Let's give it a simple task to test.

Copy and paste this (you can change the task to anything you want):

```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --start \
    --task "Write a one sentence summary of Fable mode" \
    --output-dir ~/fable-test
```

### What you'll see

1. **"Task started: task_20260614_..."** — The engine has created a task ID.
2. **"Tick result: running"** — It ran the first stage (usually Research).

### Check the output

```bash
ls ~/fable-test/
```

You should see a folder named after your task ID (e.g., `task_20260614_081500`).

Inside that folder:
- `stage1_research.md` — The research stage output

## Step 5: Continue the Task

The engine runs in **ticks**. Each tick executes one batch of stages. To continue, run another tick:

```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --tick \
    --output-dir ~/fable-test
```

You might need to run this 3-5 times for a simple task. Each time, it will pick up where it left off.

### Check progress anytime

```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --status \
    --output-dir ~/fable-test
```

This shows you all tasks and whether they're running, completed, or failed.

### When it's done

You'll see:
- `FINAL.md` — Your final deliverable
- `stage1_research.md` through `stage4_consolidate.md` — All the intermediate work

## Step 6: Set Up Auto-Run (So It Works While You Sleep)

This is where the magic happens. Instead of manually running `--tick` over and over, you can tell your computer to run it automatically every 15 minutes.

### For Linux (what you're running)

1. Open your crontab:

```bash
crontab -e
```

2. Add this line at the bottom:

```
*/15 * * * * python3 /home/case/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --tick --output-dir /home/case/fable-outputs --state-db /home/case/.hermes/fable_state.db
```

3. Save and exit (usually Ctrl+O, then Enter, then Ctrl+X).

### What this does

Every 15 minutes, your computer checks if there are any running Fable tasks and executes the next tick. You can start a task, close your laptop, and come back to a finished result.

### To see what's happening

```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --status \
    --state-db /home/case/.hermes/fable_state.db
```

### To follow a specific task's log

```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --tail task_20260614_081500 \
    --state-db /home/case/.hermes/fable_state.db
```

(Replace `task_20260614_081500` with your actual task ID from the status output.)

## Step 7: Resume an Interrupted Task

If your computer restarts or Hermes resets, your task is **not lost**. The engine saves everything to a database.

```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --resume task_20260614_081500 \
    --output-dir ~/fable-test \
    --state-db /home/case/.hermes/fable_state.db
```

(Replace `task_20260614_081500` with your actual task ID.)

## Common Commands Cheat Sheet

| What you want | Command |
|---------------|---------|
| Start a new task | `python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --start --task "Your task here" --output-dir ~/fable-outputs` |
| Run the next tick | `python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --tick --output-dir ~/fable-outputs` |
| Check all tasks | `python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --status --state-db /home/case/.hermes/fable_state.db` |
| Resume a task | `python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --resume TASK_ID --output-dir ~/fable-outputs --state-db /home/case/.hermes/fable_state.db` |
| Follow a task's log | `python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --tail TASK_ID --state-db /home/case/.hermes/fable_state.db` |

## What Task Should I Give It?

### Simple tasks (15-30 minutes)
- "Write a competitive analysis of AI ghostwriting tools"
- "Summarize the latest research on AI marketing for solopreneurs"
- "Create a Twitter thread about the future of AI content"

### Medium tasks (1-2 hours)
- "Build a Python script that scrapes a website and saves to CSV"
- "Write a 5-page ebook chapter on AI marketing"
- "Create a landing page HTML/CSS for a ghostwriting service"

### Large tasks (4+ hours, use cron)
- "Write a 20-page research report on AI marketing trends"
- "Build a complete web application with authentication and payments"
- "Create a 10-lesson online course on AI-powered content creation"

## Troubleshooting

### "No module named 'fable_engine'"

**Cause:** The script can't find the engine files.

**Fix:** Make sure you're running the script from the right place. The full path should be:

```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py
```

Not just `fable_daemon.py`.

### "Task failed after retry"

**Cause:** The model couldn't complete the stage. Usually a timeout or API error.

**Fix:**
1. Check the work log: `python3 ... --tail TASK_ID --state-db ...`
2. Resume the task: `python3 ... --resume TASK_ID ...`
3. The engine will try a different model automatically.

### "No output file produced"

**Cause:** The stage completed but didn't write to the expected file.

**Fix:** Check the stage output file (e.g., `stage1_research.md`) in the output directory. Sometimes the model puts the content in the response instead of the file. The engine logs this as a verification failure but still continues.

### "API key error" or "Authentication failed"

**Cause:** Your API keys aren't configured for the model the engine tried to use.

**Fix:**
1. Check which model failed (in the status or tail output)
2. Make sure you have that API key configured in your Hermes config
3. Or change the model routing in `~/.hermes/skills/fable-orchestrator/fable_engine/planner.py`

### "I don't know how to do any of this"

**Fix:** Just ask your Hermes agent. Copy and paste the error message and say: *"I got this error. What do I do?"* The Hermes agent is designed to help you with exactly this.

## What Each File Does (If You're Curious)

You don't need to understand these to use the tool, but if you want to know:

| File | What it does |
|------|-------------|
| `scripts/fable_daemon.py` | The main program you run. Handles all the commands. |
| `fable_engine/core.py` | The brain. Orchestrates the whole pipeline. |
| `fable_engine/state.py` | The memory. Saves everything to a SQLite database so nothing is lost. |
| `fable_engine/planner.py` | The strategist. Decides what stages to run and which models to use. |
| `fable_engine/agent_pool.py` | The worker. Spawns AI agents to run stages in parallel. |
| `fable_engine/verification.py` | The quality checker. Makes sure each stage actually produced something. |
| `fable_engine/context.py` | The editor. Keeps long outputs from overwhelming the system. |
| `fable_engine/questioner.py` | The interviewer. Asks you clarifying questions before starting. |

## Still Stuck?

Open an issue on GitHub: `https://github.com/iamnickthegeek/fable-orchestrator/issues`

Or ask your Hermes agent to help you. It's trained to troubleshoot this exact setup.
