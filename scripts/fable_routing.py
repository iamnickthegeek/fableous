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

# No default routing table. All routing MUST come from fable-config.yaml.
# See templates/fable-config-nvidia-nim.yaml for a complete example.

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
    "nvidia": "NVIDIA_API_KEY",
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
    """Load routing table from fable-config.yaml.

    Resolution order:
    1. Explicit config_path argument (if provided)
    2. Skill directory: ~/.hermes/skills/fableous/fable-config.yaml
    3. Working directory: ./fable-config.yaml

    Raises RuntimeError if no config file is found — there is no fallback
    default routing table. The user MUST provide a fable-config.yaml.
    """
    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"config file not found: {config_path}")
        return _load_yaml_routing(path)

    # Auto-discover: skill directory first
    skill_config = Path.home() / ".hermes" / "skills" / "fableous" / "fable-config.yaml"
    if skill_config.exists():
        return _load_yaml_routing(skill_config)

    # Auto-discover: working directory
    cwd_config = Path.cwd() / "fable-config.yaml"
    if cwd_config.exists():
        return _load_yaml_routing(cwd_config)

    raise RuntimeError(
        "No fable-config.yaml found. Create one at "
        "~/.hermes/skills/fableous/fable-config.yaml or in the project directory. "
        "See templates/fable-config-nvidia-nim.yaml for an example."
    )


def _load_yaml_routing(path: Path) -> dict:
    """Load routing dict from a fable-config.yaml file."""
    if yaml is None:
        raise RuntimeError(
            "PyYAML is required to read .yaml config files. "
            "Install it with: pip install pyyaml"
        )
    with path.open() as f:
        data = yaml.safe_load(f)
    if data and "routing" in data:
        return data["routing"]
    raise ValueError(f"config has no 'routing' key: {path}")


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
