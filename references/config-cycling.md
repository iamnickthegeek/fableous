# Config Cycling — v7

## How it works

1. `delegate_task` calls `_load_config()` on every invocation
2. `_load_config()` reads `~/.hermes/config.yaml` from disk (no caching)
3. `_resolve_delegation_credentials(cfg, parent_agent)` extracts `cfg.get("model")` and `cfg.get("provider")`
4. When `delegation.provider` is set, the function resolves the full credential bundle via `resolve_runtime_provider` — API key, base URL, and API mode are all derived from the provider
5. `_build_child_agent(model=creds["model"], override_provider=creds["provider"], override_base_url=creds["base_url"], override_api_key=creds["api_key"], override_api_mode=creds["api_mode"])` creates the subagent with the specified credentials

## The 5 Commands

Every config cycle is exactly these 5 commands, with the model and provider changing per stage:

```bash
hermes config set delegation.model "deepseek-v4-flash"
hermes config set delegation.provider "opencode-go"
hermes config set delegation.api_key ""
hermes config set delegation.base_url ""
hermes config set delegation.api_mode ""
```

The last 3 (clearing `api_key`, `base_url`, `api_mode`) are essential. Without them, `_resolve_delegation_credentials` uses stale endpoint values from the previous stage, causing the child agent to hit the wrong API endpoint. Setting them to empty forces the runtime provider resolver to run fresh for each stage.

## Script

Use `scripts/route_config.py` to automate config cycling:

```bash
# Set config for a stage (reads routing table, falls back through tiers)
python3 scripts/route_config.py set --stage research

# Set config with explicit model/provider
python3 scripts/route_config.py set --model deepseek-v4-flash --provider opencode-go

# Restore original config
python3 scripts/route_config.py restore

# Check current state
python3 scripts/route_config.py status

# Verify model tag in stage output
python3 scripts/route_config.py verify --output stage1_research.md --expected-model deepseek-v4-flash
```

## Complete Agent Procedure for One Stage

```
1. terminal("python3 ~/.hermes/skills/fableous/scripts/route_config.py set --stage research")
2. delegate_task(goal="Stage 1: Research — ...", context="...", toolsets=["web", "file"])
3. terminal("python3 ~/.hermes/skills/fableous/scripts/route_config.py verify --output stage1_research.md --expected-model deepseek-v4-flash")
4. (proceed to next stage — step 1 with --stage plan)
```

## Race conditions

Config cycling is not safe for concurrent `delegate_task` calls targeting different models. If two stages run simultaneously with different models, the second `set` overwrites the first, and both subagents may use the second model.

**Mitigation**: The Fable Orchestrator runs stages sequentially. The only parallel-safe stages (Research and Plan) use different models in the routing table, so they MUST be run sequentially when using config cycling. This is an acceptable trade-off because guaranteed routing is more valuable than parallel execution.

## Async Safety

Starting in v7.1, Research and Plan can be dispatched in parallel using `delegate_task(background=true)`. Config cycling between dispatches is safe because:

The child agent is constructed synchronously inside `delegate_task()` — BEFORE the background worker is dispatched to the daemon thread pool. The model, provider, base_url, api_key, and api_mode are all passed to `_build_child_agent()` at construction time and snapshotted in the child agent object. The background worker does NOT re-read config.

### Timing guarantee

```
Time →
  1. route_config.py set --stage research  → config = research-model
  2. delegate_task(goal="...", background=true)
     → child BUILT with research-model ← SNAPSHOTTED
     → dispatched to daemon thread
  3. route_config.py set --stage plan       → config = plan-model  ← SAFE
  4. delegate_task(goal="...", background=true)
     → child BUILT with plan-model ← SNAPSHOTTED
     → dispatched to daemon thread
  5. route_config.py restore               → config = original  ← SAFE
```

Both children run with their snapshotted configurations. The config cycling between dispatches does not affect already-dispatched children.

### How it affects config cycling procedure

The only difference from the sync procedure is:
1. Set config for Stage 1 → dispatch → set config for Stage 2 → dispatch → restore
2. Wait for completion events from both stages
3. Verify each output file when its completion event arrives
4. Then proceed to stage 3 (sync)

See `SKILL.md` for the full async stage execution procedure.

## Provider not configured

If `route_config.py set --stage X` finds that the primary provider's API key is not set, it falls back to the secondary provider. If secondary also fails, it falls back to tertiary. If none are configured, it reports failure and the orchestrator falls back to `run_stage.py` terminal mode.

## Custom providers

If the user's `fable-config.yaml` specifies a custom provider (not opencode-go, google, or openrouter), `route_config.py` sets `delegation.provider` to the custom provider name. `resolve_runtime_provider` attempts to resolve it. If it can't, `delegate_task` returns an error, and the orchestrator falls back to terminal mode.

## CLI_CONFIG priority

In CLI mode, `CLI_CONFIG` takes priority over `config.yaml`. If the user started Hermes with `hermes chat --delegation-model X --delegation-provider Y`, those CLI flags override the file config. Config cycling via `hermes config set` updates the file but not `CLI_CONFIG`.

**Mitigation**: Gateway sessions (Telegram, Discord, Slack) don't set `CLI_CONFIG`, so file config cycling works. For CLI sessions, document that `--delegation-*` flags override config cycling. In practice, Fable Orchestrator is typically invoked from gateway sessions where this is not an issue.

## Restore safety

`route_config.py restore` is idempotent — calling it multiple times is safe. It's also called automatically if a stage fails (the orchestrator procedure includes error recovery that restores config before reporting the failure).

## Backup file

File: `~/.hermes/skills/fableous/.routing-backup.json`

```json
{
  "original_model": "deepseek-v4-pro",
  "original_provider": "opencode-go",
  "current_stage": null,
  "timestamp": "2026-07-11T14:30:00Z"
}
```

The backup file is written on `set` and consumed on `restore`. If it doesn't exist, `restore` reads from config.yaml and assumes the current values are the originals (idempotent — safe to call twice).
