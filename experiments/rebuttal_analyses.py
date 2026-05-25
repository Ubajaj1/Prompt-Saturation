"""
Rebuttal analyses for COLM 2026.

All analyses run on existing data — no new API calls needed.
Results saved to results/rebuttal/.
"""

import json
import os

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

from experiments.saturation_analysis import (
    fit_best_curve, null_model_ftest, aggregate,
    MODEL_ORDER,
)

REBUTTAL_DIR = 'results/rebuttal'


def _ensure_dir():
    os.makedirs(REBUTTAL_DIR, exist_ok=True)


def _save_json(data, filename):
    _ensure_dir()
    path = os.path.join(REBUTTAL_DIR, filename)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Saved: {path}")


def ceiling_stratification(
    df: pd.DataFrame,
    tasks: list[str] = ['qa', 'math_reasoning'],
    threshold: float = 0.85,
) -> dict:
    """
    Split examples into near-ceiling (L1 >= threshold) and below-ceiling
    (L1 < threshold). Re-fit saturation curves on each subset.
    """
    results = {}

    for task in tasks:
        task_df = df[df['task'] == task].copy()
        models = [m for m in MODEL_ORDER if m in task_df['model'].unique()]
        results[task] = {}

        for model in models:
            model_df = task_df[task_df['model'] == model]
            l1 = model_df[model_df['level'] == 1]

            below_ids = l1[l1['quality'] < threshold]['example_id'].tolist()
            above_ids = l1[l1['quality'] >= threshold]['example_id'].tolist()

            subsets = {
                'below_ceiling': below_ids,
                'above_ceiling': above_ids,
                'all': l1['example_id'].tolist(),
            }

            model_results = {}
            for subset_name, ids in subsets.items():
                if len(ids) < 3:
                    model_results[subset_name] = {
                        'n_examples': len(ids),
                        'note': 'too few examples',
                    }
                    continue

                sub = model_df[model_df['example_id'].isin(ids)]
                agg = (sub.groupby('level')
                       .agg(mean_quality=('quality', 'mean'),
                            mean_tokens=('prompt_tokens', 'mean'),
                            n=('quality', 'count'))
                       .reset_index())

                tokens = agg['mean_tokens'].values.astype(float)
                quality = agg['mean_quality'].values.astype(float)

                fit = fit_best_curve(tokens, quality)
                ftest = null_model_ftest(tokens, quality, fit)

                model_results[subset_name] = {
                    'n_examples': len(ids),
                    'l1_mean_quality': float(sub[sub['level'] == 1]['quality'].mean()),
                    'l7_mean_quality': float(sub[sub['level'] == 7]['quality'].mean()),
                    'quality_delta': float(
                        sub[sub['level'] == 7]['quality'].mean()
                        - sub[sub['level'] == 1]['quality'].mean()
                    ),
                    'fit_type': fit['model_type'],
                    'r2': fit['r2'],
                    'saturation_tokens': fit['saturation_tokens'],
                    'ftest_F': ftest['ftest_F'],
                    'ftest_p': ftest['ftest_p'],
                    'ftest_significant': ftest['ftest_significant'],
                }

            results[task][model] = model_results

    _save_json(results, 'ceiling_stratification.json')
    return results


def threshold_sensitivity(
    df: pd.DataFrame,
    tasks: list[str] = ['classification', 'product_extraction'],
    thresholds: list[float] = [0.85, 0.90, 0.95, 0.99],
) -> dict:
    """
    Re-compute saturation points at multiple threshold percentages.
    Also compute a second-derivative knee estimate.
    """
    from experiments.saturation_analysis import log_curve, sigmoid_curve

    agg = aggregate(df)
    results = {}

    for task in tasks:
        task_agg = agg[agg['task'] == task]
        models = [m for m in MODEL_ORDER if m in task_agg['model'].unique()]
        results[task] = {}

        for model in models:
            sub = task_agg[(task_agg['model'] == model)]
            if len(sub) < 3:
                continue

            tokens = sub['mean_tokens'].values.astype(float)
            quality = sub['mean_quality'].values.astype(float)
            fit = fit_best_curve(tokens, quality)

            if fit['params'] is None:
                continue

            x_range = np.linspace(tokens.min(), tokens.max() * 2, 1000)
            if fit['model_type'] == 'logarithmic':
                y_hat = log_curve(x_range, *fit['params'])
            else:
                y_hat = sigmoid_curve(x_range, *fit['params'])

            asymptote = float(y_hat.max())

            sat_by_threshold = {}
            for t in thresholds:
                cutoff = t * asymptote
                mask = y_hat >= cutoff
                sat_by_threshold[str(t)] = float(x_range[mask][0]) if mask.any() else None

            dy = np.gradient(y_hat, x_range)
            d2y = np.gradient(dy, x_range)
            knee_idx = int(np.argmax(np.abs(d2y)))
            knee_tokens = float(x_range[knee_idx])

            results[task][model] = {
                'saturation_by_threshold': sat_by_threshold,
                'knee_estimate': knee_tokens,
                'fit_type': fit['model_type'],
                'r2': fit['r2'],
            }

    _save_json(results, 'threshold_sensitivity.json')
    return results


def marginal_contributions(df: pd.DataFrame) -> dict:
    """
    Compute quality delta between each adjacent level pair, per task and model.
    """
    agg = aggregate(df)
    tasks = [t for t in ['classification', 'product_extraction', 'qa',
                          'math_reasoning', 'summarization', 'instruction_following']
             if t in agg['task'].unique()]
    models = [m for m in MODEL_ORDER if m in agg['model'].unique()]

    layer_names = {
        1: 'bare_input', 2: 'task_label', 3: 'format_spec',
        4: 'definitions', 5: 'persona', 6: 'guidelines', 7: 'worked_example',
    }

    results = {}
    for task in tasks:
        results[task] = {'per_model': {}, 'mean_across_models': {}}

        for model in models:
            sub = agg[(agg['model'] == model) & (agg['task'] == task)].sort_values('level')
            if len(sub) < 7:
                continue
            qualities = sub['mean_quality'].values
            deltas = {}
            for i in range(1, 7):
                key = f'L{i}->L{i+1}_{layer_names[i+1]}'
                deltas[key] = float(qualities[i] - qualities[i - 1])
            results[task]['per_model'][model] = deltas

        if results[task]['per_model']:
            all_deltas = list(results[task]['per_model'].values())
            keys = list(all_deltas[0].keys())
            mean_deltas = {}
            for k in keys:
                vals = [d[k] for d in all_deltas if k in d]
                mean_deltas[k] = float(np.mean(vals))
            results[task]['mean_across_models'] = mean_deltas

            best_layer = max(mean_deltas, key=mean_deltas.get)
            total_gain = sum(v for v in mean_deltas.values() if v > 0)
            results[task]['biggest_layer'] = best_layer
            results[task]['biggest_layer_delta'] = mean_deltas[best_layer]
            results[task]['total_positive_gain'] = total_gain
            if total_gain > 0:
                results[task]['biggest_layer_pct'] = mean_deltas[best_layer] / total_gain

    _save_json(results, 'marginal_contributions.json')
    return results


def output_length_analysis(df: pd.DataFrame) -> dict:
    """
    Report mean output tokens by level per task.
    Partial correlation: quality ~ prompt_tokens controlling for output_tokens.
    """
    tasks = [t for t in ['classification', 'product_extraction', 'qa',
                          'math_reasoning', 'summarization', 'instruction_following']
             if t in df['task'].unique()]

    results = {}
    for task in tasks:
        td = df[df['task'] == task].copy()
        by_level = (td.groupby('level')
                    .agg(mean_out_tokens=('output_tokens', 'mean'),
                         mean_quality=('quality', 'mean'))
                    .reset_index())

        r_out_q, p_out_q = pearsonr(td['output_tokens'], td['quality'])
        r_prompt_q, _ = pearsonr(td['prompt_tokens'], td['quality'])
        r_prompt_out, _ = pearsonr(td['prompt_tokens'], td['output_tokens'])
        r_out_q2, _ = pearsonr(td['output_tokens'], td['quality'])

        denom = ((1 - r_prompt_out**2) * (1 - r_out_q2**2)) ** 0.5
        partial_r = (r_prompt_q - r_prompt_out * r_out_q2) / denom if denom > 0 else 0

        results[task] = {
            'output_tokens_by_level': {
                int(row['level']): round(row['mean_out_tokens'], 1)
                for _, row in by_level.iterrows()
            },
            'r_output_vs_quality': round(r_out_q, 3),
            'p_output_vs_quality': round(p_out_q, 4),
            'partial_r_prompt_quality_controlling_output': round(partial_r, 3),
        }

    _save_json(results, 'output_length.json')
    return results


def per_level_quality_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot table: rows = (task, model), columns = level, values = mean quality.
    """
    agg = (df.groupby(['task', 'model', 'level'])
           .agg(mean_quality=('quality', 'mean'))
           .reset_index())
    pivot = agg.pivot_table(
        index=['task', 'model'],
        columns='level',
        values='mean_quality',
    ).round(3)
    pivot.columns = [f'L{int(c)}' for c in pivot.columns]

    _ensure_dir()
    out_path = os.path.join(REBUTTAL_DIR, 'per_level_quality.csv')
    pivot.to_csv(out_path)
    print(f"Saved: {out_path}")
    return pivot


def qualitative_examples(
    df: pd.DataFrame,
    tasks: list[str] = ['classification', 'qa'],
    model: str = 'gpt-4o-mini',
    example_ids: list[int] = [0, 5],
    levels: list[int] = [1, 3, 5, 7],
) -> list[dict]:
    """
    Extract actual model responses at selected levels for specific examples.
    """
    examples = []

    for task in tasks:
        for eid in example_ids:
            entry = {'task': task, 'model': model, 'example_id': eid, 'responses': {}}
            for level in levels:
                rows = df[(df['task'] == task) & (df['model'] == model) &
                          (df['level'] == level) & (df['example_id'] == eid)]
                if not rows.empty:
                    row = rows.iloc[0]
                    entry['responses'][f'L{level}'] = {
                        'response_text': row.get('response_text', ''),
                        'quality': float(row['quality']),
                        'prompt_tokens': int(row['prompt_tokens']),
                    }
            examples.append(entry)

    _save_json(examples, 'qualitative_examples.json')
    return examples
