# Model Routing Table — v8

Quick lookup for the Fable Orchestrator v8. The routing table is the authority. Do not ask the user which model to use.

**v8.0 note:** The choice between full routing and single-model is not only a cost decision — it's a quality/character decision. See SKILL.md §Quality Tradeoffs and `references/token-budget-mode.md` for the full tradeoff analysis and deliverable-type-to-mode decision guidance.

## Primary / Secondary / Tertiary Chains

| Stage | Primary | Secondary | Tertiary | Key Rule |
|-------|---------|-----------|----------|----------|
| Research | `opencode-go/deepseek-v4-flash` | `google/gemini-2.5-flash-lite` | `openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | Fast, broad, cheap |
| Planning | `opencode-go/glm-5.1` | `google/gemini-2.5-pro` | `opencode-go/deepseek-v4-pro` | Structured reasoning |
| Implementation | `opencode-go/kimi-k2.7-code` | `opencode-go/kimi-k2.6` | `google/gemini-2.5-pro` | Code-specialized |
| Verification | `opencode-go/deepseek-v4-pro` | `google/gemini-2.5-pro` | `opencode-go/kimi-k2.6` | Different family from implementer |
| Critique | `opencode-go/glm-5.1` | `google/gemini-2.5-pro` | `opencode-go/kimi-k2.6` | Independent evaluation |
| Consolidation | `opencode-go/deepseek-v4-pro` | `opencode-go/glm-5.1` | `google/gemini-2.5-pro` | Reads all stages, produces canonical output |

## Hermes Config Set Commands

For config cycling (v7 method), use `route_config.py set --stage NAME` or run these commands directly:

| Stage | Primary | Config Commands |
|-------|---------|-----------------|
| Research | deepseek-v4-flash (Opencode Go) | `hermes config set delegation.model deepseek-v4-flash && hermes config set delegation.provider opencode-go && hermes config set delegation.api_key "" && hermes config set delegation.base_url "" && hermes config set delegation.api_mode ""` |
| Plan | glm-5.1 (Opencode Go) | `hermes config set delegation.model glm-5.1 && hermes config set delegation.provider opencode-go && hermes config set delegation.api_key "" && hermes config set delegation.base_url "" && hermes config set delegation.api_mode ""` |
| Implement | kimi-k2.7-code (Opencode Go) | `hermes config set delegation.model kimi-k2.7-code && hermes config set delegation.provider opencode-go && hermes config set delegation.api_key "" && hermes config set delegation.base_url "" && hermes config set delegation.api_mode ""` |
| Verify | deepseek-v4-pro (Opencode Go) | `hermes config set delegation.model deepseek-v4-pro && hermes config set delegation.provider opencode-go && hermes config set delegation.api_key "" && hermes config set delegation.base_url "" && hermes config set delegation.api_mode ""` |
| Critique | glm-5.1 (Opencode Go) | `hermes config set delegation.model glm-5.1 && hermes config set delegation.provider opencode-go && hermes config set delegation.api_key "" && hermes config set delegation.base_url "" && hermes config set delegation.api_mode ""` |
| Consolidate | deepseek-v4-pro (Opencode Go) | `hermes config set delegation.model deepseek-v4-pro && hermes config set delegation.provider opencode-go && hermes config set delegation.api_key "" && hermes config set delegation.base_url "" && hermes config set delegation.api_mode ""` |

## Critical Rules

1. **Critique must be a different model family from the implementer.** If Kimi wrote the code, GLM or Gemini must critique it.
2. **Verification must be a different model family from the implementer.** If Kimi wrote the analysis, DeepSeek or Gemini must verify it.
3. **Consolidation must be a different model family from the implementer.** Never the same brain that wrote the work.
4. **Fail open.** If the primary model fails, retry with the secondary. If the secondary fails, retry with the tertiary. Never halt.
5. **Budget exhaustion = correct SKIP.** If the user is out of budget, use the cheapest available model or flag the task as blocked.

## Model Family Definitions

| Family | Models | Provider |
|--------|--------|----------|
| DeepSeek | deepseek-v4-flash, deepseek-v4-pro | Opencode Go |
| GLM | glm-5.1 | Opencode Go |
| Kimi | kimi-k2.7-code, kimi-k2.6 | Opencode Go |
| Gemini | gemini-2.5-flash-lite, gemini-2.5-pro | Google |
| Nemotron | nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free | OpenRouter |

## Cross-Family Check Matrix

| Implementer | Allowed Verifier | Allowed Critique | Allowed Consolidation |
|-------------|-----------------|------------------|------------------------|
| Kimi | DeepSeek, Gemini, GLM | DeepSeek, Gemini, GLM | DeepSeek, Gemini, GLM |
| DeepSeek | Kimi, Gemini, GLM | Kimi, Gemini, GLM | Kimi, Gemini, GLM |
| GLM | Kimi, DeepSeek, Gemini | Kimi, DeepSeek, Gemini | Kimi, DeepSeek, Gemini |
| Gemini | Kimi, DeepSeek, GLM | Kimi, DeepSeek, GLM | Kimi, DeepSeek, GLM |

## Provider Priority

1. **Opencode Go** — primary hub, multi-model (Kimi, GLM, DeepSeek, MiMo, Qwen, MiniMax)
2. **Google** — secondary (Gemini Flash Lite, Flash, Pro)
3. **OpenRouter** — tertiary (free tier: NVIDIA Nemotron)

## Env Vars Required

- `OPENCODE_GO_API_KEY` — primary provider
- `GOOGLE_API_KEY` — secondary provider
- `OPENROUTER_API_KEY` — tertiary provider (optional)

## Auto-Detection Logic

The skill reads the user's Hermes config to determine available providers:

1. Read `~/.hermes/config.yaml` — check `model.provider`, `model.default`
2. Read `~/.hermes/.env` — check which API keys are set
3. Build provider list: rank by availability
4. Map providers to stages: use best available model for each stage type

If a `fable-config.yaml` exists in the project directory, it overrides all defaults.

## NVIDIA NIM as Unified Provider

NVIDIA's NIM marketplace (`https://build.nvidia.com`) hosts free inference endpoints for models from multiple vendors under a single `NVIDIA_API_KEY`. This allows true cross-family verification with one credential instead of juggling multiple providers.

See `references/nvidia-nim-unified-provider.md` for the aspiration verified model list, family classification, and a complete sample `fable-config.yaml`.

## Notes

- GLM 5.2 will replace GLM 5.1 for planning and critique when tested and confirmed better.
- Kimi 2.7 Code availability should be verified via `hermes models` before routing.
- DeepSeek V4 Flash and Pro are reasoning models — they may expose thinking tokens and take longer to respond.
- Config cycling is the v7 default. Use `route_config.py set --stage NAME` to set both model and provider. When falling back to terminal mode, both `-m` and `--provider` flags are required.
