# Opencode Go Model Catalog

Opencode Go is a **multi-model hub**, not a Kimi-only provider. It serves 18 models across 8 provider families through a single API endpoint (`https://opencode.ai/zen/go/v1`).

## Available Models (as of June 2026)

| Model ID | Name | Family | Notes |
|----------|------|--------|-------|
| `deepseek-v4-flash` | DeepSeek V4 Flash | deepseek-flash | Reasoning model, fast |
| `deepseek-v4-pro` | DeepSeek V4 Pro | deepseek-pro | Reasoning model, deep analysis |
| `glm-5` | GLM-5 | glm | Structured reasoning |
| `glm-5.1` | GLM-5.1 | glm | Strong at decomposition and planning |
| `kimi-k2.5` | Kimi K2.5 | kimi | General purpose |
| `kimi-k2.6` | Kimi K2.6 | kimi | Proven coding and general |
| `kimi-k2.7-code` | Kimi K2.7 Code | kimi | Code-specialized (new, verify availability) |
| `mimo-v2-omni` | MiMo V2 Omni | mimo | Xiaomi |
| `mimo-v2-pro` | MiMo V2 Pro | mimo | Xiaomi |
| `mimo-v2.5` | MiMo V2.5 | mimo | Xiaomi |
| `mimo-v2.5-pro` | MiMo V2.5 Pro | mimo | Xiaomi |
| `minimax-m2.5` | MiniMax M2.5 | minimax | |
| `minimax-m2.7` | MiniMax M2.7 | minimax | |
| `minimax-m3` | MiniMax M3 (3x usage) | minimax | 3x token usage |
| `qwen3.5-plus` | Qwen3.5 Plus | qwen | Alibaba |
| `qwen3.6-plus` | Qwen3.6 Plus | qwen | Alibaba |
| `qwen3.7-max` | Qwen3.7 Max | qwen | Alibaba |
| `qwen3.7-plus` | Qwen3.7 Plus | qwen | Alibaba |

## Key Discovery

The `models_dev_cache.json` in `~/.hermes/` is the authoritative source. Hermes fetches this from the models.dev registry at startup. The cache lives at `~/.hermes/models_dev_cache.json`.

To verify current models programmatically:
```bash
python3 -c "
import json
with open('/home/case/.hermes/models_dev_cache.json') as f:
    data = json.load(f)
models = data['opencode-go']['models']
for k in sorted(models.keys()):
    print(f'{k}: {models[k][\"name\"]}')
"
```

## Usage in `delegate_task`

Format: `opencode-go/<model-id>`

Example:
```
delegate_task(
    goal="Research AI ghostwriting tools",
    model="opencode-go/deepseek-v4-flash"
)
```

## Environment

Requires `OPENCODE_GO_API_KEY` in `.env` (or `OPENCODE_API_KEY` depending on Hermes version).
