# Helper Scripts

Fable v6 ships with a few small Python utilities in `scripts/`. They are
convenience tools, not an engine. The skill works perfectly without them.

## Scripts

| Script | Purpose |
|--------|---------|
| `verify_models.py` | Pre-flight check: confirms providers/API keys are configured. |
| `auto_detect_providers.py` | Reads `~/.hermes/.env` and suggests a `fable-config.yaml`. |
| `run_stage.py` | Hard-routes one stage via `hermes chat -q`, with fallback. |
| `fable_routing.py` | Shared constants used by the other scripts. |

## Important caveat: `.env` is not exported to subprocesses

Hermes loads `~/.hermes/.env` internally. Subprocesses spawned by `terminal()`
or by these scripts do **not** automatically inherit those variables. The
scripts therefore read `~/.hermes/.env` directly to check whether provider API
keys are set.

If you run `python3 scripts/verify_models.py` in a fresh shell and it reports
missing keys, but Hermes itself works, the keys are probably in `.env` and not
exported to the shell.

## When to use scripts vs native tools

- **Use scripts** when you want a one-line command or a quick pre-flight check.
- **Use native tools** (`delegate_task`, `terminal`, etc.) when following the
  full 6-stage procedure inside a Fable run.
- **Do not** let the scripts replace the skill's native-tool procedure. They
  are helpers, not the orchestrator.

## Adding new scripts

If you add a helper script:

1. Keep it self-contained and runnable with `python3 scripts/<name>.py`.
2. Put shared constants in `fable_routing.py`, not in a new engine module.
3. Do not reintroduce a daemon, SQLite state, or custom planner.
4. Update this file and the `Helper Scripts` table in `SKILL.md`.
