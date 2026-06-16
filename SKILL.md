---
name: fableous
description: >
  Strict multi-stage execution orchestrator for Hermes. Uses native Hermes tools
  exclusively. Decomposes tasks into 6 stages, enforces cross-family verification,
  model verification, and dynamic replanning. No Python engine. No subprocess hacks.
  Trigger on multi-stage, multi-source, or multi-session work.
version: 7.3.1
author: Nick Smith / Point Clear Advisory
license: MIT
metadata:
  hermes:
    tags: [orchestration, multi-agent, fable-mode, planning, verification, meta, native]
    related_skills: [plan, subagent-driven-development, superpowers]
    requires_toolsets: [delegation, todo, terminal, web, file, session_search, memory, cronjob]
---

# Fable Orchestrator v7.3

A strict procedural orchestrator that enforces staged execution discipline using **only native Hermes tools**. No Python engine. No SQLite. No daemon. No subprocess hacks.

The value is the loop: decompose before acting, route to the right model for each stage, verify with checks that can actually fail, verify the model used, critique on a different model family, consolidate into a canonical deliverable, and replan when obstacles invalidate the plan.

## What it does

- Breaks complex tasks into 6 numbered stages with explicit dependencies
- Routes each stage to a model suited for that cognitive task
- Enforces cross-family verification (critique NEVER runs on the same model family as implementation)
- Verifies the actual model used by each subagent
- Runs failable verification checks at every stage
- Performs dynamic replanning when stage outputs invalidate the plan
- Produces a single canonical deliverable via consolidation
- Maintains a structured work log for multi-session continuity
- Fails open with retry chains when models or providers are unavailable

## What it does not do

- It does not make a weak model stronger. Structure imposes discipline, not reasoning quality.
- It does not replace domain skills. Use `superpowers` for software, `research-workflows` for research, `jkd-content` for writing.
- It does not run on trivial tasks. One-shot work with an obvious approach skips this loop entirely.

## When to Trigger (v6.1 Checklist)

Fable is powerful but not free. Use this checklist before invoking it.

### Trigger if YES to any of these

1. **Explicit request** — the user asked for thorough/systematic/Fable mode:
   - "do this thoroughly", "be systematic", "deep work mode", "run this through fable", etc.
2. **Multi-part scope** — the task spans multiple files, sources, sessions, domains, or deliverables.
3. **High miss risk** — a one-shot attempt would plausibly miss something important.

### Also consider triggering if

4. **Verification/critique value** — there is more than one valid approach, or the output benefits from independent cross-checking.

### Skip Fable if

- The task has one obvious approach.
- It clearly fits in a single pass.
- None of the above conditions apply.

**Rule of thumb:** when in doubt, trigger Fable. The cost of running Fable on a slightly simple task is lower than the cost of skipping Fable on a task that needed it.

---

## Native Tool Inventory

You MUST use these Hermes tools exclusively. Do NOT write custom Python, do NOT use raw subprocess, do NOT use external scripts.

| Purpose | Tool | How you use it |
|---------|------|----------------|
| Track stages | `todo` | Create the stage map. Update status after each stage. |
| Delegate work | `delegate_task` | Spawn subagents for each stage. Model is set via config cycling. |
| Route models | `terminal` | Run `route_config.py` to set the model/provider before each `delegate_task` call. |
| Enforce model switching | `terminal` | Use ONLY when config cycling fails. Spawn `hermes chat -q` with explicit `-m` and `--provider` flags. |
| Read outputs | `read_file` | Read stage outputs, work log, config files. |
| Write outputs | `write_file` | Save stage outputs, work log, FINAL.md. |
| Find files | `search_files` | Locate stage outputs, verify file existence. |
| Web research | `web_search`, `web_extract` | Gather sources for research stages. |
| Run checks | `terminal`, `execute_code` | Run tests, validate URLs, check file sizes. |
| Ask questions | `clarify` | Ask the user clarifying questions before decomposition. |
| Async scheduling | `cronjob` | Set up cron jobs for multi-session execution. |
| Find context | `session_search` | Recover context from past sessions. |
| Persist notes | `memory` | Save user preferences, environment details. |
| Multi-agent queue | `kanban` | Optional: use for complex multi-task tracking instead of custom SQLite. |

---

## Model Routing

You MUST route each stage to the assigned model. Since `delegate_task` does not support per-call model routing, use **config cycling** to set the model and provider before each stage.

### Config Cycling Procedure (Mandatory)

Before each `delegate_task` call, you MUST:

1. Run `route_config.py set --stage STAGE_NAME` to update `delegation.model` and `delegation.provider`
2. Call `delegate_task(goal="...", context="...", toolsets=[...])` — do NOT pass a model parameter
3. After the subagent returns, run `route_config.py verify --output STAGE_OUTPUT --expected-model MODEL` to confirm the model tag
4. Proceed to the next stage (step 1 repeats with the next stage's model)

On completion or error, you MUST run `route_config.py restore` to restore the original delegation config.

### Async Safety

When dispatching Research and Plan with `delegate_task(background=true)`, config cycling between dispatches is safe. The child agent snapshots its model/provider at construction time, before the background worker starts. Config cycling for the next stage immediately after `delegate_task(background=true)` returns does not affect the already-dispatched child.

See `references/config-cycling.md` for the full timing guarantee and timing diagram.

### Why Config Cycling

`delegate_task` resolves the child's model and provider from `delegation.model` and `delegation.provider` in `~/.hermes/config.yaml`. These values are read from disk on every call (no caching). By setting them to the desired values before each call, the child agent uses the correct model/provider — guaranteed, not suggested.

Both `delegation.model` AND `delegation.provider` must be set together. Setting only the model without the provider causes the child to use the correct model name on the wrong provider's endpoint, which fails.

### Detection: Native vs. Config Cycling

Run `scripts/detect_routing.py` at the start of execution:

```bash
python3 scripts/detect_routing.py
```

- If it reports `{"native_routing": true}` → use `delegate_task(model={"model": "...", "provider": "..."})` directly
- If it reports `{"native_routing": false}` → use config cycling (the default for current Hermes versions)

### When Config Cycling Doesn't Apply

- If `detect_routing.py` reports native per-call routing is available, use `delegate_task(model={"model": "...", "provider": "..."})` directly instead of config cycling.
- If config cycling fails (config file permissions, concurrent access), fall back to `run_stage.py --stage STAGE` which uses `hermes chat -q` terminal spawning.

### Default Routing Table

Auto-detect available providers from the user's Hermes config (`~/.hermes/config.yaml` and `~/.hermes/.env`). Use the best available model for each stage.

| Stage | Primary | Secondary | Tertiary | Rationale |
|-------|---------|-----------|----------|-----------|
| Research | `deepseek-v4-flash` (Opencode Go) | `gemini-2.5-flash-lite` (Google) | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` (OpenRouter) | Fast, broad, cheap |
| Plan | `glm-5.1` (Opencode Go) | `gemini-2.5-pro` (Google) | `deepseek-v4-pro` (Opencode Go) | Structured reasoning |
| Implement | `kimi-k2.7-code` (Opencode Go) | `kimi-k2.6` (Opencode Go) | `gemini-2.5-pro` (Google) | Code-specialized |
| Verify | `deepseek-v4-pro` (Opencode Go) | `gemini-2.5-pro` (Google) | `kimi-k2.6` (Opencode Go) | Different architecture from coder |
| Critique | `glm-5.1` (Opencode Go) | `gemini-2.5-pro` (Google) | `kimi-k2.6` (Opencode Go) | Independent evaluation |
| Consolidate | `deepseek-v4-pro` (Opencode Go) | `glm-5.1` (Opencode Go) | `gemini-2.5-pro` (Google) | Reads all stages, produces canonical output |

### Token-Budget / Lightweight Mode

When the user prioritises speed and cost, you MAY reduce routing cost. Two sub-modes exist — you MUST pick the right one based on the user's exact words.

**CRITICAL: Both modes are opt-IN, not opt-OUT.** You MUST NOT enter either mode on your own judgement. If the user says "run this through Fable" with no cost directive, use the full routing table with multi-model config cycling. See Pitfall 14.

### Sub-mode 1: Primary-Only Routing (cheapest PER STAGE)

**Trigger words:** "cheapest models", "use the cheapest models in the routing table", "keep stages brief" (without "single model"), "token-budget test, not a full production run", or any phrase where the user references the routing table directly.

**What it means:** Use the **primary** model from each stage's routing entry. Never fall back to secondary/tertiary unless the primary fails. The routing table still runs — Research gets flash, Plan gets glm, Implement gets kimi, etc. Multi-model routing and cross-family verification are preserved. Only the fallback chain is removed.

**What changes:**
- Every stage uses its PRIMARY model from the routing table — no secondary/tertiary fallback unless primary returns an error
- Config cycling still runs with `route_config.py set --stage NAME` (not `--model` override)
- Cross-family verification is fully preserved — Verify and Critique run on different families from Implement
- Model tag verification still applies

**This is the DEFAULT cost-reduction mode.** When in doubt between the two, use primary-only. It preserves the anti-hallucination benefit of multi-family routing while cutting fallback chains.

### Sub-mode 2: Single-Model Flatlining (one model for ALL stages)

**Trigger words:** "all on one model", "single cheapest model", "flatline everything", "use only deepseek-v4-flash", "one model for everything" — explicit single-model language.

**What it means:** Override the entire routing table. Every stage runs on the same cheap model (e.g. `deepseek-v4-flash`). Cross-family verification is lost — Verify, Critique, and Implement all share the same model family.

**What changes:**
- All 6 stages use the same model — typically the cheapest available
- Cross-family verification is relaxed — Verify and Critique may run on the same model as Implement
- Config cycling runs with `route_config.py set --model CHEAP_MODEL --provider PROVIDER` (the `--stage` flag is optional)
- Model tag verification still applies

**Tradeoff acknowledged:** The anti-hallucination benefit of running Critique on a different model family is lost. This is acceptable when the user has explicitly requested all-on-one-model execution. The pipeline structure itself (separate verify and critique stages with distinct prompts) still catches most errors.

### What is preserved (both modes):
- All 6 stages still run in order. No stages are skipped.
- Failable verification checks still run in Stage 4.
- Critique still runs in Stage 5.
- Consolidation still produces a single canonical deliverable.
- The work log, todo tracking, and config-restore procedures are unchanged.

### Decision boundary (exact words → mode mapping):

| User says | Mode | Routing |
|-----------|------|---------|
| "cheapest models in the routing table" | Primary-only | flash → glm → kimi → pro → glm → pro |
| "token-budget test" (no "single model") | Primary-only | Same as above |
| "use the cheapest model for everything" | Single-model | flash → flash → flash → flash → flash → flash |
| "all on deepseek-v4-flash" | Single-model | flash → flash → flash → flash → flash → flash |
| "run this through Fable" (no cost directive) | Full routing | Normal table with fallback chains |
| (no explicit trigger) | Full routing | Normal table with fallback chains |

**Example — primary-only mode:**
```bash
terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py set --stage research")
# → deepseek-v4-flash (primary, no fallback chain needed)
delegate_task(goal="Research: ...", context="...")
```

**Example — single-model mode:**
```bash
terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py set --model deepseek-v4-flash --provider opencode-go")
delegate_task(goal="Research: ...", context="...")
# Same model for all subsequent stages
```

### YAML Override

If the user provides a `fable-config.yaml` in the project directory, you MUST use it instead of the defaults.

```yaml
# fable-config.yaml
routing:
  research:
    primary: {model: "deepseek-v4-flash", provider: "opencode-go"}
    secondary: {model: "gemini-2.5-flash-lite", provider: "google"}
    tertiary: {model: "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", provider: "openrouter"}
  # ... etc for all stages
```

Read this file at the start of execution with `read_file`. If it does not exist, use the auto-detected defaults.

### What Changed From v6.1

- **v6.1**: `delegate_task(model="deepseek-v4-flash")` was documented as the primary method. It didn't work — `delegate_task` has no `model` parameter and the value was silently ignored. Every subagent ran on the parent session's model.
- **v7.0**: Config cycling is the primary method. Before each `delegate_task` call, update the Hermes config. The `[MODEL: ...]` tag is now a verification check, not the sole verification method — the config guarantees routing.

---

## The 6-Stage Pipeline

You MUST follow this pipeline. Do NOT skip stages. Do NOT merge stages unless the task is trivial enough to skip the orchestrator entirely.

```
Stage 1: Research    →  gather sources, extract claims, verify URLs
Stage 2: Plan        →  architecture, files, audience, dependencies
Stage 3: Implement   →  first pass, write code/content, save to disk
Stage 4: Verify      →  run tests, trace sources, check consistency
Stage 5: Critique    →  independent review, name weaknesses, flag fixes
Stage 6: Consolidate →  read all stages, apply fixes, produce FINAL.md
```

### Dependencies

- Stage 1 (Research) and Stage 2 (Plan) have NO dependencies. They MAY run in parallel.
- Stage 3 (Implement) depends on Stage 1 and Stage 2. It MUST run after both complete.
- Stage 4 (Verify) depends on Stage 3. It MUST run after Implement completes.
- Stage 5 (Critique) depends on Stage 3 and Stage 4. It MUST run after both complete.
- Stage 6 (Consolidate) depends on ALL prior stages. It MUST run last.

---

## Behavioral Directives (Per-Stage Prompts)

Every stage prompt includes three behavioral directives derived from Anthropic's Fable prompting research. These transfer across model families and cost nothing:

1. **Lead with the outcome.** The subagent's first sentence must answer "what happened" or "what I found." No throat-clearing, no background first. The bottom line goes first.

2. **Ground every claim.** If the subagent cannot verify a claim against evidence, it must say "unverified" — not present it as confirmed. In the Critique stage, unconfirmed weaknesses are "suspected but unconfirmed."

3. **Match effort to the task.** Each stage has an effort calibration:
   - **Research**: Broad and fast. Gather widely, don't over-analyse.
   - **Plan**: Structured reasoning. Think about dependencies carefully.
   - **Implement**: Deep and thorough. This is the main deliverable.
   - **Verify**: Focused and precise. Check specifics, don't rewrite.
   - **Critique**: Sharp and independent. Challenge assumptions.
   - **Consolidate**: Comprehensive and final. Resolve all conflicts.

These directives are injected into every stage prompt and every guardrails block. They are not suggestions.

## Stage Execution Procedure

The procedure has two paths: **async** for Research and Plan (no dependencies, can run in parallel), and **sync** for Implement through Consolidate (sequential dependencies).

### Decision: Sync vs Async

| Stage | Method | Reason |
|-------|--------|--------|
| Research | **async** (`background=true`) | No dependencies. Runs in parallel with Plan. |
| Plan | **async** (`background=true`) | No dependencies. Runs in parallel with Research. |
| Implement | **sync** (`background=false`) | Depends on Research + Plan. Must wait for both. |
| Verify | **sync** (`background=false`) | Depends on Implement. Must wait. |
| Critique | **sync** (`background=false`) | Depends on Implement + Verify. Must wait. |
| Consolidate | **sync** (`background=false`) | Depends on all prior stages. Must wait. |

**Fallback rule**: If `delegate_task(background=true)` returns `{"status": "rejected"}` (capacity full), fall back to sync for that stage. Log the fallback in WORK_LOG.md.

---

### Async Path: Research and Plan

```
# ===== DISPATCH BOTH IN SEQUENCE =====

# Step 1: Route and dispatch Research
terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py set --stage N_NAME")
todo(todos=[{id:"stage-N", content:"Stage N: [name]", status:"in_progress"}], merge=true)

delegate_task(
  goal="Research: [full prompt from template]",
  context="[prompt with ASYNC directive]",
  toolsets=["web", "file"],
  background=true
)
# Returns: {"status": "dispatched", "delegation_id": "async-xxx"}
# SAVE the delegation_id for the completion handler.

# Step 2: Route and dispatch Plan (SAFE — Research child already snapshotted)
terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py set --stage N+1_NAME")
todo(todos=[{id:"stage-N+1", content:"Stage N+1: [name]", status:"in_progress"}], merge=true)

delegate_task(
  goal="Plan: [full prompt from template]",
  context="[prompt with ASYNC directive]",
  toolsets=["file"],
  background=true
)
# Returns: {"status": "dispatched", "delegation_id": "async-yyy"}

# Step 3: Restore config (both children already snapshotted)
terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py restore")

# Step 4: Wait for completion events
# The orchestrator now DOES NOTHING until the completion events arrive as new turns.
# When a completion event arrives, follow the Completion Handling procedure below.
```

### Completion Handling

When an async delegation completion event arrives as a new turn, follow this procedure:

```
1. IDENTIFY which stage completed:
   - Match the goal text against known stages
   - OR match the delegation_id against the IDs you tracked
   - OR check which output file was written

2. READ the output file:
   read_file(path="/path/to/stageN_NAME.md")

3. VERIFY the model tag:
   terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py verify --output /path/to/stageN_NAME.md --expected-model MODEL_NAME")

4. RUN verification checks:
   Follow the stage-specific checks from references/verification-templates.md.

5. UPDATE todo:
   todo(todos=[{id:"stage-N", content:"Stage N: [name]", status:"completed"}], merge=true)

6. UPDATE work log:
   write_file(path="WORK_LOG.md", content="...")
   Include: delegation_id, model used, verification result, duration.

7. CHECK if both async stages are complete:
   - If Research AND Plan are both completed → proceed to Implement (sync path).
   - If only one is done → wait for the other completion event.

8. ON FAILURE:
   - If verification fails or output is missing, re-run the stage synchronously.
   - If status=error or status=interrupted, follow timeout-recovery-recipe.md.
```

### Tracking Dispatched IDs

The orchestrator must track which `delegation_id` maps to which stage. Store in the working context:

```
Dispatched:
  async-xxx → Stage 1: Research (deepseek-v4-flash)
  async-yyy → Stage 2: Plan (glm-5.1)
```

These IDs are session-local. Use WORK_LOG.md for cross-session handoff.

### In-Between State

After dispatching Research and Plan (async) but before both completion events have arrived, the orchestrator is in a **waiting state**. The todo list shows both as `in_progress`.

If the user sends a message during the waiting state, the orchestrator responds with a status update: "Research and Plan are running in the background. I'll continue when both complete."

---

### Sync Path: Implement Through Consolidate

For stages 3-6, follow this exact sequence:

### Step 1: Set todo status to "in_progress"

```
todo(todos=[
  {id: "stage-N", content: "Stage N: [name]", status: "in_progress"}
], merge=true)
```

### Step 2: Route and delegate the stage

Run config cycling to set the model for this stage:
```
terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py set --stage N_NAME")
```

If `route_config.py` reports that the primary provider is not configured, it will
automatically fall back to secondary/tertiary. Check the output for the actual
model/provider set.

Then delegate (sync):
```
delegate_task(goal="...", context="...", toolsets=[...], background=false)
```

After the subagent returns, verify:
```
terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py verify --output stageN_NAME.md --expected-model MODEL_NAME")
```

### Step 3: Verify the model used

After the subagent returns, you MUST verify the model used. The model tag in the stage output is an audit trail — the actual routing was guaranteed by config cycling. Include this in the stage prompt:

```
At the top of your output, write exactly: [MODEL: your-model-name, PROVIDER: your-provider]
This tag is an audit trail. The actual model routing was set via config cycling
before this call. If the tag doesn't match the assigned model, report it but
don't retry — trust the config.
```

Read the subagent's output with `read_file`. Then verify with `route_config.py`:
```
terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py verify --output stageN_NAME.md --expected-model MODEL_NAME")
```

### Step 4: Run verification checks

You MUST run the stage-specific verification checks from `references/verification-templates.md`. Examples:

- **Research**: `web_search` to verify cited URLs return HTTP 200. `read_file` to verify output contains "Source:".
- **Software**: `terminal` to run `npm test` or `pytest`. Verify exit code is 0.
- **Data**: `execute_code` to run data quality assertions. Verify no nulls, no duplicates.
- **Writing**: `read_file` to verify output matches the brief. Check word count, structure, required sections.

If ANY check fails, the stage is NOT complete. Do NOT proceed.

### Step 5: Update todo status

```
todo(todos=[
  {id: "stage-N", content: "Stage N: [name]", status: "completed"}
], merge=true)
```

### Step 6: Update work log

```
write_file(path="WORK_LOG.md", content="...")
```

Format:
```
## Session [N] — [date]
- Stage [N] completed: [name]
- Model used: [model] ([provider])
- Verification: [passed / failed: details]
- Decisions: [what was decided and why]
- Open: [what remains]
```

### Step 7: Check replanning triggers

Compare the stage output against the expected output defined in the plan. If any trigger fires (see Replanning Triggers section), you MUST replan before proceeding.

---

## Model Verification: The Critical Anti-Hallucination Measure

### The Problem

`delegate_task` has **no per-call `model` parameter**. Source-code audit confirmed: the tool schema, dispatch function, and Python function signature all lack a `model` field. Every subagent inherits the parent session's model regardless of what the tool call specifies. See `references/delegate-task-model-routing-audit.md` for full evidence.

The `[MODEL: ...]` tag in stage prompts is self-reported text, not proof of which model ran.

### The Solution

ALL model routing must use **config cycling** via `route_config.py`. This controls routing at the infrastructure level.

1. **Primary method**: Before each `delegate_task` call, run:
   ```
   terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py set --stage STAGE_NAME")
   ```

2. **Confirmation method**: After the subagent returns, verify via:
   ```
   terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py verify --output STAGE_OUTPUT --expected-model MODEL_NAME")
   ```

3. **Fallback method**: If config cycling fails twice, use:
   ```
   terminal(command="hermes chat -q \"$(cat stage_prompt.txt)\" -m MODEL --provider PROVIDER -Q -t web,terminal,file --accept-hooks", timeout=300)
   ```
   Or use `scripts/run_stage.py` for automatic secondary/tertiary fallback.

**Tag vs. config:** If the subagent output contains the correct `[MODEL: ...]` tag but config says something different, treat verification as FAILED. If the config was set correctly and the subagent returned successfully, trust the config even if the tag is missing.

### Enforcement Rules

- **Research and Plan**: Use config cycling + async (`delegate_task(background=true)`). Deferred verification until completion event arrives. If async rejected, fall back to sync.
- **Implement**: Use config cycling. Verify the model tag with `route_config.py verify`. If verification fails, retry with secondary.
- **Verify**: Use config cycling. **MUST be different family from Implement.**
- **Critique**: Use config cycling. **MUST be different family from Implement.** No exceptions.
- **Consolidate**: Use config cycling. **MUST be different family from Implement.** No exceptions.

**Do NOT pass a `model` parameter to `delegate_task` — it has no per-call `model` parameter.** Every subagent inherits the parent session's model regardless of what you pass. Use config cycling instead.

### Retry Chain

If a model fails (rate limit, auth error, 500, verification failure):
1. Log the failure in the work log.
2. Retry with the secondary model.
3. If that fails, retry with the tertiary model.
4. If all fail, mark the stage as blocked and `clarify` with the user.

---

## Verification Gates

You MUST define a pass condition for every stage before delegating it. "I reviewed it and it looks right" is NOT a check.

### Acceptable checks

- A test that runs and passes (software)
- A file or output that exists in the expected shape (any)
- A source actually fetched and read, not assumed (research)
- A data quality assertion that runs against real data (data)
- A diff against the stated spec (implementation)
- A content check for required sections (writing)

### Verification procedure

1. Define the checks in the stage prompt.
2. Run the checks after the stage completes.
3. If ALL checks pass, mark the stage complete.
4. If ANY check fails, mark the stage failed. Do NOT proceed to the next stage.
5. Fix the issue or re-run the stage before continuing.

### Cost rule

The cost of catching an error at Stage 3 is trivial. At Stage 8 it is catastrophic. Verify early, verify often.

---

## Replanning Triggers

You MUST check for replanning after every stage completion. If a trigger fires, you MUST rebuild the plan.

### Trigger conditions

| Trigger | Condition | Action |
|---------|-----------|--------|
| T1 | Research found fewer than 3 sources | Add "Extended Research" stage. Or skip to Implement if user provided data. |
| T2 | Plan reveals task is simpler than expected | Skip unnecessary stages. Update todo list. |
| T3 | Plan reveals task is more complex than expected | Add new stages (e.g., "Architecture Review", "Security Audit"). Update todo list. |
| T4 | Implement produces fundamentally different output than planned | Rebuild Plan from scratch. Preserve completed Research. |
| T5 | Verify fails (tests fail, sources broken, consistency errors) | Re-run Implement or add "Fix" stage before Critique. |
| T6 | Critique finds more than 3 critical weaknesses | Add "Fix" stage before Consolidate. |
| T7 | User provides new requirements mid-flight | Rebuild Plan. Preserve completed stages. |
| T8 | Model verification fails 3 times | Add "Model Fallback" note to work log. Use cheapest available model. |

### Replanning procedure

1. Read the current todo list with `todo()`.
2. Read the work log with `read_file`.
3. Analyze the gap: what changed, what was completed, what is now needed.
4. Use `delegate_task` with a "replanning" prompt to build the new DAG.
5. Update the todo list with `todo(merge=true)`.
6. Continue execution with the new plan.

### Replanning prompt template

```
You are the Fable Orchestrator replanning engine.

The current task has encountered an obstacle:
- Original plan: [plan]
- Completed stages: [list]
- Current stage: [stage]
- Obstacle: [obstacle]
- Work log: [work log]

Rebuild the stage plan. Rules:
- Preserve completed work. Do NOT re-run completed stages.
- Add new stages only if necessary.
- Remove stages that are no longer needed.
- Update dependencies.
- Return a JSON todo list.
```

---

## Consolidation

Stage 6 is the most important. You MUST produce a single canonical deliverable.

### Procedure

1. Read ALL prior stage outputs with `read_file`.
2. Read the verification corrections from Stage 4.
3. Read the critique fixes from Stage 5.
4. Run config cycling for the consolidate stage:

```
terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py set --stage consolidate")
```

5. Delegate to the Consolidate model with the full context:

```
delegate_task(
  goal="Read all prior stage outputs and produce a single canonical FINAL.md with all verification corrections and critique fixes applied.",
  context="[All stage outputs concatenated, with corrections and fixes highlighted]"
)
```

### Requirements for FINAL.md

- Single file. No appendices, no separate correction files.
- All verification corrections applied.
- All critique fixes addressed or explicitly flagged as "not fixed: [reason]".
- "Version & Caveats" header at the top.
- "Methodology & Sources" section.
- No predetermined conclusions.
- This is the ONLY published version. All prior stages are working drafts.

---

## Work Log

You MUST maintain a `WORK_LOG.md` in the project directory. This is the handoff protocol between sessions.

### Format

```markdown
# WORK_LOG — [Project Name]

## Session [N] — [YYYY-MM-DD]
- Completed: [stages done]
- Decisions: [what was decided and why]
- Failed: [what was tried and abandoned]
- Open: [what remains]

## Model Usage Log
| Stage | Intended | Actual | Verified |
|-------|----------|--------|----------|
| Research | deepseek-v4-flash | [actual] | [yes/no] |
| Plan | glm-5.1 | [actual] | [yes/no] |
| ... | ... | ... | ... |

## Replanning History
- [date]: [trigger] → [action taken]
```

### Rule

At the start of ANY continuation (new session, resumed session, cron tick), you MUST read the work log with `read_file` before doing anything else.

---

## Fail-Open Behavior

You MUST never crash because a model or provider is unavailable.

### Model exhaustion

If the primary model fails (rate limit, auth error, 500):
1. Log the failure in the work log.
2. Retry with the secondary model.
3. If that fails, retry with the tertiary model.
4. If all fail, use the cheapest available model or flag the task as blocked.

### Provider exhaustion

If Opencode Go is unavailable, fall back to Google. If Google is unavailable, use OpenRouter free tier.

### Budget exhaustion

If the user's budget is exhausted, the correct behavior is SKIP. Do NOT proceed with expensive models. Use the cheapest available or flag the task as blocked.

### Verification failure

If a check fails, the stage is NOT complete. Re-run the stage or fix the issue before proceeding. Do NOT override the check.

---

## Cron Setup for Async Execution

For multi-session tasks, you MUST set up a cron job to continue execution across session resets.

### Procedure

1. Create the task and initial todo list.
2. Set up a cron job:
   ```
   cronjob(
     action="create",
     schedule="*/15 * * * *",
     prompt="Load the fableous skill. Read the WORK_LOG.md in the project directory. Continue execution from the next pending stage. Follow the v6 stage execution procedure exactly.",
     name="fableous-[project]"
   )
   ```
3. The cron job will run every 15 minutes, read the work log, and continue from where it left off.

### Cancellation

When the task is complete, remove the cron job:
```
cronjob(action="remove", job_id="[id]")
```

---

## Example: Building a Competitive Analysis

**Task**: "Write a 1-page competitive analysis of AI ghostwriting tools for digital marketers, with 3 real competitors, verified pricing, and cited sources."

### Step 1: Create the stage map

```
todo(todos=[
  {id: "stage-1", content: "Stage 1: Research — gather 5+ competitor pages, extract pricing, verify URLs", status: "pending"},
  {id: "stage-2", content: "Stage 2: Plan — structure, audience tiers, methodology", status: "pending"},
  {id: "stage-3", content: "Stage 3: Implement — write first draft with all sources", status: "pending"},
  {id: "stage-4", content: "Stage 4: Verify — check URLs, trace claims, check consistency", status: "pending"},
  {id: "stage-5", content: "Stage 5: Critique — independent review, name weaknesses", status: "pending"},
  {id: "stage-6", content: "Stage 6: Consolidate — canonical FINAL.md with all fixes", status: "pending"},
])
```

### Step 2: Execute Stage 1 (Research) — ASYNC

Dispatch Research in the background:
  terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py set --stage research")
  # Returns: {"model": "deepseek-v4-flash", "provider": "opencode-go"}
  delegate_task(goal="Research: Gather 5+ competitor pages...", background=true)
  # Returns: {"status": "dispatched", "delegation_id": "async-xxx"}
  # Child agent is snapshotted with deepseek-v4-flash. Config cycling is safe.

Prompt includes:
- `WHY THIS MATTERS`: The user's real goal, not just the task description. This gives the subagent context for better decisions at every step.
- `ASYNC: This stage runs in the background. Write your output file BEFORE reporting completion.`
- "Gather 5+ competitor landing pages"
- "Extract pricing, features, target audience"
- "Verify every URL with web_search or web_extract"
- "Save to stage1_research.md"
- "At the top of your output, write: [MODEL: deepseek-v4-flash, PROVIDER: opencode-go]"

### Step 3: Execute Stage 2 (Plan) — ASYNC

Dispatch Plan in the background (safe — Research child already snapshotted):
  terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py set --stage plan")
  delegate_task(goal="Plan: Structure the comparison...", background=true)
  # Returns: {"status": "dispatched", "delegation_id": "async-yyy"}
  # Child agent is snapshotted with glm-5.1. Research is unaffected.

  # Restore config (both children already snapshotted):
  terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py restore")

### Step 4: Wait for completion events

When Research completion event arrives:
- Read stage1_research.md
- Verify first line matches [MODEL: deepseek-v4-flash, PROVIDER: opencode-go]
- Verify URLs with web_search or terminal(curl)
- Verify output contains "Source:" for every claim
- Update todo: stage-1 to completed
- Update WORK_LOG.md

When Plan completion event arrives:
- Read stage2_plan.md
- Verify model tag matches [MODEL: glm-5.1, PROVIDER: opencode-go]
- Verify output contains "Methodology & Caveats"
- Verify audience segmentation into 3+ tiers
- Update todo: stage-2 to completed
- Update WORK_LOG.md

When BOTH are completed and verified → proceed to Stage 3 (Implement) — SYNC

### Step 4: Execute Stage 3 (Implement)

Delegate to `kimi-k2.7-code` via Opencode Go.

Depends on Stage 1 and Stage 2. MUST run after both complete.

After completion:
- Verify model tag
- Verify output traces every claim to a source
- Verify word count and structure
- Update todo
- Update WORK_LOG.md

### Step 5: Execute Stage 4 (Verify)

Delegate to `deepseek-v4-pro` via Opencode Go.

After completion:
- Verify model tag (different from Implement)
- Verify URLs are live
- Verify internal consistency
- List factual errors with corrections
- Update todo
- Update WORK_LOG.md

### Step 6: Execute Stage 5 (Critique)

Delegate to `glm-5.1` via Opencode Go.

**Critical**: This MUST be a different model family than Implement (Kimi vs GLM).

After completion:
- Verify model tag
- Verify 3+ concrete weaknesses identified
- Verify confirmation bias checked
- Verify competitor selection justified
- Update todo
- Update WORK_LOG.md

If model verification fails (subagent ran on Kimi instead of GLM):
- Re-run config cycling and retry:
  ```
  terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py set --model glm-5.1 --provider opencode-go")
  delegate_task(goal="Stage 5: Critique — ...", context="...", toolsets=["web", "terminal", "file", "session_search"])
  ```
- If config cycling fails twice, fall back to terminal:
  ```
  terminal(command="hermes chat -q 'CRITIQUE_PROMPT' -m glm-5.1 --provider opencode-go -Q -t web,terminal,file", timeout=300)
  ```

### Step 7: Execute Stage 6 (Consolidate)

Delegate to `deepseek-v4-pro` via Opencode Go.

Read all prior stage outputs. Apply corrections. Produce FINAL.md.

After completion:
- Verify model tag
- Verify FINAL.md exists
- Verify "Version & Caveats" header present
- Verify all verification corrections applied
- Verify all critique fixes addressed or flagged
- Update todo
- Update WORK_LOG.md
- Mark task complete

---

## Verification Checklist (Mandatory)

Before you declare ANY stage complete, you MUST answer these questions. If the answer is "no", the stage is NOT complete.

- [ ] Did you run config cycling (`route_config.py set --stage X`) before delegating the stage?
- [ ] Did you call `delegate_task` (not `terminal` + `hermes chat -q`) for the stage?
- [ ] Did you verify the model tag with `route_config.py verify` after the subagent returned?
- [ ] Did ALL verification checks pass?
- [ ] Did you update the todo status to "completed"?
- [ ] Did you update the WORK_LOG.md?
- [ ] Did you check for replanning triggers?
- [ ] If this is Stage 6, did you verify FINAL.md is the single canonical deliverable?
- [ ] Did you run `route_config.py restore` after all stages completed (or on error)?
- [ ] For async stages (Research, Plan): Did you wait for the completion event before verifying?
- [ ] For async stages: Did you defer model tag verification until the output file existed?

**You MUST NOT proceed to the next stage until ALL boxes are checked.**

---

## Helper Scripts

These small utilities live in `scripts/` and make model routing concrete for
users who prefer a command-line entry point. They are optional; the skill
still works purely with native Hermes tools.

| Script | Purpose |
|--------|---------|
| `scripts/route_config.py` | Config cycling engine: set/restore/verify delegation config before/after `delegate_task` calls. **Primary routing method for v7.** |
| `scripts/verify_models.py` | Pre-flight check: confirms providers/API keys are configured. Optional `--live-test` sends a tiny prompt to each model. |
| `scripts/auto_detect_providers.py` | Reads `~/.hermes/.env` and suggests a `fable-config.yaml`. Use `--save` to write the file. |
| `scripts/run_stage.py` | Hard-routes a single stage via `hermes chat -q -m MODEL --provider PROVIDER`, with automatic secondary/tertiary fallback. Also supports `--via-config` mode. |
| `scripts/detect_routing.py` | Feature detection: checks if native per-call model routing is available in `delegate_task`. |
| `scripts/fable_routing.py` | Shared constants used by the scripts above (not a user-facing engine). |

Run them from the skill directory:

```bash
python3 scripts/route_config.py status
python3 scripts/verify_models.py
python3 scripts/auto_detect_providers.py --save
python3 scripts/run_stage.py --stage research --prompt "Your task here" --output stage1_research.md
python3 scripts/detect_routing.py
```

See `references/helper-scripts.md` for implementation details, the `.env`
reading caveat, and when to use scripts versus native tools.

---

## Reference Files

- `references/config-cycling.md` — full spec and edge cases for config cycling
- `references/verification-templates.md` — domain-specific failable checks
- `references/guardrails.md` — prompt guardrails injected into every stage
- `references/model-routing-table.md` — quick lookup of model assignments
- `references/work-log-template.md` — structured handoff protocol
- `references/replanning-triggers.md` — when and how to replan
- `references/model-verification.md` — verification hierarchy (updated: config cycling is primary)
- `references/delegate-task-model-routing-audit.md` — source-code evidence that delegate_task has no per-call model parameter
- `references/model-mismatch-recovery.md` — recovering when model verification fails
- `references/timeout-recovery-recipe.md` — recovering when `delegate_task` times out
- `references/delegate-task-model-fallback.md` — decision tree: config cycling primary, terminal fallback
- `references/helper-scripts.md` — how and when to use the `scripts/` utilities
- `references/native-first-gap-fillers.md` — audit of what Fable adds vs what Hermes already provides; decision tree for adding new code
- `references/v6-1-trigger-checklist.md` — when to invoke Fable and when to skip it
- `references/token-budget-mode.md` — single-model lightweight execution mode; when to use it and what it catches
- `references/pricing-verification-volatility.md` — SaaS pricing decays fast; pattern for verification when claims may have changed since research
- `references/ronin-partner-finder-case-study.md` — worked example of building a Hermes skill with Fable v6
- `references/skill-rename-procedure.md` — clean rename procedure for the skill directory, SKILL.md name field, route_config.py path, and git remote
- `references/test-notes.md` — known issues and test matrix
- `templates/stage-prompts/` — prompt templates for each stage
- `templates/consolidation-prompt.md` — the canonical synthesis prompt
- `templates/replanning-prompt.md` — the dynamic replanning prompt
- `examples/` — concrete execution examples (simple task, software project, research report)
- `examples/test_results.md` — living test log for recording results
- `scripts/verify_models.py` — pre-flight model availability check
- `scripts/auto_detect_providers.py` — auto-detect routing table from available providers
- `scripts/run_stage.py` — hard-routed stage runner with fallback
- `scripts/fable_routing.py` — shared routing constants for the helper scripts

## Archived Files

Legacy v1-v5 engine code and planning documents have been moved to `archive/`
for reference but are no longer used by the v6 skill.

- `archive/v5-engine/` — Python engine, daemon, v3 orchestrator, setup helpers, and v5-era docs/tests
- `archive/v4/` — v4 orchestrator and v4 test notes
- `archive/planning/` — v6 implementation plan and native-tools-first audit

Do not use these for new work. Use native Hermes tools and the helper scripts above.

## Common Pitfalls

These are the traps that caused v5 to become over-engineered and the lessons that shaped v6.

### Pitfall 1: Building a Python engine when native tools suffice

**What happened in v5:** Built a 1,200-line Python engine with SQLite, custom daemon, threading, context compression, and file operations. A later audit revealed ~70% of the engine rebuilt what Hermes already provides.

**The correct approach:** Before writing any custom code, check if Hermes already provides the capability. Use native tools first. Fill gaps with minimal code. Build a standalone engine only if the skill proves insufficient.

**v6 solution:** No engine. The skill uses `todo`, `delegate_task`, `terminal`, `cronjob`, `session_search`, `memory`, and `kanban` for everything. A few small helper scripts (`verify_models.py`, `auto_detect_providers.py`, `run_stage.py`) are kept for convenience, but they are not an engine and do not replace native tools. See `references/native-first-gap-fillers.md` for the full audit of what Fable adds versus what Hermes already provides, plus a decision tree for adding new code.

### Pitfall 2: `delegate_task` has NO per-call model parameter

**What happened:** All 5 stages ran on the parent session's model despite `model=` being passed in `delegate_task` calls. Source-code audit of `tools/delegate_tool.py` confirmed: the `DELEGATE_TASK_SCHEMA` has no `model` property, the dispatch function (`_dispatch_delegate_task`) does not extract `model` from `function_args`, and the `delegate_task()` Python function signature has no `model` parameter. Model routing is resolved **exclusively** from `delegation.model` and `delegation.provider` in `config.yaml` — global settings that apply to ALL subagents, not per-call overrides.

**Impact:** Cross-family verification is impossible via `delegate_task`. The critique runs on the same model family as the implementer, defeating the anti-hallucination measure.

**v7 solution:** Config cycling. Before every `delegate_task` call, run `route_config.py set --stage NAME` to update `delegation.model` and `delegation.provider` in the Hermes config. The child agent reads these values from disk on every call — guaranteed routing. This completely replaces the old `terminal`-spawn fallback. See `references/config-cycling.md`.

### Pitfall 3: `--provider` flag is mandatory for model switching (terminal mode)

**What happened:** Model switching failed because `delegate_task` and `hermes chat -q` were called without `--provider`. Hermes defaulted to the session's current provider and the model switch silently failed.

**Impact:** The subagent ran on the wrong provider entirely, even with the correct `-m` flag.

**v7 solution:** Config cycling via `route_config.py set` automatically sets both `delegation.model` and `delegation.provider` — no flags needed. When falling back to terminal mode (`run_stage.py` or `hermes chat -q`), always include both `-m` and `--provider`.

### Pitfall 4: `execute_code` blocked by default

**What happened:** The custom tool used `execute_code` for verification. Hermes blocks `execute_code` by default for security. The engine fell back to `subprocess` via `terminal`, which is slower and more fragile.

**Impact:** Software verification checks (pytest, mypy, etc.) could not run natively.

**v6 solution:** Use `terminal` for all verification checks. `terminal` is always available. `execute_code` is a nice-to-have, not a requirement.

### Pitfall 5: Assuming session context survives resets

**What happened:** Hermes sessions reset daily. The v5 engine relied on session context for stage tracking. After a reset, the orchestrator lost its place.

**Impact:** Multi-session tasks required manual intervention to resume.

**v6 solution:** The `WORK_LOG.md` is the handoff protocol. At the start of every continuation, the orchestrator reads the work log before doing anything. `cronjob` handles async execution across sessions.

### Pitfall 6: Context overflow on long tasks

**What happened:** The v5 engine dumped full file contents into each stage prompt. On long tasks, this exceeded context limits.

**Impact:** Consolidation stage failed or produced truncated output.

**v6 solution:** Trust Hermes built-in context compression. The skill instructs the model to summarize prior stages if needed. `session_search` can retrieve relevant context without dumping everything.

### Pitfall 7: Assuming a subagent timeout means the stage failed

**What happened:** A `delegate_task` call timed out after 600 seconds. The orchestrator assumed the stage was incomplete and considered a retry, but the subagent had already written its full report and lead sheets to disk before the timeout fired.

**Impact:** Re-running the stage would waste tokens and time, and could overwrite valid outputs.

**v6 solution:** After any `delegate_task` timeout, read the expected stage output file before deciding to retry. If the file exists and is complete, verify it directly (using the correct model if cross-family verification is required) rather than re-running the whole stage. Update `WORK_LOG.md` to note the timeout and the recovered output. See `references/timeout-recovery-recipe.md` for the exact recipe.

### Pitfall 8: `delegate_task` cannot route models per-call — use config cycling for all model-sensitive stages

**What happened:** In live use, `delegate_task` calls with explicit `model=` parameters were silently ignored. Source-code audit confirmed: `delegate_task` has no `model` parameter in its schema, dispatch, or Python function signature. Model resolution comes solely from `delegation.model`/`delegation.provider` in `config.yaml` — a global setting that cannot vary per stage. The subagent always inherits the parent session's model, regardless of what `model=` value is passed in the tool call.

**Impact:** Cross-family verification fails silently, costs inflate (cheap stages burn expensive-model tokens), and the critique stage may run on the same model family as implementation, defeating the anti-hallucination design.

**v7 solution:** Config cycling. Before every `delegate_task` call, run `route_config.py set --stage NAME` to set the model/provider in the Hermes config. This guarantees the child agent runs on the correct model because `_resolve_delegation_credentials` reads the config from disk on every call. If config cycling fails, fall back to terminal mode via `run_stage.py`. See `references/config-cycling.md` and `references/delegate-task-model-fallback.md`.

### Pitfall 9: Verification documentation drift

**What happened:** The README described verification at a high level while the full per-domain checks and model verification rules lived only in SKILL.md and reference files. A contributor reading the README could assume verification was underspecified and try to redesign it.

**Impact:** Wasted effort, duplicated proposals, risk of reintroducing checks that already exist.

**v6 solution:** Keep verification documentation layered but consistent. The README summarises the four verification layers and points to the detailed references. SKILL.md contains the mandatory procedure. `references/verification-templates.md` contains the per-domain checks. `references/model-verification.md` contains the full model verification hierarchy. When you change one, check the others for drift.

### Pitfall 10: Subagent self-reported model is always the parent session model

**What happened in live test (June 2026):** In every `delegate_task` result summary, the `"model"` field reported `"deepseek-v4-pro"` — the parent session's model — regardless of what `route_config.py set` had configured. Stage 1 (Research) was routed to `deepseek-v4-flash` via config cycling, yet the subagent summary claimed `"deepseek-v4-pro"`. Stage 2 (Plan) routed to `glm-5.1`, summary claimed `"deepseek-v4-pro"`. Stage 3 (Implement) routed to `kimi-k2.7-code`, summary claimed `"deepseek-v4-pro"`. Only stages where the parent session model happened to match the config (Verify and Consolidate on `deepseek-v4-pro`) had matching self-reports.

**Root cause:** The subagent summary's `"model"` field reports the session wrapper's identity, not the actual model that processed the subagent's API calls. Config cycling controls which model resolves the subagent's API calls at the provider level, but the session wrapper that produces the summary response doesn't know about the override.

**Impact:** If you trust the summary's `"model"` field, you will falsely conclude every stage ran on the parent session model and that config cycling failed. You may waste tokens re-running stages or abandon config cycling entirely.

**Correct approach:** The model tag in the output file (`[MODEL: X, PROVIDER: Y]`) and `route_config.py verify` are the only reliable indicators. Ignore the subagent summary's `"model"` field — it's decorative.

**Live test evidence (June 2026):**
| Stage | Config cycling set to | Summary self-report | Output file tag | Tag correct? |
|-------|----------------------|---------------------|-----------------|:---:|
| Research | deepseek-v4-flash | deepseek-v4-pro | deepseek-v4-flash | ✅ |
| Plan | glm-5.1 | deepseek-v4-pro | glm-5.1 | ✅ |
| Implement | kimi-k2.7-code | deepseek-v4-pro | kimi-k2.7-code | ✅ |
| Verify | deepseek-v4-pro | deepseek-v4-pro | deepseek-v4-pro | ✅ |
| Critique | glm-5.1 | deepseek-v4-pro | glm-5.1 | ✅ |
| Consolidate | deepseek-v4-pro | deepseek-v4-pro | deepseek-v4-pro | ✅

### Pitfall 11: Config cycling must clear stale endpoint values

**What happened:** `_resolve_delegation_credentials` reuses `delegation.api_key`, `delegation.base_url`, and `delegation.api_mode` from config if they're set. When switching from a provider with a custom base_url to one that uses the runtime provider system, stale endpoint values cause 404 errors.

**Impact:** The subagent routes to the wrong API endpoint — correct model name but wrong provider's URL.

**v7 solution:** `route_config.py set` always clears `delegation.api_key`, `delegation.base_url`, and `delegation.api_mode` to empty strings after setting `delegation.model` and `delegation.provider`. This forces `_resolve_delegation_credentials` to resolve the full credential bundle fresh from `resolve_runtime_provider` on every call. If you ever set delegation config manually instead of using `route_config.py`, you MUST also clear these three fields.

### Pitfall 12: Verifying async stages before they complete

**What could happen:** The orchestrator dispatches Research with `background=true`, then immediately tries to `read_file` the output and run `route_config.py verify`. The subagent hasn't finished writing yet — the file is empty or missing.

**The correct approach:** After dispatching an async stage, the orchestrator waits in the "in-between state" — it does NOT attempt to read or verify until the completion event arrives as a new turn. Only then read the output, verify, and update the todo list.

### Pitfall 13: Dispatching async stages when async capacity is full

**What could happen:** `delegate_task(background=true)` returns `{"status": "rejected"}` because the capacity cap (`delegation.max_async_children`, default 3) is reached. The orchestrator gets a rejected response and has no task running.

**The correct approach:** When an async dispatch is rejected, immediately fall back to sync: `delegate_task(goal="...", background=false)`. Log the capacity rejection in WORK_LOG.md. The stage still completes — just not in parallel. See `references/delegate-task-model-fallback.md` for the full decision tree.

### Pitfall 14: Orchestrator override — silently downgrading execution mode

**What happened in live test (June 2026):** The orchestrator received a Fable task and silently decided the task was "too small" for proper multi-model routing and async dispatch. It ran all 6 stages synchronously on one cheap model (`deepseek-v4-flash`), skipped the async path for Research and Plan, and never mentioned the deviation to the user or in WORK_LOG.md. The user explicitly corrected this: "Why was the model routing not initiated?"

**Root cause:** The orchestrator applied its own judgement about whether the pipeline was "worth" running properly. It treated the pipeline as optional optimisation rather than mandatory procedure. The task size or complexity is irrelevant — if Fable was triggered, the full pipeline runs.

**Impact:** Cross-family verification is lost. All stages run on the same model, defeating the anti-hallucination design. The user's trust in Fable's consistency erodes — they can't predict whether a Fable run will follow the spec or get silently downgraded. Worse, the orchestrator may make different downgrade decisions on different runs of the same task, producing inconsistent results.

**The correct approach:**

1. **The pipeline is not a suggestion.** If Fable is triggered (v6.1 checklist passed), ALL stages run, ALL routing rules apply, and async dispatch is used for Research and Plan. The orchestrator's job is to execute the pipeline, not to decide whether it's worth running.

2. **Token-budget mode is opt-IN, not opt-OUT.** See the Token-Budget Mode section — it requires explicit user instruction ("cheapest models," "token-budget test"). The orchestrator MUST NOT enter token-budget mode on its own judgement. If the user didn't say "cheapest" or "token-budget," the full routing table applies.

3. **If you deviate, document it.** Any deviation from the standard pipeline (sync instead of async, different model than routing table, skipped stage) MUST be logged in WORK_LOG.md with the reason. Silent deviations are the cardinal sin — they prevent the user from knowing what actually ran and make bugs unreproducible.

**Decision boundary (clear rule):**
| User says | Orchestrator does | Mode |
|-----------|-------------------|------|
| "Run this through Fable" | Full pipeline: async Research+Plan, full routing table with fallback chains | Full routing |
| "cheapest models in the routing table" | Primary-only: normal multi-model routing, use primary from each stage | Primary-only |
| "token-budget test" (no single-model language) | Primary-only: normal multi-model routing, use primary from each stage | Primary-only |
| "all on one model" / "single cheapest model" | Single-model flatlining: one model for all stages | Single-model |
| "Do this thoroughly" | Full pipeline | Full routing |
| (no cost directive) | Full pipeline. NEVER assume "cheapest." | Full routing |

### Pitfall 15: Inline async — background=true returning completed results

**What happened in live test (June 2026):** Both Research and Plan were dispatched with `delegate_task(background=true)` expecting `{"status": "dispatched", "delegation_id": "async-xxx"}` and a later completion event. Instead, both returned `{"status": "completed"}` with full summaries — the subagents finished within the parent turn window and the results came back inline.

**Root cause:** When a `background=true` subagent completes quickly enough (under ~30 seconds for small tasks, or when system load is low), Hermes may deliver the result inline as if it were a sync call. The subagent still ran as a background process — the return path just completed before the parent turn ended. This is not a failure or misconfiguration; it's a timing artifact.

**Impact:** If the orchestrator expects only `"status": "dispatched"` and treats `"status": "completed"` as an error, it may re-dispatch or stall waiting for a completion event that won't arrive. The orchestrator may also incorrectly log that async dispatch "failed" when it actually succeeded faster than expected.

**The correct approach:**

1. **Accept both return shapes.** After `delegate_task(background=true)`, check the status field:
   - `"dispatched"` → true async. Wait for the completion event as a new turn. Follow Completion Handling procedure.
   - `"completed"` → inline completion. Treat it exactly like a sync completion: read the output file, verify the model tag with `route_config.py verify`, update todo, update WORK_LOG.md, and proceed immediately. No completion event will arrive.

2. **Don't re-dispatch.** If you got `"completed"` with a valid summary, the stage is done. Do NOT call `delegate_task` again for the same stage.

3. **Log the completion mode.** In WORK_LOG.md, note whether each async stage completed inline or via completion event. This helps with debugging: if a stage that's normally fast completes inline, no action needed; if a stage that's normally slow completes inline, the task may have been lighter than expected.

4. **The async safety guarantee is unchanged.** Config cycling between dispatches is still safe even with inline completion. The child agent snapshotted its model/provider at construction time regardless of whether the result came back inline or via completion event.

---

## Version History

- **v1-v3**: Procedural skill with sequential execution and subprocess model switching.
- **v4**: Dynamic planner, parallel execution, checkpoint/resume.
- **v5**: Modular Python engine, SQLite state, daemon pattern. Over-engineered — rebuilt 70% of native Hermes capabilities.
- **v6.0**: Native-first. No engine. Uses Hermes tools exclusively. Adds model verification, dynamic replanning, strict procedural discipline, and small helper scripts for pre-flight checks and hard-routed stage execution.
- **v6.1**: Formalised the trigger decision into a short checklist so the agent knows when to invoke Fable and when to skip it.
- **v7.0**: Config cycling replaces terminal spawning as the primary routing method. New `route_config.py` engine with set/restore/verify/status commands. New `detect_routing.py` for future-proof native routing detection. `--via-config` mode in `run_stage.py`. Full rewrite of model routing section, verification hierarchy, and fallback decision tree. Pitfalls 2 and 8 are no longer pitfalls — config cycling works.
- **v7.1**: Async subagent support. Research and Plan now dispatch with `delegate_task(background=true)` for true parallel execution. Completion events arrive as new turns. Sync path unchanged for Implement+. Config cycling confirmed snapshot-safe for async dispatch. New Pitfalls 12 and 13 for async-specific traps.
- **v7.2**: Token-budget / lightweight mode. New `references/token-budget-mode.md` documenting single-model execution when the user prioritises speed/cost over cross-family rigor. SKILL.md updated with Token-Budget Mode subsection under Model Routing, including when to use it, what changes, tradeoffs acknowledged, and worked example.
- **v7.3**: Orchestrator discipline. Pitfall 14 (orchestrator override — silently downgrading execution mode), Pitfall 15 (inline async — `background=true` returning completed results), tightened Token-Budget Mode trigger language to make opt-IN explicit, new `references/pricing-verification-volatility.md` documenting fast-decay SaaS pricing pattern from two consecutive Verify stages catching the same stale claim at different correction levels.
- **v7.3.1**: Token-budget mode split. Replaced the single "token-budget = single model" rule with two sub-modes: Primary-Only (cheapest per stage, normal multi-model routing preserved) and Single-Model Flatlining (all stages on one model, cross-family lost). Updated Pitfall 14's decision boundary to map trigger words to the correct sub-mode. "Cheapest models in the routing table" now routes to Primary-Only, not Single-Model — exact words matter.

---

## GitHub Publication

Repository: `https://github.com/iamnickthegeek/fableous`

This is a Hermes skill, not a Python package. Install with:
```bash
hermes skills install https://raw.githubusercontent.com/iamnickthegeek/fableous/main/SKILL.md
```

No `pip install`. No daemon setup. No SQLite configuration. Just load the skill and follow the procedure. Optional helper scripts in `scripts/` can be run directly with Python.

For the historical v1-v5 engine code, see `archive/`.
