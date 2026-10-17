# Reproduction package — Preregistered validity audit of Sherpa's student simulator

One-command re-verification of the results in *"No Learning Under This Protocol:
A Preregistered Validity Audit of a Downsized Frozen-Student Replication of
Sherpa's Simulator"* (manuscript prepared for the *Journal of Educational
Data Mining*).

**Author:** Prabhu Rangaraju

## One command

```bash
bash reproduce.sh
```

## What it does

1. Installs Python dependencies (`requirements.txt`; numpy/scipy/matplotlib).
2. Recomputes all preregistered metrics from the banked artifacts
   (`scripts/recompute_metrics.py`): 300 simulated episodes plus 5,000 real
   ASSISTments sequences, 24 two-sample KS tests with Holm–Bonferroni
   correction, bootstrap confidence intervals — implemented directly from the
   locked preregistration (`PREREGISTRATION.md`, §6–§7).
3. Regenerates every manuscript figure from the raw data
   (`scripts/make_figures.py` → `figures/`).
4. Verifies every headline number against `expected/headline_numbers.json`
   (`scripts/verify_reproduction.py`) and prints PASS/FAIL per check.

Expected runtime: ~2 minutes on a modern laptop. All stochastic steps use
fixed seeds; reruns are deterministic.

## What is verified

- Output completeness: 300/300 episodes (6 archetypes × 50), 5 turns each,
  5,000 real sequences.
- The zero-learning headline: 297/300 trajectories frozen at baseline;
  mean correctness 0.347 → 0.343.
- All 24 preregistered KS tests reject H0 after Holm correction.
- Gate decomposition: 478 accepted / 258 guidance-gate rejects /
  370 adaptive parse-failures / 394 reasoned rejects.
- Teacher boxed-answer leaks: 141 messages, 32 accepted, 23 episodes,
  0 probes improved.
- No dose–response (r = −0.04); 62 episodes with zero accepted turns.
- Probe stochasticity: generations varied in 54/62 zero-accepted episodes,
  verdicts flipped in 1.
- Real learning-curve endpoints: 0.499 → 0.688.

## Scope note

This package re-verifies the *analysis* from the banked artifacts. Re-running
trajectory generation itself requires the Qwen3-1.7B GGUF model and roughly
30 CPU-hours; the generation code (`code/gen_trajectories.py` in the paper's
project archive) and per-generation seeds are preserved for inspection, and
every trajectory in `data/trajectories.jsonl` carries its seed.

## Contents

- `PREREGISTRATION.md` — the locked preregistration (2026-10-08) with the
  §12 deviation log.
- `data/trajectories.jsonl` — 300 banked episodes (6 archetypes × 50 ×
  5 turns), seeds logged per generation.
- `data/real_pool.json` — 5,000 seeded real (student, skill) sequences from
  the ASSISTments 2009–2010 skill-builder data.
- `scripts/` — metric recomputation, figure generation, headline verifier.
- `expected/headline_numbers.json` — the numbers the paper reports.
- `paper/` — the manuscript PDF and LaTeX source. The JEDM submission artifact
  is `paper-jedm.pdf` (official JEDM template, 14 pages); `paper.pdf` is
  byte-identical to it. `paper.tex` is the earlier article-class source.

## Data provenance and licenses

- ASSISTments 2009–2010 skill-builder data: free to use for research
  (see the paper's references; `data/real_pool.json` is a derived,
  seeded 5,000-sequence sample).
- Sherpa upstream repository (prompts/templates replicated): Apache-2.0.
- MATH problems (the paper's shipped filtered test split): MIT license.
- This package (scripts, text): MIT license — see `LICENSE`.
