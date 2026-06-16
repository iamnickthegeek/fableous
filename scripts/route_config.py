#!/usr/bin/env python3
"""Config cycling engine for Fable Orchestrator model routing.

Updates delegation.model and delegation.provider in the Hermes config
before each delegate_task call, then restores originals on completion.

Usage:
    python3 scripts/route_config.py set --stage research [--config path]
    python3 scripts/route_config.py set --model deepseek-v4-flash --provider opencode-go
    python3 scripts/route_config.py restore [--config path]
    python3 scripts/route_config.py status
    python3 scripts/route_config.py verify --output stage1_research.md --expected-model deepseek-v4-flash
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from fable_routing import (
    flatten_entries,
    load_dotenv,
    load_routing,
    provider_env_set,
    routing_entry_to_config_commands,
)

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

STAGES = ["research", "plan", "implement", "verify", "critique", "consolidate"]

BACKUP_DIR = Path.home() / ".hermes" / "skills" / "fableous"
BACKUP_FILE = BACKUP_DIR / ".routing-backup.json"

# Hermes config file path (discovered from `hermes config path`)
_HERMES_CONFIG_PATH = None


def _get_hermes_config_path() -> Path:
    """Get the Hermes config.yaml path."""
    global _HERMES_CONFIG_PATH
    if _HERMES_CONFIG_PATH is None:
        try:
            result = subprocess.run(
                ["hermes", "config", "path"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            path = result.stdout.strip()
            if path:
                _HERMES_CONFIG_PATH = Path(path)
            else:
                _HERMES_CONFIG_PATH = Path.home() / ".hermes" / "config.yaml"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            _HERMES_CONFIG_PATH = Path.home() / ".hermes" / "config.yaml"
    return _HERMES_CONFIG_PATH


def _hermes_config_get(key: str) -> str:
    """Read a value from the Hermes config YAML by dotted key path.

    Reads directly from config.yaml rather than using `hermes config show`,
    which outputs display-only box-drawing format.
    """
    config_path = _get_hermes_config_path()
    if not config_path.exists():
        return ""
    try:
        with config_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) if yaml else {}
        if not data:
            return ""
        parts = key.split(".")
        current = data
        for part in parts:
            if not isinstance(current, dict):
                return ""
            current = current.get(part)
            if current is None:
                return ""
        if not isinstance(current, str):
            return str(current) if current is not None else ""
        return current
    except Exception:
        return ""


def _hermes_config_set(key: str, value: str) -> None:
    """Set a Hermes config value via hermes config set."""
    subprocess.run(
        ["hermes", "config", "set", key, value],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )


def _ensure_backup_dir() -> None:
    """Create the backup directory if it doesn't exist."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def _read_backup() -> dict:
    """Read the backup file, returning empty dict if it doesn't exist."""
    if not BACKUP_FILE.exists():
        return {}
    try:
        with BACKUP_FILE.open() as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write_backup(original_model: str, original_provider: str, current_stage: str | None = None) -> None:
    """Write the backup file with original config values."""
    _ensure_backup_dir()
    backup = {
        "original_model": original_model,
        "original_provider": original_provider,
        "current_stage": current_stage,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with BACKUP_FILE.open("w") as f:
        json.dump(backup, f, indent=2)


def _resolve_routing_for_stage(stage: str, config_path: str | None) -> dict:
    """Resolve the best available model/provider for a stage.

    Falls back through primary -> secondary -> tertiary, skipping
    providers that aren't configured.
    """
    routing = load_routing(config_path)
    stage_routing = routing.get(stage, {})
    hermes_env = load_dotenv()
    if config_path:
        hermes_env.update(load_dotenv(Path(config_path).parent / ".env"))

    for level in ["primary", "secondary", "tertiary"]:
        entry = stage_routing.get(level)
        if not entry or not isinstance(entry, dict):
            continue
        model = entry.get("model", "")
        provider = entry.get("provider", "")
        if model and provider and provider_env_set(provider, hermes_env):
            return {"model": model, "provider": provider, "level": level}

    raise RuntimeError(
        f"No configured provider found for stage '{stage}'. "
        "Check API keys in ~/.hermes/.env or provide a fable-config.yaml."
    )


def cmd_set(args: argparse.Namespace) -> dict:
    """Execute the 'set' command."""
    if args.stage:
        resolved = _resolve_routing_for_stage(args.stage, args.config)
        model = resolved["model"]
        provider = resolved["provider"]
        level = resolved["level"]
    elif args.model and args.provider:
        model = args.model
        provider = args.provider
        level = "explicit"
    else:
        raise ValueError("Either --stage or --model/--provider must be provided")

    # Save originals before modifying (only on first set)
    backup = _read_backup()
    if "original_model" not in backup:
        orig_model = _hermes_config_get("delegation.model")
        orig_provider = _hermes_config_get("delegation.provider")
        _write_backup(orig_model, orig_provider, args.stage)
    else:
        # Update the current stage in backup
        backup["current_stage"] = args.stage
        backup["timestamp"] = datetime.now(timezone.utc).isoformat()
        with BACKUP_FILE.open("w") as f:
            json.dump(backup, f, indent=2)

    # Run the 5 config set commands
    _hermes_config_set("delegation.model", model)
    _hermes_config_set("delegation.provider", provider)
    _hermes_config_set("delegation.api_key", "")
    _hermes_config_set("delegation.base_url", "")
    _hermes_config_set("delegation.api_mode", "")

    return {
        "action": "set",
        "stage": args.stage,
        "level": level,
        "model": model,
        "provider": provider,
    }


def cmd_restore(args: argparse.Namespace) -> dict:
    """Execute the 'restore' command.

    Reads the saved originals from backup and restores them.
    Idempotent — safe to call multiple times.
    Falls back to current config values if backup is missing.
    """
    backup = _read_backup()
    original_model = backup.get("original_model", "")
    original_provider = backup.get("original_provider", "")

    if not original_model and not original_provider:
        # No backup — read current values and treat them as originals
        original_model = _hermes_config_get("delegation.model")
        original_provider = _hermes_config_get("delegation.provider")

    _hermes_config_set("delegation.model", original_model)
    _hermes_config_set("delegation.provider", original_provider)
    _hermes_config_set("delegation.api_key", "")
    _hermes_config_set("delegation.base_url", "")
    _hermes_config_set("delegation.api_mode", "")

    # Remove backup after successful restore
    if BACKUP_FILE.exists():
        BACKUP_FILE.unlink()

    return {
        "action": "restore",
        "model": original_model,
        "provider": original_provider,
    }


def cmd_status(args: argparse.Namespace) -> dict:
    """Execute the 'status' command."""
    model = _hermes_config_get("delegation.model")
    provider = _hermes_config_get("delegation.provider")
    api_key = _hermes_config_get("delegation.api_key")
    base_url = _hermes_config_get("delegation.base_url")
    api_mode = _hermes_config_get("delegation.api_mode")

    backup = _read_backup()

    return {
        "action": "status",
        "delegation": {
            "model": model,
            "provider": provider,
            "api_key": api_key,
            "base_url": base_url,
            "api_mode": api_mode,
        },
        "backup": backup if backup else None,
    }


def cmd_verify(args: argparse.Namespace) -> dict:
    """Execute the 'verify' command.

    Reads the first line of the output file and checks for a model tag.
    Returns exit code 0 on match, 1 on mismatch, 2 on missing tag.
    """
    output_path = Path(args.output)
    if not output_path.exists():
        return {
            "action": "verify",
            "output": args.output,
            "expected_model": args.expected_model,
            "status": "error",
            "message": f"Output file not found: {args.output}",
        }

    content = output_path.read_text()
    first_line = content.lstrip().split("\n")[0].strip()

    # Match [MODEL: name, PROVIDER: provider]
    pattern = re.compile(
        r"\[MODEL:\s*(?P<model>\S+),\s*PROVIDER:\s*(?P<provider>\S+)\]"
    )
    match = pattern.search(first_line)

    if not match:
        return {
            "action": "verify",
            "output": args.output,
            "expected_model": args.expected_model,
            "status": "missing_tag",
            "first_line": first_line,
            "message": "No model tag found in first line of output",
        }

    actual_model = match.group("model")
    actual_provider = match.group("provider")
    expected_model = args.expected_model

    match_ok = actual_model == expected_model

    return {
        "action": "verify",
        "output": args.output,
        "expected_model": expected_model,
        "actual_model": actual_model,
        "actual_provider": actual_provider,
        "status": "match" if match_ok else "mismatch",
        "message": (
            f"Model tag matches: {actual_model}"
            if match_ok
            else f"Expected {expected_model}, got {actual_model}"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Config cycling engine for Fable Orchestrator model routing."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # set
    set_parser = subparsers.add_parser("set", help="Set delegation config for a stage")
    set_parser.add_argument("--stage", choices=STAGES, help="Stage to route")
    set_parser.add_argument("--model", help="Explicit model name")
    set_parser.add_argument("--provider", help="Explicit provider name")
    set_parser.add_argument("--config", help="Path to fable-config.yaml")

    # restore
    restore_parser = subparsers.add_parser("restore", help="Restore original delegation config")
    restore_parser.add_argument("--config", help="Path to fable-config.yaml")

    # status
    subparsers.add_parser("status", help="Show current delegation config")

    # verify
    verify_parser = subparsers.add_parser("verify", help="Verify model tag in stage output")
    verify_parser.add_argument("--output", required=True, help="Path to stage output file")
    verify_parser.add_argument("--expected-model", required=True, help="Expected model name")

    args = parser.parse_args()

    try:
        if args.command == "set":
            result = cmd_set(args)
        elif args.command == "restore":
            result = cmd_restore(args)
        elif args.command == "status":
            result = cmd_status(args)
        elif args.command == "verify":
            result = cmd_verify(args)
        else:
            parser.print_help()
            return 1
    except Exception as e:
        print(json.dumps({"action": args.command, "error": str(e)}))
        return 1

    print(json.dumps(result, indent=2))

    # Map verify status to exit code
    if args.command == "verify":
        status = result.get("status", "")
        if status == "match":
            return 0
        elif status == "mismatch":
            return 1
        else:
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
