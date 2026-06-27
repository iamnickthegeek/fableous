# Native-First Design — Gap-Fillers, Not Duplicates

Fable Orchestrator is a procedural layer on top of Hermes. It uses Hermes tools
exclusively and adds logic only where Hermes leaves a gap. This document records
the audit criteria so future contributors do not accidentally reintroduce v0.5.0-style
engine code.

## Core principle

If Hermes already does it, Fable does not reimplement it. If Hermes almost does
it but misses a Fable-specific requirement, Fable adds the smallest possible
shim.

## What Fable uses natively

| Fable need | Hermes tool | Why it is not duplicated |
|------------|-------------|--------------------------|
| Stage tracking | `todo()` | Native task list |
| Subagent execution | `delegate_task()` | Native agent spawning |
| Hard model routing fallback | `terminal()` running `hermes chat` | Uses Hermes CLI, just adds explicit flags |
| Multi-session continuation | `cronjob()` | Native scheduler |
| Model usage lookup | `session_search()` | Native session history |
| Durable facts | `memory()` | Native memory |
| File I/O | `read_file()` / `write_file()` | Native file tools |
| Web research | `web_search()` / `web_extract()` | Native web tools |
| Code execution for checks | `terminal()` / `execute_code()` | Native execution tools |

## What Fable adds because Hermes does not provide it

| Fable addition | Gap it fills | Artifact |
|----------------|--------------|----------|
| Stage-specific model routing table | Hermes has no per-stage model assignment | `scripts/fable_routing.py`, `fable-config.yaml` |
| Model verification | `delegate_task(model=...)` is suggestive | SKILL.md model verification procedure |
| Cross-family enforcement | Hermes does not prevent critique from running on the same family as implement | SKILL.md enforcement rules |
| Per-stage fallback chain | `hermes fallback` is global, not stage-aware | `scripts/run_stage.py` |
| Pre-flight routing check | `hermes config check` validates Hermes, not Fable's routing table | `scripts/verify_models.py` |
| Routing config generator | Hermes does not generate Fable-specific YAML | `scripts/auto_detect_providers.py` |
| 6-stage procedure with dependencies | Hermes has no built-in multi-stage workflow | SKILL.md procedure |
| Replanning triggers | Hermes does not auto-rebuild plans | SKILL.md replanning section |
| Multi-session handoff | Hermes does not persist workflow state across sessions | `WORK_LOG.md` protocol |

## Decision tree for adding new code

Before adding a Python script, a subprocess wrapper, or a state store, ask:

1. Can a native Hermes tool do this? If yes, use it.
2. Can a native Hermes tool do this with a small prompt change or flag? If yes, use it.
3. Is the missing piece specific to Fable's routing/verification/workflow? If yes, add the smallest shim.
4. Are you building a general-purpose engine, daemon, database, or state machine? If yes, stop. That is v0.5.0.

## Audit results

Last audit: 2026-06-15. Result: no duplication found.

- `scripts/fable_routing.py`: constants only, no logic that mirrors Hermes.
- `scripts/verify_models.py`: wraps `hermes config check` and adds Fable-specific key/routing checks.
- `scripts/auto_detect_providers.py`: reads Hermes config, generates Fable-specific YAML.
- `scripts/run_stage.py`: spawns `hermes chat` with explicit model/provider; fallback is per-stage and cross-family aware.
- `SKILL.md`: procedural instructions using native tools only.

## Things that look like duplication but are not

**`run_stage.py` fallback vs `hermes fallback`**
- `hermes fallback` is a global provider chain for rate-limit/overload errors.
- Fable's fallback is per-stage and respects cross-family rules. It cannot be replaced by `hermes fallback`.

**`verify_models.py --live-test` vs `hermes chat`**
- The live test is just a wrapper that pings every model in the routing table.
- Hermes has no "test every model in this list" command.

**`WORK_LOG.md` vs Hermes session memory**
- Hermes sessions reset. `WORK_LOG.md` is a durable, human-readable handoff file.
- Hermes has no equivalent workflow state persistence mechanism.

## Related

- `SKILL.md` → Common Pitfalls section, especially Pitfall 1
- `references/helper-scripts.md` → when to use scripts versus native tools
