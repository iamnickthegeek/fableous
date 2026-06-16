# Why `delegate_task(model=...)` Does Not Enforce Model Switching

## The Problem

`delegate_task` accepts a `model` parameter. In testing, it was assumed this would force the subagent to use that model. It does not.

**What happened:** A 5-stage fable loop was assigned to different models:
- Research: `deepseek-v4-flash`
- Plan: `glm-5.1`
- Implement: `kimi-k2.7-code`
- Verify: `deepseek-v4-pro`
- Critique: `glm-5.1`

**What actually happened:** All 5 stages ran on `kimi-k2.6` (the session's default model). The `delegate_task` subagent either:
1. Ignored the `model` parameter entirely, or
2. The subagent was spawned with a default model that overrode the parameter, or
3. The Hermes backend defaulted to the session model when the subagent's config didn't have the specified model available

The result: all subagents produced output consistent with Kimi's reasoning style (verbose, structured, long-form). The critique stage — which should have been on a different model family to catch Kimi's blind spots — was also running on Kimi, so it couldn't see the weaknesses.

## The Root Cause

`delegate_task` is a *suggestion* mechanism. The subagent is told "use this model if you can" but the underlying Hermes process may:
- Default to the session model if the specified model is not in the available models list
- Use the provider's default if the model ID is not recognized
- Fall back to the session model if the API key for that provider is missing

None of these failures are reported as errors. The subagent just runs on the wrong model silently.

## The Fix

Spawn `hermes chat -q` as a subprocess with explicit `-m` and `--provider` flags:

```bash
hermes chat -q "Your prompt here" -m deepseek-v4-flash --provider opencode-go -Q
```

This is hardcoded in the command string. The subagent cannot override it because the process itself is launched with the correct model. The `-m` flag is a process-level flag, not a suggestion.

## Verification

To verify which model a subagent actually used, check the process output or the subagent's response header. The programmatic tool logs this explicitly:

```
[2026-06-13T23:15:00] Stage 'research' -> opencode-go/deepseek-v4-flash (tier=primary)
[2026-06-13T23:18:52] Stage 'implement' -> opencode-go/kimi-k2.7-code (tier=primary)
```

## Recommendation

- Use `delegate_task` with `model=...` for simple tasks where model switching is not critical
- Use the programmatic `fable_orchestrator.py` tool when model switching is the core value (fable-mode execution, cross-family verification)
- Always verify model usage in the logs; never assume the model parameter was honored
