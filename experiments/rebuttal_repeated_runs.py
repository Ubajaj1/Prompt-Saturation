"""
Repeated-runs analysis: compute per-level SE, effect-vs-noise ratios,
and test whether the prompt-sensitivity gradient survives variance.
"""
import json
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, "results", "rebuttal_v2", "repeated_runs.json")
OUT = os.path.join(ROOT, "results", "rebuttal_v2", "repeated_runs_analysis.json")

TASKS = ["classification", "product_extraction", "instruction_following"]


def main():
    with open(DATA) as f:
        data = [r for r in json.load(f) if "error" not in r]

    models = sorted(set(r["model"] for r in data))
    runs = sorted(set(r.get("run_id", 0) for r in data))
    print(f"Models: {models}")
    print(f"Runs: {runs}")
    print(f"Total records: {len(data)}")

    results = {}
    for task in TASKS:
        results[task] = {}
        for model in models:
            level_stats = []
            for level in range(1, 8):
                run_means = []
                for run_id in runs:
                    sub = [r for r in data
                           if r["model"] == model
                           and r["task"] == task
                           and r["level"] == level
                           and r.get("run_id", 0) == run_id]
                    if sub:
                        run_means.append(np.mean([r["quality"] for r in sub]))

                if run_means:
                    level_stats.append({
                        "level": level,
                        "mean": float(np.mean(run_means)),
                        "std": float(np.std(run_means, ddof=1)) if len(run_means) > 1 else 0.0,
                        "se": float(np.std(run_means, ddof=1) / np.sqrt(len(run_means))) if len(run_means) > 1 else 0.0,
                        "n_runs": len(run_means),
                        "run_means": [float(m) for m in run_means],
                    })

            if level_stats:
                l1_mean = level_stats[0]["mean"]
                l7_mean = level_stats[-1]["mean"]
                delta = l7_mean - l1_mean
                max_se = max(s["se"] for s in level_stats)
                mean_se = np.mean([s["se"] for s in level_stats])

                results[task][model] = {
                    "levels": level_stats,
                    "L1_to_L7_delta": float(delta),
                    "max_se": float(max_se),
                    "mean_se": float(mean_se),
                    "effect_to_noise": float(abs(delta) / mean_se) if mean_se > 0 else float("inf"),
                }

    with open(OUT, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'Task':25s} {'Model':30s} {'L1->L7 d':>10s} {'Mean SE':>10s} {'Effect/Noise':>13s}")
    print("-" * 90)
    for task in TASKS:
        for model in sorted(results[task]):
            r = results[task][model]
            print(f"{task:25s} {model:30s} {r['L1_to_L7_delta']:+10.4f} "
                  f"{r['mean_se']:10.4f} {r['effect_to_noise']:13.1f}")
        print()


if __name__ == "__main__":
    main()
