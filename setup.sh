#!/usr/bin/env bash
# Fable Orchestrator v0.6.0 — one-click setup for non-technical users.
# This script installs the skill and runs a pre-flight provider check.

set -e

echo "Fable Orchestrator v0.6.0 Setup"
echo "============================"
echo

# Check Hermes is installed.
if ! command -v hermes &> /dev/null; then
    echo "Error: hermes command not found."
    echo "Please install Hermes Agent first: https://hermes-agent.nousresearch.com/docs"
    exit 1
fi

echo "Hermes found: $(hermes version 2>/dev/null | head -1 || true)"
echo

# Install the skill from the local SKILL.md.
echo "Installing Fable Orchestrator skill..."
hermes skills install ./SKILL.md
echo

# Run pre-flight check.
echo "Running pre-flight model check..."
python3 scripts/verify_models.py
