# Model Verification — v0.8.0 (updated)

Cross-family verification is the core anti-hallucination measure of the Fable Orchestrator. You MUST verify the model used by every subagent. Critique and Consolidation MUST run on a different model family than Implementation — **unless single-model flatlining mode is explicitly active** (see SKILL.md §Token-Budget Mode, Sub-mode 2). In single-model mode, cross-family verification is waived but the pipeline structure (separate verify and critique stages with distinct prompts) still catches most errors.

## The Problem

`delegate_task` has **no per-call `model` parameter**. Source-code audit of `tools/delegate_tool.py` confirmed: the tool schema (`DELEGATE_TASK_SCHEMA`) has no `model` property, the dispatch function (`_dispatch_delegate_task`) does not extract `model` from `function_args`, and the Python function signature has no `model` parameter. Model routing is resolved exclusively from `delegation.model` and `delegation.provider` in `config.yaml` — global settings that apply to ALL subagents. When both are empty (the default), every subagent inherits the parent session's model regardless of what `model=` value is passed in the tool call. See `references/delegate-task-model-routing-source-audit.md` for the full evidence.

The `[MODEL: ...]` tag in stage prompts is self-reported text — it proves what the subagent claims, not what model actually ran.

## Verification Hierarchy

### Method 1: Config Cycling (Authoritative)

When `route_config.py set --stage X` completes, the model/provider is guaranteed for the next `delegate_task` call. The config is read from disk by `_resolve_delegation_credentials` on every call. This is the primary verification method because it controls routing at the infrastructure level.

```
terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py set --stage research")
delegate_task(goal="...", context="...", toolsets=["web", "file"])
terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py verify --output stage1_research.md --expected-model deepseek-v0.4.0-flash")
```

### Method 2: Model Tag (Audit Trail)

Include this instruction in stage prompts as a secondary confirmation:

```
At the top of your output, write exactly: [MODEL: your-model-name, PROVIDER: your-provider]
This tag is an audit trail. The actual model routing was set via config cycling
before this call. If the tag doesn't match the assigned model, report it but
don't retry — trust the config.
```

Use `route_config.py verify` to check the tag:

```bash
python3 scripts/route_config.py verify --output stage1_research.md --expected-model deepseek-v0.4.0-flash
```

- **Exit 0**: Tag matches. Confirmed.
- **Exit 1**: Tag mismatch. Check config — probably a provider error, not a routing failure.
- **Exit 2**: Tag missing. Not a routing failure — the config was set correctly.

### Method 3: Terminal Spawn (Fallback)

If config cycling fails twice, use `run_stage.py --stage X --prompt "..."` which calls `hermes chat -q -m MODEL --provider PROVIDER` directly. No config modification needed. See `references/delegate-task-model-fallback.md`.

## Subagent Self-Report Is Unreliable (Live Test Evidence)

In the June 2026 live test of a full 6-stage Fable run, every `delegate_task` result summary's `"model"` field reported `"deepseek-v0.4.0-pro"` — the parent session model — regardless of what `route_config.py set` had configured. This is a consistent and reproducible behavior, not a one-off anomaly.

| Stage | Config routing set to | Summary `"model"` field | Output `[MODEL:]` tag | Tag verified? |
|-------|----------------------|------------------------|----------------------|:---:|
| 1 Research | deepseek-v0.4.0-flash | deepseek-v0.4.0-pro | deepseek-v0.4.0-flash | ✅ |
| 2 Plan | glm-5.1 | deepseek-v0.4.0-pro | glm-5.1 | ✅ |
| 3 Implement | kimi-k2.7-code | deepseek-v0.4.0-pro | kimi-k2.7-code | ✅ |
| 4 Verify | deepseek-v0.4.0-pro | deepseek-v0.4.0-pro | deepseek-v0.4.0-pro | ✅ |
| 5 Critique | glm-5.1 | deepseek-v0.4.0-pro | glm-5.1 | ✅ |
| 6 Consolidate | deepseek-v0.4.0-pro | deepseek-v0.4.0-pro | deepseek-v0.4.0-pro | ✅ |

**Rule:** Never trust the `delegate_task` result summary's `"model"` field. It reports the session wrapper's identity, not which model actually processed the subagent's API calls. The output file's `[MODEL:]` tag and `route_config.py verify` are the only reliable indicators.

**When the summary matches the tag** (Stages 4 and 6), it's only because the parent session coincidentally uses the same model as the config routing — not because the summary is correct.

## Enforcement Rules

| Stage | Delegate Method | Verification Required | Fallback on Failure |
|-------|----------------|----------------------|---------------------|
| Research | Config cycling + async | Deferred until completion event | Re-run sync, then terminal fallback |
| Plan | Config cycling + async | Deferred until completion event | Re-run sync, then terminal fallback |
| Implement | Config cycling | Required | Re-run config cycling, then terminal fallback |
| Verify | Config cycling | Required — MUST be different family from Implement | Re-run config cycling, then terminal fallback |
| Critique | Config cycling | Required — MUST be different family from Implement | Re-run config cycling, then terminal fallback |
| Consolidate | Config cycling | Required — MUST be different family from Implement | Re-run config cycling, then terminal fallback |

You MAY use `delegate_task` without config cycling for simple tasks where model assignment does not matter, but never rely on it for model routing.

**Single-model flatlining exception (v0.7.3.2+):** When the user explicitly bans all model routing, `route_config.py` is skipped entirely. The parent session model IS the target model; `delegate_task` inherits it naturally. Cross-family verification is waived. The model tag in stage outputs still serves as audit trail, but verification is reduced to checking the output file header matches the parent model. See SKILL.md §Token-Budget Mode, Sub-mode 2, "Edge case."

## Cross-Family Verification

### Family Definitions

| Family | Models | Provider |
|--------|--------|----------|
| DeepSeek | deepseek-v0.4.0-flash, deepseek-v0.4.0-pro | Opencode Go |
| GLM | glm-5.1 | Opencode Go |
| Kimi | kimi-k2.7-code, kimi-k2.6 | Opencode Go |
| Gemini | gemini-2.5-flash-lite, gemini-2.5-pro | Google |
| Nemotron | nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free | OpenRouter |

### Allowed Combinations

| Implementer | Allowed Verifier | Allowed Critique | Allowed Consolidation |
|-------------|-----------------|------------------|------------------------|
| Kimi | DeepSeek, Gemini, GLM | DeepSeek, Gemini, GLM | DeepSeek, Gemini, GLM |
| DeepSeek | Kimi, Gemini, GLM | Kimi, Gemini, GLM | Kimi, Gemini, GLM |
| GLM | Kimi, DeepSeek, Gemini | Kimi, DeepSeek, Gemini | Kimi, DeepSeek, Gemini |
| Gemini | Kimi, DeepSeek, GLM | Kimi, DeepSeek, GLM | Kimi, DeepSeek, GLM |

### What "Same Family" Means

If the Implementer was `kimi-k2.7-code`, the Critique CANNOT be `kimi-k2.6`. Both are Kimi models, even if they are different versions. The Critique MUST be a different family (DeepSeek, GLM, or Gemini).

## Retry Chain

If a model fails (rate limit, auth error, 500, verification failure):
1. Log the failure in the work log.
2. Re-run `route_config.py set --stage X` and retry.
3. If that fails, retry with the fallback (`run_stage.py` terminal mode).
4. If all fail, mark the stage as blocked and `clarify` with the user.

## What Changed From v0.6.0

The old verification hierarchy put the model tag first and terminal spawn last. But the model tag was self-reported and unverifiable — the subagent could type anything regardless of which model actually ran. Now config cycling is the primary verification method because it controls routing at the infrastructure level. The tag is a confirmation check, not the sole indicator.

## Work Log Entry

Every model verification result must be logged:

```markdown
## Model Verification — Session [N]
| Stage | Intended | Actual | Verified | Method | Result |
|-------|----------|--------|----------|--------|--------|
| Implement | kimi-k2.7-code | kimi-k2.7-code | Yes | config cycling | Pass |
| Verify | deepseek-v0.4.0-pro | deepseek-v0.4.0-pro | Yes | config cycling | Pass |
| Critique | glm-5.1 | glm-5.1 | Yes | config cycling | Pass |
```

## Verification Checklist

Before declaring any stage complete:

- [ ] Did you run `route_config.py set --stage X` before calling `delegate_task`?
- [ ] Did you call `delegate_task` (not terminal) for the actual delegation?
- [ ] Did you run `route_config.py verify --output FILE --expected-model M` after?
- [ ] If Verify, Critique, or Consolidate: is the model a DIFFERENT family than Implement?
- [ ] If config cycling failed, did you fall back to `run_stage.py` terminal mode?
- [ ] Did you log the verification result in the work log?

**Do NOT proceed to the next stage until ALL boxes are checked.**
