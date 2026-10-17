"""Verifier for the S9 reproduction package.

Author: Prabhu Rangaraju.

Recomputes every headline number of the paper from the bundled artifacts
(data/trajectories.jsonl, data/real_pool.json) and checks them against
expected/headline_numbers.json. Prints PASS/FAIL per check and exits
nonzero if any check fails.

Usage: python3 scripts/verify_reproduction.py   (run from the package root)
"""
import json
import math
import os
import sys

import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAJ = os.path.join(ROOT, "data", "trajectories.jsonl")
REAL_POOL = os.path.join(ROOT, "data", "real_pool.json")
EXPECTED = os.path.join(ROOT, "expected", "headline_numbers.json")

ARCHETYPES = ["attempt-diagnosis", "subgoal-decomposition",
              "contrastive-comparison", "causal-justification",
              "step-demonstration", "independent-verification"]

CHECKS = []


def check(name, actual, expected, tol=0.0):
    """Record a PASS/FAIL check. tol is absolute tolerance (0 = exact)."""
    if isinstance(expected, float) or tol:
        ok = abs(actual - expected) <= tol
    else:
        ok = actual == expected
    CHECKS.append((name, ok, actual, expected))
    return ok


def main():
    eps = [json.loads(l) for l in open(TRAJ) if l.strip()]
    real = json.load(open(REAL_POOL))
    exp = json.load(open(EXPECTED))

    # --- output completeness ---
    check("n_episodes", len(eps), exp["n_episodes"])
    check("n_archetypes", len({e["archetype"] for e in eps}), 6)
    for a in ARCHETYPES:
        check(f"n_{a}", sum(1 for e in eps if e["archetype"] == a), 50)
    check("all_turns_complete",
          all(len(e["turns"]) == 5 and len(e["c"]) == 6 for e in eps), True)
    check("n_real_sequences", len(real), 5000)

    # --- headline 1: zero learning ---
    frozen = sum(1 for e in eps if len(set(e["c"])) == 1)
    check("frozen_trajectories", frozen, exp["frozen_trajectories"])
    c0 = np.mean([e["c"][0] for e in eps])
    c5 = np.mean([e["c"][5] for e in eps])
    check("mean_c0", round(c0, 3), exp["mean_c0"], tol=0.001)
    check("mean_c5", round(c5, 3), exp["mean_c5"], tol=0.001)

    # --- headline 2: 24/24 KS tests reject (Holm) ---
    def m1(o):
        t = np.arange(1, 6)
        e = (1.0 - np.asarray(o, float)) * 0.9 + 0.05
        x, y = np.log(t), np.log(e)
        return float(np.sum((x - x.mean()) * (y - y.mean()))
                     / np.sum((x - x.mean()) ** 2))

    def m2a(o):
        errs = (np.asarray(o) == 0).astype(int)
        E = sum(1 for t in range(4) if errs[t] and errs[t + 1])
        N = int(errs[:4].sum())
        return (E + 1) / (N + 2) if N else None

    def m2b(o):
        best = cur = 0
        for v in o:
            cur = cur + 1 if v == 0 else 0
            best = max(best, cur)
        return best

    def m3s(c, turns):
        acc = [t["outcome"] == "accepted" for t in turns]
        a = [p for p, g in zip(c[1:6], acc) if g]
        r = [p for p, g in zip(c[1:6], acc) if not g]
        return float(np.mean(a) - np.mean(r)) if a and r else None

    def m3r(r, h):
        a = [r[t + 1] for t in range(4) if h[t] == 1]
        b = [r[t + 1] for t in range(4) if h[t] == 0]
        return float(np.mean(a) - np.mean(b)) if a and b else None

    sim_m = {a: {"m1": [], "m2a": [], "m2b": [], "m3": []}
             for a in ARCHETYPES}
    for e in eps:
        o = e["c"][1:6]
        d = sim_m[e["archetype"]]
        d["m1"].append(m1(o))
        v = m2a(o)
        if v is not None:
            d["m2a"].append(v)
        d["m2b"].append(m2b(o))
        v = m3s(e["c"], e["turns"])
        if v is not None:
            d["m3"].append(v)
    real_m = {"m1": [], "m2a": [], "m2b": [], "m3": []}
    for s in real:
        real_m["m1"].append(m1(s["r"]))
        v = m2a(s["r"])
        if v is not None:
            real_m["m2a"].append(v)
        real_m["m2b"].append(m2b(s["r"]))
        v = m3r(s["r"], s["h"])
        if v is not None:
            real_m["m3"].append(v)

    pvals = []
    for a in ARCHETYPES:
        for m in ("m1", "m2a", "m2b", "m3"):
            _, p = stats.ks_2samp(sim_m[a][m], real_m[m])
            pvals.append(p)
    order = np.argsort(pvals)
    adj = np.empty(len(pvals))
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (len(pvals) - rank) * pvals[i])
        adj[i] = min(run, 1.0)
    n_reject = int(np.sum(adj < 0.05))
    check("ks_reject_holm", n_reject, exp["ks_reject_holm"])

    # --- headline 3: gate decomposition ---
    n_acc = n_gg = n_parse = n_reas = 0
    for e in eps:
        for t in e["turns"]:
            o = t["outcome"]
            if o == "accepted":
                n_acc += 1
            elif "guidance" in o:
                n_gg += 1
            elif (t.get("adaptive_gate") or {}).get("parse_error"):
                n_parse += 1
            else:
                n_reas += 1
    check("gate_accepted", n_acc, exp["gate_accepted"])
    check("gate_guidance_reject", n_gg, exp["gate_guidance_reject"])
    check("gate_parse_fail", n_parse, exp["gate_parse_fail"])
    check("gate_reasoned_reject", n_reas, exp["gate_reasoned_reject"])
    check("parse_share_of_adaptive",
          round(n_parse / (n_parse + n_reas), 3),
          exp["parse_share_of_adaptive"], tol=0.002)

    # --- headline 4: boxed answers ---
    n_boxed = sum(1 for e in eps for t in e["turns"]
                  if "\\boxed{" in t["teacher_message"])
    check("teacher_boxed_messages", n_boxed, exp["teacher_boxed_messages"])
    eps_with_acc_boxed = 0
    improved_with_boxed = 0
    for e in eps:
        boxed_acc = any("\\boxed{" in t["teacher_message"]
                        and t["outcome"] == "accepted" for t in e["turns"])
        if boxed_acc:
            eps_with_acc_boxed += 1
            if e["c"][5] > e["c"][0]:
                improved_with_boxed += 1
    check("episodes_accepted_boxed", eps_with_acc_boxed,
          exp["episodes_accepted_boxed"])
    check("improved_with_accepted_boxed", improved_with_boxed, 0)

    # --- headline 5: dose-response ---
    n_acc_ep = np.array([sum(1 for t in e["turns"]
                             if t["outcome"] == "accepted") for e in eps])
    delta = np.array([e["c"][5] - e["c"][0] for e in eps])
    r = float(np.corrcoef(n_acc_ep, delta)[0, 1])
    check("dose_response_r", round(r, 2), exp["dose_response_r"], tol=0.02)
    check("mean_accepted_per_episode", round(float(n_acc_ep.mean()), 2),
          exp["mean_accepted_per_episode"], tol=0.02)
    check("episodes_zero_accepted", int(np.sum(n_acc_ep == 0)),
          exp["episodes_zero_accepted"])

    # --- headline 6: probe stochasticity ---
    zero_acc = [e for e in eps if all(t["outcome"] != "accepted"
                                      for t in e["turns"])]
    varied = sum(1 for e in zero_acc
                 if len({t["probe"]["output"]
                         for t in e["turns"]} | {e["baseline_probe"]["output"]})
                 > 1)
    flips = sum(1 for e in zero_acc if len(set(e["c"])) > 1)
    check("zero_accepted_episodes", len(zero_acc),
          exp["episodes_zero_accepted"])
    check("probe_generations_varied", varied, exp["probe_generations_varied"])
    check("probe_verdict_flips", flips, exp["probe_verdict_flips"])

    # --- real learning curve endpoints ---
    rm = np.array([s["r"] for s in real], float).mean(axis=0)
    check("real_curve_start", round(float(rm[0]), 3),
          exp["real_curve_start"], tol=0.002)
    check("real_curve_end", round(float(rm[-1]), 3),
          exp["real_curve_end"], tol=0.002)

    # --- report ---
    fails = [c for c in CHECKS if not c[1]]
    for name, ok, actual, expected in CHECKS:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: got {actual}, "
              f"expected {expected}")
    print(f"\n{len(CHECKS) - len(fails)}/{len(CHECKS)} checks passed.")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
