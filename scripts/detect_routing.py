#!/usr/bin/env python3
"""Detect whether native per-call model routing is available in delegate_task.

Exits 0 if native routing is available (delegate_task accepts a model param).
Exits 1 if native routing is NOT available (config cycling is required).

Usage:
    python3 scripts/detect_routing.py
"""

from __future__ import annotations

import json
import subprocess
import sys


def check_native_routing() -> bool:
    """Check if delegate_task supports a model parameter.

    Attempts to detect native per-call model routing by:
    1. Checking if the running Hermes exposes delegate_task with a 'model'
       parameter in its tool schema.
    """
    try:
        result = subprocess.run(
            ["hermes", "tools", "delegate_task", "--schema"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return False

        schema_text = result.stdout
        import re
        # Look for 'model' as a top-level parameter key in the schema JSON
        if '"model"' in schema_text or "'model'" in schema_text:
            return True
        # Also check if it appears as a property key
        if re.search(r'["\']model["\']\s*:', schema_text):
            return True
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    except Exception:
        return False


def main() -> int:
    native = check_native_routing()

    if native:
        print(json.dumps({
            "native_routing": True,
        }))
        return 0

    print(json.dumps({
        "native_routing": False,
        "method": "config_cycling",
    }))
    return 1


if __name__ == "__main__":
    sys.exit(main())
