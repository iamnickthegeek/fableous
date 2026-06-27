#!/usr/bin/env python3
"""Pre-flight model availability check for Fable Orchestrator v0.6.0.

Usage:
    python3 scripts/verify_models.py
    python3 scripts/verify_models.py --config ./fable-config.yaml
    python3 scripts/verify_models.py --live-test

Checks that every provider in the routing table has its API key configured.
With --live-test, it also sends a tiny prompt to each model (costs tokens).
Returns exit code 0 only if all checks pass.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

from fable_routing import (
    PROVIDER_ENV,
    flatten_entries,
    load_dotenv,
    load_routing,
    provider_env_set,
)


def check_hermes_config() -> tuple[bool, str]:
    """Run `hermes config check` to catch basic Hermes misconfiguration."""
    try:
        result = subprocess.run(
            ["hermes", "config", "check"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True, "hermes config check passed"
        return False, result.stderr.strip() or result.stdout.strip()
    except FileNotFoundError:
        return False, "hermes command not found. Is Hermes Agent installed?"
    except subprocess.TimeoutExpired:
        return False, "hermes config check timed out"
    except Exception as e:
        return False, f"hermes config check failed: {e}"


def live_test_model(model: str, provider: str) -> tuple[bool, str]:
    """Send a tiny prompt to confirm the model actually responds. Costs tokens."""
    prompt = "Reply with exactly one word: OK"
    try:
        result = subprocess.run(
            [
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
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return True, "live response OK"
        err = result.stderr.strip() or result.stdout.strip()
        return False, err[:200]
    except FileNotFoundError:
        return False, "hermes command not found"
    except subprocess.TimeoutExpired:
        return False, "live test timed out"
    except Exception as e:
        return False, f"live test failed: {e}"


def mask(value: str) -> str:
    """Mask an API key for display."""
    if len(value) > 12:
        return f"{value[:4]}...{value[-4:]}"
    return "set"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pre-flight check for Fable Orchestrator v0.6.0 model routing."
    )
    parser.add_argument(
        "--config",
        help="Path to fable-config.yaml (uses defaults if omitted)",
    )
    parser.add_argument(
        "--live-test",
        action="store_true",
        help="Send a tiny prompt to each configured model (costs tokens)",
    )
    args = parser.parse_args()

    hermes_env = load_dotenv()
    routing = load_routing(args.config)
    entries = flatten_entries(routing)

    print("# Fable Orchestrator v0.6.0 \u2014 Model Pre-flight Check\n")

    hermes_ok, hermes_detail = check_hermes_config()
    print(f"Hermes config: {'OK' if hermes_ok else 'FAIL'} \u2014 {hermes_detail}\n")

    print(f"{'Stage':<12} {'Level':<10} {'Model':<30} {'Provider':<14} {'Key':<8} {'Status'}")
    print("-" * 95)

    all_ok = hermes_ok
    for entry in entries:
        env_ok = provider_env_set(entry["provider"], hermes_env)
        status = "OK" if env_ok else "FAIL"
        if not env_ok:
            all_ok = False
        env_var = PROVIDER_ENV.get(entry["provider"], "unknown")
        key_status = "OK" if env_ok else "MISSING"
        print(
            f"{entry['stage']:<12} {entry['level']:<10} {entry['model']:<30} "
            f"{entry['provider']:<14} {key_status:<8} {status}"
        )
        if not env_ok:
            print(f"  \u2192 {env_var} not set")

    if args.live_test:
        print("\n# Live model tests (costs tokens)\n")
        for entry in entries:
            if not provider_env_set(entry["provider"], hermes_env):
                print(f"{entry['stage']}:{entry['level']} \u2014 skipped (provider not configured)")
                continue
            test_ok, test_detail = live_test_model(entry["model"], entry["provider"])
            status = "OK" if test_ok else "FAIL"
            if not test_ok:
                all_ok = False
            print(
                f"{entry['stage']:<12} {entry['level']:<10} {entry['model']:<30} "
                f"{status} \u2014 {test_detail[:60]}"
            )

    print()
    if all_ok:
        print("All checks passed. You can run Fable Orchestrator v0.6.0.")
        return 0
    print("Some checks failed. Fix the issues above before running Fable.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
