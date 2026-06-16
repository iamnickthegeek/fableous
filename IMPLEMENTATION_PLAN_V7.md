# Fable Orchestrator — Model Routing Fix: Implementation Plan

## The Problem in One Paragraph

`delegate_task` has no per-call `model` parameter. Model routing is resolved exclusively from `delegation.model` and `delegation.provider` in `config.yaml` — a single global pair that applies to every subagent. No matter what model the Fable Orchestrator asks for, every `delegate_task` call inherits the parent session's model. Cross-family verification is impossible; `[MODEL: ...]` tags are unverifiable; the routing table is decorative.

## The Fix in One Paragraph

Before each `delegate_task` call, update `delegation.model` and `delegation.provider` in the Hermes config to match the desired model/provider for that stage. After the stage completes, update the config for the next stage. On completion or error, restore the original values. This is **config cycling** — a 4-line `hermes config set` sequence that routes each subagent to the correct model without any core patches. Everything lives inside the skill directory. When Hermes eventually adds native per-call model routing to `delegate_task`, the skill detects it and uses it instead.

---

## Why Config Cycling Works

The `delegate_task` function calls `_load_config()` on every invocation. `_load_config()` reads `~/.hermes/config.yaml` from disk (no caching). When `delegation.model` and `delegation.provider` are set, `_resolve_delegation_credentials` resolves the full credential bundle (API key, base URL, API mode) via the runtime provider system and passes it to `_build_child_agent`.

This means: if you write the desired model/provider to config.yaml before calling `delegate_task`, the child agent will use that model/provider. The child's `effective_model` gets the config value, and `effective_provider` gets the resolved provider with all credentials.

**Critical**: both `delegation.model` AND `delegation.provider` must be set together. If only `model` is set, the provider stays `None` and the child inherits the parent's provider — same model name on the wrong endpoint.

---

## Deliverables

Everything is inside `~/.hermes/skills/fableous/`. No core patches.

| # | File | What |
|---|------|------|
| S1 | `scripts/route_config.py` | Config cycling engine: set/restore/verify delegation config |
| S2 | `scripts/run_stage.py` | Update existing script: add `--via-config` mode alongside existing terminal mode |
| S3 | `scripts/detect_routing.py` | Feature detection: checks if native per-call model routing is available |
| S4 | `SKILL.md` | Rewrite model routing section, update stage execution procedure, rewrite pitfalls |
| S5 | `references/model-verification.md` | Rewrite verification hierarchy |
| S6 | `references/delegate-task-model-fallback.md` | Rewrite: config cycling is primary, terminal is fallback |
| S7 | `references/model-routing-table.md` | Add `hermes config set` commands for each entry |
| S8 | `references/config-cycling.md` | New: full config cycling spec and edge cases |
| S9 | `templates/stage-prompts/*.md` | Update: remove `[MODEL:]` tag as sole verification, add config cycling steps |
| S10 | `scripts/fable_routing.py` | Add `routing_entry_to_config_commands()` helper |

---

## S1: `scripts/route_config.py` — Config Cycling Engine

```python
#!/usr/bin/env python3
"""Config cycling engine for Fable Orchestrator model routing.

Updates delegation.model and delegation.provider in the Hermes config
before each delegate_task call, then restores originals on completion.

Usage:
    python3 scripts/route_config.py set --stage research [--config path]
    python3 scripts/route_config.py set --model deepseek-v4-flash --provider opencode-go
    python3 scripts/route_config.py restore [--config path]
    python3 scripts/route_config.py status
    python3 scripts/route_config.py verify --output stage1_research.md --expected-model deepseek-v4-flash
```

### What it does

**`set --stage STAGE`**: Reads the routing table for the given stage (primary tier), then runs:
```bash
hermes config set delegation.model "deepseek-v4-flash"
hermes config set delegation.provider "opencode-go"
```

**`set --model M --provider P`**: Same, but with explicit model/provider instead of routing table lookup.

**`restore`**: Reads the saved originals from `~/.hermes/skills/fableous/.routing-backup.json` and restores them:
```bash
hermes config set delegation.model "ORIGINAL_MODEL"
hermes config set delegation.provider "ORIGINAL_PROVIDER"
```

**`status`**: Prints current `delegation.model` and `delegation.provider` from config.yaml for manual inspection.

**`verify --output FILE --expected-model M`**: Reads the first line of the output file and checks the `[MODEL: M, PROVIDER: P]` tag. Returns exit code 0 on match, 1 on mismatch, 2 on missing tag.

### Backup format

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

### Implementation notes for the implementer

1. Use `subprocess.run(["hermes", "config", "set", key, value])` to update config. Do NOT edit `config.yaml` directly — `hermes config set` handles formatting, comments, and validation.

2. `set --stage STAGE` reads the routing table from `scripts/fable_routing.py` (import `DEFAULT_ROUTING`). It falls back through primary → secondary → tertiary, skipping providers that aren't configured. Use `scripts/verify_models.py` logic to check if a provider has an API key set.

3. `restore` MUST succeed even if the backup file is missing (fall back to current values in config, or set both to empty strings).

4. All commands return JSON on stdout for easy parsing by the orchestrator:
   ```json
   {"action": "set", "stage": "research", "model": "deepseek-v4-flash", "provider": "opencode-go"}
   ```

5. On `set`, the script MUST also set `delegation.api_key`, `delegation.base_url`, and `delegation.api_mode` to empty strings. When these are empty, `_resolve_delegation_credentials` uses the `delegation.provider` path to resolve full credentials via `resolve_runtime_provider`. If they're left with stale values from a previous stage, the child might use the wrong API endpoint. So after every `set`, explicitly clear them:
   ```bash
   hermes config set delegation.model "deepseek-v4-flash"
   hermes config set delegation.provider "opencode-go"
   hermes config set delegation.api_key ""
   hermes config set delegation.base_url ""
   hermes config set delegation.api_mode ""
   ```
   This forces the runtime provider resolver to run fresh for each stage.

---

## S2: `scripts/run_stage.py` — Update Existing Script

Add a `--via-config` mode that does config cycling + `delegate_task` instead of terminal spawning:

### New flag: `--via-config`

```
python3 scripts/run_stage.py --stage research --prompt "Analyze..." --via-config
```

When `--via-config` is set:
1. Run `route_config.py set --stage research` to update the config
2. Print an instruction block telling the orchestrator to call `delegate_task(goal="...", ...)`
3. After the orchestrator calls `delegate_task`, the orchestrator should run `route_config.py verify` to check the output
4. On completion, the orchestrator runs `route_config.py restore`

This mode is intended for use from the Fable Orchestrator procedure (the agent calls `route_config.py` directly, not through `run_stage.py`). The `--via-config` flag exists so other scripts can compose with it.

The **default mode** (no `--via-config`) continues to use `hermes chat -q -m MODEL --provider PROVIDER` via subprocess — this is the atomic terminal fallback that doesn't touch config at all.

### Existing behavior: no changes

The current `run_stage.py` behavior (terminal spawning with `-m` and `--provider` flags) remains the default and is unchanged. It's the standby for when config cycling is unsuitable.

---

## S3: `scripts/detect_routing.py` — Feature Detection

```python
#!/usr/bin/env python3
"""Detect whether native per-call model routing is available in delegate_task.

Exits 0 if native routing is available (delegate_task accepts a model param).
Exits 1 if native routing is NOT available (config cycling is required).

Usage:
    python3 scripts/detect_routing.py
"""
```

### How it detects

1. Read the `delegate_task` tool schema from the running Hermes instance via `hermes tools delegate_task --schema` (or by importing `tools.delegate_tool.DELEGATE_TASK_SCHEMA` if running inside the agent).
2. Check if `model` exists in `parameters.properties`.
3. If yes → native routing is available. Print `{"native_routing": true}` and exit 0.
4. If no → native routing not available. Print `{"native_routing": false, "method": "config_cycling"}` and exit 1.

### Why

When Hermes eventually adds per-call model routing to `delegate_task`, the Fable Orchestrator should use it natively instead of config cycling. This detection script lets the orchestrator choose the right method automatically without manual configuration.

### Fallback

If detection fails (can't import, can't read schema), assume native routing is NOT available and fall back to config cycling. This is the safe default.

---

## S4: `SKILL.md` — Rewrite Model Routing Section

### Current section: "Model Routing" (summary)

> You MUST route each stage to the assigned model. Use `delegate_task` with explicit model assignment.
> Pitfall 2: `delegate_task` model parameter is suggestive.
> Pitfall 8: `delegate_task` ignores model routing.

### New section: "Model Routing"

> You MUST route each stage to the assigned model. Since `delegate_task` does not support per-call model routing, use **config cycling** to set the model and provider before each stage:
>
> ### Config Cycling Procedure (Mandatory)
>
> Before each `delegate_task` call, you MUST:
>
> 1. Run `route_config.py set --stage STAGE_NAME` to update `delegation.model` and `delegation.provider`
> 2. Call `delegate_task(goal="...", context="...", toolsets=[...])` — do NOT pass a model parameter
> 3. After the subagent returns, run `route_config.py verify --output STAGE_OUTPUT --expected-model MODEL` to confirm the model tag
> 4. Proceed to the next stage (step 1 repeats with the next stage's model)
>
> On completion or error, you MUST run `route_config.py restore` to restore the original delegation config.
>
> ### Why Config Cycling
>
> `delegate_task` resolves the child's model and provider from `delegation.model` and `delegation.provider` in `~/.hermes/config.yaml`. These values are read from disk on every call (no caching). By setting them to the desired values before each call, the child agent uses the correct model/provider — guaranteed, not suggested.
>
> Both `delegation.model` AND `delegation.provider` must be set together. Setting only the model without the provider causes the child to use the correct model name on the wrong provider's endpoint, which fails.
>
> ### When Config Cycling Doesn't Apply
>
> - If `detect_routing.py` reports native per-call routing is available, use `delegate_task(model={"model": "...", "provider": "..."})` directly instead.
> - If config cycling fails (config file permissions, concurrent access), fall back to `run_stage.py --stage STAGE` which uses `hermes chat -q` terminal spawning.
>
> ### What Changed From v6.1
>
> - **v6.1**: `delegate_task(model="deepseek-v4-flash")` was documented as the primary method. It didn't work — `delegate_task` has no `model` parameter and the value was silently ignored. Every subagent ran on the parent session's model.
> - **v6.2**: Config cycling is the primary method. Before each `delegate_task` call, update the Hermes config. The `[MODEL: ...]` tag is now a verification check, not the sole verification method — the config guarantees routing.

### Stage Execution Procedure — Updated

Replace Step 2 (Delegate the stage) with:

```
### Step 2: Route and delegate the stage

Run config cycling to set the model for this stage:
  terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py set --stage N_NAME")

If route_config.py reports that the primary provider is not configured, it will
automatically fall back to secondary/tertiary. Check the output for the actual
model/provider set.

Then delegate:
  delegate_task(goal="...", context="...", toolsets=[...])

After the subagent returns, verify:
  terminal(command="python3 ~/.hermes/skills/fableous/scripts/route_config.py verify --output stageN_NAME.md --expected-model MODEL_NAME")
```

---

## S5: `references/model-verification.md` — Rewrite

### New verification hierarchy

1. **Config cycling (authoritative)** — When `route_config.py set --stage X` completes, the model/provider is guaranteed for the next `delegate_task` call. The config is read from disk by `_resolve_delegation_credentials` on every call.

2. **Model tag (audit trail)** — Include `[MODEL: name, PROVIDER: provider]` in every stage prompt. After the stage, read the first line of the output. If it matches, confirm in the work log. If it doesn't match, it's a config cycling failure — re-run `route_config.py set` and retry.

3. **Terminal spawn (fallback)** — If config cycling fails twice, use `run_stage.py --stage X --prompt "..."` which calls `hermes chat -q -m MODEL --provider PROVIDER` directly. No config modification needed.

### What changed

The old verification hierarchy put the model tag first and terminal spawn last. But the model tag was self-reported and unverifiable — the subagent could type anything regardless of which model actually ran. Now config cycling is the primary verification method because it controls routing at the infrastructure level. The tag is a confirmation check, not the sole indicator.

---

## S6: `references/delegate-task-model-fallback.md` — Rewrite

### New decision tree

```
Is native per-call routing available? (run detect_routing.py)
├─ Yes ──> Use delegate_task(model={...}) directly. No config cycling needed.
│            Verify with model tag.
└─ No ──> Use config cycling as primary method.
           ├─ route_config.py set --stage X
           ├─ delegate_task(goal="...")
           ├─ route_config.py verify --output FILE --expected-model M
           └─ On failure: route_config.py restore, then run_stage.py --stage X
```

### When config cycling fails

- `route_config.py set` fails → Restore config, fall back to `run_stage.py` terminal mode
- `route_config.py verify` shows wrong model → Re-run `set` and retry the stage
- `delegate_task` fails after config set → Check if the provider is configured: `hermes auth` or check `.env`
- Config cycling sets the right model but subagent output doesn't match → Check the work log. The model tag is a confirmation, not a guarantee. If the config was set correctly and the subagent returned successfully, trust the config.

---

## S7: `references/model-routing-table.md` — Add Config Commands

For each routing table entry, add the equivalent `hermes config set` commands:

| Stage | Primary | Config Commands |
|-------|---------|-----------------|
| Research | deepseek-v4-flash (Opencode Go) | `hermes config set delegation.model deepseek-v4-flash && hermes config set delegation.provider opencode-go && hermes config set delegation.api_key "" && hermes config set delegation.base_url "" && hermes config set delegation.api_mode ""` |
| Plan | glm-5.1 (Opencode Go) | `hermes config set delegation.model glm-5.1 && hermes config set delegation.provider opencode-go && hermes config set delegation.api_key "" && hermes config set delegation.base_url "" && hermes config set delegation.api_mode ""` |
| Implement | kimi-k2.7-code (Opencode Go) | `hermes config set delegation.model kimi-k2.7-code && hermes config set delegation.provider opencode-go && hermes config set delegation.api_key "" && hermes config set delegation.base_url "" && hermes config set delegation.api_mode ""` |
| Verify | deepseek-v4-pro (Opencode Go) | `hermes config set delegation.model deepseek-v4-pro && hermes config set delegation.provider opencode-go && hermes config set delegation.api_key "" && hermes config set delegation.base_url "" && hermes config set delegation.api_mode ""` |
| Critique | glm-5.1 (Opencode Go) | `hermes config set delegation.model glm-5.1 && hermes config set delegation.provider opencode-go && hermes config set delegation.api_key "" && hermes config set delegation.base_url "" && hermes config set delegation.api_mode ""` |
| Consolidate | deepseek-v4-pro (Opencode Go) | `hermes config set delegation.model deepseek-v4-pro && hermes config set delegation.provider opencode-go && hermes config set delegation.api_key "" && hermes config set delegation.base_url "" && hermes config set delegation.api_mode ""` |

---

## S8: `references/config-cycling.md` — New Reference

### How it works

1. `delegate_task` calls `_load_config()` on every invocation
2. `_load_config()` reads `~/.hermes/config.yaml` from disk (no caching)
3. `_resolve_delegation_credentials(cfg, parent_agent)` extracts `cfg.get("model")` and `cfg.get("provider")`
4. When `delegation.provider` is set, the function resolves the full credential bundle via `resolve_runtime_provider` — API key, base URL, and API mode are all derived from the provider
5. `_build_child_agent(model=creds["model"], override_provider=creds["provider"], override_base_url=creds["base_url"], override_api_key=creds["api_key"], override_api_mode=creds["api_mode"])` creates the subagent with the specified credentials

### Race conditions

Config cycling is not safe for concurrent `delegate_task` calls targeting different models. If two stages run simultaneously with different models, the second `set` will overwrite the first, and both subagents may use the second model.

**Mitigation**: The Fable Orchestrator runs stages sequentially. The only parallel-safe stages (Research and Plan) use different models in the routing table, so they MUST be run sequentially when using config cycling. This is an acceptable trade-off because guaranteed routing is more valuable than parallel execution.

### Provider not configured

If `route_config.py set --stage X` finds that the primary provider's API key is not set, it falls back to the secondary provider. If secondary also fails, it falls back to tertiary. If none are configured, it reports failure and the orchestrator falls back to `run_stage.py` terminal mode.

### Custom providers

If the user's `fable-config.yaml` specifies a custom provider (not opencode-go, google, or openrouter), `route_config.py` will set `delegation.provider` to the custom provider name. `resolve_runtime_provider` will attempt to resolve it. If it can't, `delegate_task` will return an error, and the orchestrator falls back to terminal mode.

### CLI_CONFIG priority

In CLI mode, `CLI_CONFIG` takes priority over `config.yaml`. If the user started Hermes with `hermes chat --delegation-model X --delegation-provider Y`, those CLI flags override the file config. Config cycling via `hermes config set` updates the file but not `CLI_CONFIG`.

**Mitigation**: Gateway sessions (Telegram, Discord, Slack) don't set `CLI_CONFIG`, so file config cycling works. For CLI sessions, document that `--delegation-*` flags override config cycling. In practice, Fable Orchestrator is typically invoked from gateway sessions where this is not an issue.

### Restore safety

`route_config.py restore` is idempotent — calling it multiple times is safe. It's also called automatically if a stage fails (the orchestrator procedure includes error recovery that restores config before reporting the failure).

---

## S9: `templates/stage-prompts/*.md` — Updates

For each stage prompt template, replace:

```
At the top of your output, write exactly: [MODEL: MODEL_NAME, PROVIDER: PROVIDER_NAME]
```

With:

```
At the top of your output, write exactly: [MODEL: MODEL_NAME, PROVIDER: PROVIDER_NAME]
This tag is an audit trail. The actual model routing was set via config cycling
before this call. If the tag doesn't match the assigned model, report it but
don't retry — trust the config.
```

---

## S10: `scripts/fable_routing.py` — Add Helper

Add a function that returns the appropriate `hermes config set` commands for a routing entry:

```python
def routing_entry_to_config_commands(stage: str, level: str = "primary", config_path: str = None) -> list[str]:
    """Return hermes config set commands for a routing entry.

    Example:
        >>> routing_entry_to_config_commands("research")
        [
            "hermes config set delegation.model deepseek-v4-flash",
            "hermes config set delegation.provider opencode-go",
            "hermes config set delegation.api_key ''",
            "hermes config set delegation.base_url ''",
            "hermes config set delegation.api_mode ''",
        ]
    """
    routing = load_routing(config_path)
    entry = routing.get(stage, {}).get(level)
    if not entry:
        raise ValueError(f"No {level} routing for stage '{stage}'")
    return [
        f"hermes config set delegation.model {entry['model']}",
        f"hermes config set delegation.provider {entry['provider']}",
        "hermes config set delegation.api_key ''",
        "hermes config set delegation.base_url ''",
        "hermes config set delegation.api_mode ''",
    ]
```

---

## Implementation Order

### Phase 1: Scripts (can be tested independently)

1. **S10** — Add `routing_entry_to_config_commands()` to `fable_routing.py`. Quick, testable with a Python REPL.
2. **S1** — Write `route_config.py`. Test with `python3 scripts/route_config.py set --stage research` and verify with `hermes config show delegation`.
3. **S2** — Update `run_stage.py` with `--via-config` flag. This is optional — config cycling is done by the agent calling `route_config.py` directly.
4. **S3** — Write `detect_routing.py`. Quick schema check.

### Phase 2: Skill Documentation (depends on Phase 1 working)

5. **S8** — Write `references/config-cycling.md`. This is the spec that the other docs reference.
6. **S4** — Rewrite SKILL.md model routing section. This is the big one.
7. **S5** — Rewrite `references/model-verification.md`.
8. **S6** — Rewrite `references/delegate-task-model-fallback.md`.
9. **S7** — Update `references/model-routing-table.md`.
10. **S9** — Update stage prompt templates.
11. **S4 continued** — Remove Pitfalls 2 and 8 (they're no longer pitfalls — config cycling works). Update Pitfall 3 (--provider flag) to note that it applies to terminal mode only.

### Phase 3: Validation

12. Run the full Fable pipeline on a real task with config cycling.
13. Verify each stage uses the correct model by checking the model tag AND `hermes config show delegation`.
14. Confirm cross-family verification works (Implement on Kimi, Critique on GLM).
15. Test `route_config.py restore` restores original values.
16. Test fallback to `run_stage.py` when a provider is unavailable.
17. Test `detect_routing.py` on both patched and unpatched Hermes instances.

---

## What a Cheaper LLM Needs to Know

### The one key insight

`delegate_task` reads `delegation.model` and `delegation.provider` from `~/.hermes/config.yaml` on every single call. There's no cache. So if you write the right values to config before calling `delegate_task`, the child agent uses those values. This is the entire mechanism.

### The five `hermes config set` commands

Every config cycle is exactly these 5 commands, with the model and provider changing per stage:

```bash
hermes config set delegation.model "deepseek-v4-flash"
hermes config set delegation.provider "opencode-go"
hermes config set delegation.api_key ""
hermes config set delegation.base_url ""
hermes config set delegation.api_mode ""
```

The last 3 (clearing `api_key`, `base_url`, `api_mode`) are essential. Without them, `_resolve_delegation_credentials` uses stale endpoint values from the previous stage, causing 404 errors on the new provider.

### The complete agent procedure for one stage

```
1. terminal("python3 ~/.hermes/skills/fableous/scripts/route_config.py set --stage research")
2. delegate_task(goal="Stage 1: Research — ...", context="...", toolsets=["web", "file"])
3. terminal("python3 ~/.hermes/skills/fableous/scripts/route_config.py verify --output stage1_research.md --expected-model deepseek-v4-flash")
4. (proceed to next stage — step 1 with --stage plan)
```

### File locations

- Routing table: `~/.hermes/skills/fableous/scripts/fable_routing.py` (the `DEFAULT_ROUTING` dict)
- Config cycling script: `~/.hermes/skills/fableous/scripts/route_config.py` (new)
- Feature detection: `~/.hermes/skills/fableous/scripts/detect_routing.py` (new)
- Terminal fallback: `~/.hermes/skills/fableous/scripts/run_stage.py` (existing)
- Work log: Project directory `WORK_LOG.md`
- Config backup: `~/.hermes/skills/fableous/.routing-backup.json`

### Known limitations

1. **Sequential only** — Config cycling forces stages to run sequentially because there's only one global `delegation.model`/`delegation.provider`. Research and Plan cannot run in parallel if they use different models.
2. **CLI_CONFIG priority** — If Hermes was started with `--delegation-model` or `--delegation-provider` CLI flags, those override the file config. Config cycling only modifies the file. In practice, gateway sessions don't set CLI flags.
3. **Concurrent sessions** — If two Hermes conversations are running simultaneously and both use config cycling, they'll overwrite each other's delegation config. This is unlikely for single-user installations.
4. **Model tag is audit, not verification** — The `[MODEL: ...]` tag in stage output is self-reported. Config cycling is the authority. If the tag doesn't match, check config first, then fall back to terminal.

---

## Future-Proofing: When Hermes Adds Native Model Routing

When Hermes adds per-call `model`/`provider` parameters to `delegate_task` (which the maintainers may do — the architecture supports it, it's just not in the schema yet):

1. `detect_routing.py` will detect the new parameter and report `{"native_routing": true}`.
2. The orchestrator procedure will switch from config cycling to `delegate_task(goal="...", model={"model": "glm-5.1", "provider": "opencode-go"})`.
3. `route_config.py` will still exist but won't be called during normal execution.
4. All config cycling steps in the procedure become no-ops.

The skill ships both methods. No code is lost when Hermes is updated.