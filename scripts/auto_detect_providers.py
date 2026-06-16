#!/usr/bin/env python3
"""Auto-detect available providers and generate a Fable v6 routing table.

Usage:
    python3 scripts/auto_detect_providers.py
    python3 scripts/auto_detect_providers.py --save

Reads the user's Hermes .env file and config.yaml, then suggests a routing
table with primary, secondary, and tertiary models for each Fable stage.
With --save, writes the result to ./fable-config.yaml.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

from fable_routing import (
    DEFAULT_ROUTING,
    PROVIDER_ENV,
    load_dotenv,
    provider_env_set,
    render_yaml,
)

# Priority order when multiple providers are available.
PROVIDER_PRIORITY = [
    "opencode-go",
    "google",
    "openrouter",
    "anthropic",
    "openai",
    "deepseek",
    "xai",
    "kimi",
    "glm",
]


def load_configured_providers(config_path: Path) -> list[str]:
    """Read Hermes config.yaml providers section if present."""
    if not config_path.exists() or yaml is None:
        return []
    try:
        with config_path.open() as f:
            data = yaml.safe_load(f) or {}
        providers = data.get("providers", {})
        if isinstance(providers, dict):
            return [p for p in providers.keys() if p in PROVIDER_ENV]
    except Exception:
        pass
    return []


def detect_available_providers(hermes_env: dict) -> list[str]:
    """Return providers with API keys set, ordered by priority."""
    available = [
        provider
        for provider in PROVIDER_PRIORITY
        if provider_env_set(provider, hermes_env)
    ]
    return available


def fill_fallbacks(routing: dict, available: list[str]) -> dict:
    """Ensure every stage has primary, secondary, tertiary from available providers.

    Starts from the default routing and fills any empty slot with the next
    available provider in priority order.
    """
    filled = {}
    for stage, levels in routing.items():
        filled[stage] = {}
        used_providers = set()

        # Preserve defaults where the provider is available.
        for level in ["primary", "secondary", "tertiary"]:
            info = levels.get(level)
            if info and provider_env_set(info["provider"]):
                filled[stage][level] = info
                used_providers.add(info["provider"])

        # Fill missing levels from remaining available providers.
        for level in ["primary", "secondary", "tertiary"]:
            if level in filled[stage]:
                continue
            for provider in available:
                if provider in used_providers:
                    continue
                # Find the best model for this stage/provider from defaults.
                model = _model_for(stage, provider)
                if model:
                    filled[stage][level] = {"model": model, "provider": provider}
                    used_providers.add(provider)
                    break

    return filled


def _model_for(stage: str, provider: str) -> str | None:
    """Find a model assignment for a stage/provider from the default routing."""
    for level in ["primary", "secondary", "tertiary"]:
        info = DEFAULT_ROUTING.get(stage, {}).get(level)
        if info and info["provider"] == provider:
            return info["model"]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Auto-detect providers and generate a Fable v6 routing table."
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Write the generated config to ./fable-config.yaml",
    )
    args = parser.parse_args()

    hermes_env_path = Path.home() / ".hermes" / ".env"
    hermes_config_path = Path.home() / ".hermes" / "config.yaml"

    hermes_env = load_dotenv(hermes_env_path)
    env_providers = detect_available_providers(hermes_env)
    config_providers = load_configured_providers(hermes_config_path)

    providers = list(dict.fromkeys(env_providers + config_providers))

    print("# Fable Orchestrator v6 \u2014 Provider Detection\n")

    print("Detected providers:")
    if providers:
        for provider in providers:
            env_var = PROVIDER_ENV.get(provider, "unknown")
            print(f"  - {provider} ({env_var} is set)")
    else:
        print("  None. Set one of these in ~/.hermes/.env:")
        for provider, env_var in PROVIDER_ENV.items():
            print(f"    - {provider}: {env_var}")
        print("\nNo providers detected. Cannot generate routing table.")
        return 1

    routing = fill_fallbacks(DEFAULT_ROUTING, providers)
    yaml_output = render_yaml(routing)

    print("\n# Suggested fable-config.yaml\n")
    print("```yaml")
    print(yaml_output.rstrip())
    print("```")

    if args.save:
        output_path = Path("fable-config.yaml")
        if output_path.exists():
            print(f"\nWarning: {output_path} already exists. Delete it first or edit manually.")
            return 1
        output_path.write_text(yaml_output)
        print(f"\nSaved to {output_path.resolve()}")
    else:
        print("\nSave with: python3 scripts/auto_detect_providers.py --save")

    return 0


if __name__ == "__main__":
    sys.exit(main())
