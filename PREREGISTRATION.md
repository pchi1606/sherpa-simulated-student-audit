# PREREGISTRATION — Sherpa Simulated-Student Validity Audit (S9)

**Status:** LOCKED 2026-10-08, before any study trajectory is generated.
**Scope:** Phase A only. No trajectory generation, no real-data analysis beyond
schema inspection, nothing submitted anywhere.

## 1. Study question

Do Sherpa's archetype-conditioned LLM simulated students (arXiv:2610.08778)
reproduce real student learning dynamics? We replicate ONLY the student side:
frozen Qwen3-1.7B + the paper's gating mechanism, generating short student
trajectories under a fixed-strategy teacher. We compare behavioral statistics
of simulated trajectories against matched real-student trajectories from the
ASSISTments 2009–2010 skill-builder dataset.

- **H1 (research hypothesis):** Simulated students differ measurably from real
  students on at least one of: (M1) learning-curve shape (power-law exponent),
  (M2) error persistence, (M3) hint responsiveness.
- **H0 (null):** No significant distributional difference on any preregistered
  metric (all two-sample KS tests fail to reject after multiple-comparison
  correction).

No directional prediction is preregistered (two-sided tests); the sign of any
difference is reported descriptively.

## 2. Materials (provenance — filled in §9, recorded before generation)

- Paper: arXiv:2610.08778, PDF docs/sherpa-2610.08778.pdf (downloaded 2026-10-08).
- Repo: https://github.com/SALT-NLP/Sherpa @
  23e2a47c2c84fe59a087258a29d931b801a72fd5 (Apache-2.0). Student-side files
  copied verbatim to docs/upstream-student-side/.
- Student backbone: Qwen3-1.7B, GGUF Q4_K_M (source + sha256 in §9).
- Problems: the paper's shipped filtered MATH test split
  (code/sherpa-upstream/examples/sherpa/data/math_1.7b_8b/math_filtered.test.jsonl,
  528 problems). This is the paper's own filter (student fails unaided,
  teacher can solve) — the exact setting the archetypes were designed for.
- Real data: ASSISTments 2009–2010 skill-builder data (free to use; citation
  links the official data page), provenance in docs/data-provenance.md.

## 3. Archetypes (verbatim — see docs/archetypes-verbatim.md)

Six preference archetypes, each = frozen Qwen3-1.7B with system message
"You are Sam, a student talking with a teacher." + ONE adaptive gate
(preference text verbatim from Appendix D.1.2 / prompt_pools/preference_prompts.json):

1. attempt-diagnosis (Att.) — Attempt diagnosis
2. subgoal-decomposition (Sub.) — Subgoal decomposition
3. contrastive-comparison (Ctr.) — Contrastive comparison
4. causal-justification (Cau.) — Causal justification
5. step-demonstration (Stp.) — Step demonstration
6. independent-verification (Ver.) — Independent verification

The `none` (no-preference) archetype is EXCLUDED from primary hypotheses
(task target is the six gated archetypes); it may be added as an exploratory
extension with its own preregistration note.

## 4. Simulation protocol (locked)

### 4.1 Episode structure (one trajectory)

For archetype A and problem P (from the 528 filtered MATH test problems):

- **t=0 baseline probe:** student context = [system] only (no history); append
  the re-test template ("Now try to solve the problem from scratch:\n{task}\n\n
  Put your final answer in \\boxed{}."); generate; grade → c_0 ∈ {0,1}.
  (Mirrors the paper's no-teaching baseline p(x,z,C0S).)
- **Turns t=1..5:**
  1. Teacher (fixed-strategy stand-in, §4.2) produces instruction a_t given
     dialogue history.
  2. Guidance gate judges a_t (verbatim GUIDANCE_GATE_SYSTEM_PROMPT/USER_TEMPLATE;
     judge model per §4.3; pre-screen optimization per §4.6). If leaked=true → turn rejected.
  3. Adaptive gate judges a_t against A's preference (verbatim ADAPTIVE_GATE
     prompts; up to 3 retries on parse failure, fail-closed per repo). If
     FAIL → turn rejected.
  4. If rejected: student emits the scripted reply (guidance-gate failure:
     “Don’t directly show me the answer.” — paper §2.2; adaptive-gate failure:
     one complaint drawn from preference_complaints.json via
     random.Random(f"20261008:complaint:{problem_id}:{t}").choice(pool)).
     The rejected exchange NEVER enters the student-visible history (repo
     _turn_hidden_from_student); it is recorded in the teacher-visible log.
  5. If accepted: student backbone generates reply o_t from
     [system, accepted history (assistant=user-role rendering per repo
     _render_conversation), latest teacher output]; append (a_t, o_t) to the
     accepted history.
  6. **Probe branch:** fork [system, accepted history] + re-test template,
     generate, grade → c_t ∈ {0,1}. The probe is NOT appended to the
     conversation (independent branch, as in the paper).
- Trajectory record: (c_0..c_5), per-turn gate outcomes (accepted/rejected +
  which gate), full accepted transcript, all generations with seeds.

### 4.2 Teacher stand-in (fixed-strategy, from paper Appendix D.5.1)

Per episode, the teacher is fixed to the strategy matching the archetype's
preference, using the paper's D.5.1 template verbatim:

> Teaching the student using the following method.
> {strategy}
> No matter what, strictly maintain this teaching method throughout the
> entire conversation. Please do not directly reveal the final answer or an
> equivalent expression.

Strategy texts (verbatim, D.5.1):
- Att.: "Identify a specific correct or incorrect part of the student's
  latest attempt and explain why."
- Cau.: "Explain why a mathematical step holds by applying the relevant
  rule to the problem."
- Sub.: "State the current subgoal, explain how it helps solve the problem,
  and work toward it."
- Stp.: "Perform one mathematical step, show the result, briefly explain it,
  and stop."
- Ver.: "Check the student's latest mathematical answer using a different
  method. Complete the check and explain whether it confirms or refutes
  the answer."
- Ctr.: "Compare two plausible alternatives for the same step and explain
  the key difference."

Teacher call = [system: D.2 teacher system message with turn budget 5,
user: strategy template, then accepted history as user/assistant alternation
(student replies as user)]. The teacher never sees the ground-truth answer.

### 4.3 Generation parameters (locked)

| Call | Model | temp | top_p | top_k | min_p | max_tokens | seed |
|---|---|---|---|---|---|---|---|
| Teacher instruction | Qwen3-1.7B Q4_K_M | 0.7 | 0.8 | 20 | 0 | 256 | episode-seeded |
| Guidance-gate judge | Qwen3-1.7B Q4_K_M | 0.0 | 1.0 | — | — | 128 | episode-seeded |
| Adaptive-gate judge | Qwen3-1.7B Q4_K_M | 0.0 | 1.0 | — | — | 96 | episode-seeded |
| Student reply | Qwen3-1.7B Q4_K_M | 0.7 | 0.8 | 20 | 0 | 384 | episode-seeded |
| Probe (state read-out) | Qwen3-1.7B Q4_K_M | 0.0 | 1.0 | — | — | 192 | episode-seeded |
| Answer judge fallback | Qwen3-1.7B Q4_K_M | 0.0 | 1.0 | — | — | 128 | episode-seeded |

- Quantization: Q4_K_M GGUF (unsloth). Chosen over the task-suggested Q8_0
  after a head-to-head benchmark (logs/bench_quants.json, 2026-10-08):
  Q4_K_M = 7–9 tok/s vs Q8_0 = 5–6 tok/s on this 2-CPU box, with
  qualitatively equivalent outputs on student-reply, gate-judgment, and
  probe prompts (same verdict format, same solution behavior). The audit
  compares behavioral distributions, not exact paper accuracies; Q8_0 is
  retained on disk. See §4.4(6).
- Thinking mode: DISABLED (paper: chat_template_kwargs enable_thinking=false).
  Implementation: append `/no_think` to user messages (Qwen-documented
  switch; smoke test showed the model otherwise emits <think> blocks), then
  strip residual `<think>...</think>` spans from generations in post-processing
  (they are empty with /no_think). Recorded in logs/smoke_test.json.
- Answer grading: repo two-stage — exact math scorer
  (examples/sherpa/core/math.py::score_math_answer) first, then the LLM
  answer-judge (ANSWER_JUDGE_SYSTEM_PROMPT, verbatim) on failure to match.
- Seed scheme: master seed 20261008; per-episode seed =
  hash(master, archetype, problem_id, trajectory_idx); all draws derive from it.
  Gate complaint draws use the repo's task-scoped scheme with our master seed.

### 4.4 Deviations from the paper (logged, justified)

1. **Gate-judge model size:** paper eval used a 27B-class auxiliary judge;
   we use Qwen3-1.7B (CPU-only constraint). Gate prompts/criteria verbatim.
2. **Teacher model:** paper's teacher was Qwen3-8B; we use Qwen3-1.7B as the
   fixed-strategy teacher (CPU-only constraint). Teacher role here is only to
   supply strategy-conditioned instructions, not to demonstrate SOTA teaching.
3. **Teacher temperature:** paper eval config temp 1.0; we use 0.7
   (variance reduction for the audit).
4. **Probe temperature:** paper re-tests used student sampling temp; we use
   greedy (temp 0.0) probes as deterministic state read-outs.
5. **Turn count:** 5 (paper: 10). Justified: ASSISTments matching uses
   5-opportunity trajectories; keeps CPU budget feasible.
6. **Quantization:** paper used full-precision Qwen3-1.7B; we use Q4_K_M GGUF
   (CPU-only constraint). Head-to-head benchmark vs Q8_0 (logs/bench_quants.json):
   1.6× faster (7–9 vs 5–6 tok/s), qualitatively equivalent behavior on
   audit-relevant prompts. The audit tests distributional differences vs real
   students, not exact replication of the paper's accuracies.

### 4.5 Trajectory counts (locked)

- 6 archetypes × 50 trajectories × 5 turns = 300 episodes (1,500 tutoring
  turns, 1,800 probes incl. baselines).
- Problem sampling: 50 problems per archetype drawn WITHOUT replacement from
  the 528 filtered MATH test problems; disjoint across archetypes
  (300 unique problems); seed 20261008.
- Estimated generations/episode: 5 teacher + 10 gate + 5 student + 6 probe
  ≈ 26 → ≈ 7,800 generations total (plus answer-judge fallbacks).
- Estimated wall time: ≈ 2,800 tokens/episode at measured 7–9 tok/s ≈
  6 min/episode → ≈ 30 hours for 300 episodes. Phase B must run chunked
  (e.g., 6 archetype batches) as extended background work.

### 4.6 Guidance-gate cost optimization (locked)

The LLM guidance-gate judge is invoked ONLY when a cheap pre-screen finds
numeric content in the teacher message that could match the ground truth
(normalized exact containment, same criterion as the gate). The teacher is
explicitly instructed not to reveal the answer (D.5.1 template), so the
pre-screen is expected to pass through nearly all messages without an LLM
call. When the pre-screen fires, the verbatim LLM gate prompt is used.
This preserves the gate's semantics while removing ~5 LLM calls/episode.

## 5. Real-data matching procedure (locked)

- Source: ASSISTments 2009–2010 skill-builder CSV (official "free to use").
- Unit: (user_id, skill_id) sequences. Filters: original==1 (main problems
  only; scaffolding sub-steps excluded), tutor_mode=='tutor'. Order by
  order_id (chronological). Sequence index 1..k = row order within the unit.
- Keep sequences with k ≥ 5; analyze the FIRST 5 opportunities
  (length-matched to the 5-turn simulated trajectories).
- correct ∈ {0,1} as shipped (1 = correct on first attempt;
  0 = incorrect or asked for help). Rows with missing correct in positions
  1..5 → sequence excluded.
- Hint indicator: hint_count > 0 at that opportunity.
- De-duplicate: one row per order_id (multi-skill duplicates), per the
  maintainers' documented duplication note.
- Comparison pool: seeded sample (seed 20261008) of up to 5,000 eligible
  sequences; each archetype's 50 simulated trajectories are KS-tested against
  this SAME real pool (Holm correction does not require independence).
- **Domain mismatch (stated limitation):** real trajectories = 5 practice
  opportunities on DIFFERENT problems sharing a K-12 skill; simulated
  trajectories = 5 tutoring turns (+probes) on ONE competition-math problem.
  The comparison is distributional-over-sequences, not item-matched.

## 6. Metrics (exact definitions)

Notation: simulated trajectory i: probe correctness c_0..c_5 (c_0 = unaided
baseline; c_1..c_5 = post-turn probes). Real sequence j: correctness
r_1..r_5, hint flags h_1..h_5.

- **M1 — learning-curve power-law exponent.** Per trajectory/sequence, fit OLS:
  log(e_t) = α + b·log(t), t=1..5, where e_t = smoothed error rate,
  e_t = (1 − outcome_t)·(1 − 2δ) + δ, δ = 0.05 (avoids log 0).
  M1 = b (expect b < 0; more negative = faster error decay). Always defined.
- **M2a — error persistence.** Per trajectory/sequence:
  P(err_{t+1} | err_t) over adjacent pairs t=1..4 (sim) / 1..4 (real),
  Laplace-smoothed (E+1)/(N+2), E = #pairs with err_t=err_{t+1}=1,
  N = #pairs with err_t=1. Trajectories with N = 0 (no errors) are EXCLUDED
  from M2a (report exclusion counts).
- **M2b — max error streak.** Longest run of consecutive errors in the
  5-outcome window (0 if none). Always defined.
- **M3 — hint responsiveness.**
  - Simulated: per turn t, guidance delivered g_t = 1 if the teacher
    instruction was accepted (passed both gates), 0 if rejected.
    M3 = mean(c_t : g_t = 1) − mean(c_t : g_t = 0), t = 1..5.
    Trajectories with no accepted or no rejected turns are EXCLUDED from M3
    (report n; power depends on realized rejection rate).
  - Real: M3 = mean(r_{t+1} : h_t = 1) − mean(r_{t+1} : h_t = 0), t = 1..4
    (next-opportunity correctness after a hint vs after no hint; avoids the
    definitional confound that hint-taking forces correct=0 at t).
    Sequences with no hint or no no-hint opportunities in t=1..4 are EXCLUDED
    from M3.

## 7. Statistical tests (locked)

- Per metric (M1, M2a, M2b, M3) × per archetype (6): two-sample
  Kolmogorov–Smirnov test, simulated (n=50, minus exclusions) vs real pool.
  **24 preregistered tests**, two-sided, α = 0.05.
- Multiple comparisons: Holm–Bonferroni across all 24 tests.
- Effect reporting: KS D statistic + 95% bootstrap CI (10,000 resamples,
  seed 20261008) for the median difference (sim − real) per test.
- Exclusion accounting: n per test after exclusions; any test with
  effective n < 20 on either side is flagged as underpowered (not dropped).

## 8. Decision rule (locked)

- **Reject H0** iff ≥ 1 of the 24 Holm-adjusted p-values < 0.05.
  Then H1 is supported for the corresponding metric family/families:
  M1 → learning-curve shape differs; M2a/M2b → error dynamics differ;
  M3 → hint responsiveness differs.
- **Fail to reject H0** iff all 24 adjusted p-values ≥ 0.05: simulated
  students are statistically indistinguishable from real students on these
  behavioral statistics (within this design's power).
- Direction (median sim − median real sign) is descriptive only; no
  directional claim was preregistered.

## 9. Provenance records (filled as Phase A completes)

| Artifact | Value |
|---|---|
| Paper PDF | docs/sherpa-2610.08778.pdf — sha256: eb496497479dfb61c21c06c6f5f3ea63f33e30a556139bd19ec490bb49726df1 |
| Repo commit | 23e2a47c2c84fe59a087258a29d931b801a72fd5 (verified `git rev-parse HEAD`) |
| Model file | data/Qwen3-1.7B-Q4_K_M.gguf (1,107,409,472 bytes) — source: https://huggingface.co/unsloth/Qwen3-1.7B-GGUF (file Qwen3-1.7B-Q4_K_M.gguf) — sha256: b139949c5bd74937ad8ed8c8cf3d9ffb1e99c866c823204dc42c0d91fa181897 (GGUF magic verified). Q8_0 also downloaded (data/Qwen3-1.7B-Q8_0.gguf, sha256 0becaa825564295d82e9af4d008bca5f8b7f5f73bf1c6a0b58f7c53ef26b47fd) but not used — see §4.4(6). |
| ASSISTments CSV | data/assistments/skill_builder_data_corrected.csv — mirror: http://base.ustc.edu.cn/data/ASSISTment/2009_skill_builder_data_corrected.zip (official page direct links unreachable; see docs/data-provenance.md) — zip sha256: 10c4fa76ae9410d8577cf9604cf21f8eed029552717a4b281d64945cf44ebe46; csv sha256: 1aa296e00b6c88c4d6fad4ca2ae4866484d9fe5484f38f5c8c94dfc49f045e08 — 401,756 rows × 30 cols; 4,217 students; 123 skills |
| Inference stack | llama-cpp-python 0.3.36 (built from source in code/venv), CPU, n_threads=2, n_ctx=2048; measured 7–9 tok/s (Q4_K_M) on this box; smoke test logs/smoke_test.json; quant benchmark logs/bench_quants.json |

## 10. Limitations (preregistered)

1. MATH-vs-K12 domain mismatch (§5): competition math ≠ skill-builder items;
   same-problem turns ≠ cross-problem opportunities.
2. Simulated "hint" = teacher guidance passing gates; real "hint" =
   student-requested hints in an ITS — different constructs, compared by analogy.
3. Per-trajectory binary-outcome power-law fits (M1) are noisy; inference
   rests on the distribution across 50 trajectories, not individual fits.
4. Gate-judge and teacher downsized to Qwen3-1.7B (§4.4) — gate behavior may
   differ from the paper's 27B-judge eval.
5. 5 turns vs the paper's 10; only 50 trajectories per archetype (CPU budget).
6. Qwen3-1.7B is a weak student by design (paper: ~36% unaided accuracy on
   filtered MATH); floor effects possible.

## 11. Reproducibility & audit trail

- All code: work-dir code/ (study scripts; upstream copy untouched).
- All generations logged with seeds to logs/ (JSONL per episode).
- Any deviation from this document during Phase B is appended to §12
  (Deviation log) with date and justification — never edited silently.
- Manuscript/report writing begins only after the parent agent's review of
  Phase B results (report-first rule).

## 12. Deviation log

- 2026-10-09: n_ctx raised 2048 → 4096. Episode attempt-diagnosis_031
  (probe c5, 2108 tokens) deterministically overflowed the 2048-token
  window, aborting the run on every relaunch (crash loop at 31/300).
  Justification: context-buffer size does not change model logits for
  prompts that fit in 2048, so the 31 banked episodes remain fully
  comparable; the alternative (skipping the episode) would have broken
  the 300-episode design. No other parameter changed.
