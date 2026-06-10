# Tier-1 (free, no-API) findings for the ACML revision

All results below were produced from data already on disk (the main-study
responses with stored text + judge subscores, the marginal-contribution deltas,
and the deterministic heuristic evaluators). No new API calls. Scripts live in
`experiments/rebuttal_*.py` and `experiments/make_*.py`; outputs in
`results/rebuttal_v2/`.

Reproduce all four:
```
python3 experiments/make_fig2_marginal.py
python3 experiments/rebuttal_heuristic_rescore.py
python3 experiments/make_heuristic_vs_judge_fig.py
python3 experiments/rebuttal_below_ceiling.py
python3 experiments/rebuttal_subscore_decomp.py
```

---

## A. Figure 2 now exists (reviewer CRITICAL, Presentation)

The `[TODO: Marginal contribution figure]` placeholder — the item the reviewer
called "grounds for desk rejection" — is replaced by
`results/rebuttal_v2/figures/fig2_marginal_contributions.png`, rendered from
`results/rebuttal/marginal_contributions.json` (`mean_across_models`).

Key annotated values (per-layer Δquality, averaged across 7 models):
- Classification: L1→L2 (task label) **+0.072**, 49% of total positive gain — concentrated.
- Product extraction: L6→L7 (worked example) **+0.067**, 40% of gain; L1→L2 +0.054 — distributed.
- Instruction following: largest layer L5→L6 **+0.010** — diffuse.
- Math: L3→L4 **+0.363** (recovery from the −0.366 L3 chain-of-thought suppression) — non-monotonic.
- QA / summarisation: near-zero everywhere — insensitive.

## B. Heuristic re-scoring: saturation is metric-invariant (reviewer CRITICAL + Q2)

Re-scored all 3,915 main-study responses for the four ground-truth tasks with
the deterministic evaluators (`greenprompt/evaluators.py`). **Sanity check: the
judge-metric curve fits reproduce Table 4 exactly** — classification 4/7
significant, product extraction 3/7, QA 0/7, math 0/7; gemini-flash
classification F=14.53, p=0.027 (paper: 14.5, 0.027).

Per-record agreement and curve-shape agreement (judge vs heuristic):

| Task | per-record r | MAE | curve-shape r | L1→L7 dir. agree | heuristic sig. | judge sig. |
|---|---:|---:|---:|---:|---:|---:|
| Classification | 0.926 | 0.069 | **0.839** | 6/7 | 2/7 | 4/7 |
| Product extraction | 0.415 | 0.300 | **0.660** | **7/7** | **7/7** | 3/7 |
| QA | 0.178 | 0.127 | 0.098 | 0/7 | 0/7 | 0/7 |
| Math reasoning | 0.539 | 0.144 | 0.525 | 5/7 | 1/7 | 0/7 |

**The reviewer's central reliability worry is rebutted by the data.** Product
extraction was the task with the worst inter-judge Pearson r (0.247), which the
reviewer flagged because it is a strong-saturation task. On the deterministic
ground-truth metric, product extraction shows **7/7 significant** saturation fits
and **7/7** L1→L7 direction agreement with the judge — i.e., the saturation is
*more* detectable on hard ground-truth matching, not an artefact of judge noise.
QA is flat under both metrics (0/7 both), independently confirming "insensitive."
Figure: `fig_heuristic_vs_judge.png`.

Recommendation for the paper: make the heuristic the **primary** metric for the
four ground-truth tasks; keep the judge as primary only for summarisation and
instruction following (no clean heuristic), and report both.

## C. Per-dimension subscore decomposition (reviewer W-CLA minor)

`q = Σsᵢ/20` hid which dimension moves. Decomposing the stored subscores:

- **Product extraction** gain is driven by **completeness (+1.40 on 1–5; 43% of
  aggregate Δq)** — elaboration makes the model emit all four fields. Direct
  mechanistic support for the schema-compliance hypothesis.
- **Classification** gain is spread across all four dimensions (corr +0.69,
  comp +0.61, reas +0.56, conc +0.71) — concentrated in *tokens* but
  distributed across *dimensions*.
- QA aggregate Δ is negative, driven by a completeness drop (−0.72) as extra
  layers add noise to already-correct answers.

Output: `subscore_decomposition.json`.

## D. Below-ceiling stratification — HONEST, PARTIALLY ADVERSE (reviewer Q3 & Q5)

This is the result that cuts against us and must be reported honestly. Stratify
examples by observed L1 quality (ceiling = 0.85), pooled across 7 models:

| Task | % below ceiling | below-ceiling L1→L7 Δ | above-ceiling Δ | % examples w/ sig.+ trend |
|---|---:|---:|---:|---:|
| Classification | 32.9% | +0.316 | +0.036 | 20.0% |
| Product extraction | 92.8% | +0.167 | +0.120 | 36.2% |
| QA | 10.0% | **+0.061** | −0.045 | 5.7% |
| Math reasoning | 9.4% | **+0.204** | −0.000 | 5.1% |
| Summarisation | 0.0% | n/a | −0.010 | 1.4% |
| Instruction following | 32.1% | +0.013 | −0.008 | 12.1% |

**Interpretation:** For math, the ~9% of examples that start below ceiling show
a **+0.204** L1→L7 gain — i.e., *harder math problems do respond to prompt
elaboration*. QA below-ceiling examples are mildly positive (+0.061). So the
"insensitive" label is, in part, a property of the easy curated set — exactly
the reviewer's hypothesis in Q3. The task-level "insensitive" claim should be
softened to "insensitive **at the ceiling-dominated difficulty of the current
example set**."

**Mandatory caveat (do not omit):** below-ceiling examples are *selected on* low
L1 quality, so some of the positive Δ is regression-to-the-mean. With no repeated
runs (the reviewer's other MAJOR concern), selection noise and true prompt
sensitivity cannot be separated from existing data. This is honest motivation
for G (harder examples) and H (repeated runs) — it cannot be resolved by
re-analysis.

---

## Net effect on the scorecard (Tier-1 only)

- **Presentation 2→3:** the desk-reject trigger (Figure 2) is gone; subscore and
  curve-shape figures add substance.
- **Soundness 2→~2.5:** judge-reliability CRITICAL is substantially answered
  (B); but the underpowered-n CRITICAL (G) and no-repeats MAJOR (H) remain, and
  D actively shows why they matter.
- **Contribution unchanged (2):** the gradient is still a post-hoc taxonomy;
  needs I (held-out validation) to move.

Tier-1 alone does not clear the ACML bar. It removes the cheapest blocker,
neutralises one of two CRITICALs, and sharpens the case for the paid tier.
