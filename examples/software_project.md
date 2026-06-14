# Example: Software Project (Medium Complexity)

## Task
Build a Python script that scrapes a website and saves data to CSV.

## What to type
```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --start \
    --task "Build a Python script that scrapes example.com and saves data to CSV" \
    --output-dir ~/fable-outputs
```

## What happens
1. The engine asks clarifying questions (e.g., "What data to scrape?", "Which fields?")
2. It plans a 6-stage DAG: Research → Plan → Implement → Verify → Critique → Consolidate
3. The Plan stage produces a detailed implementation plan
4. The Verify stage runs the script and checks the CSV output
5. The Critique stage uses a different model family to find bugs

## How to continue
Same as simple task: run `--tick` repeatedly or set up a cron job.

## Expected output
- `stage1_research.md` — research on scraping libraries
- `stage2_plan.md` — detailed implementation plan
- `stage3_implement.md` — the actual Python script
- `stage4_verify.md` — verification results
- `stage5_critique.md` — cross-family critique
- `FINAL.md` — final script with corrections applied

## Time estimate
- 6-8 ticks
- Total: 30-60 minutes
