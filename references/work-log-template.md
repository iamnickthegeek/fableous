# Work Log Template — v0.6.0

Structured handoff protocol for multi-session Fable execution. The work log is the ONLY continuity mechanism between sessions. Hermes session_search may not retain the full context. The work log MUST survive session resets.

## File Location

`WORK_LOG.md` in the project directory (same directory as the stage outputs).

## How to Use

1. At the start of EVERY continuation (new session, resumed session, cron tick), read the work log with `read_file` before doing anything else.
2. After completing a stage, append a new entry to the work log.
3. After replanning, append a new entry describing the trigger and action.
4. After a model failure, append a new entry describing the retry chain.

## Format

```markdown
# WORK_LOG — [Project Name]

## Overview
- **Task**: [Original task description]
- **Started**: [YYYY-MM-DD]
- **Current Session**: [N]
- **Status**: [running / completed / blocked]
- **Next Stage**: [stage name or "none — all complete"]

---

## Session [N] — [YYYY-MM-DD]

### Completed
- [ ] Stage [N]: [name] — [model used] ([provider]) — [verified: yes/no]

### Verification Results
- Stage [N]: [passed / failed: details]

### Decisions
- [Decision made and why]

### Failures
- [What was tried and abandoned]

### Open Items
- [What remains]

---

## Model Usage Log

| Stage | Intended | Actual | Verified | Retry Chain |
|-------|----------|--------|----------|-------------|
| Research | deepseek-v0.4.0-flash | [actual] | [yes/no] | [none / secondary / tertiary] |
| Plan | glm-5.1 | [actual] | [yes/no] | [none / secondary / tertiary] |
| Implement | kimi-k2.7-code | [actual] | [yes/no] | [none / secondary / tertiary] |
| Verify | deepseek-v0.4.0-pro | [actual] | [yes/no] | [none / secondary / tertiary] |
| Critique | glm-5.1 | [actual] | [yes/no] | [none / secondary / tertiary] |
| Consolidate | deepseek-v0.4.0-pro | [actual] | [yes/no] | [none / secondary / tertiary] |

---

## Replanning History

- [YYYY-MM-DD HH:MM]: [Trigger T#] — [Description of obstacle] — [Action taken]

---

## Async Delegation Log

| Delegation ID | Stage | Dispatched | Completed | Model | Status |
|---------------|-------|------------|-----------|-------|--------|
| async-abc123 | Research | 14:30:00 | 14:35:19 | deepseek-v0.4.0-flash | ✅ |
| async-yyy456 | Plan | 14:30:05 | 14:30:34 | glm-5.1 | ✅ |

---

## Done Criteria

- [ ] All 6 stages complete
- [ ] FINAL.md produced
- [ ] All verification checks passed
- [ ] All model verifications passed
- [ ] Work log up to date
```

## Example Entry

```markdown
## Session 3 — 2026-06-14

### Completed
- [x] Stage 1: Research — deepseek-v0.4.0-flash (opencode-go) — verified: yes
- [x] Stage 2: Plan — glm-5.1 (opencode-go) — verified: yes
- [x] Stage 3: Implement — kimi-k2.7-code (opencode-go) — verified: yes
- [ ] Stage 4: Verify — pending
- [ ] Stage 5: Critique — pending
- [ ] Stage 6: Consolidate — pending

### Verification Results
- Stage 1: Passed — all 5 URLs verified HTTP 200, all claims have sources
- Stage 2: Passed — audience segmented into 3 tiers, methodology section present
- Stage 3: Passed — word count 1,200, all claims trace to sources

### Decisions
- Added Jasper.ai as a competitor after user clarification
- Decided to skip the "Solo tier" sub-segment after discovering insufficient data

### Failures
- Tried to verify Writer.com pricing but the page requires login; marked as "vendor-claimed, not verified"

### Open Items
- Stage 4: Verify — run consistency checks
- Stage 5: Critique — must use GLM (different family from Kimi)
- Stage 6: Consolidate — produce FINAL.md
```

## Rules

1. **Append, don't overwrite.** Each session gets a new entry. Don't delete prior entries.
2. **Be specific.** "Stage 1 passed" is not enough. "Stage 1 passed: all 5 URLs verified HTTP 200, all claims have sources" is specific.
3. **Log failures honestly.** "Tried X, failed because Y" is better than "Stage 1 passed" when it didn't.
4. **Log model usage.** The model usage log is critical for cross-family verification.
5. **Log replanning.** Every replanning trigger and action must be recorded.
6. **Update the overview.** The overview section must reflect the current status at all times.

## Recovery Procedure

If the work log is missing or corrupted:

1. Use `session_search` to find the most recent session about this task.
2. Read the session to understand what was completed.
3. Rebuild the work log from scratch.
4. Mark all stages as "status unknown — verify before proceeding."
5. Re-run verification checks for all completed stages before proceeding.
