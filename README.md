# Fable Orchestrator

**Give complex tasks to AI. Let it work while you sleep. Check the results when you wake up.**

An open-source, automated task execution system for [Hermes Agent](https://hermes-agent.nousresearch.com). Breaks big tasks into smaller stages, runs them in parallel, checks its own work, and produces a final result.

Built by Nick Smith (Point Clear Advisory). MIT licensed.

---

## What This Does (In Plain English)

You have a big task — like writing a 20-page report or building a web app. Instead of sitting at your computer and guiding the AI through every step, you:

1. **Describe the task** in one sentence
2. **The engine asks clarifying questions** (e.g., "What tone?", "How long?")
3. **It breaks the task into stages** — Research, Plan, Write, Check, Review
4. **It runs each stage** using different AI models optimized for that type of work
5. **It checks its own work** after each stage
6. **It produces a final result** saved to a file on your computer

You can set it up to run automatically every 15 minutes, so you start a task before bed and wake up to a finished report.

---

## Who This Is For

- **Solopreneurs** who want AI to handle research and writing while they sleep
- **Content creators** who need consistent, high-quality output without micromanaging
- **Non-coders** who want the power of multi-agent AI without writing code
- **Anyone** who has ever thought "I wish the AI could just work on this for a few hours and tell me when it's done"

---

## Quick Start (5 Minutes)

### 1. Install

```bash
# Clone the repo (or copy the files to ~/.hermes/skills/fable-orchestrator)
git clone https://github.com/iamnickthegeek/fable-orchestrator.git ~/.hermes/skills/fable-orchestrator

# Make the script executable
chmod +x ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py

# Run the automated setup wizard
python3 ~/.hermes/skills/fable-orchestrator/quickstart.py
```

The wizard will check everything, set up auto-execution, and optionally run a test task.

### 2. Start Your First Task

```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --start \
    --task "Write a competitive analysis of AI ghostwriting tools" \
    --output-dir ~/fable-outputs
```

### 3. Continue the Task

```bash
# Run the next tick (execute the next batch of stages)
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --tick \
    --output-dir ~/fable-outputs
```

You might need to run this 3-5 times for a simple task. Each time, it picks up where it left off.

### 4. Check the Results

```bash
# See all tasks and their status
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --status \
    --state-db ~/.hermes/fable_state.db

# Look at the output folder
ls ~/fable-outputs/
```

---

## Full Documentation

| Document | What it covers |
|----------|-------------|
| **[INSTALL.md](INSTALL.md)** | Step-by-step setup for non-coders. Troubleshooting. Cheat sheet. |
| **[examples/simple_task.md](examples/simple_task.md)** | How to run a simple task (15-30 minutes) |
| **[examples/software_project.md](examples/software_project.md)** | How to run a software project (1-2 hours) |
| **[examples/research_report.md](examples/research_report.md)** | How to run a large research report (4+ hours, with cron) |

---

## How It Works

### The Daemon Pattern

Hermes Agent runs in a single session. Fable Orchestrator works around this by using a **cron job** — a small program that runs every 15 minutes:

1. **You start a task** with `--start`. The engine plans the stages and saves them to a database.
2. **The cron job runs** `--tick` every 15 minutes. It checks for pending stages, executes one batch, and saves progress.
3. **You check the results** later with `--status` or by looking at the output files.
4. **If something interrupts** (computer restart, session reset), the task resumes automatically from the last saved point.

This is the closest thing to "AI that works while you sleep" without modifying the Hermes core.

### The Stages

Every task goes through these stages (some may be skipped for simple tasks):

1. **Research** — Gathers information from the web
2. **Plan** — Creates a detailed execution plan
3. **Implement** — Does the actual work (writing, coding, etc.)
4. **Verify** — Checks that the output is correct and complete
5. **Critique** — A different AI model reviews the work for blind spots
6. **Consolidate** — Produces the final, polished deliverable

### Why Different Models?

Each stage uses a different AI model optimized for that type of thinking:

| Stage | Primary Model | Why |
|-------|-------------|-----|
| Research | DeepSeek V4 Flash | Fast, good at web search |
| Planning | GLM 5.1 | Structured, logical thinking |
| Implementation | Kimi 2.7 Code | Best at coding and writing |
| Verification | DeepSeek V4 Pro | Thorough, detail-oriented |
| Critique | GLM 5.1 | Different family = catches different errors |
| Consolidation | DeepSeek V4 Pro | Synthesizes everything into a polished result |

If a model fails, the engine automatically tries a fallback model.

---

## Examples

### Example 1: Simple Blog Post

```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --start \
    --task "Write a 500-word blog post about AI marketing for solopreneurs" \
    --output-dir ~/fable-outputs
```

**Result:** `~/fable-outputs/task_YYYYMMDD_HHMMSS/FINAL.md`

**Time:** 15-30 minutes

### Example 2: Software Project

```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --start \
    --task "Build a Python script that scrapes a website and saves to CSV" \
    --output-dir ~/fable-outputs
```

**Result:**
- `stage1_research.md` — Research on scraping libraries
- `stage2_plan.md` — Implementation plan
- `stage3_implement.md` — The actual Python script
- `stage4_verify.md` — Test results
- `stage5_critique.md` — Code review
- `FINAL.md` — Final script with fixes applied

**Time:** 30-60 minutes

### Example 3: Large Research Report (With Cron)

```bash
# Start the task
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --start \
    --task "Write a 20-page research report on AI marketing trends for 2026" \
    --output-dir ~/fable-outputs

# The cron job handles the rest automatically
```

**Result:** `~/fable-outputs/task_YYYYMMDD_HHMMSS/FINAL.md` (20 pages)

**Time:** 2-4 hours (runs while you sleep)

---

## Setting Up Auto-Run (Cron)

To make tasks run automatically without you manually typing `--tick`:

```bash
# Add this to your crontab (run 'crontab -e' to edit)
*/15 * * * * python3 /home/case/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --tick --output-dir /home/case/fable-outputs --state-db /home/case/.hermes/fable_state.db
```

Or run the quickstart wizard which does this for you:

```bash
python3 ~/.hermes/skills/fable-orchestrator/quickstart.py
```

---

## Common Commands

| What you want | Command |
|---------------|---------|
| Start a new task | `python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --start --task "Your task" --output-dir ~/fable-outputs` |
| Run the next tick | `python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --tick --output-dir ~/fable-outputs` |
| Check all tasks | `python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --status --state-db ~/.hermes/fable_state.db` |
| Resume a task | `python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --resume TASK_ID --output-dir ~/fable-outputs --state-db ~/.hermes/fable_state.db` |
| Follow a task's log | `python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --tail TASK_ID --state-db ~/.hermes/fable_state.db` |

---

## Requirements

- Hermes Agent (any recent version)
- Python 3.10 or higher (your Hermes machine already has this)
- API keys for Opencode Go, Google, and optionally OpenRouter
- Linux (your Hermes machine runs this)

---

## Architecture

```
fable-orchestrator/
├── fable_engine/          # Core engine (you don't need to touch these)
│   ├── core.py            # Main orchestrator
│   ├── state.py           # SQLite database (saves your task progress)
│   ├── planner.py         # Decides what to do and which AI to use
│   ├── agent_pool.py      # Runs multiple AI agents at once
│   ├── verification.py    # Checks the AI's work
│   ├── context.py         # Keeps things from getting too long
│   └── questioner.py      # Asks you clarifying questions
├── scripts/
│   ├── fable_daemon.py    # Main program you run (this is the one you use)
│   └── verify_models.py   # Checks your API keys are working
├── tests/                 # Test suite (for developers)
├── examples/              # Example tasks (see these for ideas)
├── quickstart.py          # Automated setup wizard (run this first)
├── README.md              # This file
├── INSTALL.md             # Detailed setup guide for non-coders
├── LICENSE                # MIT license
└── SKILL.md               # Hermes skill definition
```

---

## Status & Roadmap

**Current (v1.0.0):**
- Core engine, daemon, state persistence, dynamic planning, parallel execution, verification, proactive questioning
- Tested end-to-end on real tasks

**Planned (v5.1):**
- Vision integration (analyze images automatically)
- Dynamic re-planning mid-flight

**Planned (v5.2):**
- Distributed agent pool (hundreds of agents across multiple machines)

---

## License

MIT. See [LICENSE](LICENSE).

---

## Questions?

- Open an issue: [github.com/iamnickthegeek/fable-orchestrator/issues](https://github.com/iamnickthegeek/fable-orchestrator/issues)
- Ask your Hermes agent to help you troubleshoot
- Read [INSTALL.md](INSTALL.md) for step-by-step troubleshooting
