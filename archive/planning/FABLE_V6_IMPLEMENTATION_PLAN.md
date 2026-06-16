# Fable Orchestrator v6 Implementation Plan

**Status:** Planning Phase — user answers incorporated, awaiting final go-ahead before any code changes.  
**Date:** June 2026  
**Goal:** Rework the Fable Orchestrator to use Hermes native functions FIRST, then identify only what must be added to duplicate Claude Fable's workflow.

---

## 1. Current State Analysis

### What the v5 Engine Does (9 modules, ~1,200 lines)

| Module | Responsibility | Lines |
|--------|---------------|-------|
| `core.py` | Main orchestrator, tick execution, finalization | 201 |
| `state.py` | SQLite persistence (tasks, stages, checkpoints, work logs) | 202 |
| `planner.py` | Dynamic DAG builder, model routing table, guardrails | 97 |
| `agent_pool.py` | Parallel execution via `subprocess.run("hermes chat -q...")` | 151 |
| `verification.py` | Domain-specific failable checks (file, URL, content, test) | 80 |
| `context.py` | Context compression (head + tail + omission count) | 32 |
| `questioner.py` | Proactive clarifying questions with structured JSON intake | 61 |
| `fable_daemon.py` | CLI wrapper (start, tick, status, resume, tail) | 80 |
| `setup.py` | Pip install support | 31 |

**Total:** ~935 lines of Python across the core engine.

### What Hermes Already Provides Natively

| Hermes Feature | Native Tool/Command | What It Does |
|----------------|---------------------|--------------|
| **Multi-agent orchestration** | `delegate_task` | Spawns subagents with isolated context. Batch mode runs up to 3 in parallel. Supports `model` parameter (suggestive, not enforcing). |
| **Cron scheduling** | `cronjob` tool + `hermes cron` CLI | Durable scheduler with per-job model/toolset overrides, context chaining, workdir support, multi-platform delivery. Runs independently of sessions. |
| **Task planning** | `todo` tool | In-session task list with priority ordering, status tracking (pending/in_progress/completed). |
| **Session persistence** | `session_search` + `memory` | FTS5 search across past sessions. Persistent user profile and environment notes. |
| **File operations** | `write_file`, `read_file`, `search_files`, `patch` | Full filesystem access with syntax checking. |
| **Web research** | `web_search`, `web_extract`, `browser` | Search, extract, and browse. |
| **Terminal execution** | `terminal` | Shell commands, process management, background processes. |
| **Code execution** | `execute_code` | Sandboxed Python execution with tool access. |
| **Context compression** | Built-in auto-compression | Automatic summarization when approaching token limits. |
| **Checkpoints** | `/rollback` + `checkpoints` config | Filesystem snapshots for rollback. |
| **Clarifying questions** | `clarify` tool | Ask user multiple-choice or open-ended questions mid-task. |
| **Kanban** | `kanban` toolset | Multi-agent work queue with task assignment, blocking, comments. |
| **Skills** | `skill_manage` + `skill_view` | Reusable procedures that load into sessions. |
| **Vision** | `vision_analyze` | Image analysis. |
| **Gateway** | Multi-platform messaging | Telegram, Discord, Slack, etc. |
| **Standing goals** | `/goal` | Hermes works toward a goal across turns until achieved. |
| **Background execution** | `/background` | Run prompt in background without blocking. |
| **Queueing** | `/queue` | Queue work for next turn. |

---

## 2. Duplication Audit: What v5 Rebuilds That Hermes Already Has

### 2.1 SQLite State Manager (`state.py`) — UNNECESSARY DUPLICATION

**What it does:** Tracks tasks, stages, subagents, checkpoints, work logs in a custom SQLite DB.

**What Hermes already has:**
- `session_search` — search past sessions by content (FTS5-backed)
- `memory` — persistent user profile and environment notes
- `todo` — in-session task tracking
- `kanban` — multi-agent work queue with full state persistence
- Hermes's own SQLite session store (`hermes_state.py`) already persists conversation history

**Verdict:** The custom SQLite DB is a complete rebuild of Hermes's native persistence. The `kanban` toolset is specifically designed for multi-agent task tracking with state persistence. The v5 engine should use `kanban` for task/stage tracking instead of a custom DB.

**What we'd lose:** The custom DB schema with stage-specific fields (model_used, error_log, result_summary). But `kanban_comment` and `kanban_link` can attach metadata to tasks.

### 2.2 Cron Daemon (`fable_daemon.py`) — UNNECESSARY DUPLICATION

**What it does:** Runs `--tick` every 15 minutes via cron to process running tasks.

**What Hermes already has:**
- `cronjob` tool — durable scheduler with `context_from` chaining, per-job model overrides, multi-platform delivery
- `hermes cron` CLI — full CRUD for cron jobs
- Cron jobs survive session resets and run independently

**Verdict:** The custom daemon is a rebuild of Hermes's native cron. A `cronjob` action can run the fable skill on a schedule. The `--tick` concept is exactly what a cron job does.

### 2.3 Parallel Agent Pool (`agent_pool.py`) — PARTIAL DUPLICATION

**What it does:** Spawns `hermes chat -q` subprocesses with threading to bypass the 3-agent `delegate_task` limit.

**What Hermes already has:**
- `delegate_task` with batch mode — runs up to 3 children in parallel
- `terminal` with `background=True` — can spawn `hermes chat -q` processes
- The skill itself documents that spawning via `terminal` is a native Hermes capability

**Verdict:** The `AgentPool` is doing exactly what `delegate_task` + `terminal` already do. The threading wrapper is unnecessary — Hermes handles process management. The only "innovation" is bypassing the 3-agent limit, which is a Hermes constraint we should work within rather than hack around.

### 2.4 File Operations (throughout engine) — UNNECESSARY DUPLICATION

**What the engine does:** `path.read_text()`, `path.write_text()`, `path.exists()`, `path.mkdir()`.

**What Hermes already has:** `read_file`, `write_file`, `search_files`, `patch` — all with syntax checking, line numbers, and pagination.

**Verdict:** Every file operation in the engine should be a native Hermes tool call. The engine's file handling is less capable than Hermes's native tools (no syntax checking, no pagination, no search).

### 2.5 Context Compression (`context.py`) — UNNECESSARY DUPLICATION

**What it does:** Truncates long files to head + tail + omission count.

**What Hermes already has:** Built-in context compression that triggers automatically near token limits. Also `session_search` for retrieving relevant context.

**Verdict:** Hermes's compression is more sophisticated (it uses an LLM to summarize, not just truncate). The custom compressor is a naive version of what Hermes does natively.

### 2.6 Proactive Questioning (`questioner.py`) — PARTIAL DUPLICATION

**What it does:** Spawns a subprocess to ask clarifying questions and returns structured JSON.

**What Hermes already has:** `clarify` tool — asks the user questions directly within the session. No subprocess needed.

**Verdict:** The `clarify` tool is simpler and more direct. The engine's subprocess approach is slower and more fragile. However, the `clarify` tool is interactive (asks the user), while the engine's questioner is autonomous (answers its own questions with defaults). This is a design difference, not a capability gap.

### 2.7 Terminal/Subprocess Execution (throughout) — UNNECESSARY DUPLICATION

**What the engine does:** `subprocess.run("hermes chat -q...", shell=True)` for every stage.

**What Hermes already has:** `terminal` tool — runs shell commands with full process management, background support, notify_on_complete.

**Verdict:** Every `subprocess.run` call in the engine should be a `terminal` tool call. The engine is using raw Python subprocesses instead of Hermes's managed terminal.

---

## 3. What Hermes CANNOT Do (The Real Gaps)

These are the capabilities that Claude Fable has which Hermes lacks, and which require custom implementation.

### 3.1 Structured Stage Decomposition with Guardrails

**What Fable does:** Breaks every task into a specific 6-stage pipeline (Research → Plan → Implement → Verify → Critique → Consolidate) with stage-specific guardrails injected into prompts.

**What Hermes does:** `todo` can create task lists, but has no concept of "stages" with dependencies, guardrails, or model routing. `kanban` has tasks and dependencies but no guardrail injection.

**Gap:** Hermes needs a structured stage decomposition system that:
- Defines stage types with guardrails
- Enforces the dependency DAG
- Routes each stage to the right model
- Runs verification as a formal stage, not an afterthought

**Implementation needed:** A `stage_planner` module that uses `todo` or `kanban` for tracking but adds the Fable-specific discipline.

### 3.2 Cross-Family Verification & Critique

**What Fable does:** Verification and critique MUST run on a different model family than the implementer. This is the anti-hallucination measure.

**What Hermes does:** `delegate_task` has a `model` parameter, but it's suggestive — the subagent can ignore it. The skill documents this exact pitfall.

**Gap:** Hermes has no native way to ENFORCE model switching for specific subagents. The `delegate_task` model parameter is advisory.

**Implementation needed:** A verification mechanism that either:
- Uses the subprocess method (as v5 does) to hardcode model assignment
- Or uses a custom tool that validates the model was actually used

**Critical question:** Do we keep the subprocess workaround, or accept that `delegate_task` is suggestive and document the limitation?

### 3.3 Fail-Open Routing Table

**What Fable does:** Primary → Secondary → Tertiary model fallback per stage. If DeepSeek fails, switch to Gemini. If Gemini fails, switch to Nemotron.

**What Hermes does:** `delegate_task` has a `model` parameter but no fallback chain. The credential pool rotates API keys but doesn't switch models on failure.

**Gap:** Hermes has no native retry-with-different-model logic.

**Implementation needed:** A `routing_table` module that wraps `delegate_task` or `terminal` with retry logic and model fallback.

### 3.4 Domain-Specific Failable Verification

**What Fable does:** After each stage, run checks that can actually fail (tests pass, sources exist, content has required sections).

**What Hermes does:** No native "verification stage" concept. You can run tests via `terminal` or `execute_code`, but there's no framework that says "this stage is not complete until these checks pass."

**Gap:** Hermes needs a verification framework that:
- Defines pass/fail criteria per stage
- Blocks progression if checks fail
- Triggers retry automatically

**Implementation needed:** A `verification` module that uses `terminal` or `execute_code` to run checks but adds the Fable-specific discipline of "verification is a gate, not a suggestion."

### 3.5 Work Log as Structured Handoff Protocol

**What Fable does:** Maintains a `WORK_LOG.md` with specific sections (Completed, Decisions, Failed, Open) that serves as the handoff protocol between sessions.

**What Hermes does:** `session_search` can find past conversations, but there's no structured work log format. `memory` stores user preferences, not task history.

**Gap:** Hermes needs a structured work log that:
- Survives session resets
- Is readable by both humans and the agent
- Contains specific sections for decisions, failures, and open items

**Implementation needed:** A `work_log` module that uses `write_file` to maintain the structured format. This is simple enough that it could just be a skill convention, not a module.

### 3.6 Dynamic Replanning

**What Fable does:** When a stage produces unexpected results, Fable replans the remaining stages.

**What Hermes does:** No native dynamic replanning. `todo` can be updated, but there's no automatic trigger to replan when obstacles are encountered.

**Gap:** Hermes needs a replanning trigger that:
- Detects when stage output invalidates the plan
- Rebuilds the DAG with new information
- Doesn't lose completed work

**Implementation needed:** A `replanning` module that checks stage outputs against expectations and rebuilds the plan if needed.

### 3.7 Consolidation as a Canonical Stage

**What Fable does:** Stage 6 reads all prior stages and produces a single `FINAL.md` with all fixes applied.

**What Hermes does:** No native "consolidation" concept. The closest is `session_search` for gathering context, but there's no formal stage that synthesizes all prior work.

**Gap:** Hermes needs a consolidation stage that:
- Gathers all stage outputs
- Applies verification corrections
- Addresses critique fixes
- Produces a single canonical deliverable

**Implementation needed:** This is essentially a specific type of `delegate_task` with a specific prompt. It could be a skill convention rather than a module.

---

## 4. User Answers (June 2026)

### Q1: Pure Hermes skill, or keep the Python engine?
**Answer:** "Whichever delivers the consistently most results."

**Interpretation:** Reliability wins. The pure Hermes skill is MORE reliable because it uses native tools rather than brittle subprocess hacks. The Python engine is where the fragility comes from (subprocess timeouts, shell escaping, threading issues, SQLite lock contention). 

**Decision:** **Pure Hermes skill.** No Python engine. The skill is the orchestration logic.

### Q2: Model routing hardcoded to your providers. Make it configurable?
**Answer:** "B but also allow them to configure a YAML config file for provider/model for each task type"

**Interpretation:** Auto-detect from Hermes config as the default, but allow a YAML override for power users.

**Decision:** The skill will auto-detect available providers from the user's Hermes config (`~/.hermes/config.yaml` and `~/.hermes/.env`), then fall back to a `fable-config.yaml` in the project directory if the user wants explicit control.

### Q3: GitHub publication — still want it as a standalone project?
**Answer:** "That'll depend on the answer to Q1"

**Interpretation:** Since Q1 is "pure Hermes skill", the GitHub repo becomes a skill repository (SKILL.md + templates + references), not a Python package.

**Decision:** Publish as a Hermes skill repository. The `README.md` will explain installation via `hermes skills install URL`.

### Q4: Non-coder ease of use vs. task reliability?
**Answer:** "I want ease of installation and use but I want task reliability. I want instructions to be followed 100% of the time"

**Interpretation:** The skill must be a **strict procedure** that the model follows. The model should not have "choice" about whether to execute the stages. The skill documentation must be prescriptive, not suggestive.

**Decision:** The SKILL.md will use imperative language ("You MUST...", "You WILL...", "Do NOT...") and include a verification checklist that the model must complete before declaring a stage done.

### Q5: Model switching enforcement — `delegate_task` is suggestive, not enforcing.
**Answer:** "C = otherwise, what's the point?"

**Interpretation:** Build verification that checks the model actually used and retries if wrong. The cross-family verification is the core anti-hallucination measure. Without enforcement, the whole system is compromised.

**Decision:** Implement a **model verification step** that inspects the subagent's output or session metadata to confirm the correct model was used. If not, retry with a different method (subprocess with hardcoded flags, or a different delegate_task invocation).

### Q6: Dynamic replanning (when obstacles change the plan mid-flight)
**Answer:** "A (let's go crazy)"

**Interpretation:** Include dynamic replanning in v6. This is a complex feature but it's the differentiator.

**Decision:** Implement a **replanning trigger** that compares stage output against expected output (defined in the plan) and rebuilds the DAG if the actual output invalidates the remaining plan.

---

## 5. Proposed v6 Architecture

### Principle: Hermes Native FIRST

Every capability that Hermes already has should be used natively. Custom code should only fill the gaps identified above.

### 5.1 What Stays (The Real Value)

| Component | Why It Stays | Form |
|-----------|-------------|------|
| **Stage decomposition logic** | Hermes has no native 6-stage discipline | Skill documentation + `todo`/`kanban` integration |
| **Guardrails** | Hermes has no native guardrail injection per stage | Skill documentation + prompt templates |
| **Model routing table** | Hermes has no native fallback chain | Auto-detected from Hermes config + optional YAML override |
| **Verification framework** | Hermes has no native verification gates | A `verification` module that uses `terminal`/`execute_code` |
| **Work log format** | Hermes has no structured handoff protocol | A markdown template + `write_file` convention |
| **Consolidation prompt** | Hermes has no native synthesis stage | A prompt template for `delegate_task` |
| **Model verification** | Hermes has no native model enforcement | A verification step that inspects subagent output |
| **Dynamic replanning** | Hermes has no native replanning | A trigger that rebuilds the DAG when obstacles are encountered |

### 5.2 What Goes (The Duplications)

| Component | Replacement |
|-----------|------------|
| `state.py` (SQLite) | `kanban` toolset for task tracking + `memory` for persistence |
| `fable_daemon.py` (cron) | `cronjob` tool with `--skill fable-orchestrator` |
| `agent_pool.py` (threading) | `delegate_task` batch mode + `terminal` for spawning |
| `context.py` (compression) | Hermes built-in context compression + `session_search` |
| `questioner.py` (subprocess) | `clarify` tool for interactive, or `delegate_task` for autonomous |
| File operations (raw Python) | `read_file`, `write_file`, `search_files` |
| `subprocess.run` calls | `terminal` tool calls |

### 5.3 What v6 Will Look Like

```
fable-orchestrator/
├── SKILL.md                          # The main orchestration logic (strict, prescriptive)
├── references/
│   ├── model-routing-table.md        # Quick lookup of model assignments
│   ├── guardrails.md                 # Prompt guardrails per stage
│   ├── verification-templates.md     # Domain-specific failable checks
│   ├── work-log-template.md          # Structured handoff protocol
│   ├── replanning-triggers.md        # When and how to replan
│   └── model-verification.md         # How to verify the correct model was used
├── templates/
│   ├── stage-prompts/
│   │   ├── research.md
│   │   ├── plan.md
│   │   ├── implement.md
│   │   ├── verify.md
│   │   ├── critique.md
│   │   └── consolidate.md
│   ├── consolidation-prompt.md       # The canonical synthesis prompt
│   └── replanning-prompt.md          # The dynamic replanning prompt
├── scripts/
│   └── verify_models.py              # Optional: pre-flight model availability check
├── examples/
│   ├── simple_task.md
│   ├── software_project.md
│   └── research_report.md
├── README.md
├── LICENSE
└── CONTRIBUTING.md
```

**No Python engine.** The v6 is a **Hermes skill** that uses native tools.

### 5.4 How v6 Will Work

1. **User loads the skill:** `hermes -s fable-orchestrator` or `/skill fable-orchestrator`
2. **User gives a task:** "Build a competitive analysis of AI ghostwriting tools"
3. **Skill uses `todo` to create the stage map:**
   ```
   todo(todos=[
     {id: "1", content: "Research: gather 5 competitor landing pages", status: "pending"},
     {id: "2", content: "Plan: architecture and component list", status: "pending"},
     {id: "3", content: "Implement: write HTML/CSS/JS", status: "pending"},
     {id: "4", content: "Verify: build succeeds, responsive test passes", status: "pending"},
     {id: "5", content: "Critique: review on different model", status: "pending"},
     {id: "6", content: "Consolidate: canonical FINAL.md", status: "pending"},
   ])
   ```
4. **Skill delegates stages:** `delegate_task` with model routing, or `terminal` for hardcoded model enforcement
5. **Skill runs verification:** `terminal` or `execute_code` to run failable checks
6. **Skill verifies model used:** Inspects subagent output or session metadata
7. **Skill maintains work log:** `write_file` to `WORK_LOG.md`
8. **Skill checks for replanning triggers:** If stage output invalidates the plan, rebuild the `todo` list
9. **For async execution:** `cronjob` to run the skill on a schedule

---

## 6. Portability Assessment

### Is v6 portable to another Hermes installation?

**Yes, entirely.** A Hermes skill is:
- A `SKILL.md` file with documentation
- Optional reference files (markdown, templates)
- Optional helper scripts

Any Hermes user can:
```bash
hermes skills install https://github.com/iamnickthegeek/fable-orchestrator/SKILL.md
```

The skill uses ONLY native Hermes tools (`delegate_task`, `todo`, `terminal`, `write_file`, `read_file`, `cronjob`, `clarify`, `kanban`). No external dependencies. No Python packages to install.

### What the user needs:
- Hermes Agent installed
- API keys configured for their providers
- The skill installed

That's it. No `pip install`, no SQLite setup, no cron configuration, no daemon management.

---

## 7. Detailed Implementation Plan

### Phase 1: Foundation (SKILL.md rewrite)

**Goal:** Rewrite the skill definition to be a strict, prescriptive procedure that uses only native Hermes tools.

**Deliverables:**
- `SKILL.md` with:
  - Trigger conditions (when to use the skill)
  - The 6-stage pipeline with explicit dependencies
  - Model routing logic (auto-detect + YAML override)
  - Guardrails per stage (injected into prompts)
  - Verification gates (must pass before proceeding)
  - Model verification step (confirm correct model used)
  - Work log convention (structured markdown)
  - Replanning triggers (when to rebuild the plan)
  - Consolidation procedure (canonical FINAL.md)
  - Fail-open behavior (retry with fallback models)
  - Cron setup for async execution

**Language:** Imperative. "You MUST...", "You WILL...", "Do NOT...".

**Verification:** The skill must include a self-check at the end of each stage: "Did you verify the model used? Did you run the failable checks? Did you update the work log?"

### Phase 2: Reference Documents

**Goal:** Create the reference documents that support the skill.

**Deliverables:**
- `references/model-routing-table.md` — The primary/secondary/tertiary assignments per stage, with auto-detection logic
- `references/guardrails.md` — The exact guardrails injected into each stage prompt
- `references/verification-templates.md` — Domain-specific pass/fail criteria (software, research, data, writing)
- `references/work-log-template.md` — The structured WORK_LOG.md format
- `references/replanning-triggers.md` — Specific conditions that trigger replanning (e.g., "research found fewer than 3 sources", "implementation failed tests", "critique found more than 3 critical weaknesses")
- `references/model-verification.md` — How to verify the model used by a subagent (inspect output headers, session metadata, or use a known "model fingerprint" prompt)

### Phase 3: Prompt Templates

**Goal:** Create reusable prompt templates for each stage.

**Deliverables:**
- `templates/stage-prompts/research.md` — Prompt template for research stage
- `templates/stage-prompts/plan.md` — Prompt template for planning stage
- `templates/stage-prompts/implement.md` — Prompt template for implementation stage
- `templates/stage-prompts/verify.md` — Prompt template for verification stage
- `templates/stage-prompts/critique.md` — Prompt template for critique stage
- `templates/stage-prompts/consolidate.md` — Prompt template for consolidation stage
- `templates/consolidation-prompt.md` — The master synthesis prompt that reads all prior stages
- `templates/replanning-prompt.md` — The prompt used when replanning is triggered

**Each template must include:**
- The stage-specific guardrails
- The model routing assignment
- The verification criteria
- The expected output format
- The file path where output must be saved

### Phase 4: Helper Scripts (Optional)

**Goal:** Provide optional utility scripts for power users.

**Deliverables:**
- `scripts/verify_models.py` — Pre-flight check: verify that the models in the routing table are available and responsive
- `scripts/auto_detect_providers.py` — Read the user's Hermes config and suggest a routing table

**Note:** These are optional. The skill works without them. They are conveniences for power users.

### Phase 5: Examples

**Goal:** Provide concrete examples of how to use the skill.

**Deliverables:**
- `examples/simple_task.md` — A simple task (e.g., "Write a blog post") with the full 6-stage execution
- `examples/software_project.md` — A software project (e.g., "Build a FastAPI auth service") with verification gates
- `examples/research_report.md` — A research report (e.g., "Competitive analysis of AI ghostwriting tools") with source verification

### Phase 6: Testing and Validation

**Goal:** Test the skill against real tasks to verify it works.

**Deliverables:**
- `examples/test_results.md` — Log of test tasks, what worked, what didn't, adjustments made
- `references/test-notes.md` — Known issues and recommended test matrix

### Phase 7: Documentation

**Goal:** Write the user-facing documentation.

**Deliverables:**
- `README.md` — Installation, usage, configuration
- `CONTRIBUTING.md` — How to contribute to the skill
- `LICENSE` — MIT license

---

## 8. Configuration: Auto-Detect + YAML Override

### Auto-Detection Logic

The skill will inspect the user's Hermes config to build a default routing table:

1. **Read `~/.hermes/config.yaml`** — Check `model.provider`, `model.default`, `delegation.model`
2. **Read `~/.hermes/.env`** — Check which API keys are set (OPENROUTER_API_KEY, ANTHROPIC_API_KEY, etc.)
3. **Build a provider list** — Rank providers by availability
4. **Map providers to stages** — Use the best available model for each stage type

### YAML Override

If the user wants explicit control, they create a `fable-config.yaml` in the project directory:

```yaml
# fable-config.yaml
routing:
  research:
    primary: {model: "deepseek-v4-flash", provider: "opencode-go"}
    secondary: {model: "gemini-2.5-flash-lite", provider: "google"}
    tertiary: {model: "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", provider: "openrouter"}
  plan:
    primary: {model: "glm-5.1", provider: "opencode-go"}
    secondary: {model: "gemini-2.5-pro", provider: "google"}
    tertiary: {model: "deepseek-v4-pro", provider: "opencode-go"}
  # ... etc for all stages

guardrails:
  # Override default guardrails per stage
  research: "Custom guardrails for research..."
  plan: "Custom guardrails for plan..."

verification:
  # Override verification criteria per domain
  software:
    - "tests pass"
    - "build succeeds"
  research:
    - "every claim has a source"
    - "all URLs are live"

replanning:
  enabled: true
  triggers:
    - "research.sources.count < 3"
    - "verify.tests.passed == false"
    - "critique.critical_weaknesses > 3"
```

The skill reads this file at the start of execution. If it doesn't exist, it uses the auto-detected defaults.

---

## 9. Model Verification: How to Enforce Cross-Family Execution

### The Problem

`delegate_task(model="glm-5.1")` is a suggestion. The subagent may default to the session model (`kimi-k2.6`) and ignore the parameter.

### The Solution: Model Verification Step

After every stage, the skill runs a **model verification check**:

1. **Method A: Inspect session metadata** — If the subagent's session is searchable, check what model was actually used.
2. **Method B: Known "model fingerprint"** — Include a prompt like "What model are you?" in the stage output and verify the response.
3. **Method C: Use `terminal` with hardcoded flags** — Spawn `hermes chat -q` with explicit `-m` and `--provider` flags. This is the v5 approach but used only for verification-critical stages.

**The skill's rule:**
- For Research and Plan: Use `delegate_task` with model suggestion. Accept best-effort.
- For Implement and Verify: Use `delegate_task` with model suggestion, but run a verification check.
- For Critique: **MUST use a different model family than Implement.** If verification fails, retry with `terminal` hardcoded flags.
- For Consolidate: **MUST use a different model family than Implement.** If verification fails, retry with `terminal` hardcoded flags.

### Retry Logic

If verification fails:
1. Log the failure in the work log
2. Retry with `terminal` spawning `hermes chat -q` with hardcoded flags
3. If that fails, retry with the secondary model in the routing table
4. If that fails, retry with the tertiary model
5. If all fail, mark the stage as blocked and flag to the user

---

## 10. Dynamic Replanning: How to Rebuild the DAG Mid-Flight

### The Trigger

The skill checks for replanning after every stage completion:

1. **Research stage:** If sources found < 3, or if the task is simpler than expected, skip Plan and go straight to Implement.
2. **Verify stage:** If tests fail, or if the implementation is fundamentally wrong, rebuild the plan from Implement.
3. **Critique stage:** If critical weaknesses > 3, add a new "Fix" stage before Consolidate.
4. **Any stage:** If the user provides new requirements mid-flight, rebuild the plan.

### The Replanning Procedure

1. **Read the current todo list** — `todo()` to get the current state
2. **Read the work log** — `read_file` on `WORK_LOG.md`
3. **Analyze the gap** — Use `delegate_task` with a "replanning" prompt to analyze what changed
4. **Build the new plan** — Use `delegate_task` with a "planning" prompt to build the new DAG
5. **Update the todo list** — `todo(merge=true)` to update with the new stages
6. **Continue execution** — Proceed with the new plan

### The Replanning Prompt

Stored in `templates/replanning-prompt.md`:

```
You are the Fable Orchestrator replanning engine.

The current task has encountered an obstacle:
- Original plan: [plan]
- Current stage: [stage]
- Obstacle: [obstacle]
- Work log: [work log]

Rebuild the stage plan. Rules:
- Preserve completed work. Do not re-run completed stages.
- Add new stages only if necessary.
- Remove stages that are no longer needed.
- Update dependencies.
- Return a JSON todo list.
```

---

## 11. Size Reduction

| Component | v5 Lines | v6 Lines | Reduction |
|-----------|----------|----------|-----------|
| Engine (core, state, planner, agent_pool, verification, context, questioner, daemon) | ~935 | 0 | -100% |
| SKILL.md | 0 | ~300 | +300 |
| Reference docs | 0 | ~200 | +200 |
| Prompt templates | 0 | ~150 | +150 |
| Helper scripts | ~80 | ~50 | -38% |
| Setup/install | ~31 | 0 | -100% |
| **Total** | **~1,046** | **~700** | **-33%** |

The v6 is smaller, more portable, and more reliable.

---

## 12. Summary

### What the v5 engine duplicates (should be removed):
- SQLite state manager → `kanban` + `memory`
- Custom daemon → `cronjob`
- Threading agent pool → `delegate_task` + `terminal`
- Context compression → Hermes built-in
- Proactive questioner subprocess → `clarify` or `delegate_task`
- Raw file operations → `read_file`, `write_file`, `search_files`
- Raw subprocess calls → `terminal`

### What Hermes lacks (the real gaps to fill):
- Structured 6-stage decomposition with guardrails
- Cross-family verification/critique enforcement
- Fail-open model routing with retry
- Domain-specific verification gates
- Structured work log handoff protocol
- Dynamic replanning
- Consolidation as a canonical stage
- Model verification (confirm the right model was used)

### What v6 becomes:
A **Hermes skill** that uses native tools for everything, plus reference documents and prompt templates for the Fable-specific discipline. The skill is the orchestration logic, not a Python engine.

**Estimated size reduction:** From ~1,046 lines (v5 engine) to ~700 lines (skill + templates + references).

**Estimated portability:** 100% — any Hermes installation can install and use the skill immediately.

**Estimated reliability:** Higher than v5 because:
- No subprocess fragility
- No SQLite lock contention
- No threading issues
- Uses Hermes's battle-tested native tools

---

## 13. Next Steps

Awaiting user go-ahead to proceed with Phase 1 (SKILL.md rewrite).

When approved, I will:
1. Rewrite `SKILL.md` as a strict, prescriptive procedure
2. Create the reference documents
3. Create the prompt templates
4. Create the optional helper scripts
5. Create the examples
6. Test against a real task
7. Update the README and documentation

**No code changes to existing files until explicit approval.**

---

*End of plan. Ready for user go-ahead.*
