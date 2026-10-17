"""Regenerate all S9 manuscript figures from raw artifacts.

Reads results/trajectories.jsonl (300 episodes) and analysis/real_pool.json
(5,000 real sequences). Writes paper/figures/*.png. No mock data; every
plotted value is computed from the banked artifacts.

Author: Prabhu Rangaraju.
"""
import json
import numpy as np
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ARCH_SHORT = {
    "attempt-diagnosis": "Att.",
    "subgoal-decomposition": "Sub.",
    "contrastive-comparison": "Ctr.",
    "causal-justification": "Cau.",
    "step-demonstration": "Stp.",
    "independent-verification": "Ver.",
}
ARCH_ORDER = list(ARCH_SHORT)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGDIR = os.path.join(ROOT, "figures")
os.makedirs(FIGDIR, exist_ok=True)


def load():
    eps = [json.loads(l) for l in open(os.path.join(ROOT, "data", "trajectories.jsonl"))
           if l.strip()]
    real = json.load(open(os.path.join(ROOT, "data", "real_pool.json")))
    return eps, real


def fig_learning_curves(eps, real, path):
    """Mean correctness by probe position (sim) / opportunity (real), +-SE."""
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    xs = np.arange(6)
    for a in ARCH_ORDER:
        mat = np.array([e["c"] for e in eps if e["archetype"] == a],
                       dtype=float)
        m = mat.mean(axis=0)
        se = mat.std(axis=0, ddof=1) / np.sqrt(len(mat))
        ax.errorbar(xs, m, yerr=se, marker="o", ms=4, lw=1.4,
                    label=ARCH_SHORT[a], capsize=2)
    rmat = np.array([s["r"] for s in real], dtype=float)
    # real opportunities r_1..r_5 plotted at x=1..5; prepend mean at x=0 n/a
    rm = rmat.mean(axis=0)
    rse = rmat.std(axis=0, ddof=1) / np.sqrt(len(rmat))
    ax.errorbar(xs[1:], rm, yerr=rse, marker="s", ms=5, lw=2.0,
                color="black", label="Real (ASSISTments)", capsize=2)
    ax.set_xlim(-0.2, 5.2)
    ax.set_ylim(0, 1.0)
    ax.set_xticks(xs)
    ax.set_xticklabels(["c0 (baseline)"] + [f"c{i}" for i in range(1, 6)])
    ax.set_xlabel("Probe position (simulated) / opportunity (real)")
    ax.set_ylabel("Mean correctness")
    ax.set_title("Learning curves: simulated vs real students")
    ax.legend(ncol=4, fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def fig_gate_decomp(eps, path):
    """Stacked bars of turn outcomes per archetype."""
    cats = ["accepted", "rejected_guidance_gate",
            "rejected_adaptive_parse", "rejected_adaptive_reasoned"]
    labels = {"accepted": "accepted",
              "rejected_guidance_gate": "guidance-gate reject",
              "rejected_adaptive_parse": "adaptive reject (parse failure)",
              "rejected_adaptive_reasoned": "adaptive reject (reasoned)"}
    colors = {"accepted": "#2ca02c",
              "rejected_guidance_gate": "#ff7f0e",
              "rejected_adaptive_parse": "#d62728",
              "rejected_adaptive_reasoned": "#1f77b4"}
    counts = {a: {c: 0 for c in cats} for a in ARCH_ORDER}
    for e in eps:
        for t in e["turns"]:
            o = t["outcome"]
            ag = t.get("adaptive_gate") or {}
            if o == "accepted":
                counts[e["archetype"]]["accepted"] += 1
            elif "guidance" in o:
                counts[e["archetype"]]["rejected_guidance_gate"] += 1
            elif "adaptive" in o:
                # parse failure = explicit fail-closed parse_error flag
                # (aligns 1:1 with empty reason text)
                if ag.get("parse_error"):
                    counts[e["archetype"]]["rejected_adaptive_parse"] += 1
                else:
                    counts[e["archetype"]]["rejected_adaptive_reasoned"] += 1
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    x = np.arange(len(ARCH_ORDER))
    bottom = np.zeros(len(ARCH_ORDER))
    for c in cats:
        vals = np.array([counts[a][c] for a in ARCH_ORDER])
        ax.bar(x, vals, bottom=bottom, label=labels[c], color=colors[c])
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels([ARCH_SHORT[a] for a in ARCH_ORDER])
    ax.set_ylabel("Teacher turns (250 per archetype)")
    ax.set_title("Gate-pipeline outcomes per archetype")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def fig_dose_response(eps, path):
    """Mean change in probe correctness by accepted turns per episode."""
    deltas = {}
    for e in eps:
        n_acc = sum(1 for t in e["turns"] if t["outcome"] == "accepted")
        d = e["c"][5] - e["c"][0]
        deltas.setdefault(n_acc, []).append(d)
    xs = sorted(deltas)
    m = [np.mean(deltas[x]) for x in xs]
    se = [np.std(deltas[x], ddof=1) / np.sqrt(len(deltas[x])) for x in xs]
    n = [len(deltas[x]) for x in xs]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.errorbar(xs, m, yerr=se, marker="o", ms=6, lw=1.6, capsize=3,
                color="#1f77b4")
    for x, nn in zip(xs, n):
        ax.text(x, 0.035, f"n={nn}", ha="center", fontsize=7, color="gray")
    ax.axhline(0, color="gray", lw=0.8, ls="--")
    ax.set_xlabel("Accepted tutoring turns per episode")
    ax.set_ylabel("Mean change in probe correctness (c5 - c0)")
    ax.set_title("Dose-response: accepted tutoring vs probe improvement")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    eps, real = load()
    fig_learning_curves(eps, real, os.path.join(FIGDIR, "fig_learning_curves.png"))
    fig_gate_decomp(eps, os.path.join(FIGDIR, "fig_gate_decomp.png"))
    fig_dose_response(eps, os.path.join(FIGDIR, "fig_dose_response.png"))
    print("figures written to " + FIGDIR)


if __name__ == "__main__":
    main()
