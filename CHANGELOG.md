# Changelog

## v0.8.2

- **Removed `DEFAULT_ROUTING` table entirely.** `load_routing()` now raises `RuntimeError` if no `fable-config.yaml` is found. All routing MUST come from the user's config file — no fallback defaults.
- **Fixed `providers.nvidia.base_url`** in Hermes config (was missing, causing subagents to fall back to parent session provider).
- **Removed duplicate top-level `nvidia:` key** from config.yaml that was conflicting with `providers.nvidia`.
- **Added Pitfall 18** (NVIDIA provider setup requires base_url + env var in gateway process).
- **Changed version numbering** from v0.1.0/v0.2.0/v0.3.0 to v0.1/v0.2/v0.3 scheme.

## v0.8.1

- **Config file auto-discovery.** Fixed `load_routing()` in `fable_routing.py` to auto-discover `fable-config.yaml` from skill directory and working directory when `--config` flag is not explicitly passed. Previously the function silently fell back to `DEFAULT_ROUTING` even when a valid config file existed.
- **Updated SKILL.md YAML Override section** to document skill directory as canonical config location.
- **Added Pitfall 16** (config file silently ignored) and **Pitfall 17** (search_files glob can miss files that ls finds).
- **Updated `references/config-cycling.md`** with config file discovery order.

## v0.8.0

- **Quality intelligence.** Six improvements derived from cross-run analysis:
  1. Deliverable type classification in Plan stage (research brief, execution playbook, credential asset, reference document, decision memo)
  2. Cross-run reconciliation in Verify stage
  3. Methodology consistency verification
  4. Strategic insight preservation across stages
  5. Fix calibration in Consolidation (weighed against deliverable type)
  6. Model routing mode reframed as quality/character decision, not just cost
- **Behavioral directives** updated for all six stages.
- **New "Quality Tradeoffs" subsection** under Token-Budget Mode.

## v0.7.3.3

- **Single-model flatlining edge case.** When user explicitly bans all model routing, `route_config.py` is skipped entirely.

## v0.7.3.2

- **T6 Fix stage template.** New `templates/stage-prompts/fix.md` for consistent handling of critique finding >3 critical weaknesses.

## v0.7.3.1

- **Token-budget mode split.** Primary-Only (cheapest per stage, multi-model preserved) vs Single-Model Flatlining (all stages on one model).

## v0.7.3

- **Orchestrator discipline.** Pitfall 14 (orchestrator override), Pitfall 15 (inline async). Tightened token-budget mode triggers.

## v0.7.2

- **Token-budget / lightweight mode.** Single-model execution when user prioritises speed/cost.

## v0.7.1

- **Async subagent support.** Research and Plan dispatch with `delegate_task(background=true)`. Completion events arrive as new turns.

## v0.7.0

- **Config cycling** replaces terminal spawning as primary routing method.
- **New `route_config.py`** engine with set/restore/verify/status commands.
- **New `detect_routing.py`** for native routing detection.
- **Source-code audit confirmed** `delegate_task` has no per-call model parameter.

## v0.6.1

- **Trigger checklist** formalized in SKILL.md.

## v0.6.0

- **Native-first rewrite.** Removed Python engine, daemon, SQLite state.
- Uses only native Hermes tools: `todo`, `delegate_task`, `terminal`, `cronjob`, `session_search`, `memory`.
- Added mandatory model verification, cross-family verification, dynamic replanning, strict 6-stage procedure.
- Added helper scripts: `verify_models.py`, `auto_detect_providers.py`, `run_stage.py`, `fable_routing.py`.
- Archived legacy v0.1.0-v0.5.0 code in `archive/`.

## Earlier versions

See `archive/v0.5.0-engine/CHANGELOG.md` for v0.1.0-v0.5.0 history.
