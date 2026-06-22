# Fableous v0.8.2

**Strict multi-stage execution for Hermes Agent. No engine. Just the skill and a few helper scripts.**

A Hermes-native orchestrator, inspired by Claude Fable 5, that decomposes complex tasks into 6 stages, enforces cross-family verification, verifies model usage, and dynamically replans when obstacles appear. Uses only native Hermes tools — no Python engine, no SQLite, no daemon.

Built by Nick Smith. MIT licensed.

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

Trigger Fableous when:

1. You explicitly ask for thorough/systematic/Fable mode ("do this thoroughly", "run this through fableous").
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

### 3. Create a fable-config.yaml

Create a `fable-config.yaml` in the skill directory (`~/.hermes/skills/fableous/fable-config.yaml`) with your preferred models:

```yaml
routing:
  research:
    primary:
      model: deepseek-ai/deepseek-v4-flash
      provider: nvidia
    secondary:
      model: gemini-2.5-flash-lite
      provider: google
  # ... etc for all stages
```

See `templates/fable-config-nvidia-nim.yaml` for a complete example. **No default routing table exists** — you MUST provide a fable-config.yaml.

### 4. Load the Skill

```
/skill fableous
```

Or start Hermes with the skill preloaded:

```bash
hermes -s fableous
```

### 5. Give a Task

```
"Run this through Fableous: write a competitive analysis of AI ghostwriting tools for digital marketers, with 3 real competitors, verified pricing, and cited sources."
```

The skill will:
1. Create a 6-stage todo list
2. Delegate each stage to the right model
3. Run verification checks
4. Verify the models used
5. Critique on a different model family
6. Consolidate into FINAL.md
7. Maintain a WORK_LOG.md for multi-session continuity

### 6. For Multi-Session Tasks

Set up a cron job to continue execution across session resets:

```
cronjob(
  action="create",
  schedule="*/15 * * * *",
  prompt="Load the fableous skill. Read the WORK_LOG.md in the project directory. Continue execution from the next pending stage. Follow the stage execution procedure exactly.",
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

All routing is driven by `fable-config.yaml` in the skill directory. **There is no default routing table.** If no config file is found, the skill raises an error with instructions.

Example config (NVIDIA NIM):

| Stage | Primary | Provider |
|-------|---------|----------|
| Research | deepseek-ai/deepseek-v4-flash | nvidia |
| Plan | z-ai/glm-5.1 | nvidia |
| Implement | nvidia/nemotron-3-ultra-550b-a55b | nvidia |
| Verify | moonshotai/kimi-k2.6 | nvidia |
| Critique | qwen/qwen3.5-397b-a17b | nvidia |
| Consolidate | nvidia/nemotron-3-ultra-550b-a55b | nvidia |

### Cross-Family Verification

The critical anti-hallucination measure: **Critique and Consolidate must run on a different model family than Implement.**

If Kimi wrote the code, GLM or Gemini must critique it. This is non-negotiable.

### Model Verification

`delegate_task` has **no per-call model parameter** (confirmed by source-code audit). All model routing uses **config cycling** via `route_config.py`:

1. **Config cycling** — Before each `delegate_task` call, run `route_config.py set --stage STAGE_NAME` to update `delegation.model` and `delegation.provider`. The child agent reads these from disk — guaranteed routing.
2. **Model tag** — Each stage output includes `[MODEL: name, PROVIDER: provider]` as audit trail. Verified with `route_config.py verify`.
3. **Terminal fallback** — If config cycling fails twice, use `run_stage.py` or `hermes chat -q` with explicit `-m` and `--provider` flags.

### Dynamic Replanning

When a stage produces unexpected results, the skill rebuilds the plan:

- Insufficient research? Add an "Extended Research" stage.
- Verification failed? Add a "Fix" stage.
- New requirements? Rebuild the plan, preserve completed work.

### Work Log

The `WORK_LOG.md` is the handoff protocol between sessions. At the start of any continuation, the skill reads the work log before doing anything else.

---

## Verification

Fableous uses four layers of verification. Every stage is only complete once all relevant checks pass.

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

`delegate_task` has **no per-call model parameter** (source-code audit confirmed). Fableous uses **config cycling** to guarantee routing:

1. **Config cycling** — `route_config.py set --stage STAGE_NAME` updates `delegation.model` and `delegation.provider` before every `delegate_task` call. The child agent reads these from disk — not a suggestion.
2. **Model tag** — the subagent writes `[MODEL: name, PROVIDER: provider]` as the first line of output. Verified with `route_config.py verify`.
3. **Terminal fallback** — if config cycling fails twice, retry with `run_stage.py` or `hermes chat -q -m MODEL --provider PROVIDER`.

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
"Run this through Fableous: write a 500-word blog post about AI marketing for solopreneurs."
```

**Result:** `FINAL.md` with Version & Caveats header.

**Time:** 30-45 minutes.

### Example 2: Software Project

```
"Run this through Fableous: build a FastAPI authentication service with JWT tokens, rate limiting, and user registration."
```

**Result:**
- `app/` — The actual code
- `tests/` — pytest suite
- `FINAL.md` — README with setup instructions

**Time:** 1-2 hours.

### Example 3: Large Research Report (With Cron)

```
"Run this through Fableous: write a 20-page research report on AI marketing trends for 2026."
```

**Result:** `FINAL.md` (20 pages) with all sources verified.

**Time:** 2-4 hours (runs via cron job).

See `examples/` for full execution details.

---

## Configuration

### fable-config.yaml (Required)

Create a `fable-config.yaml` in the skill directory (`~/.hermes/skills/fableous/fable-config.yaml`). This is the **only** source of routing configuration. There is no default fallback.

Config is auto-discovered from:
1. Skill directory: `~/.hermes/skills/fableous/fable-config.yaml`
2. Working directory: `./fable-config.yaml`

If neither exists, the skill raises `RuntimeError` with setup instructions.

### Helper Scripts

Run these from the skill directory:

```bash
# Config cycling — set model/provider before each stage
python3 scripts/route_config.py set --stage research
python3 scripts/route_config.py verify --output stage1.md --expected-model deepseek-v4-flash
python3 scripts/route_config.py restore

# Check providers and API keys
python3 scripts/verify_models.py

# Generate a custom fable-config.yaml
python3 scripts/auto_detect_providers.py --save

# Run a single stage with hard routing and fallback
python3 scripts/run_stage.py --stage research --prompt "Your task" --output stage1.md

# Detect routing capability (native vs config cycling)
python3 scripts/detect_routing.py
```

---

## Requirements

- Hermes Agent (any recent version)
- API keys for at least one provider (configured in `~/.hermes/.env`)
- A `fable-config.yaml` in the skill directory
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
│   ├── config-cycling.md         # Config cycling spec and edge cases
│   ├── model-routing-table.md    # Quick lookup
│   ├── model-verification.md     # Verification hierarchy (config cycling primary)
│   ├── verification-templates.md # Domain-specific failable checks
│   ├── guardrails.md             # Prompt guardrails per stage
│   ├── work-log-template.md      # Structured handoff protocol
│   ├── replanning-triggers.md    # When and how to replan
│   ├── v6-1-trigger-checklist.md # When to invoke Fableous, when to skip
│   ├── delegate-task-model-routing-audit.md  # Source-code evidence
│   ├── delegate-task-model-fallback.md       # Config cycling → terminal fallback
│   ├── timeout-recovery-recipe.md            # Recovering from subagent timeouts
│   ├── model-mismatch-recovery.md            # Model verification failure procedures
│   ├── native-first-gap-fillers.md           # What Fable adds vs Hermes provides
│   ├── helper-scripts.md         # When and how to use the scripts/ utilities
│   ├── github-publication.md     # Publishing to GitHub
│   ├── token-budget-mode.md      # Running Fable on cheapest models
│   ├── pricing-verification-volatility.md    # AI pricing changes fast
│   ├── nvidia-nim-unified-provider.md        # NVIDIA NIM as unified provider
│   ├── cross-run-quality-analysis.md         # Cross-run quality case study
│   ├── ronin-partner-finder-case-study.md    # Worked example: building a skill
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
│   ├── replanning-prompt.md      # Dynamic replanning prompt
│   └── fable-config-nvidia-nim.yaml            # Ready-to-use NVIDIA NIM config
├── scripts/
│   ├── route_config.py           # Config cycling engine (set/restore/verify)
│   ├── fable_routing.py          # Shared routing constants (no default table)
│   ├── detect_routing.py         # Feature detection (native vs config cycling)
│   ├── run_stage.py              # Hard-routed stage runner with fallback
│   ├── verify_models.py          # Pre-flight model availability check
│   └── auto_detect_providers.py  # Auto-detect routing table from config
├── examples/
│   ├── simple_task.md            # Blog post example
│   ├── software_project.md       # FastAPI example
│   ├── research_report.md        # Competitive analysis example
│   └── test_results.md           # Living test log
└── archive/                      # Old v1-v5 engine code and planning docs
```

---

## Version History

- **v0.1-v0.3:** Procedural skill with sequential execution and subprocess model switching.
- **v0.4:** Dynamic planner, parallel execution, checkpoint/resume.
- **v0.5:** Modular Python engine, SQLite state, daemon pattern. Over-engineered — rebuilt 70% of native Hermes capabilities.
- **v0.6.0:** Native-first. No engine. Uses Hermes tools exclusively. Adds model verification, dynamic replanning, strict procedural discipline, and small helper scripts for pre-flight checks and hard-routed stage execution.
- **v0.6.1:** Formalised the trigger decision into a short checklist so the agent knows when to invoke Fableous and when to skip it.
- **v0.7.0:** Config cycling replaces terminal spawning as the primary routing method. New `route_config.py` engine with set/restore/verify/status commands. New `detect_routing.py` for future-proof native routing detection. Full rewrite of model verification hierarchy — source-code audit confirmed `delegate_task` has no per-call model parameter. Pitfalls 2 and 8 resolved.
- **v0.7.1:** Async subagent support. Research and Plan now dispatch with `delegate_task(background=true)` for true parallel execution. Completion events arrive as new turns. Sync path unchanged for Implement+. Config cycling confirmed snapshot-safe for async dispatch. New pitfalls for async-specific traps (verification timing, capacity rejection).
- **v0.7.2:** Token-budget / lightweight mode. Single-model execution when user prioritises speed/cost over cross-family rigor.
- **v0.7.3:** Orchestrator discipline. Pitfall 14 (orchestrator override), Pitfall 15 (inline async). Tightened token-budget mode triggers.
- **v0.7.3.1:** Token-budget mode split into Primary-Only and Single-Model Flatlining sub-modes.
- **v0.7.3.2:** T6 Fix stage template for critique finding >3 critical weaknesses.
- **v0.7.3.3:** Single-model flatlining edge case (user bans all model routing).
- **v0.8.0:** Quality intelligence. Deliverable type classification, cross-run reconciliation, methodology consistency, strategic insight preservation, fix calibration, quality tradeoffs documentation.
- **v0.8.1:** Config file auto-discovery. `load_routing()` now finds fable-config.yaml from skill directory and working directory. Added Pitfall 16 (config silently ignored) and Pitfall 17 (search_files glob misses files).
- **v0.8.2:** Removed `DEFAULT_ROUTING` table entirely — all routing MUST come from fable-config.yaml. Fixed `providers.nvidia.base_url` in Hermes config. Removed duplicate `nvidia:` key. Added Pitfall 18 (NVIDIA provider setup requires base_url + env var in gateway process). Changed version numbering to v0.x scheme.

---

## License

MIT. See [LICENSE](LICENSE).

---

## Shoutouts

Written by a combination of [GLM 5.1](https://github.com/zai-org), [Deepseek V4 Pro](https://github.com/deepseek-ai) and a little sprinkling of [Kimi 2.7 Coder](https://github.com/MoonshotAI) under my "guidance" ...

Inspired by [Claude Fable 5](https://www.anthropic.com/), [@mrtooher's](https://github.com/mrtooher/fable-mode) Fable Model skill & [@papajos](https://github.com/papajo/Fable-Brain-Module) Fable Brain system.

Also, huge shoutout to [Teknium](https://github.com/teknium1) & [NousResearch](https://nousresearch.com/) for creating Hermes.

---

## Questions?

- Read [`INSTALL.md`](INSTALL.md) for setup help.
- Open an issue: [github.com/iamnickthegeek/fableous/issues](https://github.com/iamnickthegeek/fableous/issues)
- Ask your Hermes agent to help you troubleshoot.
- Read the skill with `skill_view(name='fableous')`.
