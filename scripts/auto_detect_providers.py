#!/usr/bin/env python3
"""Auto-detect available providers and generate a Fable v0.6.0 routing table.

Usage:
    python3 scripts/auto_detect_providers.py
    python3 scripts/auto_detect_providers.py --save

Reads the user's Hermes .env file and config.yaml, detects which providers
have API keys, then generates a fable-config.yaml *skeleton* that maps those
providers onto every Fable stage with placeholder model names to fill in.
There is no built-in routing table (removed in v0.8.2), so model names are
left as placeholders — only provider detection is automatic.
With --save, writes the skeleton to ./fable-config.yaml.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

from fable_routing import (
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

# The six Fable stages, in pipeline order.
STAGES = ["research", "plan", "implement", "verify", "critique", "consolidate"]

# Placeholder model name written into each routing slot. auto-detect knows which
# providers have API keys but not which model to use — the user fills these in.
MODEL_PLACEHOLDER = "<set-model-here>"


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


def build_skeleton(available: list[str]) -> dict:
    """Build a routing skeleton mapping each stage onto the available providers.

    Assigns the detected providers (in priority order) to primary, secondary,
    and tertiary for every stage, leaving each model name as a placeholder for
    the user to fill in. There is no built-in routing table (removed in
    v0.8.2), so only provider detection is automatic — choosing model names
    stays an explicit user decision.
    """
    levels = ["primary", "secondary", "tertiary"]
    skeleton = {}
    for stage in STAGES:
        stage_routing = {}
        for level, provider in zip(levels, available):
            stage_routing[level] = {"model": MODEL_PLACEHOLDER, "provider": provider}
        skeleton[stage] = stage_routing
    return skeleton


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Auto-detect providers and generate a Fable v0.6.0 routing table."
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

    print("# Fable Orchestrator v0.6.0 \u2014 Provider Detection\n")

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

    routing = build_skeleton(providers)
    yaml_output = render_yaml(routing)

    print("\n# fable-config.yaml skeleton\n")
    print(f"# Replace every '{MODEL_PLACEHOLDER}' with a real model name for that")
    print("# provider. Remember the cross-family rule: verify, critique, and")
    print("# consolidate should each use a different model family than implement.")
    print("```yaml")
    print(yaml_output.rstrip())
    print("```")

    if args.save:
        output_path = Path("fable-config.yaml")
        if output_path.exists():
            print(f"\nWarning: {output_path} already exists. Delete it first or edit manually.")
            return 1
        output_path.write_text(yaml_output)
        print(f"\nSaved skeleton to {output_path.resolve()}")
        print(f"Edit it and replace every '{MODEL_PLACEHOLDER}' before running Fable.")
    else:
        print("\nSave with: python3 scripts/auto_detect_providers.py --save")

    return 0


if __name__ == "__main__":
    sys.exit(main())
