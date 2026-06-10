"""
Per-dimension subscore decomposition (reviewer W-CLA minor point).

The aggregate q = sum(4 subscores)/20 obscures WHICH quality dimension drives
the saturation signal. The judge stored all four subscores (correctness,
completeness, reasoning, conciseness, each 1-5), so we can decompose the
L1->L7 gain per dimension with no new API calls.

Outputs:
  results/rebuttal_v2/subscore_decomposition.json
"""
import json
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "results", "rebuttal_v2", "main_study_combined.json")
OUT = os.path.join(ROOT, "results", "rebuttal_v2", "subscore_decomposition.json")

TASKS = ["classification", "product_extraction", "qa", "math_reasoning",
         "summarization", "instruction_following"]
DIMS = ["correctness", "completeness", "reasoning", "conciseness"]


def main():
    records = json.load(open(DATA))
    report = {}
    for task in TASKS:
        # mean subscore per level, pooled across models+examples
        per_level = {d: {lvl: [] for lvl in range(1, 8)} for d in DIMS}
        for r in records:
            if r["task"] != task or "error" in r:
                continue
            js = r.get("judge_scores")
            if not js:
                continue
            lvl = int(r["level"])
            for d in DIMS:
                if d in js:
                    per_level[d][lvl].append(js[d])

        dim_report = {}
        for d in DIMS:
            means = [np.mean(per_level[d][lvl]) if per_level[d][lvl] else np.nan
                     for lvl in range(1, 8)]
            l1, l7 = means[0], means[-1]
            dim_report[d] = {
                "L1_mean_1to5": round(float(l1), 3),
                "L7_mean_1to5": round(float(l7), 3),
                "L1_L7_delta_1to5": round(float(l7 - l1), 3),
                # contribution to normalised q (each dim is /20, so /5 of the /4 share)
                "delta_in_q_units": round(float((l7 - l1) / 20.0), 4),
                "level_means_1to5": [round(float(m), 3) for m in means],
            }
        # which dimension drives the aggregate gain?
        driver = max(DIMS, key=lambda d: dim_report[d]["delta_in_q_units"])
        total_q_delta = sum(dim_report[d]["delta_in_q_units"] for d in DIMS)
        report[task] = {
            "dimensions": dim_report,
            "driver_dimension": driver,
            "driver_share_of_q_delta": (round(dim_report[driver]["delta_in_q_units"]
                                              / total_q_delta, 3)
                                        if abs(total_q_delta) > 1e-9 else None),
            "total_q_L1_L7_delta": round(total_q_delta, 4),
        }

    json.dump(report, open(OUT, "w"), indent=2)

    print(f"{'task':22s} {'driver dim':13s} {'driver Δq':>9s} {'total Δq':>9s}  per-dim Δ(1-5 scale)")
    print("-" * 100)
    for task in TASKS:
        r = report[task]
        per_dim = "  ".join(f"{d[:4]}={r['dimensions'][d]['L1_L7_delta_1to5']:+.2f}"
                            for d in DIMS)
        share = r["driver_share_of_q_delta"]
        share_s = f"{share*100:.0f}%" if share is not None else "n/a"
        print(f"{task:22s} {r['driver_dimension']:13s} "
              f"{r['dimensions'][r['driver_dimension']]['delta_in_q_units']:+9.4f} "
              f"{r['total_q_L1_L7_delta']:+9.4f}  [{per_dim}]  driver={share_s}")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
