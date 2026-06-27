---
name: fableous
description: >
  Strict multi-stage execution orchestrator for Hermes. Uses native Hermes tools
  exclusively. Decomposes tasks into 6 stages, enforces cross-family verification,
  model verification, deliverable type classification, cross-run reconciliation,
  and dynamic replanning. No Python engine. No subprocess hacks.
  Trigger on multi-stage, multi-source, or multi-session work.
version: 0.8.3
author: Nick Smith / Point Clear Advisory
license: MIT
metadata:
  hermes:
    tags: [orchestration, multi-agent, fable-mode, planning, verification, meta, native]
    related_skills: [plan, subagent-driven-development, superpowers]
    requires_toolsets: [delegation, todo, terminal, web, file, session_search, memory, cronjob]
---

# Fable Orchestrator v0.8.2

A strict procedural orchestrator that enforces staged execution discipline using **only native Hermes tools**. No Python engine. No SQLite. No daemon. No subprocess hacks.

The value is the loop: decompose before acting, route to the right model for each stage, verify with checks that can actually fail, verify the model used, critique on a different model family, consolidate into a canonical deliverable, and replan when obstacles invalidate the plan.

## What it does

- Breaks complex tasks into 6 numbered stages with explicit dependencies
- Routes each stage to a model suited for that cognitive task
- Enforces cross-family verification (critique NEVER runs on the same model family as implementation)
- Verifies the actual model used by each subagent
- Classifies the deliverable type in the Plan stage to calibrate downstream effort
- Runs failable verification checks at every stage
- Checks for cross-run discrepancies when prior run outputs exist in the project directory
- Performs dynamic replanning when stage outputs invalidate the plan
- Produces a single canonical deliverable via consolidation
- Maintains a structured work log for multi-session continuity
- Fails open with retry chains when models or providers are unavailable

## What it does not do

- It does not make a weak model stronger. Structure imposes discipline, not reasoning quality.
- It does not replace domain skills. Use `superpowers` for software, `research-workflows` for research, `jkd-content` for writing.
- It does not run on trivial tasks. One-shot work with an obvious approach skips this loop entirely.

## When to Trigger (v0.6.1 Checklist)

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

### Why Config Cycling

`delegate_task` resolves the child's model and provider from `delegation.model` and `delegation.provider` in `~/.hermes/config.yaml`. These values are read from disk on every call (no caching). By setting them to the desired values before each call, the child agent uses the correct model/provider — guaranteed, not suggested.

Both `delegation.model` AND `delegation.provider` must be set together. Setting only the model without the provider causes the child to use the correct model name on the wrong provider's endpoint, which fails.

### YAML Override

If a `fable-config.yaml` exists, you MUST use it instead of the defaults. Check these locations in order:

1. **Skill directory** (`~/.hermes/skills/fableous/fable-config.yaml`) — the canonical place for a user-provided config
2. **Project/working directory** — if placed there by the user

Read the first file found with `read_file`. If neither exists, use the auto-detected defaults.

```yaml
# fable-config.yaml
routing:
  research:
    primary: {model: "deepseek-v0.4.0-flash", provider: "opencode-go"}
    secondary: {model: "gemini-2.5-flash-lite", provider: "google"}
    tertiary: {model: "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", provider: "openrouter"}
  # ... etc for all stages
```

### Default Routing Table

Auto-detect available providers from the user's Hermes config (`~/.hermes/config.yaml` and `~/.hermes/.env`). Use the best available model for each stage.

| Stage | Primary | Secondary | Tertiary | Rationale |
|-------|---------|-----------|----------|-----------|
| Research | `deepseek-v0.4.0-flash` (Opencode Go) | `gemini-2.5-flash-lite` (Google) | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` (OpenRouter) | Fast, broad, cheap |
| Plan | `glm-5.1` (Opencode Go) | `gemini-2.5-pro` (Google) | `deepseek-v0.4.0-pro` (Opencode Go) | Structured reasoning |
| Implement | `kimi-k2.7-code` (Opencode Go) | `kimi-k2.6` (Opencode Go) | `gemini-2.5-pro` (Google) | Code-specialized |
| Verify | `deepseek-v0.4.0-pro` (Opencode Go) | `gemini-2.5-pro` (Google) | `kimi-k2.6` (Opencode Go) | Different architecture from coder |
| Critique | `glm-5.1` (Opencode Go) | `gemini-2.5-pro` (Google) | `kimi-k2.6` (Opencode Go) | Independent evaluation |
| Consolidate | `deepseek-v0.4.0-pro` (Opencode Go) | `glm-5.1` (Opencode Go) | `gemini-2.5-pro` (Google) | Reads all stages, produces canonical output |

### Provider Setup

**NVIDIA NIM provider** requires all of the following:
1. `providers.nvidia.base_url: https://integrate.api.nvidia.com/v0.1.0` in `~/.hermes/config.yaml`
2. `providers.nvidia.api_key: ${NVIDIA_API_KEY}` in `~/.hermes/config.yaml`
3. `NVIDIA_API_KEY=...` in `~/.hermes/.env`
4. **Gateway restart** after any env var changes: `hermes gateway restart` (from a separate shell)
5. No duplicate top-level `nvidia:` key in config.yaml (only `providers.nvidia`)

**NVIDIA free-tier rate limits:** The NVIDIA free-tier has aggressive rate limits. Subagents may hit HTTP 429 after 1-2 API calls. If this happens:
- Try secondary/tertiary models from fable-config.yaml
- Switch to another provider (e.g., Google)
- As a last resort, execute the stage directly in the parent session using the same behavioral directives
- Document in WORK_LOG which stages ran in parent session vs. subagent

See `references/pitfall-19-nvidia-rate-limits.md` for details.

### Token-Budget / Lightweight Mode

When the user prioritises speed and cost, you MAY reduce routing cost. Two sub-modes exist — you MUST pick the right one based on the user's exact words.

**CRITICAL: Both modes are opt-IN, not opt-OUT.** You MUST NOT enter either mode on your own judgement. If the user says "run this through Fable" with no cost directive, use the full routing table with multi-model config cycling. See Pitfall 14.

### Sub-mode 1: Primary-Only Routing (cheapest PER STAGE)

**Trigger words:** "cheapest models", "use the cheapest models in the routing table", "keep stages brief" (without "single model"), "token-budget test, not a full production run", or any phrase where the user references the routing table directly.

**What it means:** Use the **primary** model from each stage's routing entry. Never fall back to secondary/tertiary unless the primary fails. The routing table still runs — Research gets flash, Plan gets glm, Implement gets kimi, etc. Multi-model routing and cross-family verification are preserved. Only the fallback chain is removed.

### Sub-mode 2: Single-Model Flatlining (one model for ALL stages)

**Trigger words:** "all on one model", "single cheapest model", "flatline everything", "use only deepseek-v0.4.0-flash", "one model for everything" — explicit single-model language.

**What it means:** Override the entire routing table. Every stage runs on the same cheap model (e.g. `deepseek-v0.4.0-flash`). Cross-family verification is lost — Verify, Critique, and Implement all share the same model family.

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
| "all on deepseek-v0.4.0-flash" | Single-model | flash → flash → flash → flash → flash → flash |
| "run this through Fable" (no cost directive) | Full routing | Normal table with fallback chains |
| (no explicit trigger) | Full routing | Normal table with fallback chains |

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

## Deliverable Type Classification (v0.8.0)

The Plan stage MUST classify the deliverable into one of five canonical types. This classification calibrates downstream effort — the Implement stage writes differently for a research brief than for an execution playbook, and the Consolidate stage applies critique fixes differently for a credential asset than for a creative brief.

### The Five Types

| Type | Description | Implement Emphasis | Consolidate Fix Calibration |
|------|-------------|-------------------|---------------------------|
| **Research Brief** | Broad landscape scan with key findings and sources. Meant to inform, not execute. | Voice, insight, breadth. Don't over-structure — let the findings breathe. | Light touch. Don't over-hedge — a research brief loses value if it reads like a legal disclaimer. |
| **Execution Playbook** | Step-by-step actionable guide with templates, scripts, timelines. Meant to be followed. | Templates, scripts, specificity. Every section should be executable. | Fix operational gaps but preserve confidence. A playbook that hedges every instruction is unusable. |
| **Credential Asset** | Evidence-backed document designed to withstand skeptical scrutiny. Meant to be shared with prospects/stakeholders. | Rigor, sourcing, caveats. Every claim must be defensible. | Apply all fixes thoroughly. Caveats and disclosures strengthen this type. |
| **Reference Document** | Comprehensive, structured reference for ongoing use. Meant to be consulted, not read end-to-end. | Completeness, organization, navigability. Index and cross-reference matter. | Fix structural and accuracy issues. Don't optimise for voice — optimise for findability. |
| **Decision Memo** | Analysis of options with a recommended course of action. Meant to drive a decision. | Clarity of tradeoffs, strength of recommendation. Don't present every option as equal. | Fix analytical gaps but preserve the recommendation. Don't soften the conclusion — fix the reasoning. |

---

## Behavioral Directives (Per-Stage Prompts)

Every stage prompt includes three behavioral directives derived from Anthropic's Fable prompting research. These transfer across model families and cost nothing:

1. **Lead with the outcome.** The subagent's first sentence must answer "what happened" or "what I found." No throat-clearing, no background first. The bottom line goes first.

2. **Ground every claim.** If the subagent cannot verify a claim against evidence, it must say "unverified" — not present it as confirmed. In the Critique stage, unconfirmed weaknesses are "suspected but unconfirmed."

3. **Match effort to the task.** Each stage has an effort calibration:
   - **Research**: Broad and fast. Gather widely, don't over-analyse. BUT — capture non-obvious strategic insights, creative applications, and synthesis-level recommendations in a "Strategic Insights" subsection.
   - **Plan**: Structured reasoning. Think about dependencies carefully. Classify the deliverable type — it calibrates downstream effort.
   - **Implement**: Deep and thorough. This is the main deliverable. Pull from the Research stage's "Strategic Insights" subsection — don't just regurgitate source data.
   - **Verify**: Focused and precise. Check specifics, don't rewrite. If prior run outputs exist, compare stats across runs and flag discrepancies.
   - **Critique**: Sharp and independent. Challenge assumptions. Check whether strategic insights from Research survived into Implementation.
   - **Consolidate**: Comprehensive and final. Resolve all conflicts. Weigh each critique fix against the deliverable type — don't over-hedge punchy documents or under-hedge credential assets.

---

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
terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py set --stage research")
todos=[{id:"stage-1", content:"Stage 1: Research", status:"in_progress"}], merge=true)

delegate_task(
  goal="Research: [full prompt from template]",
  context="[prompt with ASYNC directive]",
  toolsets=["web", "file"],
  background=true
)
# Returns: {"status": "dispatched", "delegation_id": "async-xxx"}
# SAVE the delegation_id for the completion handler.

# Step 2: Route and dispatch Plan (SAFE — Research child already snapshotted)
terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py set --stage plan")
todos=[{id:"stage-2", content:"Stage 2: Plan", status:"in_progress"}], merge=true)

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
```

### Completion Handling

When an async delegation completion event arrives as a new turn:

1. IDENTIFY which stage completed (match goal text or delegation_id)
2. READ the output file with `read_file`
3. VERIFY the model tag with `route_config.py verify`
4. RUN verification checks
5. UPDATE todo to "completed"
6. UPDATE WORK_LOG.md
7. CHECK if both async stages are complete → proceed to Implement

### Sync Path: Implement Through Consolidate

For stages 3-6, follow this exact sequence:

1. Set todo to "in_progress"
2. Route and delegate the stage via config cycling + `delegate_task(background=false)`
3. Verify the model tag with `route_config.py verify`
4. Run verification checks from `references/verification-templates.md`
5. Update todo to "completed"
6. Update WORK_LOG.md
7. Check for replanning triggers

---

## Model Verification

### The Problem

`delegate_task` has **no per-call `model` parameter**. Source-code audit confirmed: the tool schema, dispatch function, and Python function signature all lack a `model` field. Every subagent inherits the parent session's model regardless of what the tool call specifies.

The `[MODEL: ...]` tag in stage prompts is self-reported text, not proof of which model ran.

### The Solution

ALL model routing must use **config cycling** via `route_config.py`. This controls routing at the infrastructure level.

### Enforcement Rules

- **Research and Plan**: Use config cycling + async. Deferred verification until completion event.
- **Implement**: Use config cycling. Verify the model tag. If verification fails, retry with secondary.
- **Verify**: Use config cycling. **MUST be different family from Implement.**
- **Critique**: Use config cycling. **MUST be different family from Implement.** No exceptions.
- **Consolidate**: Use config cycling. **MUST be different family from Implement.** No exceptions.

**Do NOT pass a `model` parameter to `delegate_task` — it has no per-call `model` parameter.**

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

---

## Replanning Triggers

You MUST check for replanning after every stage completion. If a trigger fires, you MUST rebuild the plan.

| Trigger | Condition | Action |
|---------|-----------|--------|
| T1 | Research found fewer than 3 sources | Add "Extended Research" stage. |
| T2 | Plan reveals task is simpler than expected | Skip unnecessary stages. |
| T3 | Plan reveals task is more complex than expected | Add new stages. |
| T4 | Implement produces fundamentally different output than planned | Rebuild Plan from scratch. |
| T5 | Verify fails | Re-run Implement or add "Fix" stage. |
| T6 | Critique finds more than 3 critical weaknesses | Add "Fix" stage before Consolidate. |
| T7 | User provides new requirements mid-flight | Rebuild Plan. |
| T8 | Model verification fails 3 times | Use cheapest available model. |

---

## Consolidation

Stage 6 is the most important. You MUST produce a single canonical deliverable.

### Procedure

1. Read ALL prior stage outputs with `read_file`
2. Read the verification corrections from Stage 4
3. Read the critique fixes from Stage 5
4. Run config cycling for the consolidate stage
5. Delegate to the Consolidate model with full context

### Requirements for FINAL.md

- Single file. No appendices, no separate correction files.
- All verification corrections applied.
- All critique fixes addressed or explicitly flagged as "not fixed: [reason]".
- "Version & Caveats" header at the top.
- "Methodology & Sources" section.
- No predetermined conclusions.
- This is the ONLY published version.

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
| Research | deepseek-v0.4.0-flash | [actual] | [yes/no] |
...
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

If the configured provider is unavailable, fall back to the next provider in the routing table.

### Budget exhaustion

If the user's budget is exhausted, the correct behavior is SKIP. Do NOT proceed with expensive models.

---

## Cron Setup for Async Execution

For multi-session tasks, set up a cron job:

```
cronjob(
  action="create",
  schedule="*/15 * * * *",
  prompt="Load the fableous skill. Read the WORK_LOG.md in the project directory. Continue execution from the next pending stage.",
  name="fableous-[project]"
)
```

---

## Common Pitfalls

### Pitfall 1: Building a Python engine when native tools suffice

Use native tools first. Fill gaps with minimal code. Build a standalone engine only if the skill proves insufficient.

### Pitfall 2: `delegate_task` has NO per-call model parameter

Use config cycling. The `[MODEL: ...]` tag is an audit trail, not proof.

### Pitfall 3: `--provider` flag is mandatory for model switching

When falling back to terminal mode, always include both `-m` and `--provider`.

### Pitfall 4: `execute_code` blocked by default

Use `terminal` for all verification checks.

### Pitfall 5: Assuming session context survives resets

The `WORK_LOG.md` is the handoff protocol. Read it at the start of every continuation.

### Pitfall 6: Context overflow on long tasks

Trust Hermes built-in context compression.

### Pitfall 7: Assuming a subagent timeout means the stage failed

Read the expected stage output file before deciding to retry.

### Pitfall 8: `delegate_task` cannot route models per-call

Use config cycling for all model-sensitive stages.

### Pitfall 9: Verification documentation drift

Keep verification documentation layered but consistent.

### Pitfall 10: Subagent self-reported model is always the parent session model

The subagent summary's `"model"` field reports the session wrapper's identity, not the actual model. The model tag in the output file and `route_config.py verify` are the only reliable indicators.

### Pitfall 11: Config cycling must clear stale endpoint values

`route_config.py set` always clears `delegation.api_key`, `delegation.base_url`, and `delegation.api_mode` to empty strings.

### Pitfall 12: Verifying async stages before they complete

Wait for the completion event before reading/verifying.

### Pitfall 13: Dispatching async stages when async capacity is full

Fall back to sync when async is rejected.

### Pitfall 14: Orchestrator override — silently downgrading execution mode

If Fable is triggered, ALL stages run, ALL routing rules apply. Token-budget mode is opt-IN only.

### Pitfall 15: Inline async — background=true returning completed results

Accept both return shapes. Don't re-dispatch if you got "completed".

### Pitfall 16: Config file silently ignored

`load_routing()` now auto-discovers fable-config.yaml. Check skill directory first.

### Pitfall 17: search_files glob can miss files that ls finds

Verify with `terminal(ls -la <path>)` when search_files returns 0.

### Pitfall 18: NVIDIA provider requires base_url AND env var in gateway process

See Provider Setup section above and `references/pitfall-19-nvidia-rate-limits.md`.

### Pitfall 19: NVIDIA free-tier rate limits may require parent-session fallback

See `references/pitfall-19-nvidia-rate-limits.md`.

---

## Version History

- **v0.1-v0.3**: Procedural skill with sequential execution and subprocess model switching.
- **v0.4**: Dynamic planner, parallel execution, checkpoint/resume.
- **v0.5**: Modular Python engine, SQLite state, daemon pattern. Over-engineered — rebuilt 70% of native Hermes capabilities.
- **v0.6.0**: Native-first. No engine. Uses Hermes tools exclusively. Adds model verification, dynamic replanning, strict procedural discipline, and small helper scripts for pre-flight checks and hard-routed stage execution.
- **v0.6.1**: Formalised the trigger decision into a short checklist so the agent knows when to invoke Fable and when to skip it.
- **v0.7.0**: Config cycling replaces terminal spawning as the primary routing method. New `route_config.py` engine with set/restore/verify/status commands. New `detect_routing.py` for future-proof native routing detection. `--via-config` mode in `run_stage.py`. Full rewrite of model routing section, verification hierarchy, and fallback decision tree. Pitfalls 2 and 8 are no longer pitfalls — config cycling works.
- **v0.7.1**: Async subagent support. Research and Plan now dispatch with `delegate_task(background=true)` for true parallel execution. Completion events arrive as new turns. Sync path unchanged for Implement+. Config cycling confirmed snapshot-safe for async dispatch. New Pitfalls 12 and 13 for async-specific traps.
- **v0.7.2**: Token-budget / lightweight mode. New `references/token-budget-mode.md` documenting single-model execution when the user prioritises speed/cost over cross-family rigor.
- **v0.7.3**: Orchestrator discipline. Pitfall 14 (orchestrator override), Pitfall 15 (inline async).
- **v0.7.3.1**: Token-budget mode split into Primary-Only and Single-Model Flatlining.
- **v0.7.3.2**: T6 Fix stage template.
- **v0.7.3.3**: Single-model flatlining edge case.
- **v0.8.0**: Quality intelligence. Six improvements: deliverable type classification, cross-run reconciliation, methodology consistency, strategic insight preservation, fix calibration, model routing as quality decision.
- **v0.8.1**: Config file auto-discovery. Fixed `load_routing()` to auto-discover fable-config.yaml.
- **v0.8.2**: Removed `DEFAULT_ROUTING` table entirely. Fixed `providers.nvidia.base_url`. Removed duplicate `nvidia:` key. Added Pitfall 18 (NVIDIA provider setup). Changed version numbering to v0.x scheme.
- **v0.8.3**: Added Pitfall 19 (NVIDIA free-tier rate limits). Added provider setup section to SKILL.md. Updated test-notes.md with June 2026 NVIDIA run results.

---

## GitHub Publication

Repository: `https://github.com/iamnickthegeek/fableous`

This is a Hermes skill, not a Python package. Install with:
```bash
hermes skills install https://raw.githubusercontent.com/iamnickthegeek/fableous/main/SKILL.md
```

No `pip install`. No daemon setup. No SQLite configuration. Just load the skill and follow the procedure. Optional helper scripts in `scripts/` can be run directly with Python.

For the historical v0.1.0-v0.5.0 engine code, see `archive/`.

## Reference Files

- `references/config-cycling.md` — full spec and edge cases for config cycling
- `references/nvidia-nim-unified-provider.md` — using NVIDIA NIM as a single provider for multi-vendor model routing
- `references/verification-templates.md` — domain-specific failable checks
- `references/guardrails.md` — prompt guardrails injected into every stage
- `references/model-routing-table.md` — quick lookup of model assignments
- `references/work-log-template.md` — structured handoff protocol
- `references/replanning-triggers.md` — when and how to replan
- `references/model-verification.md` — verification hierarchy
- `references/delegate-task-model-routing-audit.md` — source-code evidence
- `references/model-mismatch-recovery.md` — recovering when model verification fails
- `references/timeout-recovery-recipe.md` — recovering when `delegate_task` times out
- `references/delegate-task-model-fallback.md` — decision tree
- `references/helper-scripts.md` — how and when to use the `scripts/` utilities
- `references/native-first-gap-fillers.md` — audit of what Fable adds vs what Hermes provides
- `references/v0.6.0-1-trigger-checklist.md` — when to invoke Fable and when to skip it
- `references/token-budget-mode.md` — single-model lightweight execution mode
- `references/pricing-verification-volatility.md` — SaaS pricing decays fast
- `references/ronin-partner-finder-case-study.md` — worked example
- `references/skill-rename-procedure.md` — clean rename procedure
- `references/test-notes.md` — known issues and test matrix
- `references/cross-run-quality-analysis.md` — v0.8.0 case study
- `references/pitfall-19-nvidia-rate-limits.md` — NVIDIA free-tier rate limit workaround
- `templates/stage-prompts/` — prompt templates for each standard stage
- `templates/fable-config-nvidia-nim.yaml` — ready-to-use config for NVIDIA NIM
- `templates/stage-prompts/fix.md` — prompt template for the T6 Fix stage
- `templates/consolidation-prompt.md` — the canonical synthesis prompt
- `templates/replanning-prompt.md` — the dynamic replanning prompt
- `examples/` — concrete execution examples
- `examples/test_results.md` — living test log
- `scripts/verify_models.py` — pre-flight model availability check
- `scripts/auto_detect_providers.py` — auto-detect routing table from available providers
- `scripts/run_stage.py` — hard-routed stage runner with fallback
- `scripts/fable_routing.py` — shared routing constants for the helper scripts
- `scripts/route_config.py` — config cycling engine
- `scripts/detect_routing.py` — feature detection for native routing