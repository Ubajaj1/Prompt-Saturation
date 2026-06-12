"""
Generate Figure 2: per-layer marginal quality contributions for each task.

PRIMARY (main-text) figure uses the DETERMINISTIC metric for the four
ground-truth tasks (classification, product extraction, QA, math) and the LLM
judge only for the two tasks that lack clean ground truth (summarisation,
instruction following). This enforces "deterministic is primary" structurally:
the headline 87% / 92% concentration claims are read off the deterministic bars.

A companion APPENDIX figure shows the judge-scored version of the four
ground-truth tasks, documenting the judge artefact (product extraction's gain
spuriously spread onto the L6->L7 worked example).

Deterministic per-layer deltas are computed directly from the per-record
heuristic re-scoring (results/rebuttal_v2/heuristic_rescore.json); judge-only
panels come from results/rebuttal/marginal_contributions.json.

Output:
  results/rebuttal_v2/figures/fig2_marginal_contributions.png (+ .pdf)   [main]
  results/rebuttal_v2/figures/fig2b_marginal_judge_artifact.png (+ .pdf) [appendix]
"""
import json
import os
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESCORE_PATH = os.path.join(ROOT, "results", "rebuttal_v2", "heuristic_rescore.json")
JUDGE_MC_PATH = os.path.join(ROOT, "results", "rebuttal", "marginal_contributions.json")
OUT_DIR = os.path.join(ROOT, "results", "rebuttal_v2", "figures")
os.makedirs(OUT_DIR, exist_ok=True)

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

POS_COLOR = "#2c7fb8"
NEG_COLOR = "#d7301f"

GT_TASKS = ["classification", "product_extraction", "qa", "math_reasoning"]


def deterministic_deltas():
    """Per-layer deltas on the deterministic metric, averaged across models."""
    recs = json.load(open(RESCORE_PATH))
    out = {}
    for task in GT_TASKS:
        bymodel = defaultdict(lambda: defaultdict(list))
        for r in recs:
            if r["task"] == task:
                bymodel[r["model"]][r["level"]].append(r["heuristic_quality"])
        levelvals = defaultdict(list)
        for _, lv in bymodel.items():
            for L in range(1, 8):
                if lv[L]:
                    levelvals[L].append(sum(lv[L]) / len(lv[L]))
        means = {L: sum(levelvals[L]) / len(levelvals[L]) for L in range(1, 8)}
        out[task] = [means[L + 1] - means[L] for L in range(1, 7)]
    return out


def judge_deltas():
    mc = json.load(open(JUDGE_MC_PATH))
    out = {}
    for task in mc:
        m = mc[task]["mean_across_models"]
        out[task] = [m[k] for k in LAYER_KEYS]
    return out


def draw_panel(ax, deltas, title):
    colors = [POS_COLOR if d >= 0 else NEG_COLOR for d in deltas]
    ax.bar(range(len(deltas)), deltas, color=colors,
           edgecolor="black", linewidth=0.5, width=0.7)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_xticks(range(len(deltas)))
    ax.set_xticklabels(LAYER_LABELS, fontsize=7.5)
    ax.set_ylabel("Δ quality", fontsize=9)
    ax.grid(axis="y", alpha=0.3, linewidth=0.5)
    big_i = int(np.argmax(np.abs(deltas)))
    big_v = deltas[big_i]
    va = "bottom" if big_v >= 0 else "top"
    off = 0.012 if big_v >= 0 else -0.012
    ax.text(big_i, big_v + off, f"{big_v:+.3f}", ha="center", va=va,
            fontsize=8, fontweight="bold")
    lo, hi = min(deltas), max(deltas)
    pad = max(0.05, 0.18 * (hi - lo))
    ax.set_ylim(lo - pad, hi + pad)


def legend_and_save(fig, suptitle, basename):
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=POS_COLOR, ec="black", lw=0.5),
        plt.Rectangle((0, 0), 1, 1, color=NEG_COLOR, ec="black", lw=0.5),
    ]
    fig.legend(handles, ["quality gain", "quality loss"],
               loc="upper right", fontsize=9, ncol=2,
               bbox_to_anchor=(0.995, 1.0))
    fig.suptitle(suptitle, fontsize=12.5, y=1.0)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    png = os.path.join(OUT_DIR, basename + ".png")
    pdf = os.path.join(OUT_DIR, basename + ".pdf")
    fig.savefig(png, dpi=200, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    print("wrote", png)
    print("wrote", pdf)


def main():
    det = deterministic_deltas()
    jud = judge_deltas()

    # ---- Main-text figure: deterministic for GT tasks, judge for the two
    # judge-only tasks (clearly labelled). ----
    main_panels = [
        (det["classification"], "Classification — deterministic\n(schema-gated)"),
        (det["product_extraction"], "Product extraction — deterministic\n(schema-gated)"),
        (det["math_reasoning"], "Math reasoning — deterministic\n(knowledge-gated, L3 collapse)"),
        (det["qa"], "QA — deterministic\n(knowledge-gated)"),
        (jud["instruction_following"], "Instruction following — judge\n(difficulty-gated)"),
        (jud["summarization"], "Summarisation — judge\n(knowledge-gated)"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(13, 7), sharey=False)
    for ax, (deltas, title) in zip(axes.flatten(), main_panels):
        draw_panel(ax, deltas, title)
    legend_and_save(
        fig,
        "Per-layer marginal quality contributions "
        "($\\Delta_{k\\rightarrow k+1}$). Deterministic metric for the four "
        "ground-truth tasks; LLM judge where no ground truth exists.",
        "fig2_marginal_contributions",
    )

    # ---- Appendix figure: judge-scored GT tasks, documenting the artefact. ----
    art_panels = [
        (jud["classification"], "Classification — LLM judge"),
        (jud["product_extraction"], "Product extraction — LLM judge\n(gain spuriously on worked ex.)"),
        (jud["math_reasoning"], "Math reasoning — LLM judge"),
        (jud["qa"], "QA — LLM judge"),
    ]
    fig2, axes2 = plt.subplots(2, 2, figsize=(9, 7), sharey=False)
    for ax, (deltas, title) in zip(axes2.flatten(), art_panels):
        draw_panel(ax, deltas, title)
    legend_and_save(
        fig2,
        "Judge-scored marginal contributions for the four ground-truth tasks "
        "(artefact reference). Compare with the deterministic Figure 2.",
        "fig2b_marginal_judge_artifact",
    )

    # Echo key numbers.
    for task in GT_TASKS:
        d = det[task]
        tot = sum(d)
        bi = int(np.argmax(np.abs(d)))
        pct = d[bi] / tot * 100 if abs(tot) > 1e-9 else float("nan")
        print(f"  DET {task:20s} biggest={LAYER_KEYS[bi]:22s} "
              f"delta={d[bi]:+.3f} pct_of_total={pct:.1f}%")


if __name__ == "__main__":
    main()
