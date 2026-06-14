#!/usr/bin/env python3
"""
Verify model availability before running the fable orchestrator.

Usage:
    python3 verify_models.py

Checks each model in the routing table by attempting a lightweight hermes call.
Reports which models are available and which are not.
"""

import subprocess
import sys

ROUTING_TABLE = {
    "research": {
        "primary":   {"model": "deepseek-v4-flash", "provider": "opencode-go"},
        "secondary": {"model": "gemini-2.5-flash-lite", "provider": "google"},
        "tertiary":  {"model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "provider": "openrouter"},
    },
    "plan": {
        "primary":   {"model": "glm-5.1", "provider": "opencode-go"},
        "secondary": {"model": "gemini-2.5-pro", "provider": "google"},
        "tertiary":  {"model": "deepseek-v4-pro", "provider": "opencode-go"},
    },
    "implement": {
        "primary":   {"model": "kimi-k2.7-code", "provider": "opencode-go"},
        "secondary": {"model": "kimi-k2.6", "provider": "opencode-go"},
        "tertiary":  {"model": "gemini-2.5-pro", "provider": "google"},
    },
    "verify": {
        "primary":   {"model": "deepseek-v4-pro", "provider": "opencode-go"},
        "secondary": {"model": "gemini-2.5-pro", "provider": "google"},
        "tertiary":  {"model": "kimi-k2.6", "provider": "opencode-go"},
    },
    "critique": {
        "primary":   {"model": "glm-5.1", "provider": "opencode-go"},
        "secondary": {"model": "gemini-2.5-pro", "provider": "google"},
        "tertiary":  {"model": "kimi-k2.6", "provider": "opencode-go"},
    },
}

def check_model(model: str, provider: str) -> bool:
    """Check if a model is available by running a lightweight hermes call."""
    cmd = [
        "hermes", "chat", "-q", "Say 'ok' and nothing else.",
        "-m", model,
        "--provider", provider,
        "-Q",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0 and "ok" in result.stdout.lower()
    except Exception:
        return False


def main():
    print("Fable Orchestrator Model Availability Check")
    print("=" * 60)
    
    all_available = True
    
    for stage, tiers in ROUTING_TABLE.items():
        print(f"\nStage: {stage}")
        for tier, cfg in tiers.items():
            model = cfg["model"]
            provider = cfg["provider"]
            available = check_model(model, provider)
            status = "✓ AVAILABLE" if available else "✗ UNAVAILABLE"
            print(f"  [{tier:10s}] {provider}/{model} -> {status}")
            if not available:
                all_available = False
    
    print("\n" + "=" * 60)
    if all_available:
        print("All models available. Ready to run fable orchestrator.")
    else:
        print("Some models unavailable. Check config and API keys.")
    
    return 0 if all_available else 1


if __name__ == "__main__":
    sys.exit(main())
