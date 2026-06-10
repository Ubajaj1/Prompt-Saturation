"""
Generate Figure 2: per-layer marginal quality contributions for each task.

Replaces the [TODO] placeholder in the paper. Reads the precomputed per-layer
deltas from results/rebuttal/marginal_contributions.json (mean_across_models),
which were derived from the main-study per-example data.

Output: results/rebuttal_v2/figures/fig2_marginal_contributions.png (+ .pdf)
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MC_PATH = os.path.join(ROOT, "results", "rebuttal", "marginal_contributions.json")
OUT_DIR = os.path.join(ROOT, "results", "rebuttal_v2", "figures")
os.makedirs(OUT_DIR, exist_ok=True)

# Layer transition order (L1->L2 ... L6->L7) and short human labels.
LAYER_KEYS = [
    "L1->L2_task_label",
    "L2->L3_format_spec",
    "L3->L4_definitions",
    "L4->L5_persona",
    "L5->L6_guidelines",
    "L6->L7_worked_example",
]
LAYER_LABELS = [
    "L1→L2\ntask label",
    "L2→L3\nformat spec",
    "L3→L4\ndefinitions",
    "L4→L5\npersona",
    "L5→L6\nguidelines",
    "L6→L7\nworked ex.",
]

# Panel order chosen to read as the gradient: concentrated -> distributed ->
# diffuse -> insensitive (with math's non-monotonic L3 collapse).
TASK_ORDER = [
    ("classification", "Classification (concentrated)"),
    ("product_extraction", "Product extraction (distributed)"),
    ("instruction_following", "Instruction following (diffuse)"),
    ("math_reasoning", "Math reasoning (non-monotonic)"),
    ("qa", "QA (insensitive)"),
    ("summarization", "Summarisation (insensitive)"),
]

POS_COLOR = "#2c7fb8"
NEG_COLOR = "#d7301f"


def main():
    mc = json.load(open(MC_PATH))

    fig, axes = plt.subplots(2, 3, figsize=(13, 7), sharey=False)
    axes = axes.flatten()

    for ax, (task, title) in zip(axes, TASK_ORDER):
        means = mc[task]["mean_across_models"]
        deltas = [means[k] for k in LAYER_KEYS]
        colors = [POS_COLOR if d >= 0 else NEG_COLOR for d in deltas]

        bars = ax.bar(range(len(deltas)), deltas, color=colors,
                      edgecolor="black", linewidth=0.5, width=0.7)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xticks(range(len(deltas)))
        ax.set_xticklabels(LAYER_LABELS, fontsize=7.5)
        ax.set_ylabel("Δ quality", fontsize=9)
        ax.grid(axis="y", alpha=0.3, linewidth=0.5)

        # Annotate the largest-magnitude bar so the "where the gain lives" story
        # is legible without reading values off the axis.
        big_i = int(np.argmax(np.abs(deltas)))
        big_v = deltas[big_i]
        va = "bottom" if big_v >= 0 else "top"
        off = 0.012 if big_v >= 0 else -0.012
        ax.text(big_i, big_v + off, f"{big_v:+.3f}", ha="center", va=va,
                fontsize=8, fontweight="bold")

        # Per-task y-limits with headroom; keep math on a wide axis so the
        # L3 collapse is visible at true scale.
        lo, hi = min(deltas), max(deltas)
        pad = max(0.05, 0.18 * (hi - lo))
        ax.set_ylim(lo - pad, hi + pad)

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=POS_COLOR, ec="black", lw=0.5),
        plt.Rectangle((0, 0), 1, 1, color=NEG_COLOR, ec="black", lw=0.5),
    ]
    fig.legend(handles, ["quality gain", "quality loss"],
               loc="upper right", fontsize=9, ncol=2,
               bbox_to_anchor=(0.995, 1.0))

    fig.suptitle("Per-layer marginal quality contributions "
                 "($\\Delta_{k\\rightarrow k+1}$, averaged across seven models)",
                 fontsize=12.5, y=1.0)
    fig.tight_layout(rect=[0, 0, 1, 0.96])

    png = os.path.join(OUT_DIR, "fig2_marginal_contributions.png")
    pdf = os.path.join(OUT_DIR, "fig2_marginal_contributions.pdf")
    fig.savefig(png, dpi=200, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    print("wrote", png)
    print("wrote", pdf)

    # Echo the key numbers the caption/text rely on.
    for task, _ in TASK_ORDER:
        d = mc[task]
        print(f"  {task:22s} biggest={d['biggest_layer']:22s} "
              f"delta={d['biggest_layer_delta']:+.3f} "
              f"pct_of_pos_gain={d.get('biggest_layer_pct', float('nan')):.1%}")


if __name__ == "__main__":
    main()
