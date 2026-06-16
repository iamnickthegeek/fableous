# Model Routing Decision Tree — v7

## The problem

`delegate_task` has **no per-call `model` parameter**. Source-code audit confirmed: the tool schema, dispatch function, and Python function signature all lack a `model` field. Model routing is resolved exclusively from `delegation.model` and `delegation.provider` in `config.yaml` — global settings that apply to ALL subagents. Any `model=` value passed in a `delegate_task` tool call is silently ignored.

This means `delegate_task` CANNOT be used for model routing without config cycling.

## Decision tree

```
Is native per-call routing available? (run detect_routing.py)
 Yes --> Use delegate_task(model={"model": "...", "provider": "..."}) directly.
          No config cycling needed. Verify with model tag.
 No --> Use config cycling as primary method.
         - Is this Research or Plan?
           - Yes -> Try async: delegate_task(goal="...", background=true)
             - Returns {"status": "dispatched"} -> Wait for completion event.
             - Returns {"status": "rejected"} -> Fall back to sync.
           - No -> Use sync: delegate_task(goal="...", background=false)
         - route_config.py set --stage X
         - delegate_task(goal="...")
         - route_config.py verify --output FILE --expected-model M
         - On failure: route_config.py restore, then run_stage.py --stage X
```

## When config cycling fails

- `route_config.py set` fails → Restore config, fall back to `run_stage.py` terminal mode
- `route_config.py verify` shows wrong model → Re-run `set` and retry the stage
- `delegate_task` fails after config set → Check if the provider is configured: `hermes auth` or check `.env`
- Config cycling sets the right model but subagent output doesn't match → Check the work log. The model tag is a confirmation, not a guarantee. If the config was set correctly and the subagent returned successfully, trust the config.

## Config cycling procedure

```bash
# 1. Set config for the stage
python3 scripts/route_config.py set --stage research

# 2. Call delegate_task (no model parameter)
delegate_task(goal="...")

# 3. Verify the output
python3 scripts/route_config.py verify --output stage1_research.md --expected-model deepseek-v4-flash

# 4. Restore when done
python3 scripts/route_config.py restore
```

## Terminal fallback (standby)

When config cycling fails, use `run_stage.py`:

```bash
python3 scripts/run_stage.py --stage research --prompt-file task.md --output stage1_research.md
```

This uses `hermes chat -q -m MODEL --provider PROVIDER` via subprocess. It does not touch the delegation config and will not affect other stages.

## Command template for direct terminal fallback

```bash
hermes chat -q "$(cat /path/to/stage_prompt.txt)" \
  -m MODEL_NAME --provider PROVIDER_NAME \
  -Q -t file,web --accept-hooks
```

## Flags explained

- `-q "$(cat prompt.txt)"`: passes the prompt from a file, avoiding shell-escaping issues for long prompts.
- `-m MODEL_NAME`: the exact model slug.
- `--provider PROVIDER_NAME`: the provider that serves the model; mandatory for reliable routing.
- `-Q`: quiet/programmatic mode — suppresses banner, spinner, and tool previews.
- `-t file,web`: comma-separated toolsets; adjust to the stage's needs.
- `--accept-hooks`: auto-approves shell hooks declared in `config.yaml` so the run does not hang waiting for a TTY.

## Verification

```bash
python3 scripts/route_config.py verify --output stage1_research.md --expected-model deepseek-v4-flash
```

Because config cycling controlled the routing, the model tag in the output should match. If it doesn't, re-run `route_config.py set` and retry. If the tag is missing entirely, it's not a routing failure — trust the config.
