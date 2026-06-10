"""
Below-ceiling stratification + per-example saturation (reviewer Q3 & Q5).

The reviewer's MAJOR concern: are QA/math "insensitive" only because the 20
curated examples are easy (already at ceiling at L1)? If the *below-ceiling*
examples also fail to improve with elaboration, the insensitive label is a task
property, not an artefact. If they DO improve, it's an artefact.

Method (all on existing main-study data, no API calls):
  - For each (model, task), classify each example as above/below ceiling by its
    L1 quality (threshold 0.85, matching the paper's Section 4.5).
  - Compute mean L1->L7 delta for the below-ceiling subset vs the above-ceiling
    subset, pooled across models per task.
  - Per-example: fit a monotone trend (Spearman rho between level and quality)
    for each example; report the fraction of examples with a significant
    positive trend. This is the "within-example analysis" the reviewer asked for
    in Q5.

Outputs:
  results/rebuttal_v2/below_ceiling.json
"""
import json
import os
import numpy as np
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "results", "rebuttal_v2", "main_study_combined.json")
OUT = os.path.join(ROOT, "results", "rebuttal_v2", "below_ceiling.json")

TASKS = ["classification", "product_extraction", "qa", "math_reasoning",
         "summarization", "instruction_following"]
CEILING = 0.85


def clean(records):
    out = []
    for r in records:
        if "prompt_tokens" not in r or "error" in r:
            continue
        out.append({
            "model": r["model"], "task": r["task"], "level": int(r["level"]),
            "example_id": int(r["example_id"]), "quality": r["quality"],
        })
    return out


def example_curve(rows, model, task, ex):
    """Return quality[1..7] for one (model, task, example), or None if incomplete."""
    q = []
    for lvl in range(1, 8):
        sub = [x["quality"] for x in rows
               if x["model"] == model and x["task"] == task
               and x["example_id"] == ex and x["level"] == lvl]
        if not sub:
            return None
        q.append(np.mean(sub))
    return np.array(q)


def main():
    rows = clean(json.load(open(DATA)))
    models = sorted({x["model"] for x in rows})
    examples = sorted({x["example_id"] for x in rows})

    report = {}
    for task in TASKS:
        below_deltas, above_deltas = [], []
        n_below, n_above = 0, 0
        # per-example monotone-trend test, pooled across models
        pos_sig = 0      # examples with significant positive level->quality trend
        total_ex = 0
        below_curves = []  # mean curve over below-ceiling examples

        for model in models:
            for ex in examples:
                curve = example_curve(rows, model, task, ex)
                if curve is None:
                    continue
                total_ex += 1
                delta = curve[-1] - curve[0]
                rho, p = spearmanr(np.arange(1, 8), curve)
                if not np.isnan(rho) and rho > 0 and p < 0.05:
                    pos_sig += 1
                if curve[0] < CEILING:
                    below_deltas.append(delta)
                    below_curves.append(curve)
                    n_below += 1
                else:
                    above_deltas.append(delta)
                    n_above += 1

        below_mean_curve = (np.mean(below_curves, axis=0).tolist()
                            if below_curves else None)
        report[task] = {
            "n_below_ceiling": n_below,
            "n_above_ceiling": n_above,
            "pct_below_ceiling": round(n_below / max(1, n_below + n_above), 3),
            "below_ceiling_mean_L1_L7_delta": (round(float(np.mean(below_deltas)), 4)
                                               if below_deltas else None),
            "above_ceiling_mean_L1_L7_delta": (round(float(np.mean(above_deltas)), 4)
                                               if above_deltas else None),
            "below_ceiling_mean_curve": ([round(x, 3) for x in below_mean_curve]
                                         if below_mean_curve else None),
            "pct_examples_significant_positive_trend": round(pos_sig / max(1, total_ex), 3),
            "n_example_curves": total_ex,
        }

    json.dump(report, open(OUT, "w"), indent=2)

    # console report
    print(f"Ceiling threshold = {CEILING} (L1 quality). Pooled across {len(models)} models.\n")
    hdr = (f"{'task':22s} {'%below':>7s} {'below Δ':>9s} {'above Δ':>9s} "
           f"{'%ex sig+ trend':>15s}")
    print(hdr)
    print("-" * len(hdr))
    for task in TASKS:
        r = report[task]
        bd = r["below_ceiling_mean_L1_L7_delta"]
        ad = r["above_ceiling_mean_L1_L7_delta"]
        print(f"{task:22s} {r['pct_below_ceiling']*100:6.1f}% "
              f"{(bd if bd is not None else float('nan')):9.4f} "
              f"{(ad if ad is not None else float('nan')):9.4f} "
              f"{r['pct_examples_significant_positive_trend']*100:14.1f}%")

    print("\nInterpretation:")
    print("  QA/math: if below-ceiling Δ is also small/negative, 'insensitive' is")
    print("  a task property; if large positive, it is an easy-example artefact.")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
