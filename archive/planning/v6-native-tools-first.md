# v6 Implementation Plan: Native Tools First

## Status

Planning phase. No code changes made yet. This document is the result of the user asking: "is there anything about this software that Hermes is already capable of doing and the software is simply unnecessarily duplicating functionality?"

## The Discovery

After building a 1,200-line Python engine (v5), a full audit revealed that ~70% of the engine rebuilds capabilities Hermes already provides natively.

## What Hermes Already Does (That v5 Engine Duplicates)

| v5 Engine Module | Hermes Native Equivalent | Verdict |
|---|---|---|
| `state.py` (SQLite) | `kanban` + `memory` + `session_search` | Replace |
| `fable_daemon.py` (cron) | `cronjob` tool + `hermes cron` CLI | Replace |
| `agent_pool.py` (threading) | `delegate_task` batch + `terminal` | Replace |
| `context.py` (compression) | Built-in auto-compression | Replace |
| `questioner.py` (subprocess) | `clarify` tool | Replace |
| File operations (raw Python) | `read_file`, `write_file`, `search_files` | Replace |
| `subprocess.run` calls | `terminal` tool | Replace |

## What Hermes Lacks (The Real Gaps to Fill)

| Fable Capability | Hermes Gap | v6 Approach |
|---|---|---|
| Structured 6-stage decomposition | No native stage discipline | Skill documentation + `todo`/`kanban` |
| Stage-specific guardrails | No native guardrail injection | Prompt templates per stage |
| Cross-family verification/critique | `delegate_task` model is suggestive | Subprocess workaround OR document limitation |
| Fail-open model routing | No native retry-with-different-model | Simple JSON config + retry wrapper |
| Domain-specific verification gates | No native verification framework | `terminal`/`execute_code` with discipline |
| Structured work log handoff | No structured format | Markdown template + `write_file` |
| Dynamic replanning | No auto-replan trigger | Manual or future feature |
| Consolidation as canonical stage | No native synthesis stage | Prompt template for `delegate_task` |

## Proposed v6 Architecture

**Principle:** Hermes native FIRST. Custom code only fills gaps.

**Form:** A Hermes skill (not a Python engine). The skill is the orchestration logic, not a standalone package.

**Size:** ~300 lines (skill documentation + templates) instead of ~1,200 lines (v5 engine).

**Portability:** 100% — any Hermes installation can install the skill immediately. No pip install, no daemon setup, no SQLite configuration.

## How v6 Would Work

1. User loads the skill: `hermes -s fable-orchestrator` or `/skill fable-orchestrator`
2. User gives a task: "Build a competitive analysis of AI ghostwriting tools"
3. Skill uses `todo` or `kanban` to create the 6-stage map
4. Skill delegates stages via `delegate_task` (with model routing) or `terminal` (for hardcoded enforcement)
5. Skill runs verification via `terminal` or `execute_code`
6. Skill maintains work log via `write_file`
7. For async execution: `cronjob` to run the skill on a schedule

## Open Questions (Awaiting User Answers)

1. **Pure skill vs. hybrid:** Pure Hermes skill (simplest), or keep some Python helpers?
2. **Model routing configuration:** Hardcoded to user's providers, or configurable YAML?
3. **GitHub publication:** Skill-only repo acceptable (not a Python package)?
4. **Non-coder accessibility:** Pure skill is actually easier for non-coders
5. **Model switching enforcement:** Accept `delegate_task` limitation, or keep subprocess workaround?
6. **Dynamic replanning:** Include in v6, or document as future feature?

## Key Lesson

**Build the skill first, then add an engine only if the skill proves insufficient.** The v5 engine was built before fully understanding what Hermes already provides. The correct sequence is: (1) use native tools, (2) identify gaps, (3) fill gaps with custom code, (4) only then consider building a standalone engine.

## Security Check Before Publication

The user explicitly asked: "Just to confirm there are no API key, vars, etc. published to the repo?"

The v5 repo was scanned with `search_files` and `grep` for patterns like `api_key`, `secret`, `token`, `sk-`, `ghp_`, `-----BEGIN`. No secrets were found. The only sensitive-looking content was author name and email in `setup.py` (standard open-source attribution).

**Procedure:** Always run `grep -rI "sk-[a-zA-Z0-9]\|ghp_[a-zA-Z0-9]\|api_key\|secret_key\|private_key\|-----BEGIN" .` before any GitHub push. Also check `git ls-files` for `.env`, `.key`, `.pem` files.
