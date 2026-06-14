---
name: fable-orchestrator
description: >
  Meta-orchestrator skill that emulates fable-mode's staged execution discipline
  within Hermes. Decomposes complex tasks, delegates stages to model-optimized
  subagents, enforces failable verification, and runs independent critique before
  delivery. Trigger on multi-file, multi-source, or multi-session work, or when
  the user explicitly requests systematic execution.
version: 1.5.0
author: Nick Smith / Point Clear Advisory
license: MIT
metadata:
  hermes:
    tags: [orchestration, multi-agent, fable-mode, planning, verification, meta]
    related_skills: [plan, subagent-driven-development, superpowers]
    requires_toolsets: [delegation, todo, terminal, web, file]
---

# Fable Orchestrator

A meta-orchestrator that enforces staged execution discipline on complex tasks.
It does not replace the model's capability — it shapes the *procedure* through
which a model works on hard problems. The value is the loop: decompose before
acting, delegate to the right model for each stage, verify with checks that can
actually fail, and critique before delivery.

## What it does

- Breaks complex tasks into numbered stages with verifiable outputs
- Routes each stage to the model best suited for that cognitive task
- Delegates independent work in parallel where the runtime allows
- Runs a failable verification check at each stage
- Performs a skeptical self-critique before final delivery
- Fails open: if a model/provider is unavailable, falls back to the next in chain

## What it does not do

- It does not make a weak model stronger. Structure imposes discipline, not
  reasoning quality.
- It does not replace domain skills. Use `superpowers` for software, `research-workflows`
  for research, `jkd-content` for writing — this skill orchestrates *how* they run.
- It does not run on trivial tasks. One-shot work with an obvious approach should
  skip this loop entirely.

## When to trigger

Trigger when the user says:
- "do this thoroughly", "be systematic", "deep work mode", "run this through fable"
- Or when the task spans: multiple files, multiple sources, multiple sessions,
  or any work where a one-shot attempt would plausibly miss something.

Do NOT trigger when a task has one obvious approach and fits in a single pass.

## Model Routing

Each stage is assigned to a primary model. If the primary is unavailable
(rate-limited, exhausted, error), the stage falls back to the secondary.
If the secondary fails, it falls back to the tertiary. The orchestrator
never halts because of a model failure — it degrades gracefully.

| Stage | Primary | Secondary | Tertiary | Rationale |
|-------|---------|-----------|----------|-----------|
| Research / Data gathering | `deepseek-v4-flash` (Opencode Go) | `gemini-2.5-flash-lite` (Google) | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` (OpenRouter) | Fast, broad, cheap. DeepSeek for breadth, Gemini for context, Nemotron for overflow |
| Stage mapping / Planning | `glm-5.1` (Opencode Go) | `gemini-2.5-pro` (Google) | `deepseek-v4-pro` (Opencode Go) | Structured reasoning. GLM excels at decomposition; Gemini Pro as backup |
| Implementation / Coding | `kimi-k2.7-code` (Opencode Go) | `kimi-k2.6` (Opencode Go) | `gemini-2.5-pro` (Google) | Code-specialized. Kimi 2.7 for primary, proven 2.6 as fallback |
| Verification / Testing | `deepseek-v4-pro` (Opencode Go) | `gemini-2.5-pro` (Google) | `kimi-k2.6` (Opencode Go) | Different architecture from the coder. DeepSeek reasoning for rigorous checks |
| Self-critique / Final review | `glm-5.1` (Opencode Go) | `gemini-2.5-pro` (Google) | `kimi-k2.6` (Opencode Go) | Independent evaluation. GLM 5.2 replaces 5.1 when tested and better |
| Consolidation / Canonical version | `deepseek-v4-pro` (Opencode Go) | `glm-5.1` (Opencode Go) | `gemini-2.5-pro` (Google) | Reads all prior stages, applies corrections, produces the single published deliverable. DeepSeek for thoroughness, GLM for clarity. Never the same model as the implementer. |

### How to invoke the routing

**Critical: There are two ways to run this orchestrator. Only Method 2 enforces model switching.**

#### Method 1: Prompt-based (instructive only — does NOT enforce model switching)

When delegating a stage via `delegate_task`, set the model explicitly:

```
delegate_task(
    goal="Research the competitive landscape for AI ghostwriting tools",
    context="...",
    model="opencode-go/deepseek-v4-flash"
)
```

**Pitfall:** The model parameter is a *suggestion* to the subagent. The subagent can ignore it and default to the session model. This happened in testing — all 5 stages ran on `kimi-k2.6` despite the routing table assigning different models. Use this method only for simple tasks where model switching is not critical.

#### Method 2: Programmatic tool (enforces model switching — recommended)

Use the custom `fable_orchestrator.py` script. It spawns `hermes chat -q` with explicit `-m` and `--provider` flags, so the model assignment is hardcoded in the command string and cannot be overridden.

```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_orchestrator.py \
    --task "Your task here" \
    --output-dir ./results \
    --domain research
```

Or inside Hermes:

```python
import sys
sys.path.insert(0, "~/.hermes/skills/fable-orchestrator/scripts")
from fable_orchestrator import FableOrchestrator

orch = FableOrchestrator("./output")
result = orch.execute("Your task here", domain="research")
```

The script handles the retry logic automatically. Do not ask the user which model to use — the routing table is the authority.

## Core Loop

### 1. Stage map (before touching anything)

Write the full plan using the `todo` tool. Number the stages. Each stage must
produce one verifiable artifact. If a stage produces nothing checkable, merge it
with the next.

The standard loop is 6 stages:
```
Stage 1: Research → sources read, claims extracted
Stage 2: Plan → architecture decided, files listed, audience segmented
Stage 3: Draft → first pass written
Stage 4: Verify → tests pass, sources traced, errors corrected
Stage 5: Critique → weaknesses named, fixed or flagged
Stage 6: Consolidate → canonical version with all fixes applied
```

Stage 6 is the most important: it reads all prior stages and produces a single
`FINAL.md` (or equivalent). Without consolidation, verification corrections exist
in a separate file but never reach the published deliverable. All prior stages
are working drafts; the consolidated output is the only published version.

Update the plan when new information invalidates prior assumptions. The map
is a living document, not a contract.

### 2. Delegate independent work

For each stage, decide: sequential or parallel?
- If stages N and M have no dependency, delegate them concurrently via
  `delegate_task` with the appropriate model.
- If stage N feeds into stage N+1, run them sequentially.

Each subagent briefing must include:
- Specific task
- Expected output
- Where to save outputs
- Relevant context from prior stages

Good delegation: "research X while I plan Y" or "process these 3 files".  
Bad delegation: splitting a single coherent thought just to use subagents.

### 3. Verify with a check that can fail

Each stage must define a pass condition that an external artifact satisfies.
Acceptable checks:
- A test that runs and passes (software)
- A file or output that exists in the expected shape (any)
- A source actually fetched and read, not assumed (research)
- A data quality assertion that runs against real data (data)
- A diff against the stated spec (implementation)

"I reviewed it and it looks right" is NOT a check. If a stage has no failable
check, say so explicitly and mark its output as unverified so the gap is visible.

The cost of catching an error at stage 3 is trivial; at stage 8 it is catastrophic.

If a fix at stage N invalidates a prior stage, re-run that stage's check before
continuing. The loop goes forward and backward.

### 4. Self-critique before delivery

Before presenting final output, read it as a skeptical reviewer would. The critique
stage runs on a *different model* than the one that produced the work (see routing
table). This is the critical anti-hallucination measure.

Name at least one weakness or limitation. Either fix it or flag it to the user.

## Verification Templates by Domain

The verification artifact changes by domain. Use the template that matches
the work:

### Software engineering
- Read the entire relevant codebase section before writing
- Write tests before or alongside implementation
- Failable check: tests run; error paths exercised, not just happy path
- Delegate to: `kimi-k2.7-code` or `kimi-k2.6`

### Research / knowledge work
- Gather sources before synthesizing. Do not write as you search.
- For each load-bearing claim: what's the evidence? what would falsify it?
- Failable check: every claim traces to a source actually read
- Delegate to: `deepseek-v4-flash` for gathering, `deepseek-v4-pro` for verification

### Data analysis
- Understand data shape before analysis
- State hypothesis before computing, not after seeing numbers
- Check for nulls, duplicates, outliers first
- Failable check: data quality assertions run against actual data and pass
- Delegate to: `gemini-2.5-flash-lite` (huge context) or `deepseek-v4-flash`

### Writing / content creation
- Define audience and constraints before drafting
- Failable check: output matches the brief/spec; plagiarism scan if needed
- Delegate to: `glm-5.1` for planning, `kimi-k2.6` for drafting

### Long-running / multi-session tasks
- Maintain a work log: decisions made, why, what was tried and failed
- At start of any continuation, re-read the work log before doing anything
- Define done criteria upfront
- Failable check: done criteria are written and testable
- Delegate to: any model; the work log is the continuity mechanism

## Work Log

For multi-session tasks, maintain a work log file on disk:

```
WORK_LOG.md (in the project directory)
---
Session N: [date]
- Completed: [stages done]
- Decisions: [what was decided and why]
- Failed: [what was tried and abandoned]
- Open: [what remains]
```

At the start of any continuation, read the work log before doing anything.
The work log is the handoff protocol between sessions, not the conversation
history (which the model may not retain).

## Fail-Open Behavior

The orchestrator must never crash because a model or provider is unavailable.

1. **Model exhaustion**: If the primary model fails (rate limit, auth error,
   500), retry with the secondary. If the secondary fails, retry with the
   tertiary. Log the degradation.

2. **Provider exhaustion**: If Opencode Go is unavailable, fall back to Google.
   If both are unavailable, use the OpenRouter free tier.

3. **Budget exhaustion**: If the user's budget is exhausted, the correct
   behavior is SKIP — do not proceed with expensive models. Use the cheapest
   available or flag the task as blocked.

4. **Verification failure**: If a check fails, the stage is not complete.
   Re-run the stage or fix the issue before proceeding. Do not override the
   check.

## Example: Building a landing page

**Task**: "Build a landing page for my book"

**Step 1 — Stage map**
```
Stage 1: Research → gather 5 competitor landing pages, extract patterns
Stage 2: Design → wireframe + component list
Stage 3: Implementation → write HTML/CSS/JS
Stage 4: Verification → build succeeds, responsive test passes
Stage 5: Critique → review on a different model, flag weaknesses
```

**Step 2 — Delegate**
- Stage 1 (Research): delegate to `deepseek-v4-flash` via Opencode Go
- Stage 2 (Design): delegate to `glm-5.1` via Opencode Go
- Stage 3 (Implementation): delegate to `kimi-k2.7-code` via Opencode Go
- Stage 4 (Verification): delegate to `deepseek-v4-pro` via Opencode Go
- Stage 5 (Critique): delegate to `glm-5.1` via Opencode Go

Stages 1-2 can run in parallel if independent. Stage 3 depends on Stage 2.
Stage 4 depends on Stage 3. Stage 5 depends on Stage 4.

**Step 3 — Verification**
Stage 4 check: `npm run build` exits 0 and `npm run test` passes. If not, the
implementation stage is re-run, not the critique stage.

**Step 4 — Critique**
Stage 5: "The CTA button is below the fold on mobile. The headline is generic.
The social proof section is missing." Fix or flag.

## Test Results and Lessons

### First test: Competitive analysis of AI ghostwriting tools — V2

**Date:** June 2026  
**Task:** Write a 1-page competitive analysis of AI ghostwriting tools for digital marketers, with 3 real competitors, verified pricing, and cited sources.

**What worked:**
- The 5-stage loop executed cleanly: Research → Plan → Draft → Verify → Critique
- Model routing worked: DeepSeek for research, GLM for planning, Kimi for drafting, DeepSeek Pro for verification, GLM for critique
- All 3 source URLs verified HTTP 200
- The critique subagent (running a different model family) found **5 real weaknesses** in the draft

**What the critique caught:**
1. Missing competitors (ChatGPT, Claude, Gemini are the tools most marketers actually use)
2. Writer.com doesn't belong in a ghostwriting comparison (it's an enterprise workflow platform)
3. Missing critical dimensions (LLM transparency, hallucination rates, SEO integration, plagiarism detection)
4. Generic recommendations without a decision framework
5. Unsubstantiated quality claims ("fastest time-to-output") despite no hands-on testing

**Key lesson:** The critique stage is the most valuable part of the loop. The model that produced the work (Kimi) would not have caught these weaknesses. The independent critique subagent (GLM) found them because it thinks differently. **Cross-family critique is non-negotiable.**

**Adjustment made:** The skill now routes critique explicitly to `glm-5.1`, never to the same model family that produced the work.

### Second test: Competitive analysis — V3 with guardrails and consolidation

**Date:** June 2026  
**Task:** Same task, but with built-in guardrails and a 6th consolidation stage.

**What changed:**
- Added **Stage 6: Consolidation** — a `deepseek-v4-pro` subagent reads all prior stages and produces a single `FINAL.md` with all verification fixes applied
- Added **prompt guardrails** injected into every stage prompt:
  - Research: "If you cite percentages, label the exact source and date. Do not present vendor claims as verified facts."
  - Plan: "Segment the audience into at least 3 tiers. Include a Methodology & Caveats section."
  - Implement: "Every claim must trace to a source. Flag vendor claims as unverified. The final line must not reveal a predetermined conclusion."
  - Verify: "Check for internal consistency. Flag hallucination data that shifts between stages. List all factual errors with corrections."
  - Critique: "Check for confirmation bias. Verify competitor selection is justified. Assess audience segmentation."
  - Consolidate: "Produce a single canonical deliverable. Apply all verification corrections. Add a Version & Caveats header."

**What V3 proved:**
- The guardrails worked. The FINAL.md included a "Version & Caveats" section, explicit "vendor-claimed, not independently verified" flags, and a "Methodology & Sources" section
- All 5 V2 weaknesses were addressed: baseline competitors included, Writer.com reframed, decision framework added, comparisons expanded, citations traced
- New critique found 6 refinements (not flaws), mostly about adding brief exclusion rationales for Rytr/Anyword and splitting the Solo tier. These were addressable in the consolidation stage

**Critical technical detail:** The custom tool requires `execute_code` to be enabled. If blocked (default security setting), the script falls back to `subprocess` via the `terminal` tool. This is slower but works. To enable native execution, set `hermes config set approvals.cron_mode approve` and restart the session.

**The `--provider` flag is mandatory.** Model switching fails without it. The command format is:
```
hermes chat -q '...' -m MODEL_NAME --provider PROVIDER_NAME -Q -t web,terminal,file
```
Without `--provider`, Hermes defaults to the session's current provider and the model switch silently fails.

**Key lesson:** The 6th consolidation stage is the most important structural fix. Without it, verification corrections exist in a separate file but never reach the published deliverable. The consolidation stage is the canonical version — all prior stages are working drafts. This prevents the "error propagation" problem that the V2 critique identified.

## Reference Files

- `references/verification-templates.md` — domain-specific failable checks
- `references/guardrails.md` — prompt guardrails injected into every stage
- `references/model-routing-table.md` — quick lookup of model assignments
- `references/opencode-go-models.md` — full catalog of Opencode Go models
- `references/execution-modes.md` — comparison of prompt-based vs programmatic tool modes
- `references/hermes-model-switching.md` — why `delegate_task` is suggestive, not enforcing
- `scripts/fable_orchestrator.py` — programmatic enforcement tool (v3, 6-stage)
- `scripts/verify_models.py` — pre-flight check for model availability

## Notes on the skill design

This skill is intentionally a *conductor*, not a *performer*. It delegates to
domain-specific skills for the actual work. The value is the discipline:
- The model does not skip decomposition
- The model does not verify its own work with the same brain that wrote it
- The model does not ship without a critique pass

Treat this as a checklist, not a capability transplant. The models in the
routing table do the reasoning. This skill shapes the *procedure*.

## When a task is genuinely beyond capability

Flag it. Do not produce plausible-sounding wrong output. The orchestrator's
job is to catch errors early, not to make a model smarter than it is.

---

## v4 Upgrade: Dynamic Parallel Execution

Released: June 2026

### What changed

The v3 script was strictly sequential: 6 stages, one after another. v4 adds:

1. **Parallel execution**: Independent stages run concurrently via threads. The Stage 0 planner identifies which stages have no dependencies and runs them in parallel.
2. **Checkpoint / resume**: `state.json` is saved after every stage. If the process is interrupted, run with `--resume` to continue from where it stopped.
3. **Dynamic stage planner**: Stage 0 analyzes the task and builds a custom DAG. Some tasks skip research; some add extra stages. The planner runs on `glm-5.1` and returns a JSON stage graph.
4. **Context pruning**: Dependencies are summarized to ~100 lines (head + tail + omission count) instead of dumping full file contents into each stage prompt.
5. **Self-healing retries**: Failed stages automatically retry with the secondary model. If that fails, the tertiary model is attempted.
6. **Dependency graph execution**: Stages only run when all upstream dependencies are satisfied. This enables true parallel execution where the graph allows it.

### How to run v4

```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_orchestrator_v4.py \
    --task "Your task here" \
    --output-dir ./output \
    --domain research
```

Resume after interruption:
```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_orchestrator_v4.py \
    --task "Your task here" \
    --output-dir ./output \
    --domain research \
    --resume
```

### What v4 still can't do

- **True asynchronous execution**: Hermes sessions are synchronous. We can't "hand off and review later" without a cron job.
- **Vision-based verification**: Hermes has vision tools but integrating them into the automated loop requires manual coordination.
- **Hundreds of parallel agents**: Hermes `delegate_task` has concurrency limits. The v4 script uses threading + subprocess, bounded by machine resources.
- **Cross-session context**: Hermes sessions reset daily. The state.json survives, but the orchestrator must be re-triggered manually.
- **Dynamic re-planning mid-flight**: The v4 planner runs once at the start. Real Fable re-plans when it encounters obstacles.

### Reference files added in v4

- `references/v4-analysis.md` — detailed analysis of what Fable does, what v3 captured, and what was missing
- `references/v4-test-notes.md` — test results, known issues, and recommended test matrix
- `scripts/fable_orchestrator_v4.py` — the v4 orchestrator (parallel, checkpointed, dynamic)

### Test notes

v4 has been syntax-checked and lightly tested against a live task. The dynamic planner correctly simplified a trivial task to 4 stages (skipping Plan and Critique). The parallel execution and checkpoint logic are sound. The `hermes chat -q` subprocess spawning works but is slow (~20s per stage cold-start). For large jobs, test with a small task first. See `references/v4-test-notes.md` for the full test log.

### Recommended workflow

1. For small tasks (< 30 min): Use the prompt-based mode (Method 1) — load the skill and let the model orchestrate directly.
2. For medium tasks (30 min – 2 hours): Use v4 with default settings.
3. For large tasks (multi-session, multi-day): Use v4 with `--resume`, maintain a `WORK_LOG.md`, and trigger the orchestrator via a cron job if you need true async execution.

### Migration from v3

v3 (`fable_orchestrator.py`) is still available. v4 is a separate script. The routing table and guardrails are unchanged. The main difference is the execution engine: sequential vs parallel, static vs dynamic.

---

## v5 Engine: Full Fable Architecture

Released: June 2026. The open-source publication release.

### What changed

v5 replaces the monolithic scripts with a **modular Python engine** (`fable_engine/`) and a **daemon** (`scripts/fable_daemon.py`). This is the architecture for GitHub publication.

### Architecture

```
fable_engine/
  core.py          # FableEngine: orchestrates the full pipeline
  state.py         # StateManager: SQLite persistence
  planner.py       # StagePlanner: dynamic DAG + model routing
  agent_pool.py    # AgentPool: parallel execution via subprocess
  verification.py # VerificationEngine: failable checks
  context.py       # ContextCompressor: summary-based context passing
  questioner.py    # ProactiveQuestioner: intake clarifying questions
```

### Key innovations

1. **SQLite state**: `state.db` replaces `state.json`. Supports concurrent access, complex queries, and ACID guarantees.
2. **Daemon pattern**: `fable_daemon.py --tick` runs one execution cycle. Set up as a cron job for true async execution across sessions.
3. **Proactive questioning**: Before decomposition, the engine asks 3-5 clarifying questions and enriches the task description.
4. **Context compression**: Dependencies are summarized to ~100 lines before being passed downstream. Prevents context overflow on long-running tasks.
5. **Verification engine**: Domain-specific failable checks (file existence, content shape, URL validation, test execution) run automatically after each stage.
6. **Self-healing retries**: Failed stages automatically retry with the secondary model. The state DB tracks the retry chain.
7. **Work log integration**: Every decision, failure, and open item is logged to SQLite. Multi-session continuity is automatic.

### How to run v5

```bash
# Start a task
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --start --task "Your task here" --output-dir ./output

# Process all running tasks (cron job)
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --tick

# Check status
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --status

# Resume a specific task
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --resume task_20260614_120000

# Follow work log
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
    --tail task_20260614_120000
```

### Cron setup for async execution

```bash
# Edit crontab
hermes cron create --name fable-tick --schedule "*/15 * * * *" \
    --prompt "Run python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --tick"
```

Or manually:
```
*/15 * * * * python3 /home/case/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py --tick --output-dir /home/case/fable-outputs
```

### What v5 still can't do

- **Vision-based verification**: Hermes has `vision_analyze` but integrating it into the automated loop requires manual image capture. Planned for v5.1.
- **Dynamic re-planning mid-flight**: The planner runs once at start. If a stage produces fundamentally different results than expected, the engine doesn't automatically replan. Planned for v5.1.
- **Distributed agent pool**: "Hundreds of agents" requires a message queue (Redis/RabbitMQ) across multiple machines. The current `AgentPool` is single-node. A `DistributedAgentPool` is planned for v5.2.

### GitHub publication

This skill is designed to be published as an open-source project:
- `README.md` — project overview, installation, quick start
- `LICENSE` — MIT
- `fable_engine/` — core Python library (installable via pip)
- `tests/` — test suite
- `examples/` — usage examples
- `scripts/` — CLI entry points

Repository: `https://github.com/iamnickthegeek/fable-orchestrator` (when published)

### Non-coder Quick Start

If you don't know how to code, here's the simplest way to use this:

1. **Run the setup wizard** (one time):
   ```bash
   python3 ~/.hermes/skills/fable-orchestrator/quickstart.py
   ```
   This checks everything, sets up auto-execution, and optionally runs a test.

2. **Start a task**:
   ```bash
   python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
       --start --task "Your task here" --output-dir ~/fable-outputs
   ```

3. **Continue the task** (run 3-5 times for simple tasks):
   ```bash
   python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
       --tick --output-dir ~/fable-outputs
   ```

4. **Check results**:
   ```bash
   python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_daemon.py \
       --status --state-db ~/.hermes/fable_state.db
   ```

5. **Find your output** in `~/fable-outputs/task_YYYYMMDD_HHMMSS/FINAL.md`

For the full step-by-step guide, see `INSTALL.md`. For example tasks, see `examples/`.

### Version history

- **v1.0-v3**: Procedural skill. 6-stage loop, sequential execution, JSON state, subprocess model switching.
- **v4**: Dynamic planner, parallel execution, checkpoint/resume, context pruning.
- **v5**: Modular engine, SQLite state, daemon pattern, proactive questioning, verification engine, open-source release.

### Reference files added in v5

- `references/v5-pitfalls.md` — session-tested fixes and gotchas from v5 engine implementation
- `references/v5-test-suite.md` — test coverage documentation and testing lessons
- `templates/cron-setup.md` — template for cron-based async execution
- `fable_engine/core.py` — main orchestrator
- `fable_engine/state.py` — SQLite persistence
- `fable_engine/planner.py` — dynamic DAG + model routing table
- `fable_engine/agent_pool.py` — parallel execution
- `fable_engine/verification.py` — failable checks
- `fable_engine/context.py` — context compression
- `fable_engine/questioner.py` — proactive questioning
- `quickstart.py` — automated setup wizard for non-coders (checks prerequisites, sets up cron, runs test)
- `scripts/fable_daemon.py` — cron-friendly daemon
- `tests/` — test suite (test_state.py, test_planner.py, all passing)
- `examples/` — usage examples (simple_task, software_project, research_report)
- `setup.py` — pip install support for GitHub publication
- `README.md` — project README for GitHub
- `LICENSE` — MIT license

### Test notes

v5 has been syntax-checked and the engine classes verified for import correctness. The daemon CLI has been tested with `--help`. Live end-to-end testing completed successfully on a trivial task: the engine correctly planned 5 stages (Research → Implement → Verify → Critique → Consolidate), executed them across 5 cron ticks, produced all stage files and a FINAL.md deliverable. The SQLite state DB correctly tracked all stage transitions, model usage, and retry logic. The model routing table and guardrails are inherited from v3-v4 and have been live-tested previously.

### Recommended workflow

1. **Small tasks** (< 30 min): Load the skill and use the prompt-based mode. The model orchestrates directly.
2. **Medium tasks** (30 min – 2 hours): Use the daemon with `--start` and watch the output directory.
3. **Large tasks** (multi-session, multi-day): Use the daemon with a cron job. Check `--status` periodically. Use `--resume` if the session resets.
4. **Emergency**: Use `--tail <task_id>` to see the work log and understand what went wrong.
