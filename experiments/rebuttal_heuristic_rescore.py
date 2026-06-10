"""
Heuristic re-scoring of the main study (free; no API calls).

Addresses the reviewer's CRITICAL "LLM-as-judge is the sole evaluation method"
and Question 2 ("do heuristic and judge agree on the SHAPE of the saturation
curve, not just overall correlation?").

For the four tasks with clean ground truth (classification, product_extraction,
qa, math_reasoning) we re-score every stored main-study response with the
deterministic heuristic evaluators in greenprompt/evaluators.py, then:

  1. Recompute per-(model, task, level) mean quality on the heuristic metric.
  2. Fit the same log/sigmoid saturation curves + null-model F-test used in the
     paper, on the heuristic means.
  3. Compare judge vs heuristic on:
       - per-record Pearson r and MAE (reproduces Table 7-style agreement),
       - per-(model,task) curve SHAPE: Pearson r between the 7 judge level-means
         and the 7 heuristic level-means, plus agreement on L1->L7 direction,
       - significance concordance (does the heuristic metric also find the
         curve significant?).

Outputs:
  results/rebuttal_v2/heuristic_rescore.json      (per-record heuristic scores)
  results/rebuttal_v2/heuristic_vs_judge.json      (agreement + curve stats)
  results/rebuttal_v2/heuristic_curve_fits.csv     (F-test/T* on heuristic metric)
"""
import json
import os
import sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from greenprompt.evaluators import (
    get_evaluator, InstructionFollowingEvaluator,
)
from experiments.prompting_strategies import BENCHMARK_EXAMPLES
from experiments.saturation_analysis import (
    fit_best_curve, null_model_ftest,
)

DATA = os.path.join(ROOT, "results", "rebuttal_v2", "main_study_combined.json")
OUT_DIR = os.path.join(ROOT, "results", "rebuttal_v2")

# Tasks with clean, deterministic ground-truth matching. Summarisation and
# instruction-following heuristics are weak proxies (length/ROUGE, constraint
# regex), so we keep the judge primary for those and re-score only these four.
GT_TASKS = ["classification", "product_extraction", "qa", "math_reasoning"]


def heuristic_score(task, example_id, response_text):
    """Deterministic heuristic quality for one stored response."""
    ex = BENCHMARK_EXAMPLES[task][example_id]
    gt = ex.get("ground_truth")
    if task == "instruction_following":
        ev = InstructionFollowingEvaluator(constraints=ex.get("constraints", []))
    else:
        ev = get_evaluator(task)
    q, _ = ev.evaluate(response_text or "", gt)
    return q


def rescore(records):
    """Attach heuristic quality to every GT-task record."""
    out = []
    skipped = 0
    for r in records:
        if r["task"] not in GT_TASKS:
            continue
        # API-error rows carry no response/tokens — skip (matches the paper,
        # which analyses recorded outputs only).
        if "prompt_tokens" not in r or "error" in r:
            skipped += 1
            continue
        example_id = int(r["example_id"])
        if not r.get("completed", True):
            # match benchmark behaviour: incomplete generations score 0
            hq = 0.0
        else:
            hq = heuristic_score(r["task"], example_id, r.get("response_text", ""))
        out.append({
            "model": r["model"], "task": r["task"], "level": int(r["level"]),
            "example_id": example_id, "prompt_tokens": r["prompt_tokens"],
            "judge_quality": r["quality"], "heuristic_quality": hq,
        })
    if skipped:
        print(f"  (skipped {skipped} API-error rows with no response)")
    return out


def level_means(rows, model, task, qkey):
    """Return (token_means[7], quality_means[7]) ordered by level 1..7."""
    toks, quals = [], []
    for lvl in range(1, 8):
        sub = [x for x in rows if x["model"] == model and x["task"] == task and x["level"] == lvl]
        if not sub:
            return None, None
        toks.append(np.mean([x["prompt_tokens"] for x in sub]))
        quals.append(np.mean([x[qkey] for x in sub]))
    return np.array(toks), np.array(quals)


def fit_and_test(tokens, quality):
    """Fit best curve + F-test; return dict with T*, F, p, R2, significant."""
    try:
        fit = fit_best_curve(tokens, quality)
        ft = null_model_ftest(tokens, quality, fit)
        p = ft["ftest_p"]
        return {
            "fit_type": fit["model_type"], "r2": fit["r2"],
            "saturation_tokens": fit.get("saturation_tokens"),
            "F": ft["ftest_F"], "p": p,
            "significant": bool(ft["ftest_significant"]),
        }
    except Exception as e:
        return {"fit_type": None, "r2": None, "saturation_tokens": None,
                "F": None, "p": None, "significant": False, "error": str(e)}


def main():
    records = json.load(open(DATA))
    rescored = rescore(records)
    json.dump(rescored, open(os.path.join(OUT_DIR, "heuristic_rescore.json"), "w"))
    print(f"Re-scored {len(rescored)} records across {GT_TASKS}")

    models = sorted({x["model"] for x in rescored})

    # ---- (1) per-record agreement, per task ----
    agreement = {}
    for task in GT_TASKS:
        sub = [x for x in rescored if x["task"] == task]
        j = np.array([x["judge_quality"] for x in sub])
        h = np.array([x["heuristic_quality"] for x in sub])
        if len(j) > 2 and j.std() > 0 and h.std() > 0:
            r = float(np.corrcoef(j, h)[0, 1])
        else:
            r = float("nan")
        agreement[task] = {
            "n": len(sub), "pearson_r": r, "mae": float(np.mean(np.abs(j - h))),
            "judge_mean": float(j.mean()), "heuristic_mean": float(h.mean()),
        }

    # ---- (2) curve-shape agreement + (3) significance concordance ----
    curve_rows = []
    shape_rows = []
    for task in GT_TASKS:
        for model in models:
            jt, jq = level_means(rescored, model, task, "judge_quality")
            ht, hq = level_means(rescored, model, task, "heuristic_quality")
            if jq is None or hq is None:
                continue
            jfit = fit_and_test(jt, jq)
            hfit = fit_and_test(ht, hq)
            curve_rows.append({"model": model, "task": task, "metric": "judge", **jfit})
            curve_rows.append({"model": model, "task": task, "metric": "heuristic", **hfit})

            # shape correlation between the two 7-point level-mean vectors
            if jq.std() > 0 and hq.std() > 0:
                shape_r = float(np.corrcoef(jq, hq)[0, 1])
            else:
                shape_r = float("nan")
            j_dir = np.sign(jq[-1] - jq[0])
            h_dir = np.sign(hq[-1] - hq[0])
            shape_rows.append({
                "model": model, "task": task,
                "shape_pearson_r": shape_r,
                "judge_L1_L7_delta": float(jq[-1] - jq[0]),
                "heuristic_L1_L7_delta": float(hq[-1] - hq[0]),
                "direction_agree": bool(j_dir == h_dir),
                "judge_significant": jfit["significant"],
                "heuristic_significant": hfit["significant"],
                "significance_concordant": bool(jfit["significant"] == hfit["significant"]),
            })

    curve_df = pd.DataFrame(curve_rows)
    curve_df.to_csv(os.path.join(OUT_DIR, "heuristic_curve_fits.csv"), index=False)

    shape_df = pd.DataFrame(shape_rows)

    # ---- summary roll-ups ----
    summary = {"per_task_agreement": agreement}
    summary["curve_shape"] = {}
    for task in GT_TASKS:
        t = shape_df[shape_df["task"] == task]
        summary["curve_shape"][task] = {
            "mean_shape_r": float(t["shape_pearson_r"].mean()),
            "median_shape_r": float(t["shape_pearson_r"].median()),
            "direction_agree": f"{int(t['direction_agree'].sum())}/{len(t)}",
            "significance_concordant": f"{int(t['significance_concordant'].sum())}/{len(t)}",
            "judge_sig": f"{int(t['judge_significant'].sum())}/{len(t)}",
            "heuristic_sig": f"{int(t['heuristic_significant'].sum())}/{len(t)}",
        }
    summary["shape_table"] = shape_rows

    json.dump(summary, open(os.path.join(OUT_DIR, "heuristic_vs_judge.json"), "w"), indent=2)

    # ---- console report ----
    print("\n=== Per-record agreement (judge vs heuristic) ===")
    print(f"{'task':22s} {'n':>5s} {'pearson_r':>10s} {'MAE':>7s} {'judge_mu':>9s} {'heur_mu':>9s}")
    for task in GT_TASKS:
        a = agreement[task]
        print(f"{task:22s} {a['n']:5d} {a['pearson_r']:10.3f} {a['mae']:7.3f} "
              f"{a['judge_mean']:9.3f} {a['heuristic_mean']:9.3f}")

    print("\n=== Curve-shape agreement (the reviewer's Q2) ===")
    print(f"{'task':22s} {'mean_shape_r':>13s} {'dir_agree':>10s} {'sig_concord':>12s} "
          f"{'judge_sig':>10s} {'heur_sig':>9s}")
    for task in GT_TASKS:
        s = summary["curve_shape"][task]
        print(f"{task:22s} {s['mean_shape_r']:13.3f} {s['direction_agree']:>10s} "
              f"{s['significance_concordant']:>12s} {s['judge_sig']:>10s} {s['heuristic_sig']:>9s}")

    print("\nWrote heuristic_rescore.json, heuristic_vs_judge.json, heuristic_curve_fits.csv")


if __name__ == "__main__":
    main()
