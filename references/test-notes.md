# Test Notes — v6

## Test Matrix

| Test | Task | Expected | Status |
|------|------|----------|--------|
| T1 | Simple blog post (800 words) | 6 stages complete, FINAL.md produced | Pending |
| T2 | Competitive analysis (3 competitors) | All URLs verified, all claims sourced | ✅ PASS — June 2026 |
| T3 | Software project (FastAPI auth) | Tests pass, lint clean, coverage >= 80% | Pending |
| T4 | Multi-session task (cron) | Task survives session reset, continues from work log | Pending |
| T5 | Model verification failure | Fallback to secondary model works | Pending |
| T6 | Replanning trigger (T1 — insufficient research) | Extended Research stage added | Pending |
| T7 | Replanning trigger (T5 — verification failure) | Fix stage added, Verify re-run | Pending |
| T8 | Cross-family verification | Critique uses different model family than Implement | ✅ PASS — June 2026 |
| T9 | YAML config override | Custom routing table used | Pending |
| T10 | Auto-detect providers | Routing table built from available API keys | Pending |

## Known Issues

### Issue 1: `delegate_task` model parameter does not exist ✅ RESOLVED v7

**Symptom:** Subagent ignores any `model` parameter and runs on the session default.
**Root cause:** The `model` parameter doesn't exist in the tool schema, dispatch, or function signature. Confirmed by source-code audit.
**Resolution:** Config cycling via `route_config.py set --stage X` replaces it entirely. `delegation.model` and `delegation.provider` are read from disk on every `delegate_task` call. All 6 stages in the June 2026 live test routed correctly.
**Caveat:** The subagent summary's `"model"` field still reports the parent session model (Pitfall 10). Ignore it.

### Issue 2: `execute_code` blocked by default

**Symptom:** Verification checks that use `execute_code` fail silently.
**Impact:** Software verification (pytest, mypy) cannot run.
**Workaround:** Use `terminal` instead of `execute_code` for verification.
**Fix:** None. This is a security setting. The user must enable `execute_code` in their config.

### Issue 3: Session reset loses context

**Symptom:** Hermes session resets daily. The orchestrator must re-read the work log.
**Impact:** Multi-session tasks require manual intervention or cron jobs.
**Workaround:** Use `cronjob` for async execution. The work log is the continuity mechanism.
**Fix:** None. This is a Hermes session management policy.

### Issue 4: Cron job may run before stage is ready

**Symptom:** Cron job runs every 15 minutes but a stage takes 30 minutes.
**Impact:** Next tick tries to execute a stage that is still running.
**Workaround:** The `todo` status prevents double-execution. If a stage is "in_progress", the next tick skips it.
**Fix:** None needed. The todo system handles this.

### Issue 5: Vision-based verification not yet implemented

**Symptom:** No automated way to verify visual outputs (screenshots, diagrams).
**Impact:** UI/UX tasks cannot be fully verified.
**Workaround:** Manual verification for visual outputs.
**Fix:** Planned for v6.1.

### Issue 6: Dynamic replanning may create loops

**Symptom:** Replanning trigger T5 (verification failure) adds a Fix stage. If Fix fails, another Fix stage is added. Infinite loop.
**Impact:** Task never completes.
**Workaround:** Limit replanning to 3 iterations per trigger. After 3, flag to user.
**Fix:** Add iteration counter to replanning procedure.

### Issue 7: Large context overflow

**Symptom:** Consolidation stage reads all prior outputs. If outputs are large, context may overflow.
**Impact:** Consolidation stage fails or produces truncated output.
**Workaround:** Use Hermes built-in context compression. The skill instructs the model to summarize prior stages if needed.
**Fix:** None. Hermes handles this natively.

## Recommended Test Order

1. **T1 (Simple blog post)** — Validate the basic 6-stage loop works.
2. **T2 (Competitive analysis)** — Validate URL verification and source tracing.
3. **T8 (Cross-family verification)** — Validate model verification catches wrong models.
4. **T5 (Model verification failure)** — Validate fallback to secondary model.
5. **T6 (Replanning trigger)** — Validate dynamic replanning adds stages.
6. **T3 (Software project)** — Validate software verification gates (tests, lint).
7. **T4 (Multi-session cron)** — Validate cron job continues across sessions.
8. **T9 (YAML config)** — Validate custom routing table.
9. **T10 (Auto-detect)** — Validate provider detection from env vars.
10. **T7 (Replanning verification failure)** — Validate Fix stage and re-run.

## Test Results Log

### 2026-06-15 — T2 + T8 Combined Run

**Tests:** T2 (Competitive analysis) + T8 (Cross-family verification)
**Task:** Compare Jasper, Copy.ai, Writesonic for a solo content creator on a tight budget — under 400 words.
**Result:** ✅ ALL PASS
**Duration:** ~12 minutes total across 6 stages.

**Stage-by-stage:**
| Stage | Model (intended) | Model (actual tag) | Duration | Result |
|-------|-----------------|-------------------|----------|--------|
| 1 Research | deepseek-v4-flash | deepseek-v4-flash | 5m 19s | ✅ 3 tools researched, all URLs verified live |
| 2 Plan | glm-5.1 | glm-5.1 | 29s | ✅ Structure designed, recommendation-first |
| 3 Implement | kimi-k2.7-code | kimi-k2.7-code | 28s | ✅ 360 words, all claims sourced |
| 4 Verify | deepseek-v4-pro | deepseek-v4-pro | 1m 51s | ✅ PASS — 0 discrepancies (traceability audit) |
| 5 Critique | glm-5.1 | glm-5.1 | 1m 40s | ✅ 7 weaknesses, 5 priority fixes |
| 6 Consolidate | deepseek-v4-pro | deepseek-v4-pro | 1m 44s | ✅ All fixes applied, FINAL.md canonical |

**Cross-family check:** Implement (kimi) → Verify (deepseek) → Critique (glm) → Consolidate (deepseek) — all different families. ✅

**Key findings:**
- **Subagent self-report is unreliable**: Every summary's `"model"` field reported `"deepseek-v4-pro"` (parent session) regardless of config cycling. Only the output file tag and `route_config.py verify` are trustworthy. Documented as Pitfall 10.
- **Behavioral directives worked**: All stage outputs led with the outcome, grounded claims, and matched effort to the task type.
- **Critique was genuinely useful**: Caught confirmation bias in the budget framing, flagged the misleading "0 errors" claim from verification (traceability audit ≠ quality audit), and noted that Copy.ai's distinguishing feature (GTM Workflows) is irrelevant to solo creators.
- **Writesonic free tier ambiguity was caught and handled**: Three stages flagged it; final document gives a definitive verdict ("verify before relying on third-party claims").

**Adjustments:** Added Pitfall 10 (subagent self-report unreliability) and Pitfall 11 (clear stale endpoint values) to SKILL.md. Updated model-verification.md with live test evidence table.

---

### Date: [YYYY-MM-DD]

**Test:** [T1 / T2 / etc]
**Task:** [Description]
**Result:** [PASS / FAIL]
**Details:** [What happened]
**Adjustments:** [What was changed in the skill]

---

*Fill in the test results as you run them. This is the living record of what works.*
