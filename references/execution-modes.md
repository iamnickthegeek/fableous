# Execution Modes: Prompt-Based vs Programmatic

The fable orchestrator can run in two modes. Only one enforces model switching.

## Method 1: Prompt-Based (instructive only)

When the skill is loaded via `/skill fable-orchestrator`, the model receives
instructions about the staged loop and the routing table. It then uses
`delegate_task` to spawn subagents.

**Problem:** `delegate_task` accepts a `model` parameter, but it is a *suggestion*.
The subagent may ignore it and default to the session model. In testing, all 5
stages ran on `kimi-k2.6` despite the routing table assigning different models.

Use this mode only for simple tasks where model switching is not critical.

## Method 2: Programmatic Tool (enforces model switching)

Use `scripts/fable_orchestrator.py`. It spawns `hermes chat -q` with explicit
`-m` and `--provider` flags:

```bash
hermes chat -q '...' -m MODEL --provider PROVIDER -Q -t web,terminal,file
```

The model assignment is hardcoded in the command string and cannot be overridden.
The script waits for each stage's output file, then proceeds to the next stage.

### Running the script

**Standalone (via terminal tool):**
```bash
python3 ~/.hermes/skills/fable-orchestrator/scripts/fable_orchestrator.py \
    --task "Your task" \
    --output-dir ./results \
    --domain research
```

**Inside Hermes (via execute_code):**
```python
import sys
sys.path.insert(0, "~/.hermes/skills/fable-orchestrator/scripts")
from fable_orchestrator import FableOrchestrator

orch = FableOrchestrator("./output")
result = orch.execute("Your task", domain="research")
```

**Critical:** `execute_code` may be blocked by default (security setting). The
script detects this and falls back to `subprocess` via the `terminal` tool.
This is slower but works. To enable native execution:

```bash
hermes config set approvals.cron_mode approve
```

Then restart the session (`/restart` in Telegram).

### The `--provider` flag is mandatory

Model switching fails without `--provider`. The command must be:
```
hermes chat -q '...' -m MODEL_NAME --provider PROVIDER_NAME ...
```

Without `--provider`, Hermes defaults to the session's current provider and the
model switch silently fails. The user will see only the session model in their
provider dashboard.

### Opencode Go is a multi-model hub

Opencode Go serves DeepSeek, GLM, Kimi, MiMo, Qwen, and MiniMax under one API
key. The models are:
- `deepseek-v4-flash` (research, fast)
- `deepseek-v4-pro` (verification, reasoning)
- `glm-5.1` (planning, critique)
- `kimi-k2.7-code` (coding, implementation)
- `kimi-k2.6` (fallback for all stages)
- `mimo-v2.5-pro` (not yet used in routing)
- `minimax-m3` (not yet used in routing)
- `qwen3.7-max` (not yet used in routing)

These model IDs were confirmed in `~/.hermes/models_dev_cache.json` on June 2026.
