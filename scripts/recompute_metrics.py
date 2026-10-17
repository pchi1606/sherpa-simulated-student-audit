"""Clean-room recomputation of S9 audit metrics from preregistration definitions.

Author: Prabhu Rangaraju.


Implements PREREGISTRATION.md Section 6 (Metrics) and Section 7 (Statistical
tests) EXACTLY, from raw artifacts only:
  - results/trajectories.jsonl (300 simulated episodes)
  - analysis/real_pool.json (5,000 real (user, skill) sequences)

Outputs analysis/cleanroom_metrics.json for diffing against the banked
analysis/*.json files. Written independently of the original analysis code
(which was not archived), directly from the locked preregistration text.
"""
import json
import math
import os
import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAJ = os.path.join(ROOT, "data", "trajectories.jsonl")
REAL_POOL = os.path.join(ROOT, "data", "real_pool.json")
OUT = os.path.join(ROOT, "expected", "recomputed_metrics.json")

RNG = np.random.default_rng(20261008)  # preregistered bootstrap seed
DELTA = 0.05  # preregistered smoothing constant
ARCHETYPES = ["attempt-diagnosis", "subgoal-decomposition",
              "contrastive-comparison", "causal-justification",
              "step-demonstration", "independent-verification"]


def m1_slope(outcomes):
    """M1: OLS slope of log(e_t) on log(t), e_t = (1-o_t)*(1-2d)+d, t=1..5."""
    t = np.arange(1, 6)
    e = (1.0 - np.asarray(outcomes, dtype=float)) * (1.0 - 2 * DELTA) + DELTA
    x = np.log(t)
    y = np.log(e)
    # closed-form OLS slope
    slope = np.sum((x - x.mean()) * (y - y.mean())) / np.sum((x - x.mean()) ** 2)
    return float(slope)


def m2a_persistence(outcomes):
    """M2a: Laplace-smoothed P(err_{t+1}|err_t), pairs t=1..4. None if N=0."""
    errs = (np.asarray(outcomes) == 0).astype(int)
    E = sum(1 for t in range(4) if errs[t] == 1 and errs[t + 1] == 1)
    N = sum(1 for t in range(4) if errs[t] == 1)
    if N == 0:
        return None
    return (E + 1) / (N + 2)


def m2b_max_streak(outcomes):
    """M2b: longest run of consecutive errors (0 if none)."""
    best = cur = 0
    for o in outcomes:
        cur = cur + 1 if o == 0 else 0
        best = max(best, cur)
    return best


def m3_sim(c, turns):
    """M3 sim: mean(c_t|g_t=1) - mean(c_t|g_t=0). None if all acc/all rej."""
    acc = [turns[t]["outcome"] == "accepted" for t in range(5)]
    probes = c[1:6]
    a = [p for p, g in zip(probes, acc) if g]
    r = [p for p, g in zip(probes, acc) if not g]
    if not a or not r:
        return None
    return float(np.mean(a) - np.mean(r))


def m3_real(r, h):
    """M3 real: mean(r_{t+1}|h_t=1) - mean(r_{t+1}|h_t=0), t=1..4."""
    a = [r[t + 1] for t in range(4) if h[t] == 1]
    b = [r[t + 1] for t in range(4) if h[t] == 0]
    if not a or not b:
        return None
    return float(np.mean(a) - np.mean(b))


def load_trajectories():
    eps = []
    with open(TRAJ) as f:
        for line in f:
            line = line.strip()
            if line:
                eps.append(json.loads(line))
    return eps


def holm_bonferroni(pvals):
    """Holm-Bonferroni adjusted p-values."""
    m = len(pvals)
    order = np.argsort(pvals)
    adj = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * pvals[idx])
        adj[idx] = min(running, 1.0)
    return adj


def main():
    eps = load_trajectories()
    assert len(eps) == 300, f"expected 300 episodes, got {len(eps)}"
    real = json.load(open(REAL_POOL))
    assert len(real) == 5000, f"expected 5000 real sequences, got {len(real)}"

    # --- per-episode metrics ---
    sim = {a: {"m1": [], "m2a": [], "m2b": [], "m3": [],
               "m2a_excl": 0, "m3_excl": 0, "n": 0} for a in ARCHETYPES}
    for ep in eps:
        a = ep["archetype"]
        c = ep["c"]
        assert len(c) == 6 and all(v in (0, 1) for v in c)
        turns = ep["turns"]
        assert len(turns) == 5
        outcomes = c[1:6]
        d = sim[a]
        d["n"] += 1
        d["m1"].append(m1_slope(outcomes))
        v = m2a_persistence(outcomes)
        if v is None:
            d["m2a_excl"] += 1
        else:
            d["m2a"].append(v)
        d["m2b"].append(m2b_max_streak(outcomes))
        v = m3_sim(c, turns)
        if v is None:
            d["m3_excl"] += 1
        else:
            d["m3"].append(v)

    real_m = {"m1": [], "m2a": [], "m2b": [], "m3": [],
              "m2a_excl": 0, "m3_excl": 0}
    for seq in real:
        r, h = seq["r"], seq["h"]
        real_m["m1"].append(m1_slope(r))
        v = m2a_persistence(r)
        if v is None:
            real_m["m2a_excl"] += 1
        else:
            real_m["m2a"].append(v)
        real_m["m2b"].append(m2b_max_streak(r))
        v = m3_real(r, h)
        if v is None:
            real_m["m3_excl"] += 1
        else:
            real_m["m3"].append(v)

    # --- 24 KS tests + Holm + bootstrap CI for median difference ---
    tests = []
    for a in ARCHETYPES:
        for metric in ["m1", "m2a", "m2b", "m3"]:
            xs = np.array(sim[a][metric])
            ys = np.array(real_m[metric])
            D, p = stats.ks_2samp(xs, ys)
            tests.append({"arch": a, "metric": metric, "D": float(D),
                          "p_raw": float(p), "n_sim": int(len(xs)),
                          "n_real": int(len(ys))})
    adj = holm_bonferroni([t["p_raw"] for t in tests])
    for t, p in zip(tests, adj):
        t["p_holm"] = float(p)
        # bootstrap CI for median difference (sim - real), 10k resamples
        xs = np.array(sim[t["arch"]][t["metric"]])
        ys = np.array(real_m[t["metric"]])
        diffs = []
        for _ in range(10000):
            diffs.append(np.median(RNG.choice(xs, len(xs), replace=True))
                         - np.median(RNG.choice(ys, len(ys), replace=True)))
        lo, hi = np.percentile(diffs, [2.5, 97.5])
        t["median_diff_ci"] = [float(lo), float(hi)]

    out = {
        "sim": {a: {k: (float(np.mean(v)) if v else None,
                        float(np.std(v, ddof=0)) if v else None,
                        float(np.median(v)) if v else None)
                    for k, v in d.items() if k in ("m1", "m2a", "m2b", "m3")}
                for a, d in sim.items()},
        "sim_n": {a: {"n": d["n"], "m2a_excl": d["m2a_excl"],
                      "m3_excl": d["m3_excl"]} for a, d in sim.items()},
        "real": {k: (float(np.mean(v)), float(np.std(v, ddof=0)),
                     float(np.median(v))) for k, v in real_m.items()
                 if k in ("m1", "m2a", "m2b", "m3")},
        "real_excl": {"m2a_excl": real_m["m2a_excl"],
                      "m3_excl": real_m["m3_excl"]},
        "ks_tests": tests,
        "n_reject_holm": sum(1 for t in tests if t["p_holm"] < 0.05),
    }
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)

    # --- headline sanity prints ---
    print("episodes:", len(eps))
    print("KS rejects (Holm, a=0.05):", out["n_reject_holm"], "/ 24")
    print("real exclusions:", out["real_excl"])
    for a in ARCHETYPES:
        print(a, {k: [round(x, 4) if x is not None else None for x in v]
                  for k, v in out["sim"][a].items()})
    print("real:", {k: [round(x, 4) for x in v]
                    for k, v in out["real"].items()})


if __name__ == "__main__":
    main()
