# Fable Orchestrator v6 — Installation Guide

This guide is written for non-technical users. You do not need to write code or
run a server. Fable v6 is a **Hermes skill** — a set of instructions and small
helper scripts that Hermes can follow.

## What you need before you start

1. **Hermes Agent** installed on your computer.
2. At least one AI provider API key configured in Hermes (usually in
   `~/.hermes/.env`).

If you do not have Hermes installed, follow the official Hermes setup first.

## Step 1: Install the skill

The easiest way is to run the setup script:

```bash
./setup.sh
```

This installs the skill and runs the pre-flight check in one go.

Or install manually:

```bash
hermes skills install ./SKILL.md
```

Or install directly from GitHub:

```bash
hermes skills install https://raw.githubusercontent.com/iamnickthegeek/fableous/main/SKILL.md
```

Hermes will load the skill. There is no daemon to start and no database to set
up.

## Step 2: Check your providers

Fable routes different stages (Research, Plan, Implement, Verify, Critique,
Consolidate) to different AI models. Before you use it, make sure the providers
are configured.

Run the pre-flight check:

```bash
python3 scripts/verify_models.py
```

You should see a table like this:

```
Stage        Level      Model                          Provider       Key      Status
-----------------------------------------------------------------------------------------------
research     primary    deepseek-v4-flash              opencode-go    OK       OK
plan         primary    glm-5.1                        opencode-go    OK       OK
...
All checks passed. You can run Fable Orchestrator v6.
```

If any row says `FAIL`, that provider's API key is missing. Add it to
`~/.hermes/.env` (for example `OPENCODE_GO_API_KEY=your-key-here`).

## Step 3: Create your routing config (optional)

If you only have one provider, you can skip this. Fable will use its built-in
defaults.

If you have multiple providers, generate a custom routing file:

```bash
python3 scripts/auto_detect_providers.py --save
```

This creates `fable-config.yaml` in the current folder. It tells Fable which
model to use for each stage.

## Step 4: Try a single stage (optional)

You can run one Fable stage by itself to test the routing:

```bash
python3 scripts/run_stage.py \
  --stage research \
  --prompt "Find three AI ghostwriting tools and their prices" \
  --output stage1_research.md
```

This runs the Research stage on the correct model, then saves the result to
`stage1_research.md`. If the primary model fails, it automatically tries the
secondary and tertiary models.

## Step 5: Use Fable inside a chat

The normal way to use Fable is to ask Hermes to run it for a task:

> "Run this through Fable: write a competitive analysis of AI ghostwriting
tools, with verified pricing and cited sources."

Hermes will load the skill and follow the 6-stage procedure.

## If something goes wrong

- **"hermes command not found"**: Hermes is not installed or not in your shell
  path. Fix that first.
- **"Some checks failed"** from `verify_models.py`: An API key is missing. Check
  `~/.hermes/.env`.
- **A stage times out**: Increase the timeout:
  ```bash
  python3 scripts/run_stage.py --stage research --prompt "..." --timeout 600
  ```
- **Wrong model was used**: Check the first line of the output file. It should
  contain a tag like `[MODEL: deepseek-v4-flash, PROVIDER: opencode-go]`.

## Files you can ignore

- `archive/` contains old v1-v5 code and planning documents. You do not need to
  touch it.
- `__pycache__/` and `.pytest_cache/` are auto-generated Python caches.

## Next steps

Read `README.md` for a quick overview, or `SKILL.md` for the full procedure.
