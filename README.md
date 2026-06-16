# Fable Orchestrator v6.1

**Strict multi-stage execution for Hermes Agent. No engine. Just the skill and a few helper scripts.**

A Hermes-native orchestrator that decomposes complex tasks into 6 stages, enforces cross-family verification, verifies model usage, and dynamically replans when obstacles appear. Uses only native Hermes tools — no Python engine, no SQLite, no daemon.

Built by Nick Smith (Point Clear Advisory). MIT licensed.

---

## What This Does

You have a complex task — a research report, a software project, a competitive analysis. Instead of a one-shot attempt that might miss things, you:

1. **Load the skill** and describe the task
2. **The skill decomposes it** into 6 stages with explicit dependencies
3. **Each stage is delegated** to a model optimized for that cognitive task
4. **Verification checks** run after every stage — checks that can actually fail
5. **Model verification** confirms the right model was used
6. **Critique runs on a different model family** — the anti-hallucination measure
7. **Dynamic replanning** rebuilds the plan when obstacles invalidate it
8. **Consolidation** produces a single canonical deliverable

For multi-session tasks, a cron job continues execution across session resets.

---

## Who This Is For

- **Solopreneurs** who want AI to handle complex work without micromanaging
- **Content creators** who need consistent, high-quality, verified output
- **Non-coders** who want the power of multi-agent AI without writing code
- **Anyone** who has ever thought "I wish the AI could just work on this for a few hours and tell me when it's done"

## When to Use It

Trigger Fable when:

1. You explicitly ask for thorough/systematic/Fable mode ("do this thoroughly", "run this through fable").
2. The task spans multiple files, sources, sessions, or domains.
3. A one-shot attempt would plausibly miss something important.

Skip Fable when the task has one obvious approach and fits in a single pass.

## Quick Start

### 1. Install the Skill

See [`INSTALL.md`](INSTALL.md) for a step-by-step guide. The quickest way:

```bash
./setup.sh
```

Or install manually:

```bash
hermes skills install https://raw.githubusercontent.com/iamnickthegeek/fableous/main/SKILL.md
```

No `pip install`. No daemon setup. No SQLite configuration. Just the skill.

### 2. Check Your Setup

```bash
python3 scripts/verify_models.py
```

This confirms your API keys are configured.

### 3. Load the Skill

```
/skill fableous
```

Or start Hermes with the skill preloaded:

```bash
hermes -s fableous
```

### 4. Give a Task

```
"Run this through Fable: write a competitive analysis of AI ghostwriting tools for digital marketers, with 3 real competitors, verified pricing, and cited sources."
```

The skill will:
1. Create a 6-stage todo list
2. Delegate each stage to the right model
3. Run verification checks
4. Verify the models used
5. Critique on a different model family
6. Consolidate into FINAL.md
7. Maintain a WORK_LOG.md for multi-session continuity

### 5. For Multi-Session Tasks

Set up a cron job to continue execution across session resets:

```
cronjob(
  action="create",
  schedule="*/15 * * * *",
  prompt="Load the fableous skill. Read the WORK_LOG.md in the project directory. Continue execution from the next pending stage. Follow the v6 stage execution procedure exactly.",
  name="fableous-[project]"
)
```

---

## How It Works

### The 6-Stage Pipeline

Every task goes through these stages:

1. **Research** — Gather sources, extract claims, verify URLs
2. **Plan** — Architecture, audience segmentation, methodology
3. **Implement** — Write the deliverable, save to disk
4. **Verify** — Run failable checks, trace sources, check consistency
5. **Critique** — Independent review on a different model family
6. **Consolidate** — Read all stages, apply fixes, produce FINAL.md

### Dependencies

- Stage 1 (Research) and Stage 2 (Plan) have no dependencies. They can run in parallel.
- Stage 3 (Implement) depends on both. It runs after both complete.
- Stage 4 (Verify) depends on Stage 3.
- Stage 5 (Critique) depends on Stage 3 and Stage 4.
- Stage 6 (Consolidate) depends on all prior stages.

### Model Routing

| Stage | Primary | Secondary | Tertiary | Rationale |
|-------|---------|-----------|----------|-----------|
| Research | `deepseek-v4-flash` (Opencode Go) | `gemini-2.5-flash-lite` (Google) | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` (OpenRouter) | Fast, broad, cheap |
| Plan | `glm-5.1` (Opencode Go) | `gemini-2.5-pro` (Google) | `deepseek-v4-pro` (Opencode Go) | Structured reasoning |
| Implement | `kimi-k2.7-code` (Opencode Go) | `kimi-k2.6` (Opencode Go) | `gemini-2.5-pro` (Google) | Code-specialized |
| Verify | `deepseek-v4-pro` (Opencode Go) | `gemini-2.5-pro` (Google) | `kimi-k2.6` (Opencode Go) | Different family from coder |
| Critique | `glm-5.1` (Opencode Go) | `gemini-2.5-pro` (Google) | `kimi-k2.6` (Opencode Go) | Independent evaluation |
| Consolidate | `deepseek-v4-pro` (Opencode Go) | `glm-5.1` (Opencode Go) | `gemini-2.5-pro` (Google) | Reads all stages, produces canonical output |

Auto-detects available providers from your Hermes config. Or provide a `fable-config.yaml` in your project directory for explicit control.

### Cross-Family Verification

The critical anti-hallucination measure: **Critique and Consolidate must run on a different model family than Implement.**

If Kimi wrote the code, GLM or Gemini must critique it. This is non-negotiable.

### Model Verification

`delegate_task` has a `model` parameter, but it is suggestive — the subagent can ignore it. The skill verifies the model actually used by:

1. **Model tag** — Include `[MODEL: name, PROVIDER: provider]` in the prompt. Check the first line of output.
2. **Session search** — Find the subagent's session and inspect the model used.
3. **Terminal spawn** — Retry with hardcoded flags if verification fails.

For a ready-made hard-routing wrapper, use `scripts/run_stage.py`.

### Dynamic Replanning

When a stage produces unexpected results, the skill rebuilds the plan:

- Insufficient research? Add an "Extended Research" stage.
- Verification failed? Add a "Fix" stage.
- New requirements? Rebuild the plan, preserve completed work.

### Work Log

The `WORK_LOG.md` is the handoff protocol between sessions. At the start of any continuation, the skill reads the work log before doing anything else.

---

## Verification

Fable uses four layers of verification. Every stage is only complete once all relevant checks pass.

### 1. Domain-specific failable checks

Each stage must have a pass condition defined before it is delegated. "It looks right" is not a check. The actual checks depend on the work type:

| Domain | Example checks |
|--------|----------------|
| **Software** | Tests pass (`pytest -q`), build succeeds, type check passes, lint clean |
| **Research** | At least 3 cited sources, URLs return 200, every claim traces to a source, no internal contradictions |
| **Data** | No nulls/duplicates, outliers within threshold, hypothesis test returns expected result |
| **Writing** | Matches brief (word count, sections, tone), claims trace to research, plagiarism check, audience/tone check |
| **Generic** | File exists and has content, required section or string present, diff against expected output |

If any check fails, the stage fails and the pipeline stops until it is fixed or re-run.

### 2. Model verification

`delegate_task(model=...)` is only a suggestion, so Fable verifies the actual model used for every stage:

1. **Model tag** — the subagent writes `[MODEL: name, PROVIDER: provider]` as the first line of output.
2. **Session search** — if the tag is missing, search the subagent's session metadata.
3. **Terminal spawn** — if still uncertain, retry with `hermes chat -m MODEL --provider PROVIDER`.

Required for Implement, Verify, Critique, and Consolidate. Best-effort for Research and Plan.

### 3. Cross-family verification

Verify, Critique, and Consolidate must run on a different model family than Implement. If Kimi wrote the code, DeepSeek, GLM, or Gemini must verify and critique it. Same-family retry counts as a failure.

### 4. Replanning triggers

After every stage, the skill checks whether the output invalidates the plan. If so, it rebuilds the plan before continuing:

| Trigger | Condition | Action |
|---------|-----------|--------|
| T1 | Research found fewer than 3 sources | Add "Extended Research" stage |
| T2 | Plan is simpler than expected | Skip unnecessary stages |
| T3 | Plan is more complex than expected | Add new stages (e.g., "Security Audit") |
| T4 | Implement output differs from plan | Rebuild plan, preserve research |
| T5 | Verify fails | Re-run Implement or add "Fix" stage |
| T6 | Critique finds more than 3 critical weaknesses | Add "Fix" stage before Consolidate |
| T7 | New requirements mid-flight | Rebuild plan, preserve completed stages |
| T8 | Model verification fails 3 times | Use cheapest available model, flag to user |

All results are logged in `WORK_LOG.md`.

For the full per-domain checklists, see `references/verification-templates.md`. For the full model verification rules, see `references/model-verification.md`.

---

## Examples

### Example 1: Simple Blog Post

```
"Run this through Fable: write a 500-word blog post about AI marketing for solopreneurs."
```

**Result:** `FINAL.md` with Version & Caveats header.

**Time:** 30-45 minutes.

### Example 2: Software Project

```
"Run this through Fable: build a FastAPI authentication service with JWT tokens, rate limiting, and user registration."
```

**Result:**
- `app/` — The actual code
- `tests/` — pytest suite
- `FINAL.md` — README with setup instructions

**Time:** 1-2 hours.

### Example 3: Large Research Report (With Cron)

```
"Run this through Fable: write a 20-page research report on AI marketing trends for 2026."
```

**Result:** `FINAL.md` (20 pages) with all sources verified.

**Time:** 2-4 hours (runs via cron job).

See `examples/` for full execution details.

---

## Configuration

### Auto-Detection

The skill reads your Hermes config (`~/.hermes/config.yaml` and `~/.hermes/.env`) to determine available providers and models.

### Helper Scripts

Run these from the skill directory:

```bash
# Check providers and API keys
python3 scripts/verify_models.py

# Generate a custom fable-config.yaml
python3 scripts/auto_detect_providers.py --save

# Run a single stage with hard routing and fallback
python3 scripts/run_stage.py --stage research --prompt "Your task" --output stage1.md
```

### YAML Override

Create a `fable-config.yaml` in your project directory:

```yaml
routing:
  research:
    primary:
      model: deepseek-v4-flash
      provider: opencode-go
    secondary:
      model: gemini-2.5-flash-lite
      provider: google
    tertiary:
      model: nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free
      provider: openrouter
  # ... etc for all stages
```

The skill uses this instead of auto-detection.

---

## Requirements

- Hermes Agent (any recent version)
- API keys for at least one provider (Opencode Go, Google, or OpenRouter)
- The skill installed via `hermes skills install`

---

## Architecture

```
fableous/
├── SKILL.md                      # Main skill definition (strict procedure)
├── INSTALL.md                    # Step-by-step installation for non-technical users
├── README.md                     # This file
├── CHANGELOG.md                  # Version history
├── setup.sh                      # One-click install + pre-flight check
├── LICENSE                       # MIT license
├── references/
│   ├── model-routing-table.md    # Quick lookup
│   ├── guardrails.md             # Prompt guardrails per stage
│   ├── verification-templates.md # Domain-specific checks
│   ├── work-log-template.md      # Handoff protocol
│   ├── replanning-triggers.md    # When to rebuild the plan
│   ├── model-verification.md     # How to verify models
│   └── test-notes.md             # Known issues and test matrix
├── templates/
│   ├── stage-prompts/            # Prompt templates for each stage
│   │   ├── research.md
│   │   ├── plan.md
│   │   ├── implement.md
│   │   ├── verify.md
│   │   ├── critique.md
│   │   └── consolidate.md
│   ├── consolidation-prompt.md   # Master synthesis prompt
│   └── replanning-prompt.md      # Dynamic replanning prompt
├── scripts/
│   ├── verify_models.py          # Pre-flight model check
│   ├── auto_detect_providers.py  # Auto-detect routing table
│   ├── run_stage.py              # Hard-routed stage runner with fallback
│   └── fable_routing.py          # Shared constants for the scripts
├── examples/
│   ├── simple_task.md            # Blog post example
│   ├── software_project.md       # FastAPI example
│   ├── research_report.md        # Competitive analysis example
│   └── test_results.md           # Living test log
└── archive/                      # Old v1-v5 engine code and planning docs
```

---

## Version History

- **v1-v3:** Procedural skill with sequential execution and subprocess model switching.
- **v4:** Dynamic planner, parallel execution, checkpoint/resume.
- **v5:** Modular Python engine, SQLite state, daemon pattern. Over-engineered — rebuilt 70% of native Hermes capabilities.
- **v6.0:** Native-first. No engine. Uses Hermes tools exclusively. Adds model verification, dynamic replanning, strict procedural discipline, and small helper scripts for pre-flight checks and hard-routed stage execution.
- **v6.1:** Formalised the trigger decision into a short checklist so the agent knows when to invoke Fable and when to skip it.

---

## License

MIT. See [LICENSE](LICENSE).

---

## Questions?

- Read [`INSTALL.md`](INSTALL.md) for setup help.
- Open an issue: [github.com/iamnickthegeek/fableous/issues](https://github.com/iamnickthegeek/fableous/issues)
- Ask your Hermes agent to help you troubleshoot.
- Read the skill with `skill_view(name='fableous')`.
