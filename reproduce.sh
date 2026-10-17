#!/usr/bin/env bash
# Author: Prabhu Rangaraju
# One-command reproduction of the S9 Sherpa student-simulator audit analysis.
#
# Usage:  bash reproduce.sh
# Run from this directory. Requires Python 3.10+ and pip.
#
# What it does:
#   1. installs Python dependencies (requirements.txt)
#   2. recomputes all preregistered metrics from the banked artifacts
#      (scripts/recompute_metrics.py: 300 episodes + 5,000 real sequences,
#      24 KS tests with Holm-Bonferroni, bootstrap CIs)
#   3. regenerates every manuscript figure from the raw data
#      (scripts/make_figures.py -> figures/)
#   4. verifies every headline number against expected/headline_numbers.json
#      (scripts/verify_reproduction.py) and reports PASS/FAIL
#
# What it does NOT do: re-run trajectory generation. Generating the 300
# episodes requires the Qwen3-1.7B model and ~30 CPU-hours; the banked
# trajectories (data/trajectories.jsonl, seeds logged per generation) are
# the audited artifacts, and this package re-verifies every number the
# paper reports from them. The generation code is archived alongside the
# paper for inspection.
#
# Expected runtime: ~2 minutes on a modern laptop.
set -euo pipefail
cd "$(dirname "$0")"

echo "================================================================"
echo " STEP 1/4: dependencies"
echo "================================================================"
pip install -r requirements.txt || echo "WARNING: pip install failed; continuing with installed dependencies."

echo "================================================================"
echo " STEP 2/4: recompute preregistered metrics from banked artifacts"
echo "================================================================"
python3 scripts/recompute_metrics.py

echo "================================================================"
echo " STEP 3/4: regenerate manuscript figures"
echo "================================================================"
python3 scripts/make_figures.py

echo "================================================================"
echo " STEP 4/4: verify headline numbers"
echo "================================================================"
python3 scripts/verify_reproduction.py
