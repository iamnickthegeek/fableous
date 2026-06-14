# Example: Simple Task (No Coding Required)

## Task
Write a competitive analysis of AI ghostwriting tools.

## What to type
```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --start \
    --task "Write a competitive analysis of AI ghostwriting tools" \
    --output-dir ~/fable-outputs
```

## What happens
1. The engine asks you 3-5 clarifying questions (e.g., "What tone do you want?", "How many competitors?")
2. It plans a 4-stage DAG: Research → Implement → Verify → Consolidate
3. It runs the first tick (usually Research)
4. It saves state and exits

## How to continue
```bash
# Run the next tick
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --tick \
    --output-dir ~/fable-outputs

# Check progress
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --status

# Or set up a cron job to run automatically
```

## Expected output
- `~/fable-outputs/task_YYYYMMDD_HHMMSS/stage1_research.md`
- `~/fable-outputs/task_YYYYMMDD_HHMMSS/stage2_implement.md`
- `~/fable-outputs/task_YYYYMMDD_HHMMSS/stage3_verify.md`
- `~/fable-outputs/task_YYYYMMDD_HHMMSS/FINAL.md` ← Your deliverable

## Time estimate
- 4-5 ticks (each tick ~2-5 minutes depending on model)
- Total: 15-30 minutes
