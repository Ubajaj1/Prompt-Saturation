"""
Bootstrap SE bands on level means for Figure 1 saturation curves.
Uses the main study data (20 examples per level) to compute bootstrap SE
at each (model, task, level), then replots the saturation curves with
shaded +/-1 SE bands.
"""
import json
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, "results", "rebuttal_v2", "main_study_combined.json")
OUT_DIR = os.path.join(ROOT, "results", "rebuttal_v2", "figures")
N_BOOTSTRAP = 1000

TASKS_TO_PLOT = ["classification", "product_extraction", "instruction_following",
                 "qa", "math_reasoning", "summarization"]
TASK_LABELS = {
    "classification": "Classification",
    "product_extraction": "Product Extraction",
    "instruction_following": "Instruction Following",
    "qa": "QA",
    "math_reasoning": "Math Reasoning",
    "summarization": "Summarisation",
}


def bootstrap_se(values, n_boot=N_BOOTSTRAP):
    """Bootstrap standard error of the mean."""
    values = np.array(values)
    n = len(values)
    if n < 2:
        return 0.0
    boot_means = np.array([
        np.mean(np.random.choice(values, size=n, replace=True))
        for _ in range(n_boot)
    ])
    return float(np.std(boot_means, ddof=1))


def main():
    np.random.seed(42)
    with open(DATA) as f:
        data = [r for r in json.load(f) if "error" not in r]

    models = sorted(set(r["model"] for r in data))

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for ax_idx, task in enumerate(TASKS_TO_PLOT):
        ax = axes[ax_idx]
        for model in models:
            toks, means, ses = [], [], []
            for level in range(1, 8):
                sub = [r for r in data
                       if r["model"] == model and r["task"] == task and r["level"] == level]
                if not sub:
                    continue
                qualities = [r["quality"] for r in sub]
                toks.append(np.mean([r["prompt_tokens"] for r in sub]))
                means.append(np.mean(qualities))
                ses.append(bootstrap_se(qualities))

            if not toks:
                continue
            toks, means, ses = np.array(toks), np.array(means), np.array(ses)
            line, = ax.plot(toks, means, marker="o", markersize=3, label=model)
            ax.fill_between(toks, means - ses, means + ses, alpha=0.15, color=line.get_color())

        ax.set_title(TASK_LABELS.get(task, task), fontsize=12)
        ax.set_xlabel("Prompt tokens")
        ax.set_ylabel("Quality")
        ax.set_ylim(-0.05, 1.1)

    axes[0].legend(fontsize=6, loc="lower right")
    plt.tight_layout()
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "fig1_with_error_bars.png")
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.savefig(out_path.replace(".png", ".pdf"), bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.close()


if __name__ == "__main__":
    main()
