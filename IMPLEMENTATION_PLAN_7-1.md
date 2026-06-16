# IMPLEMENTATION_PLAN_7-1.md — Async Subagents

## Summary

Hermes now supports `delegate_task(background=true)`, which dispatches a
subagent on a daemon thread pool and returns a handle immediately. When the
subagent finishes, its result re-enters the conversation as a **new turn** via
the `process_registry.completion_queue`. The current Fable v7.0 stage
execution procedure assumes synchronous blocking — this plan adds an async
path that enables true parallel execution of Research and Plan, while keeping
the sequential stages (Implement+) on the existing sync path.

**Zero changes to the config cycling mechanism.** The child agent is built
BEFORE dispatch, so the model/provider is snapshotted at construction time.
Cycling delegation config for the next stage immediately after dispatch is
safe — no race condition.

---

## 1. What the feature does (the implementer must understand)

### 1.1 The dispatch

```python
delegate_task(goal="Research: ...", context="...", toolsets=["web","file"],
              background=true)
```

Returns immediately:
```json
{"status": "dispatched", "delegation_id": "async-abc123"}
```

Capacity is capped at `delegation.max_async_children` (default 3). When at
capacity, the call is rejected — the orchestrator must fall back to sync
(`background=false`).

### 1.2 The completion

When the subagent finishes, Hermes pushes a completion event onto
`process_registry.completion_queue` with `type="async_delegation"`. The
gateway/CLI drain loop picks it up and delivers it as a **new turn** in the
conversation — it looks like a new user message to the orchestrator agent.

The completion payload carries the original goal, context, toolsets, model,
dispatch time, status, duration, and the full result summary. The orchestrator
agent sees something like:

```
[ASYNC DELEGATION COMPLETE]
delegation_id: async-abc123
goal: Research: Pull and verify current pricing...
status: completed
model: deepseek-v4-flash
duration: 319s
summary: |
  Research complete. Found verified pricing for all three tools...
  File created: /tmp/fable-test/stage1_research.md
```

### 1.3 Single-task only

Async delegation only supports single tasks (`goal=`), not batch (`tasks=`).
This is fine for Fable — each stage is a single task anyway.

### 1.4 Interrupt behaviour

The existing interrupt path (`/stop`, gateway shutdown) interrupts all running
async delegations. Interrupted children emit a completion event with
`status="interrupted"`. The orchestrator should treat this like a timeout —
check if the output file was written, verify what exists, and either retry
or mark blocked.

---

## 2. What changes vs what doesn't

### 2.1 Files that need changes

| File | Change |
|------|--------|
| `SKILL.md` | Rewrite Stage Execution Procedure. Add async path, completion handling. Update todos section. Update verification gating. |
| `references/guardrails.md` | Add completion-event guardrails for Research and Plan templates. |
| `templates/stage-prompts/research.md` | Add `ASYNC: true` directive. |
| `templates/stage-prompts/plan.md` | Add `ASYNC: true` directive. |
| `references/config-cycling.md` | Add async timing section. Document snapshot safety. |
| `references/model-verification.md` | Add deferred verification for async stages. |
| `references/delegate-task-model-fallback.md` | Add async capacity rejection → sync fallback. |
| `references/work-log-template.md` | Add async completion event logging format. |
| `IMPLEMENTATION_PLAN.md` | Update version history to reference v7.1. |

### 2.2 Files that need ZERO changes

| File | Why untouched |
|------|--------------|
| `scripts/route_config.py` | Config cycling is snapshot-safe. Same `set`/`restore`/`verify` commands. |
| `scripts/detect_routing.py` | Native routing still not available. Async is orthogonal to model routing. |
| `scripts/run_stage.py` | Terminal fallback unchanged. Async is a `delegate_task` feature, not a terminal feature. |
| `scripts/fable_routing.py` | Routing table unchanged. |
| `scripts/verify_models.py` | Provider check unchanged. |
| `scripts/auto_detect_providers.py` | Provider detection unchanged. |
| `templates/stage-prompts/implement.md` | Stays sync. No `ASYNC` directive. |
| `templates/stage-prompts/verify.md` | Stays sync. No `ASYNC` directive. |
| `templates/stage-prompts/critique.md` | Stays sync. No `ASYNC` directive. |
| `templates/stage-prompts/consolidate.md` | Stays sync. No `ASYNC` directive. |
| `references/verification-templates.md` | Same verification checks, just deferred for async stages. |
| `references/replanning-triggers.md` | Same triggers, applied when completion event arrives. |
| `references/model-routing-table.md` | Same routing table. |
| `references/timeout-recovery-recipe.md` | Same recovery logic, applied to interrupted async stages. |
| `references/native-first-gap-fillers.md` | No new native gaps created. |
| `templates/consolidation-prompt.md` | Unchanged. |
| `templates/replanning-prompt.md` | Unchanged. |

---

## 3. Stage Execution Procedure — Rewritten

### 3.1 Decision: sync vs async

The orchestrator decides per stage:

| Stage | Method | Reason |
|-------|--------|--------|
| Research | **async** (`background=true`) | No dependencies. Can run in parallel with Plan. |
| Plan | **async** (`background=true`) | No dependencies. Can run in parallel with Research. |
| Implement | **sync** (`background=false`) | Depends on Research + Plan. Must wait for both. |
| Verify | **sync** (`background=false`) | Depends on Implement. Must wait. |
| Critique | **sync** (`background=false`) | Depends on Implement + Verify. Must wait. |
| Consolidate | **sync** (`background=false`) | Depends on all prior stages. Must wait. |

**Fallback rule**: If `delegate_task(background=true)` returns `{"status": "rejected"}` (capacity full), fall back to sync for that stage. Log the fallback in WORK_LOG.md.

### 3.2 Async path: Research and Plan

```
# ===== FIRE BOTH IN SEQUENCE (dispatch is instant, config cycle between is safe) =====

# Step 1: Route and dispatch Research
terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py set --stage research")
todo(todos=[{id:"stage-1", content:"Stage 1: Research — ...", status:"in_progress"}], merge=true)
delegate_task(
  goal="Research: Pull and verify current pricing, free tier availability, and one
        distinguishing feature each for Jasper, Copy.ai, and Writesonic. Verify all
        claims against actual websites. Save to /tmp/fable-test/stage1_research.md.",
  context="[Full research prompt from template, including]" +
    "ASYNC: This stage runs in the background. When you finish, your result will " +
    "re-enter the conversation as a completion event. Write your output file BEFORE " +
    "reporting completion — the orchestrator will verify it after you finish.\n\n" +
    "[... rest of template ...]",
  toolsets=["web", "file"],
  background=true
)
# Returns: {"status": "dispatched", "delegation_id": "async-xxx"}
# CRITICAL: Save the delegation_id. You need it for the completion handler.

# Step 2: Route and dispatch Plan (SAFE — Research child already snapshotted flash)
terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py set --stage plan")
todo(todos=[{id:"stage-2", content:"Stage 2: Plan — ...", status:"in_progress"}], merge=true)
delegate_task(
  goal="Plan: Read the research, then design the structure for a sub-400-word
        comparison. Audience is a solo content creator on tight budget. Save to
        /tmp/fable-test/stage2_plan.md.",
  context="[Full plan prompt from template, including]" +
    "ASYNC: This stage runs in the background. When you finish, your result will " +
    "re-enter the conversation as a completion event. Write your output file BEFORE " +
    "reporting completion — the orchestrator will verify it after you finish.\n\n" +
    "[... rest of template ...]",
  toolsets=["file"],
  background=true
)
# Returns: {"status": "dispatched", "delegation_id": "async-yyy"}

# Step 3: Restore config (both children already snapshotted)
terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py restore")

# Step 4: Wait for completion events
# The orchestrator now DOES NOTHING. It waits for the completion events to arrive
# as new turns. When a completion event arrives, follow the Completion Handling
# procedure (Section 4).
```

### 3.3 Sync path: Implement through Consolidate

Same as v7.0 — no changes. The sync path is exactly what the current SKILL.md
describes. Implement, Verify, Critique, and Consolidate all block.

### 3.4 The in-between state

After dispatching Research and Plan (async), but before both completion events
have arrived, the orchestrator is in a **waiting state**. The todo list shows
both as `in_progress`. The orchestrator must NOT proceed to Implement until
BOTH are `completed` and verified.

If the user sends a message during the waiting state, the orchestrator
responds with a status update: "Research and Plan are running in the
background. I'll continue when both complete."

---

## 4. Completion Handling — New Section

This is the most critical new section in SKILL.md. It tells the orchestrator
what to do when an async delegation completion event arrives as a new turn.

### 4.1 Recognition

The completion event arrives as a message in the conversation. It contains the
`delegation_id`, `goal`, `status`, `model`, `duration`, and `summary`. The
orchestrator must recognise it as a completion event (not a user message) and
route it to the correct stage handler.

**Recognition keywords**: The event will contain phrases like "async
delegation complete", "background task finished", or it will be structured
with a `delegation_id` and `status` field. The exact format depends on the
Hermes gateway's completion rendering. The orchestrator should check for:

- A `delegation_id` that matches one it dispatched
- A `goal` that matches a stage it delegated
- Content describing a completed subagent task

If uncertain, read the output file — if it exists and is complete, treat it as
a completion.

### 4.2 Procedure per completion event

```
When a completion event arrives:

1. IDENTIFY which stage completed:
   - Match the goal text against known stages
   - OR match the delegation_id against tracked IDs
   - OR check which output file was written

2. READ the output file:
   read_file(path="/tmp/fable-test/stageN_NAME.md")

3. VERIFY the model tag:
   terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py verify --output /tmp/fable-test/stageN_NAME.md --expected-model MODEL_NAME")

4. RUN verification checks:
   Follow the stage-specific verification from references/verification-templates.md.
   For Research: web_search URLs, check source count, check output structure.
   For Plan: check structure, audience tiers, methodology section.

5. UPDATE todo:
   todo(todos=[{id:"stage-N", content:"Stage N: [name]", status:"completed"}], merge=true)

6. UPDATE work log:
   write_file(path="WORK_LOG.md", content="...")
   Include: delegation_id, model used, verification result, duration.

7. CHECK if both async stages are complete:
   If Research AND Plan are both completed → proceed to Implement (sync path).
   If only one is done → wait for the other completion event.

8. ON FAILURE:
   If verification fails or output is missing:
   - Log the failure in WORK_LOG.md
   - If model tag mismatch: re-run config cycling and retry the stage (sync this time)
   - If output file missing but status=completed: subagent may have failed before
     writing. Re-run the stage (sync).
   - If status=error or status=interrupted: follow timeout-recovery-recipe.md
```

### 4.3 Tracking dispatched IDs

The orchestrator must track which `delegation_id` maps to which stage. Store
this in a temporary note (not persistent memory — it's session-local):

```
Dispatched:
  async-abc123 → Stage 1: Research (deepseek-v4-flash)
  async-yyy456 → Stage 2: Plan (glm-5.1)
```

Use simple text in the working context. No file needed — the IDs only matter
within the current session. If the session resets before completions arrive,
the cron continuation procedure handles recovery (read WORK_LOG.md, check
which stages are still pending).

---

## 5. Config Cycling Timing — Documentation Update

### 5.1 The snapshot guarantee

The child agent is built by `_build_child_agent()` BEFORE `executor.submit()`
dispatches the worker. The model, provider, base_url, api_key, and api_mode
are all passed to the constructor at build time. The background worker runs
with a fully-initialised child agent — it does not re-read the config.

**This means**: cycling delegation config for Stage 2 immediately after
dispatching Stage 1 is safe. Stage 1's child already has its model/provider
snapshotted.

### 5.2 The async cycle sequence

```
Time →
  1. route_config.py set --stage research  → config = flash, opencode-go
  2. delegate_task(goal="Research...", background=true)
     → child BUILT with flash, opencode-go ← SNAPSHOT
     → dispatched to daemon thread
  3. route_config.py set --stage plan       → config = glm, opencode-go  ← SAFE
  4. delegate_task(goal="Plan...", background=true)
     → child BUILT with glm, opencode-go ← SNAPSHOT
     → dispatched to daemon thread
  5. route_config.py restore                → config = original  ← SAFE
```

Both children run with their snapshotted configs. No race condition.

### 5.3 What to add to config-cycling.md

A new subsection "Async Safety" that documents the snapshot guarantee and the
timing diagram above. No procedural changes.

---

## 6. Verification Gating — Updated

### 6.1 Deferred verification

For async stages, verification cannot run immediately after dispatch because
the output file doesn't exist yet. Verification is **deferred** until the
completion event arrives.

The verification procedure itself is identical — same checks from
`references/verification-templates.md`. Only the timing changes:

| | Sync stages | Async stages |
|---|------------|-------------|
| When to verify | Immediately after delegate_task returns | When completion event arrives |
| How to verify | Same checks | Same checks |
| File exists? | Guaranteed (subagent just wrote it) | Check with read_file — if missing, subagent failed |
| Retry on failure | Re-run delegate_task (sync) | Re-run delegate_task (sync) — never retry async |

### 6.2 The "both must pass" gate

The Implement stage depends on BOTH Research AND Plan. It must NOT start
until BOTH completion events have arrived AND BOTH verification checks have
passed.

If Research passes but Plan fails verification, the orchestrator must:
1. Log Plan's failure in WORK_LOG.md
2. Re-run Plan (sync) with the same prompt
3. Wait for it to complete
4. Re-verify
5. Only then proceed to Implement

---

## 7. SKILL.md Changes — Exact Sections to Patch

### 7.1 Version header

Change `version: 7.0.0` to `version: 7.1.0`.

### 7.2 Section: "Stage Execution Procedure"

Replace the entire section. The new version has:

1. **Decision table**: Which stages use async vs sync (the table from §3.1)
2. **Async path**: The Research + Plan dispatch sequence from §3.2
3. **Sync path**: The existing Implement+ procedure (unchanged)
4. **Completion handling**: The procedure from §4.2
5. **In-between state**: What to do while waiting (§3.4)

### 7.3 Section: "Model Routing"

Add a note under "Config Cycling Procedure (Mandatory)":

> **Async safety**: When dispatching Research and Plan with `background=true`,
> config cycling between dispatches is safe. The child agent snapshots its
> model/provider at construction time, before the background worker starts.
> See `references/config-cycling.md` for the timing guarantee.

### 7.4 Section: "Verification Checklist (Mandatory)"

Add two checklist items:

```
- [ ] For async stages: Did you wait for the completion event before verifying?
- [ ] For async stages: Did you defer model tag verification until the output file exists?
```

### 7.5 Section: "Example: Building a Competitive Analysis"

Update the example to show the async dispatch of Research and Plan:

```
### Step 2: Execute Stage 1 (Research) — ASYNC

Dispatch Research in the background:
  terminal(route_config.py set --stage research)
  delegate_task(goal="Research: ...", background=true)
  # Returns delegation_id: async-abc123

### Step 3: Execute Stage 2 (Plan) — ASYNC

Dispatch Plan in the background (safe — Research child already snapshotted):
  terminal(route_config.py set --stage plan)
  delegate_task(goal="Plan: ...", background=true)
  # Returns delegation_id: async-yyy456

### Step 4: Wait for completion events

When Research completes:
  - Read /tmp/fable-test/stage1_research.md
  - Verify model tag
  - Run verification checks
  - Update todo and work log

When Plan completes:
  - Read /tmp/fable-test/stage2_plan.md
  - Verify model tag
  - Run verification checks
  - Update todo and work log

When BOTH are verified → proceed to Stage 3 (Implement) — SYNC
```

### 7.6 Section: "Common Pitfalls"

Add two new pitfalls:

```
### Pitfall 10: Verifying async stages before they complete

**What could happen:** The orchestrator dispatches Research with
`background=true`, then immediately tries to `read_file` the output and run
`route_config.py verify`. The subagent hasn't finished writing yet — the file
is empty or missing.

**The correct approach:** After dispatching an async stage, DO NOTHING until
the completion event arrives as a new turn. Only then read the output, verify,
and update the todo list.

### Pitfall 11: Cycling config for the next stage while an async child is
still being built

**What could happen:** If the orchestrator cycles config between
`delegate_task(background=true)` and the child's internal construction,
the child might read the wrong config.

**Why this can't happen:** The child agent is built synchronously inside
`delegate_task()` BEFORE the background worker is dispatched to the thread
pool. The config is read at construction time and snapshotted. Cycling config
immediately after `delegate_task()` returns is safe.

**The correct approach:** Cycle config for the next stage immediately after
`delegate_task(background=true)` returns. The previous child is already
snapshotted.
```

### 7.7 Section: "Version History"

Add:

```
- **v7.1**: Async subagent support. Research and Plan now dispatch with
  `delegate_task(background=true)` for true parallel execution. Completion
  events arrive as new turns. Sync path unchanged for Implement+. Config
  cycling confirmed snapshot-safe for async dispatch.
```

---

## 8. Reference File Changes

### 8.1 `references/guardrails.md`

In the Research and Plan guardrails blocks, add one line after the effort
directive:

```
- ASYNC: This stage runs in the background. Write your output file BEFORE
  reporting completion — the orchestrator will verify it after you finish.
```

Do NOT add this to Implement/Verify/Critique/Consolidate guardrails — those
stages stay sync.

### 8.2 `references/config-cycling.md`

Add a new section at the end:

```markdown
## Async Safety

When `delegate_task(background=true)` is used, the child agent is constructed
synchronously inside the `delegate_task()` call — before the background worker
is dispatched to the daemon thread pool. The model, provider, base_url,
api_key, and api_mode are all passed to `_build_child_agent()` at construction
time and snapshotted in the child agent object.

### Timing guarantee

\```
Time →
  1. route_config.py set --stage research  → config = research-model
  2. delegate_task(goal="...", background=true)
     → child BUILT with research-model ← SNAPSHOTTED
     → dispatched to daemon thread
  3. route_config.py set --stage plan      → config = plan-model  ← SAFE
  4. delegate_task(goal="...", background=true)
     → child BUILT with plan-model ← SNAPSHOTTED
     → dispatched to daemon thread
  5. route_config.py restore              → config = original  ← SAFE
\```

Both children run with their snapshotted configurations. The config cycling
between dispatches does not affect already-dispatched children.
```

### 8.3 `references/model-verification.md`

Add a subsection "Deferred Verification for Async Stages":

```markdown
### Deferred Verification (Async Stages)

When Research and Plan are dispatched with `delegate_task(background=true)`,
verification is deferred until the completion event arrives as a new turn.

1. **After dispatch**: Do not attempt to verify — the output file doesn't
   exist yet.
2. **When completion event arrives**: The output file now exists. Proceed with
   normal verification: read file, check model tag with `route_config.py
   verify`, run stage-specific checks.
3. **If verification fails**: Re-run the stage synchronously
   (`background=false`). Never retry an async stage with `background=true` —
   the capacity might be exhausted and you need the result immediately.

The verification checks themselves are identical — only the timing changes.
```

### 8.4 `references/delegate-task-model-fallback.md`

Update the decision tree to include the async capacity rejection path:

```
Is native per-call routing available? (run detect_routing.py)
├─ Yes ──> Use delegate_task(model={...}) directly.
└─ No ──> Use config cycling.
           ├─ Is this Research or Plan?
           │  ├─ Yes → Try async: delegate_task(goal="...", background=true)
           │  │         ├─ Returns {"status": "dispatched"} → Wait for completion event.
           │  │         └─ Returns {"status": "rejected"} → Fall back to sync.
           │  └─ No → Use sync: delegate_task(goal="...", background=false)
           └─ On failure: fall back to run_stage.py terminal mode.
```

### 8.5 `references/work-log-template.md`

Add an async delegation log entry format:

```markdown
## Async Delegation Log
| Delegation ID | Stage | Dispatched | Completed | Model | Status |
|---------------|-------|------------|-----------|-------|--------|
| async-abc123 | Research | 14:30:00 | 14:35:19 | deepseek-v4-flash | ✅ |
| async-yyy456 | Plan | 14:30:05 | 14:30:34 | glm-5.1 | ✅ |
```

---

## 9. Template Changes

### 9.1 `templates/stage-prompts/research.md`

After the `BEHAVIORAL DIRECTIVES` block and before `GUARDRAILS`, add:

```
ASYNC: This stage runs in the background via delegate_task(background=true).
Write your complete output to {{output_path}} BEFORE reporting completion.
The orchestrator will read your output file and verify it after you finish.
Do not wait for verification — just write the file and return your summary.
```

### 9.2 `templates/stage-prompts/plan.md`

Same addition as research.md — the async directive.

### 9.3 Other templates

No changes. Implement, Verify, Critique, Consolidate stay sync.

---

## 10. Script Changes

**None required.** Every script in `scripts/` works as-is:

- `route_config.py` — config cycling is snapshot-safe, no changes
- `detect_routing.py` — async is orthogonal to model routing
- `run_stage.py` — terminal fallback is sync-only by nature, no changes
- `fable_routing.py` — routing table unchanged
- `verify_models.py` — provider check unchanged
- `auto_detect_providers.py` — provider detection unchanged

---

## 11. Implementation Order

### Phase 1: Documentation (no dependencies)

1. **§7.1** — Bump version to 7.1.0 in SKILL.md
2. **§7.2** — Rewrite "Stage Execution Procedure" section
3. **§7.3** — Add async safety note to "Model Routing"
4. **§7.4** — Add async items to verification checklist
5. **§7.5** — Update example to show async dispatch
6. **§7.6** — Add Pitfalls 10 and 11
7. **§7.7** — Update version history
8. **§8.1** — Add `ASYNC` directive to guardrails (Research and Plan only)
9. **§8.2** — Add async safety section to config-cycling.md
10. **§8.3** — Add deferred verification to model-verification.md
11. **§8.4** — Update decision tree in delegate-task-model-fallback.md
12. **§8.5** — Add async delegation log format to work-log-template.md
13. **§9.1** — Add async directive to research.md template
14. **§9.2** — Add async directive to plan.md template

### Phase 2: Validation

15. Run the full Fable pipeline with `background=true` on Research and Plan
16. Verify completion events arrive correctly
17. Verify config cycling between async dispatches is safe (different models)
18. Verify sync fallback when capacity is full
19. Verify deferred verification works (output file exists when event arrives)
20. Test interruption: `/stop` during async stages, verify recovery

---

## 12. Testing Checklist

- [ ] Research dispatched async with correct model (verify tag after completion)
- [ ] Plan dispatched async with correct model (verify tag after completion)
- [ ] Config cycling between Research and Plan dispatches — both get correct models
- [ ] Config restored after both dispatches
- [ ] Completion events arrive as new turns with delegation_id and summary
- [ ] Orchestrator identifies completion events and routes to correct stage
- [ ] Deferred verification passes — output file exists when event arrives
- [ ] Todo updated correctly after each completion event
- [ ] WORK_LOG.md updated with async delegation IDs
- [ ] Implement starts only after BOTH Research and Plan verified
- [ ] Sync stages (Implement+) work exactly as before
- [ ] Capacity rejection → sync fallback works
- [ ] Interruption during async stages → files verified, retried if needed

---

## 13. Edge Cases

### 13.1 Only one async stage completes

If Research finishes but Plan is still running (or vice versa), the
orchestrator verifies the completed stage and waits for the other. It must NOT
proceed to Implement with only partial research/plan data.

### 13.2 Completion event arrives during sync stage execution

If the orchestrator is mid-Implement (sync) when Plan's completion event
arrives, it must NOT interrupt the sync stage. It should note the completion,
queue the verification, and handle it after the current sync stage finishes.
In practice, this is unlikely because Research and Plan are typically much
faster than Implement — but the orchestrator must handle it.

### 13.3 Session resets before completions arrive

If the session resets (daily reset, `/new`, crash) while Research and Plan are
running async, the completion events will still arrive in the new session. The
cron continuation procedure must handle this:

1. Read WORK_LOG.md — see Research and Plan marked as `in_progress`
2. Wait for completion events (they'll arrive as new turns in the new session)
3. Or, if completions never arrive (child crashed), check if output files
   exist — if yes, verify them directly. If no, re-run the stages sync.

### 13.4 User sends a message during async waiting

The orchestrator responds with a status update: which stages are running,
expected completion, model assigned. Then returns to waiting.

---

## 14. What the Implementer Must NOT Do

1. **Do NOT add async to Implement, Verify, Critique, or Consolidate.**
   These stages have sequential dependencies. Async adds complexity with
   no parallelism benefit.

2. **Do NOT change `route_config.py`.** Config cycling is snapshot-safe.
   Adding async-specific logic to the config cycler would couple it to
   a delegate_task feature that may change.

3. **Do NOT remove the sync path.** It remains the default for 4 of 6
   stages and is the fallback when async capacity is full.

4. **Do NOT attempt batch async (`tasks=[...]` with `background=true`).**
   The feature doesn't support it. Single-task async only.

5. **Do NOT persist delegation IDs to memory.** They are session-local.
   Use WORK_LOG.md for cross-session handoff.
