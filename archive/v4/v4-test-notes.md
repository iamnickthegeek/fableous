# Fable Orchestrator v4 Test Notes

## Test 1: Trivial task — dynamic planner validation

**Date:** 2026-06-14
**Task:** "Write a one-sentence summary of the Fable orchestrator concept"
**Command:**
```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_orchestrator_v4.py \
    --task "Write a one-sentence summary of the Fable orchestrator concept" \
    --output-dir /tmp/fable-test \
    --domain research
```
**Result:** Planner correctly simplified to 4 stages (skipped Plan and Critique as unnecessary for a single-sentence task). Research and Implement ran sequentially. Verify timed out at 120s (terminal-level timeout, not script-level).

**Key observation:** The dynamic planner works. For a trivial task, it produced:
```json
{"stages": [
  {"id": "research", "name": "Research", "parallel": false, "depends_on": [], "output": "stage1_research.md"},
  {"id": "implement", "name": "Implementation", "parallel": false, "depends_on": ["research"], "output": "stage2_implement.md"},
  {"id": "verify", "name": "Verification", "parallel": false, "depends_on": ["implement"], "output": "stage3_verify.md"},
  {"id": "consolidate", "name": "Consolidation", "parallel": false, "depends_on": ["research", "implement", "verify"], "output": "FINAL.md"}
]}
```
Rationale: "One-sentence summary task: plan and critique clearly unnecessary — nothing to architect for a single sentence, and critique adds no value beyond what verify already catches."

**Pitfall:** When running via `terminal()`, the `timeout` parameter must be at least as long as the script's internal stage timeout (300s). The test used 120s and timed out during the Verify stage. Always use `timeout=300` or higher when running v4 via `terminal()`.

**Pitfall:** The script falls back to subprocess mode because `execute_code` is blocked by default. This is expected and documented, but it means each stage spawns a cold `hermes chat -q` process with no shared session context. Each stage takes ~20s to spin up. For 6 stages, expect ~2 minutes of overhead before any work is done.

## Test 2: Competitive analysis — V3 (historical)

**Date:** June 2026
**Task:** "Write a 1-page competitive analysis of AI ghostwriting tools"
**Result:** 5-stage loop executed cleanly. Model routing worked. Critique subagent found 5 real weaknesses. Consolidation stage (v3 addition) propagated fixes. See SKILL.md for full test notes.

## Known issues

- **Context window pressure on large tasks:** The `summarize_file()` function limits dependency inputs to 100 lines, but for research tasks with many sources, even the summary can grow. Consider adding a max-chars limit in addition to max-lines.
- **State file corruption:** If `state.json` is corrupted (e.g., partial write during crash), the orchestrator starts fresh. The user loses the checkpoint. Consider atomic writes (write to temp, then rename).
- **Background mode untested:** The `background=True` parameter in `run_stage()` is implemented but not exercised in any test. The parallel execution uses threads, but the actual subprocess spawning is still foreground. Background mode may have race conditions with file writing.

## Recommended test matrix

| Test | Purpose | Expected result |
|------|---------|---------------|
| Trivial task (1 sentence) | Planner simplification | Skips unnecessary stages |
| Pure coding task | Planner adaptation | Skips research, adds test stage |
| Multi-source research | Parallel execution | Research + Plan run concurrently |
| Kill mid-execution | Checkpoint/resume | `--resume` continues from last completed stage |
| Model failure | Self-healing retry | Falls back to secondary model automatically |
| Large file dependencies | Context pruning | Summaries stay under 100 lines |
