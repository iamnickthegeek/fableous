#!/usr/bin/env python3
"""Run a single Fable v6 stage with hard-coded model/provider routing.

This is the concrete implementation of model routing. It bypasses the
soft `delegate_task` model parameter by invoking `hermes chat -q` directly
with explicit `-m` and `--provider` flags, then falls back through
secondary and tertiary models if the primary fails.

Usage:
    python3 scripts/run_stage.py --stage research --prompt "Analyze competitors"
    python3 scripts/run_stage.py --stage implement --prompt-file task.md --output stage3.md
    python3 scripts/run_stage.py --stage verify --prompt-file task.md --model deepseek-v4-pro --provider opencode-go
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from fable_routing import (
    DEFAULT_ROUTING,
    flatten_entries,
    load_dotenv,
    load_routing,
    provider_env_set,
)

STAGES = ["research", "plan", "implement", "verify", "critique", "consolidate"]


def build_hermes_command(model: str, provider: str, prompt: str, toolsets: str) -> list[str]:
    """Build the hard-routed hermes chat command."""
    return [
        "hermes",
        "chat",
        "-q",
        prompt,
        "-m",
        model,
        "--provider",
        provider,
        "-Q",
        "--accept-hooks",
        "-t",
        toolsets,
    ]


def run_hermes(model: str, provider: str, prompt: str, toolsets: str, timeout: int) -> tuple[bool, str]:
    """Run hermes chat and return (ok, output_or_error)."""
    cmd = build_hermes_command(model, provider, prompt, toolsets)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return True, result.stdout
        err = result.stderr.strip() or result.stdout.strip()
        return False, err
    except FileNotFoundError:
        return False, "hermes command not found. Is Hermes Agent installed?"
    except subprocess.TimeoutExpired:
        return False, f"timed out after {timeout}s"
    except Exception as e:
        return False, f"subprocess failed: {e}"


def ensure_model_tag(output: str, model: str, provider: str) -> str:
    """Prepend a model tag if the output does not already contain one."""
    marker = f"[MODEL: {model}, PROVIDER: {provider}]"
    stripped = output.lstrip()
    if stripped.startswith("[MODEL:"):
        return output
    return f"{marker}\n\n{output}"


def toolsets_for_stage(stage: str) -> str:
    """Return the recommended toolsets for a stage."""
    if stage == "research":
        return "web,file"
    if stage in {"verify", "critique"}:
        return "web,terminal,file,session_search"
    return "terminal,file,web"


def via_config_mode(stage: str, config_path: str | None, model: str | None = None, provider: str | None = None) -> int:
    """Run a stage using config cycling + delegate_task instructions.

    This mode uses route_config.py for model routing instead of direct
    terminal spawning. Run this from an orchestrator agent that will
    call delegate_task after config is set.
    """
    import json

    # Step 1: Set config via route_config.py
    cmd = [sys.executable, str(Path(__file__).parent / "route_config.py")]
    if config_path:
        cmd.extend(["--config", config_path])

    if model and provider:
        cmd.extend(["set", "--model", model, "--provider", provider])
    else:
        cmd.extend(["set", "--stage", stage])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(result.stdout, file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            print("Config cycling set failed. Falling back to terminal mode.", file=sys.stderr)
            return 1
        routing_info = json.loads(result.stdout)
    except Exception as e:
        print(f"Config cycling set failed: {e}", file=sys.stderr)
        return 1

    # Step 2: Print delegate_task instruction block for the orchestrator
    print(f"# Fable Orchestrator v7 - Via Config Mode")
    print(f"# Stage: {stage}")
    print(f"# Model: {routing_info.get('model', 'unknown')}")
    print(f"# Provider: {routing_info.get('provider', 'unknown')}")
    print(f"# Level: {routing_info.get('level', routing_info.get('level', 'explicit'))}")
    print()
    print(f"Config has been set for {stage}. Call delegate_task now.")
    print()
    print("After delegate_task returns, verify with:")
    print(f"  python scripts/route_config.py verify --output <output_file> --expected-model {routing_info.get('model', 'unknown')}")
    print()
    print("On completion or error, restore with:")
    print("  python scripts/route_config.py restore")
    print()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a single Fable v6 stage with hard-coded model routing."
    )
    parser.add_argument(
        "--stage",
        required=True,
        choices=STAGES,
        help="Fable stage to run",
    )
    parser.add_argument(
        "--via-config",
        action="store_true",
        help="Use config cycling (route_config.py) instead of direct terminal spawning",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prompt", help="Prompt text to send")
    group.add_argument("--prompt-file", help="Path to a file containing the prompt")
    parser.add_argument(
        "--config",
        help="Path to fable-config.yaml (uses defaults if omitted)",
    )
    parser.add_argument(
        "--model",
        help="Override the model for this run",
    )
    parser.add_argument(
        "--provider",
        help="Override the provider for this run",
    )
    parser.add_argument(
        "--output",
        help="Path to write the stage output (prints to stdout if omitted)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds for each model attempt (default: 300)",
    )
    args = parser.parse_args()

    # Via-config mode: set config and print delegate_task instructions
    if args.via_config:
        result = via_config_mode(args.stage, args.config, args.model, args.provider)
        if args.prompt_file:
            prompt_path = Path(args.prompt_file)
            if prompt_path.exists():
                prompt = prompt_path.read_text()
            else:
                print(f"# Prompt (intended for delegate_task):")
                print()
                print("No prompt file found.")
        else:
            print(f"# Prompt (intended for delegate_task):")
            print()
            print(args.prompt)
        return result

    if args.prompt_file:
        prompt_path = Path(args.prompt_file)
        if not prompt_path.exists():
            print(f"Error: prompt file not found: {args.prompt_file}", file=sys.stderr)
            return 1
        prompt = prompt_path.read_text()
    else:
        prompt = args.prompt

    routing = load_routing(args.config)
    stage_routing = routing.get(args.stage, {})

    # Build ordered list of attempts.
    attempts = []
    if args.model and args.provider:
        attempts.append({"level": "override", "model": args.model, "provider": args.provider})
    for level in ["primary", "secondary", "tertiary"]:
        info = stage_routing.get(level)
        if info and isinstance(info, dict):
            attempts.append({"level": level, **info})

    if not attempts:
        print(f"Error: no routing configured for stage '{args.stage}'", file=sys.stderr)
        return 1

    hermes_env = load_dotenv()
    toolsets = toolsets_for_stage(args.stage)

    print(f"# Fable Orchestrator v6 \u2014 Running stage: {args.stage}\n")

    for attempt in attempts:
        model = attempt["model"]
        provider = attempt["provider"]
        level = attempt["level"]

        if not provider_env_set(provider, hermes_env):
            print(f"[{level}] {model} ({provider}) \u2014 skipped, provider not configured")
            continue

        print(f"[{level}] Trying {model} via {provider}...")
        ok, output = run_hermes(model, provider, prompt, toolsets, args.timeout)

        if ok:
            tagged_output = ensure_model_tag(output, model, provider)
            if args.output:
                Path(args.output).write_text(tagged_output)
                print(f"\nSuccess. Output written to {args.output}")
            else:
                print("\nSuccess. Output:\n")
                print(tagged_output)
            return 0

        print(f"  \u2192 failed: {output[:200]}")

    print("\nAll model attempts failed.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
