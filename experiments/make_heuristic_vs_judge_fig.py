"""
Figure: heuristic vs LLM-judge saturation curves for the four ground-truth tasks.

Shows that the SHAPE of the quality-vs-token curve is the same under both metrics
(the reviewer's Q2), using per-(model,task) level means from heuristic_rescore.json.

Output: results/rebuttal_v2/figures/fig_heuristic_vs_judge.png (+ .pdf)
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESCORE = os.path.join(ROOT, "results", "rebuttal_v2", "heuristic_rescore.json")
AGREE = os.path.join(ROOT, "results", "rebuttal_v2", "heuristic_vs_judge.json")
OUT_DIR = os.path.join(ROOT, "results", "rebuttal_v2", "figures")

TASKS = [
    ("classification", "Classification"),
    ("product_extraction", "Product extraction"),
    ("qa", "QA"),
    ("math_reasoning", "Math reasoning"),
]


def level_means(rows, task, qkey):
    """Mean over all models+examples per level -> (tokens[7], quality[7])."""
    toks, quals = [], []
    for lvl in range(1, 8):
        sub = [x for x in rows if x["task"] == task and x["level"] == lvl]
        if not sub:
            return None, None
        toks.append(np.mean([x["prompt_tokens"] for x in sub]))
        quals.append(np.mean([x[qkey] for x in sub]))
    return np.array(toks), np.array(quals)


def main():
    rows = json.load(open(RESCORE))
    agree = json.load(open(AGREE))

    fig, axes = plt.subplots(2, 2, figsize=(10, 7.5))
    axes = axes.flatten()
    for ax, (task, title) in zip(axes, TASKS):
        jt, jq = level_means(rows, task, "judge_quality")
        ht, hq = level_means(rows, task, "heuristic_quality")
        ax.plot(jt, jq, "o-", color="#2c7fb8", label="LLM judge (gpt-4o-mini)", lw=2, ms=6)
        ax.plot(ht, hq, "s--", color="#d7301f", label="Heuristic (ground truth)", lw=2, ms=6)
        shape_r = agree["curve_shape"][task]["mean_shape_r"]
        ax.set_title(f"{title}\n(curve-shape r = {shape_r:.2f})", fontsize=11, fontweight="bold")
        ax.set_xlabel("Mean prompt tokens", fontsize=9)
        ax.set_ylim(0.4, 1.02)
        ax.grid(alpha=0.3)
        ax.set_ylabel("Mean quality", fontsize=10)
        if task == "classification":
            ax.legend(fontsize=8, loc="lower right")

    fig.suptitle("Saturation curve shape is metric-invariant: LLM judge vs deterministic heuristic",
                 fontsize=12.5, fontweight="bold", y=1.04)
    fig.tight_layout()
    png = os.path.join(OUT_DIR, "fig_heuristic_vs_judge.png")
    pdf = os.path.join(OUT_DIR, "fig_heuristic_vs_judge.pdf")
    fig.savefig(png, dpi=200, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    print("wrote", png)
    print("wrote", pdf)


if __name__ == "__main__":
    main()
