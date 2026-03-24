"""
Paper-style analysis for replication results.

Normalizes replication_results.json into the shape expected by the existing
saturation analysis utilities, then generates paper-style figures and a summary.
"""

import argparse
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

import experiments.saturation_analysis as sa


REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = REPO_ROOT / "results" / "replication_results.json"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "results" / "replication_analysis"

TASK_LABELS = {
    "classification": "Classification",
    "qa": "QA",
}

MODEL_COLORS = {
    "llama-3.1-8b": "#e41a1c",
    "llama-3.1-8b-instant": "#ff7f00",
    "gpt-4o-mini": "#377eb8",
}


def load_replication_data(path: Path, models: list[str] | None = None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Replication results not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    rows = []
    for record in raw:
        if "error" in record:
            continue
        model = record.get("model")
        if models and model not in models:
            continue
        task = record.get("task")
        level = record.get("level", record.get("prompt_level"))
        quality = record.get("quality", record.get("score"))
        prompt_tokens = record.get("prompt_tokens")
        if prompt_tokens is None:
            prompt_tokens = record.get("tokens")

        if model is None or task is None or level is None or quality is None or prompt_tokens is None:
            continue

        rows.append(
            {
                "model": model,
                "task": task,
                "level": int(level),
                "example_id": int(record.get("example_id", 0)),
                "prompt_tokens": float(prompt_tokens),
                "quality": float(quality),
            }
        )

    if not rows:
        raise ValueError("No usable replication records found after filtering.")

    df = pd.DataFrame(rows)
    return df


def configure_analysis_globals(models_present: list[str], tasks_present: list[str]) -> None:
    sa.TASKS = tasks_present
    sa.TASK_LABELS = {task: TASK_LABELS.get(task, task.title()) for task in tasks_present}
    sa.MODEL_ORDER = models_present
    sa.MODEL_COLORS = {
        model: MODEL_COLORS.get(model, "#333333")
        for model in models_present
    }


def run_analysis(df: pd.DataFrame, output_dir: Path, bootstrap_iterations: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    models_present = list(df["model"].drop_duplicates())
    tasks_present = list(df["task"].drop_duplicates())
    configure_analysis_globals(models_present, tasks_present)

    print(f"Loaded {len(df)} valid records")
    print(f"Models: {models_present}")
    print(f"Tasks: {tasks_present}")
    print(f"Levels: {sorted(df['level'].unique())}")

    agg = sa.aggregate(df)

    print("\nFitting curves ...")
    fits: dict = {}
    for model in models_present:
        for task in tasks_present:
            sub = agg[(agg["model"] == model) & (agg["task"] == task)]
            if len(sub) < 3:
                fits[(model, task)] = {
                    "model_type": "none",
                    "params": None,
                    "rmse": np.nan,
                    "r2": np.nan,
                    "saturation_tokens": np.nan,
                    "asymptote": np.nan,
                }
                continue
            tokens = sub["mean_tokens"].values.astype(float)
            quality = sub["mean_quality"].values.astype(float)
            fit = sa.fit_best_curve(tokens, quality)
            fits[(model, task)] = fit
            print(
                f"  {model:20s} | {task:15s} | {fit['model_type']:11s} "
                f"R2={fit['r2']:.3f} sat={fit['saturation_tokens']:.0f}"
            )

    sa.print_correlation_stats(df)

    print("\nRunning null model F-tests ...")
    ftests: dict = {}
    for model in models_present:
        for task in tasks_present:
            key = (model, task)
            sub = agg[(agg["model"] == model) & (agg["task"] == task)]
            if len(sub) < 3 or fits[key].get("params") is None:
                ftests[key] = {
                    "ftest_F": np.nan,
                    "ftest_p": np.nan,
                    "ftest_significant": False,
                }
                continue
            tokens = sub["mean_tokens"].values.astype(float)
            quality = sub["mean_quality"].values.astype(float)
            ftests[key] = sa.null_model_ftest(tokens, quality, fits[key])

    print(f"\nRunning bootstrap CIs ({bootstrap_iterations} iterations per pair) ...")
    boot_cis: dict = {}
    for model in models_present:
        for task in tasks_present:
            boot_cis[(model, task)] = sa.bootstrap_saturation_ci(
                df, model, task, n_bootstrap=bootstrap_iterations
            )

    print("\nGenerating figures ...")
    sa.plot_scaling_curves(agg, fits, str(fig_dir / "fig_rep1_scaling_curves.png"))
    sa.plot_saturation_heatmap(fits, models_present, str(fig_dir / "fig_rep2_saturation_points.png"))

    summary = sa.build_summary(fits, ftests, boot_cis, models_present, tasks_present)
    summary_path = output_dir / "replication_analysis_summary.csv"
    summary.to_csv(summary_path, index=False)
    print(f"  Saved: {summary_path}")

    sa.plot_forest(summary, str(fig_dir / "fig_rep3_forest_plot.png"))

    print("\n== Saturation points (tokens) ==")
    pivot = summary.pivot(index="model", columns="task", values="saturation_tokens")
    pivot = pivot.reindex(models_present)
    print(pivot.to_string(float_format="{:.0f}".format))


def main() -> None:
    parser = argparse.ArgumentParser(description="Replication analysis")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--models", nargs="*", default=None)
    parser.add_argument("--bootstrap-iterations", type=int, default=1000)
    args = parser.parse_args()

    df = load_replication_data(Path(args.input), args.models)
    run_analysis(df, Path(args.output_dir), args.bootstrap_iterations)


if __name__ == "__main__":
    main()
