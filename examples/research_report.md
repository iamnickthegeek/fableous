# Example: Research Report (High Complexity)

## Task
Write a 20-page research report on the future of AI marketing for solopreneurs.

## What to type
```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --start \
    --task "Write a 20-page research report on the future of AI marketing for solopreneurs in 2026" \
    --output-dir ~/fable-outputs
```

## What happens
1. The engine asks clarifying questions (e.g., "What sections?", "Citation style?", "Target audience?")
2. It plans a 6+ stage DAG with parallel research tracks
3. Multiple research stages run in parallel (different models, different sources)
4. The Plan stage synthesizes findings into a chapter structure
5. The Implement stage writes each chapter
6. The Critique stage checks for hallucinations and bias

## How to continue
This is a multi-session task. Set up the cron job:

```bash
# Add to your crontab (runs every 15 minutes)
*/15 * * * * python3 /home/case/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --tick --output-dir /home/case/fable-outputs
```

## Expected output
- `stage1_research.md` through `stage3_research.md` — parallel research tracks
- `stage4_plan.md` — chapter outline
- `stage5_implement.md` through `stage8_implement.md` — individual chapters
- `stage9_verify.md` — fact-checking
- `stage10_critique.md` — cross-family critique
- `FINAL.md` — complete 20-page report

## Time estimate
- 10-15 ticks
- Total: 2-4 hours (with cron job, it runs while you sleep)
