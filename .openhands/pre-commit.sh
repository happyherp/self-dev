#!/bin/bash
# Pre-commit hook for OpenHands
# This script is called by the git pre-commit hook installed by OpenHands

set -e

# Run the OpenHands-specific pre-commit checks
make run-pre-commit_for-openhands