"""Shared routing constants and helpers for Fable Orchestrator v6 scripts.

This is not an engine. It is a small shared module used by the helper scripts
(verify_models.py, auto_detect_providers.py, run_stage.py) so the default
routing table lives in one place.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

# Default routing table for Fable v6.
DEFAULT_ROUTING = {
    "research": {
        "primary": {"model": "deepseek-v4-flash", "provider": "opencode-go"},
        "secondary": {"model": "gemini-2.5-flash-lite", "provider": "google"},
        "tertiary": {"model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "provider": "openrouter"},
    },
    "plan": {
        "primary": {"model": "glm-5.1", "provider": "opencode-go"},
        "secondary": {"model": "gemini-2.5-pro", "provider": "google"},
        "tertiary": {"model": "deepseek-v4-pro", "provider": "opencode-go"},
    },
    "implement": {
        "primary": {"model": "kimi-k2.7-code", "provider": "opencode-go"},
        "secondary": {"model": "kimi-k2.6", "provider": "opencode-go"},
        "tertiary": {"model": "gemini-2.5-pro", "provider": "google"},
    },
    "verify": {
        "primary": {"model": "deepseek-v4-pro", "provider": "opencode-go"},
        "secondary": {"model": "gemini-2.5-pro", "provider": "google"},
        "tertiary": {"model": "kimi-k2.6", "provider": "opencode-go"},
    },
    "critique": {
        "primary": {"model": "glm-5.1", "provider": "opencode-go"},
        "secondary": {"model": "gemini-2.5-pro", "provider": "google"},
        "tertiary": {"model": "kimi-k2.6", "provider": "opencode-go"},
    },
    "consolidate": {
        "primary": {"model": "deepseek-v4-pro", "provider": "opencode-go"},
        "secondary": {"model": "glm-5.1", "provider": "opencode-go"},
        "tertiary": {"model": "gemini-2.5-pro", "provider": "google"},
    },
}

# Map provider names to the environment variables they need.
PROVIDER_ENV = {
    "opencode-go": "OPENCODE_GO_API_KEY",
    "google": "GOOGLE_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "xai": "XAI_API_KEY",
    "kimi": "KIMI_API_KEY",
    "glm": "GLM_API_KEY",
}


def load_dotenv(path: Path | None = None) -> dict:
    """Read a simple KEY=VALUE .env file."""
    if path is None:
        path = Path.home() / ".hermes" / ".env"
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def load_routing(config_path: str | None) -> dict:
    """Load routing table from fable-config.yaml or use defaults."""
    if not config_path:
        return DEFAULT_ROUTING.copy()

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"config file not found: {config_path}")

    if yaml is None:
        raise RuntimeError(
            "PyYAML is required to read .yaml config files. "
            "Install it with: pip install pyyaml"
        )

    with path.open() as f:
        data = yaml.safe_load(f)

    if data and "routing" in data:
        return data["routing"]

    raise ValueError("config has no 'routing' key")


def flatten_entries(routing: dict) -> list[dict]:
    """Flatten routing table into a list of entries with stage/level."""
    entries = []
    for stage, levels in routing.items():
        for level in ["primary", "secondary", "tertiary"]:
            info = levels.get(level)
            if info and isinstance(info, dict):
                entries.append(
                    {
                        "stage": stage,
                        "level": level,
                        "model": info.get("model", ""),
                        "provider": info.get("provider", ""),
                    }
                )
    return entries


def routing_entry_to_config_commands(stage: str, level: str = "primary", config_path: str | None = None) -> list[str]:
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


def provider_env_set(provider: str, hermes_env: dict | None = None) -> bool:
    """Check whether a provider's API key is set."""
    if hermes_env is None:
        hermes_env = load_dotenv()
    env_var = PROVIDER_ENV.get(provider)
    if not env_var:
        return False
    return bool(os.getenv(env_var) or hermes_env.get(env_var))


def render_yaml(routing: dict) -> str:
    """Render routing table as clean YAML."""
    if yaml is None:
        lines = ["routing:"]
        for stage, levels in routing.items():
            lines.append(f"  {stage}:")
            for level, info in levels.items():
                lines.append(f"    {level}:")
                lines.append(f"      model: {info['model']}")
                lines.append(f"      provider: {info['provider']}")
        return "\n".join(lines) + "\n"
    return yaml.dump({"routing": routing}, default_flow_style=False, sort_keys=False)
