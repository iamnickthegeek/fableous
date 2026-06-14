# Model Routing Table — Quick Lookup

## Primary / Secondary / Tertiary Chains

| Stage | Primary | Secondary | Tertiary | Key Rule |
|-------|---------|-----------|----------|----------|
| Research | `opencode-go/deepseek-v4-flash` | `google/gemini-2.5-flash-lite` | `openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | Fast, broad, cheap |
| Planning | `opencode-go/glm-5.1` | `google/gemini-2.5-pro` | `opencode-go/deepseek-v4-pro` | Structured reasoning |
| Coding | `opencode-go/kimi-k2.7-code` | `opencode-go/kimi-k2.6` | `google/gemini-2.5-pro` | Code-specialized |
| Verification | `opencode-go/deepseek-v4-pro` | `google/gemini-2.5-pro` | `opencode-go/kimi-k2.6` | Different family from coder |
| Critique | `opencode-go/glm-5.1` | `google/gemini-2.5-pro` | `opencode-go/kimi-k2.6` | Independent evaluation |

## Critical Rules

1. **Critique must be a different model family from the one that produced the work.** If Kimi wrote the code, Kimi cannot be the critique model.
2. **Verification must be a different model family from the implementer.** If Kimi wrote the analysis, DeepSeek or Gemini must verify it.
3. **Fail open.** If the primary model fails, retry with the secondary. If the secondary fails, retry with the tertiary. Never halt.
4. **Budget exhaustion = correct SKIP.** If the user is out of budget, use the cheapest available model or flag the task as blocked.

## Provider Priority

1. **Opencode Go** — primary hub, multi-model (Kimi, GLM, DeepSeek, MiMo, Qwen, MiniMax)
2. **Google** — secondary (Gemini Flash Lite, Flash, Pro)
3. **OpenRouter** — tertiary (free tier: NVIDIA Nemotron)

## Env Vars Required

- `OPENCODE_GO_API_KEY` — primary provider
- `GOOGLE_API_KEY` — secondary provider
- `OPENROUTER_API_KEY` — tertiary provider (optional)

## Notes

- GLM 5.2 will replace GLM 5.1 for planning and critique when tested and confirmed better.
- Kimi 2.7 Code availability should be verified via `models_dev_cache.json` before routing.
- DeepSeek V4 Flash and Pro are reasoning models — they may expose thinking tokens and take longer to respond.
