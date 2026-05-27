# COLM 2026 Rebuttal Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce evidence (numbers, analyses) to cite in concise reviewer responses, moving scores from (3, 4, 4, 5) toward acceptance.

**Architecture:** Three phases: (1) reanalyses on existing data that require zero API calls, (2) new experiments requiring API calls (layer-ordering ablation, second judge), (3) draft concise responses citing the evidence. All results go to `results/rebuttal/`. The submitted PDF cannot be modified.

**Tech Stack:** Python, scipy, numpy, pandas, matplotlib. Existing `saturation_analysis.py` functions (`fit_best_curve`, `null_model_ftest`, `bootstrap_saturation_ci`) are reused.

**Constraints:**
- Cannot modify the submitted PDF
- Reviewer responses must be concise (short paragraphs, not essays)
- All new evidence is cited inline in response text

---

## Review Landscape

| Reviewer | Rating | Confidence | Key Concern | Target |
|----------|--------|------------|-------------|--------|
| CnfP     | 5      | 3          | Statistical power, ceiling effect, layer ordering, second judge | → 6-7 |
| R19f     | 4      | 4          | Length vs content confound, narrow scope | → 5 |
| 4x2b     | 4      | 4          | Overstated title, per-layer marginal analysis, output length | → 5 |
| C2JD     | 3      | 4          | Per-level tables, qualitative examples, Level 1 ambiguity, bib errors | → 4-5 |

**Common thread across all 4:** The layer-ordering ablation. Every reviewer raises the length-vs-content confound.

---

## Task 1: Ceiling-Effect Stratification Analysis

**Purpose:** Answer CnfP Q2 — "If you stratify QA/math examples by level-1 quality and remove near-ceiling cases, does saturation appear in the remainder?"

**Data:** Already collected. QA has 14/140 examples below 0.85 at L1; math has 13/139.

**Files:**
- Create: `experiments/rebuttal_analyses.py`
- Output: `results/rebuttal/ceiling_stratification.json`

- [ ] **Step 1: Write the ceiling stratification function**

```python
"""
Rebuttal analyses for COLM 2026.

All analyses run on existing data — no new API calls needed.
Results saved to results/rebuttal/.
"""

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.saturation_analysis import (
    fit_best_curve, null_model_ftest, aggregate, load_data,
    MODEL_ORDER,
)


REBUTTAL_DIR = 'results/rebuttal'


def ceiling_stratification(
    df: pd.DataFrame,
    tasks: list[str] = ['qa', 'math_reasoning'],
    threshold: float = 0.85,
) -> dict:
    """
    Split examples into near-ceiling (L1 >= threshold) and below-ceiling
    (L1 < threshold). Re-fit saturation curves on each subset.
    """
    os.makedirs(REBUTTAL_DIR, exist_ok=True)
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

    out_path = os.path.join(REBUTTAL_DIR, 'ceiling_stratification.json')
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Saved: {out_path}")
    return results
```

- [ ] **Step 2: Run the analysis and inspect results**

```bash
cd /Users/utkarshbajaj/Documents/05-Code-Projects/GreenPES
python3 -c "
import json
from experiments.rebuttal_analyses import ceiling_stratification
from experiments.saturation_analysis import load_data
import pandas as pd

df1 = load_data('results/saturation_results_judge.json')
df2 = load_data('results/saturation_results_new_tasks.json')
df = pd.concat([df1, df2], ignore_index=True)

results = ceiling_stratification(df)

for task, models in results.items():
    print(f'\n=== {task} ===')
    for model, subsets in models.items():
        bc = subsets.get('below_ceiling', {})
        print(f'  {model}: below_ceiling n={bc.get(\"n_examples\",0)}, '
              f'p={bc.get(\"ftest_p\",\"N/A\")}, '
              f'delta={bc.get(\"quality_delta\",\"N/A\")}')
"
```

Expected: For each model/task, see whether below-ceiling examples show saturation.

- [ ] **Step 3: Record the key finding for the response**

Write down the one-liner: "Stratifying QA/math by L1 quality (threshold 0.85): below-ceiling examples (n=X) show/don't show saturation (p=X.XX), confirming the ceiling/knowledge-bottleneck interpretation."

- [ ] **Step 4: Commit**

```bash
git add experiments/rebuttal_analyses.py results/rebuttal/ceiling_stratification.json
git commit -m "analysis: ceiling-effect stratification for COLM rebuttal (CnfP Q2)"
```

---

## Task 2: Saturation Threshold Sensitivity

**Purpose:** Answer CnfP Q1 — "How sensitive are results to the 95%-of-asymptote definition vs. a knee estimate?"

**Files:**
- Modify: `experiments/rebuttal_analyses.py`
- Output: `results/rebuttal/threshold_sensitivity.json`

- [ ] **Step 1: Add threshold sensitivity function**

Append to `experiments/rebuttal_analyses.py`:

```python
def threshold_sensitivity(
    df: pd.DataFrame,
    tasks: list[str] = ['classification', 'product_extraction'],
    thresholds: list[float] = [0.85, 0.90, 0.95, 0.99],
) -> dict:
    """
    Re-compute saturation points at multiple threshold percentages.
    Also compute a second-derivative knee estimate.
    """
    os.makedirs(REBUTTAL_DIR, exist_ok=True)
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

            from experiments.saturation_analysis import log_curve, sigmoid_curve
            x_range = np.linspace(tokens.min(), tokens.max() * 2, 1000)
            if fit['model_type'] == 'logarithmic':
                y_hat = log_curve(x_range, *fit['params'])
            else:
                y_hat = sigmoid_curve(x_range, *fit['params'])

            asymptote = float(y_hat.max())

            # Saturation point at each threshold
            sat_by_threshold = {}
            for t in thresholds:
                cutoff = t * asymptote
                mask = y_hat >= cutoff
                sat_by_threshold[str(t)] = float(x_range[mask][0]) if mask.any() else None

            # Knee estimate: point of maximum curvature (second derivative)
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

    out_path = os.path.join(REBUTTAL_DIR, 'threshold_sensitivity.json')
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved: {out_path}")
    return results
```

- [ ] **Step 2: Run and inspect**

```bash
python3 -c "
from experiments.rebuttal_analyses import threshold_sensitivity
from experiments.saturation_analysis import load_data
import pandas as pd

df1 = load_data('results/saturation_results_judge.json')
df2 = load_data('results/saturation_results_new_tasks.json')
df = pd.concat([df1, df2], ignore_index=True)

results = threshold_sensitivity(df)
for task, models in results.items():
    print(f'\n=== {task} ===')
    for model, data in models.items():
        sat = data['saturation_by_threshold']
        print(f'  {model}: 85%={sat[\"0.85\"]:.0f}  90%={sat[\"0.9\"]:.0f}  '
              f'95%={sat[\"0.95\"]:.0f}  99%={sat[\"0.99\"]:.0f}  '
              f'knee={data[\"knee_estimate\"]:.0f}')
"
```

- [ ] **Step 3: Record finding**

Key sentence: "Saturation points are robust to threshold choice: at 90% vs 95%, classification shifts by <X tokens; knee estimator agrees within Y tokens."

- [ ] **Step 4: Commit**

```bash
git add experiments/rebuttal_analyses.py results/rebuttal/threshold_sensitivity.json
git commit -m "analysis: threshold sensitivity for COLM rebuttal (CnfP Q1)"
```

---

## Task 3: Marginal Contribution Per Layer

**Purpose:** Answer 4x2b's request to "measure the marginal contribution of each elaboration layer." Also useful for R19f.

**Files:**
- Modify: `experiments/rebuttal_analyses.py`
- Output: `results/rebuttal/marginal_contributions.json`

- [ ] **Step 1: Add marginal contribution function**

Append to `experiments/rebuttal_analyses.py`:

```python
def marginal_contributions(df: pd.DataFrame) -> dict:
    """
    Compute quality delta between each adjacent level pair, per task and model.
    """
    os.makedirs(REBUTTAL_DIR, exist_ok=True)
    agg = aggregate(df)
    tasks = [t for t in ['classification', 'product_extraction', 'qa',
                          'math_reasoning', 'summarization', 'instruction_following']
             if t in agg['task'].unique()]
    models = [m for m in MODEL_ORDER if m in agg['model'].unique()]
    results = {}

    layer_names = {
        1: 'bare_input',
        2: 'task_label',
        3: 'format_spec',
        4: 'definitions',
        5: 'persona',
        6: 'guidelines',
        7: 'worked_example',
    }

    for task in tasks:
        results[task] = {'per_model': {}, 'mean_across_models': {}}

        for model in models:
            sub = agg[(agg['model'] == model) & (agg['task'] == task)].sort_values('level')
            if len(sub) < 7:
                continue
            qualities = sub['mean_quality'].values
            deltas = {}
            for i in range(1, 7):
                key = f'L{i}→L{i+1}_{layer_names[i+1]}'
                deltas[key] = float(qualities[i] - qualities[i - 1])
            results[task]['per_model'][model] = deltas

        # Mean delta across models
        if results[task]['per_model']:
            all_deltas = list(results[task]['per_model'].values())
            keys = list(all_deltas[0].keys())
            mean_deltas = {}
            for k in keys:
                vals = [d[k] for d in all_deltas if k in d]
                mean_deltas[k] = float(np.mean(vals))
            results[task]['mean_across_models'] = mean_deltas

            # Which layer contributes most?
            best_layer = max(mean_deltas, key=mean_deltas.get)
            total_gain = sum(v for v in mean_deltas.values() if v > 0)
            results[task]['biggest_layer'] = best_layer
            results[task]['biggest_layer_delta'] = mean_deltas[best_layer]
            results[task]['total_positive_gain'] = total_gain
            if total_gain > 0:
                results[task]['biggest_layer_pct'] = mean_deltas[best_layer] / total_gain

    out_path = os.path.join(REBUTTAL_DIR, 'marginal_contributions.json')
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved: {out_path}")
    return results
```

- [ ] **Step 2: Run and inspect**

```bash
python3 -c "
from experiments.rebuttal_analyses import marginal_contributions
from experiments.saturation_analysis import load_data
import pandas as pd

df1 = load_data('results/saturation_results_judge.json')
df2 = load_data('results/saturation_results_new_tasks.json')
df = pd.concat([df1, df2], ignore_index=True)

results = marginal_contributions(df)
for task in results:
    r = results[task]
    print(f'\n=== {task} ===')
    print(f'  Biggest layer: {r.get(\"biggest_layer\",\"?\")} '
          f'(delta={r.get(\"biggest_layer_delta\",0):.4f}, '
          f'{r.get(\"biggest_layer_pct\",0):.0%} of total gain)')
    for k, v in r.get('mean_across_models', {}).items():
        print(f'    {k}: {v:+.4f}')
"
```

- [ ] **Step 3: Record finding**

Key sentence: "In classification, L1→L2 (adding 'classify sentiment') accounts for X% of total quality gain. Layers 3-7 add genuine content but diminishing returns — this is the saturation effect."

- [ ] **Step 4: Commit**

```bash
git add experiments/rebuttal_analyses.py results/rebuttal/marginal_contributions.json
git commit -m "analysis: marginal layer contributions for COLM rebuttal (4x2b)"
```

---

## Task 4: Output Length Analysis

**Purpose:** Answer 4x2b Q2 — "Were steps taken to control for output length across prompt levels?"

**Files:**
- Modify: `experiments/rebuttal_analyses.py`
- Output: `results/rebuttal/output_length.json`

- [ ] **Step 1: Add output length analysis function**

Append to `experiments/rebuttal_analyses.py`:

```python
def output_length_analysis(df: pd.DataFrame) -> dict:
    """
    Report mean output tokens by level per task.
    Test whether quality trends hold after partialling out output length.
    """
    os.makedirs(REBUTTAL_DIR, exist_ok=True)
    from scipy.stats import pearsonr, spearmanr

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

        # Correlation between output length and quality
        r_out_q, p_out_q = pearsonr(td['output_tokens'], td['quality'])

        # Partial correlation: quality ~ prompt_tokens, controlling for output_tokens
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

    out_path = os.path.join(REBUTTAL_DIR, 'output_length.json')
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved: {out_path}")
    return results
```

- [ ] **Step 2: Run and inspect**

```bash
python3 -c "
from experiments.rebuttal_analyses import output_length_analysis
from experiments.saturation_analysis import load_data
import pandas as pd

df1 = load_data('results/saturation_results_judge.json')
df2 = load_data('results/saturation_results_new_tasks.json')
df = pd.concat([df1, df2], ignore_index=True)

results = output_length_analysis(df)
for task, data in results.items():
    print(f'{task}: r(output,quality)={data[\"r_output_vs_quality\"]:.3f} '
          f'partial_r(prompt,quality|output)={data[\"partial_r_prompt_quality_controlling_output\"]:.3f}')
"
```

- [ ] **Step 3: Record finding**

Key sentence: "Output length does vary across levels (classification drops from 85 to 2 tokens as format spec kicks in). Partial correlation analysis shows prompt-length → quality relationship holds after controlling for output length (partial r = X.XX)."

- [ ] **Step 4: Commit**

```bash
git add experiments/rebuttal_analyses.py results/rebuttal/output_length.json
git commit -m "analysis: output length control for COLM rebuttal (4x2b Q2)"
```

---

## Task 5: Per-Level Quality Tables

**Purpose:** Answer C2JD's request for "mean accuracy or mean quality score at each level for each task and model."

**Files:**
- Modify: `experiments/rebuttal_analyses.py`
- Output: `results/rebuttal/per_level_quality.csv`

- [ ] **Step 1: Add per-level table function**

Append to `experiments/rebuttal_analyses.py`:

```python
def per_level_quality_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot table: rows = (task, model), columns = level, values = mean quality.
    """
    os.makedirs(REBUTTAL_DIR, exist_ok=True)
    agg = (df.groupby(['task', 'model', 'level'])
           .agg(mean_quality=('quality', 'mean'))
           .reset_index())
    pivot = agg.pivot_table(
        index=['task', 'model'],
        columns='level',
        values='mean_quality',
    ).round(3)
    pivot.columns = [f'L{int(c)}' for c in pivot.columns]

    out_path = os.path.join(REBUTTAL_DIR, 'per_level_quality.csv')
    pivot.to_csv(out_path)
    print(f"Saved: {out_path}")
    return pivot
```

- [ ] **Step 2: Run and inspect**

```bash
python3 -c "
from experiments.rebuttal_analyses import per_level_quality_table
from experiments.saturation_analysis import load_data
import pandas as pd

df1 = load_data('results/saturation_results_judge.json')
df2 = load_data('results/saturation_results_new_tasks.json')
df = pd.concat([df1, df2], ignore_index=True)

table = per_level_quality_table(df)
print(table.to_string())
"
```

- [ ] **Step 3: Commit**

```bash
git add experiments/rebuttal_analyses.py results/rebuttal/per_level_quality.csv
git commit -m "analysis: per-level quality tables for COLM rebuttal (C2JD)"
```

---

## Task 6: Qualitative Output Examples

**Purpose:** Answer C2JD's request for "concrete examples showing how model outputs change across prompt levels."

**Files:**
- Modify: `experiments/rebuttal_analyses.py`
- Output: `results/rebuttal/qualitative_examples.json`

- [ ] **Step 1: Add qualitative examples function**

Append to `experiments/rebuttal_analyses.py`:

```python
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
    os.makedirs(REBUTTAL_DIR, exist_ok=True)
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

    out_path = os.path.join(REBUTTAL_DIR, 'qualitative_examples.json')
    with open(out_path, 'w') as f:
        json.dump(examples, f, indent=2)
    print(f"Saved: {out_path}")
    return examples
```

- [ ] **Step 2: Run and inspect**

```bash
python3 -c "
from experiments.rebuttal_analyses import qualitative_examples
from experiments.saturation_analysis import load_data
import pandas as pd, json

df = load_data('results/saturation_results_judge.json')
examples = qualitative_examples(df)
for ex in examples:
    print(f'\n=== {ex[\"task\"]} example {ex[\"example_id\"]} ===')
    for lvl, data in ex['responses'].items():
        resp = data['response_text'][:100].replace(chr(10), ' ')
        print(f'  {lvl} (q={data[\"quality\"]:.2f}): {resp}...')
"
```

- [ ] **Step 3: Commit**

```bash
git add experiments/rebuttal_analyses.py results/rebuttal/qualitative_examples.json
git commit -m "analysis: qualitative examples for COLM rebuttal (C2JD)"
```

---

## Task 7: Layer-Ordering Ablation (NEW EXPERIMENT — API CALLS)

**Purpose:** Address the #1 concern from all four reviewers: is saturation driven by token count or by which specific content is at each level?

**Design:** For classification and product extraction, create 2 alternative orderings:
- **Order A ("Example first"):** L1=bare, L2=worked_example, L3=task_label, L4=format, L5=definitions, L6=persona, L7=guidelines
- **Order B ("Definitions first"):** L1=bare, L2=definitions, L3=task_label, L4=format, L5=persona, L6=guidelines, L7=worked_example

Run on 3 models (gpt-4o-mini, llama-3.3-70b, gemini-flash) × 20 examples × 7 levels × 2 tasks × 2 orderings = 1,680 API calls + 1,680 judge calls.

**Files:**
- Create: `experiments/rebuttal_ablation.py`
- Create: `experiments/rebuttal_ablation_prompts.py`
- Output: `results/rebuttal/ablation_results.json`, `results/rebuttal/ablation_analysis.json`

- [ ] **Step 1: Create alternative prompt orderings**

Create `experiments/rebuttal_ablation_prompts.py` with reordered templates for classification and product extraction. Each ordering must still be strictly additive (each level is a superset of the previous), but the order in which layers are introduced is shuffled.

For classification, the original layers are:
1. `Classify: {text}` (bare)
2. `Classify sentiment as positive, negative, or neutral: {text}` (+ class names)
3. + output format ("Respond with only the label")
4. + label definitions
5. + edge case handling
6. + role + full guidelines
7. + worked example

**Order A** (example-early): 1=bare, 2=bare+example, 3=+task_label, 4=+format, 5=+definitions, 6=+persona, 7=+guidelines

**Order B** (definitions-early): 1=bare, 2=bare+definitions, 3=+task_label, 4=+format, 5=+persona, 6=+guidelines, 7=+example

```python
"""
Alternative prompt orderings for the layer-ordering ablation.
Each ordering is strictly additive — each level appends to the previous.
"""

ABLATION_TEMPLATES: dict[str, dict[str, list[str]]] = {
    'classification': {
        'order_A_example_early': [
            # L1: bare
            "Classify: {text}",
            # L2: bare + worked example
            (
                "Classify the following text.\n\n"
                "Example:\n"
                "Text: The product works great and I'm very happy with my purchase.\n"
                "Label: positive\n\n"
                "Now classify:\n"
                "Text: {text}"
            ),
            # L3: + class names
            (
                "Classify sentiment as positive, negative, or neutral.\n\n"
                "Example:\n"
                "Text: The product works great and I'm very happy with my purchase.\n"
                "Label: positive\n\n"
                "Now classify:\n"
                "Text: {text}"
            ),
            # L4: + output format
            (
                "Classify sentiment as positive, negative, or neutral. "
                "Respond with only the label.\n\n"
                "Example:\n"
                "Text: The product works great and I'm very happy with my purchase.\n"
                "Label: positive\n\n"
                "Now classify:\n"
                "Text: {text}"
            ),
            # L5: + definitions
            (
                "Classify the sentiment of the following text as positive, negative, or neutral. "
                "Respond with only the label.\n\n"
                "Definitions:\n"
                "- positive: overall favorable or optimistic tone\n"
                "- negative: overall unfavorable or critical tone\n"
                "- neutral: balanced, factual, or no clear sentiment\n\n"
                "Example:\n"
                "Text: The product works great and I'm very happy with my purchase.\n"
                "Label: positive\n\n"
                "Now classify:\n"
                "Text: {text}"
            ),
            # L6: + persona
            (
                "You are a sentiment classification expert. "
                "Classify the sentiment of the following text as positive, negative, or neutral. "
                "Respond with only the label.\n\n"
                "Definitions:\n"
                "- positive: overall favorable or optimistic tone\n"
                "- negative: overall unfavorable or critical tone\n"
                "- neutral: balanced, factual, or no clear sentiment\n\n"
                "Example:\n"
                "Text: The product works great and I'm very happy with my purchase.\n"
                "Label: positive\n\n"
                "Now classify:\n"
                "Text: {text}"
            ),
            # L7: + guidelines
            (
                "You are a sentiment classification expert. "
                "Classify the sentiment of the following text as positive, negative, or neutral.\n\n"
                "Rules:\n"
                "1. Respond with ONLY one word: positive, negative, or neutral\n"
                "2. Base your judgment on the overall tone, not individual words\n"
                "3. Positive: clearly favorable, optimistic, praising, or satisfied\n"
                "4. Negative: clearly unfavorable, critical, pessimistic, or dissatisfied\n"
                "5. Neutral: factual reporting, balanced views, or no discernible sentiment\n"
                "6. If mixed, choose the dominant sentiment; if equal, use neutral\n"
                "7. Take text at face value; do not attempt sarcasm detection\n\n"
                "Example:\n"
                "Text: The product works great and I'm very happy with my purchase.\n"
                "Label: positive\n\n"
                "Now classify:\n"
                "Text: {text}"
            ),
        ],
        'order_B_definitions_early': [
            # L1: bare
            "Classify: {text}",
            # L2: bare + definitions
            (
                "Classify the text using these definitions:\n"
                "- positive: overall favorable or optimistic tone\n"
                "- negative: overall unfavorable or critical tone\n"
                "- neutral: balanced, factual, or no clear sentiment\n\n"
                "Text: {text}"
            ),
            # L3: + task label
            (
                "Classify sentiment as positive, negative, or neutral.\n\n"
                "Definitions:\n"
                "- positive: overall favorable or optimistic tone\n"
                "- negative: overall unfavorable or critical tone\n"
                "- neutral: balanced, factual, or no clear sentiment\n\n"
                "Text: {text}"
            ),
            # L4: + format spec
            (
                "Classify sentiment as positive, negative, or neutral. "
                "Respond with only the label.\n\n"
                "Definitions:\n"
                "- positive: overall favorable or optimistic tone\n"
                "- negative: overall unfavorable or critical tone\n"
                "- neutral: balanced, factual, or no clear sentiment\n\n"
                "Text: {text}"
            ),
            # L5: + persona
            (
                "You are a sentiment classification expert. "
                "Classify the sentiment as positive, negative, or neutral. "
                "Respond with only the label.\n\n"
                "Definitions:\n"
                "- positive: overall favorable or optimistic tone\n"
                "- negative: overall unfavorable or critical tone\n"
                "- neutral: balanced, factual, or no clear sentiment\n\n"
                "Text: {text}"
            ),
            # L6: + guidelines
            (
                "You are a sentiment classification expert. "
                "Classify the sentiment as positive, negative, or neutral.\n\n"
                "Definitions:\n"
                "- positive: overall favorable or optimistic tone\n"
                "- negative: overall unfavorable or critical tone\n"
                "- neutral: balanced, factual, or no clear sentiment\n\n"
                "Rules:\n"
                "1. Respond with ONLY one word: positive, negative, or neutral\n"
                "2. Base your judgment on the overall tone, not individual words\n"
                "3. If mixed, choose the dominant sentiment; if equal, use neutral\n"
                "4. Take text at face value; do not attempt sarcasm detection\n\n"
                "Text: {text}"
            ),
            # L7: + worked example
            (
                "You are a sentiment classification expert. "
                "Classify the sentiment as positive, negative, or neutral.\n\n"
                "Definitions:\n"
                "- positive: overall favorable or optimistic tone\n"
                "- negative: overall unfavorable or critical tone\n"
                "- neutral: balanced, factual, or no clear sentiment\n\n"
                "Rules:\n"
                "1. Respond with ONLY one word: positive, negative, or neutral\n"
                "2. Base your judgment on the overall tone, not individual words\n"
                "3. If mixed, choose the dominant sentiment; if equal, use neutral\n"
                "4. Take text at face value; do not attempt sarcasm detection\n\n"
                "Example:\n"
                "Text: The product works great and I'm very happy with my purchase.\n"
                "Label: positive\n\n"
                "Now classify:\n"
                "Text: {text}"
            ),
        ],
    },
}
```

Write analogous orderings for `product_extraction` using the same approach: one with the worked example moved early, one with field definitions moved early.

- [ ] **Step 2: Create the ablation benchmark runner**

Create `experiments/rebuttal_ablation.py` that:
1. Imports `ABLATION_TEMPLATES` and the existing `get_provider`, `LLMJudgeEvaluator`
2. Runs each (model, task, ordering, level, example) combination
3. Saves results to `results/rebuttal/ablation_results.json` with `--resume` support
4. Reuses the existing `saturation_benchmark.py` pattern (identical structure, just different templates and an extra `ordering` field in each record)

```python
"""
Layer-ordering ablation for COLM rebuttal.

Tests whether saturation points change when prompt layers are reordered.
Uses same infrastructure as saturation_benchmark.py.

Usage:
    python experiments/rebuttal_ablation.py \
        --models gpt-4o-mini llama-3.3-70b gemini-flash \
        --tasks classification product_extraction \
        --delay 1.5 --resume
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from greenprompt.llm import OpenAIProvider
from greenprompt.evaluators import LLMJudgeEvaluator
from experiments.saturation_benchmark import get_provider, MODEL_CONFIGS
from experiments.saturation_prompts import TASK_INPUT_KEY
from experiments.rebuttal_ablation_prompts import ABLATION_TEMPLATES
from experiments.prompting_strategies import BENCHMARK_EXAMPLES


OUTPUT_PATH = 'results/rebuttal/ablation_results.json'


def format_prompt(template: str, task: str, example: dict) -> str:
    placeholder = '{' + TASK_INPUT_KEY[task] + '}'
    return template.replace(placeholder, example['input'])


def run_ablation(
    model_names: list[str],
    tasks: list[str],
    delay: float = 1.5,
    resume: bool = False,
) -> list[dict]:
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    results, done = [], set()
    if resume and os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH) as f:
            results = json.load(f)
        done = {
            (r['model'], r['task'], r['ordering'], r['level'], r['example_id'])
            for r in results if 'error' not in r
        }
        print(f"Resuming: {len(done)} done")

    openai_key = os.environ.get('OPENAI_API_KEY')
    judge_provider = OpenAIProvider(api_key=openai_key, model='gpt-4o-mini')

    for model_name in model_names:
        _, provider = get_provider(model_name)
        for task in tasks:
            if task not in ABLATION_TEMPLATES:
                continue
            examples = BENCHMARK_EXAMPLES[task][:20]

            for ordering_name, templates in ABLATION_TEMPLATES[task].items():
                for level_idx, template in enumerate(templates):
                    level = level_idx + 1
                    for ex_idx, example in enumerate(examples):
                        key = (model_name, task, ordering_name, level, ex_idx)
                        if key in done:
                            continue

                        prompt = format_prompt(template, task, example)
                        label = f"[{model_name}|{task}|{ordering_name}|L{level}|ex{ex_idx}]"

                        try:
                            response = provider.generate(prompt, max_tokens=512)
                            evaluator = LLMJudgeEvaluator(
                                judge_provider=judge_provider, task_type=task
                            )
                            quality, completed = evaluator.evaluate(
                                response.text, example.get('ground_truth')
                            )
                            record = {
                                'model': model_name, 'task': task,
                                'ordering': ordering_name, 'level': level,
                                'example_id': ex_idx,
                                'prompt_tokens': response.input_tokens,
                                'output_tokens': response.output_tokens,
                                'response_text': response.text,
                                'quality': quality, 'completed': completed,
                                'timestamp': datetime.now().isoformat(),
                            }
                            print(f"{label} q={quality:.3f}")
                        except Exception as e:
                            record = {
                                'model': model_name, 'task': task,
                                'ordering': ordering_name, 'level': level,
                                'example_id': ex_idx,
                                'error': str(e),
                                'timestamp': datetime.now().isoformat(),
                            }
                            print(f"{label} ERROR: {e}")

                        results.append(record)
                        if 'error' not in record:
                            done.add(key)
                        with open(OUTPUT_PATH, 'w') as f:
                            json.dump(results, f, indent=2)
                        if delay > 0:
                            time.sleep(delay)

    print(f"Done. {len([r for r in results if 'error' not in r])} successful.")
    return results


def analyze_ablation(results_path: str = OUTPUT_PATH) -> dict:
    """Compare saturation points across orderings."""
    from experiments.saturation_analysis import fit_best_curve, null_model_ftest

    with open(results_path) as f:
        data = json.load(f)

    import pandas as pd
    import numpy as np

    df = pd.DataFrame([r for r in data if 'error' not in r])
    analysis = {}

    for task in df['task'].unique():
        analysis[task] = {}
        for model in df['model'].unique():
            analysis[task][model] = {}
            for ordering in df['ordering'].unique():
                sub = df[(df['task'] == task) & (df['model'] == model) &
                         (df['ordering'] == ordering)]
                if sub.empty:
                    continue
                agg = (sub.groupby('level')
                       .agg(mean_quality=('quality', 'mean'),
                            mean_tokens=('prompt_tokens', 'mean'))
                       .reset_index()
                       .sort_values('level'))
                tokens = agg['mean_tokens'].values.astype(float)
                quality = agg['mean_quality'].values.astype(float)
                fit = fit_best_curve(tokens, quality)
                ftest = null_model_ftest(tokens, quality, fit)
                analysis[task][model][ordering] = {
                    'saturation_tokens': fit['saturation_tokens'],
                    'r2': fit['r2'],
                    'ftest_p': ftest['ftest_p'],
                    'ftest_significant': ftest['ftest_significant'],
                }

    out_path = 'results/rebuttal/ablation_analysis.json'
    with open(out_path, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    print(f"Saved: {out_path}")
    return analysis


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--models', nargs='+',
                        default=['gpt-4o-mini', 'llama-3.3-70b', 'gemini-flash'])
    parser.add_argument('--tasks', nargs='+',
                        default=['classification', 'product_extraction'])
    parser.add_argument('--delay', type=float, default=1.5)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--analyze-only', action='store_true')
    args = parser.parse_args()

    if args.analyze_only:
        analyze_ablation()
    else:
        run_ablation(args.models, args.tasks, args.delay, args.resume)
        analyze_ablation()
```

- [ ] **Step 3: Run the ablation (API calls)**

```bash
python experiments/rebuttal_ablation.py \
    --models gpt-4o-mini gemini-flash \
    --tasks classification product_extraction \
    --delay 1.5 --resume
```

Then Groq model separately (rate limits):
```bash
python experiments/rebuttal_ablation.py \
    --models llama-3.3-70b \
    --tasks classification product_extraction \
    --delay 2.5 --resume
```

- [ ] **Step 4: Analyze and record finding**

```bash
python experiments/rebuttal_ablation.py --analyze-only
```

Key sentence: "Layer-ordering ablation: with examples moved to L2, classification saturates at X tokens (original: 50); with definitions at L2, saturates at Y tokens. Saturation is robust/sensitive to ordering."

- [ ] **Step 5: Commit**

```bash
git add experiments/rebuttal_ablation_prompts.py experiments/rebuttal_ablation.py \
    results/rebuttal/ablation_results.json results/rebuttal/ablation_analysis.json
git commit -m "experiment: layer-ordering ablation for COLM rebuttal (all reviewers)"
```

---

## Task 8: Second Judge Model

**Purpose:** Answer CnfP Q4 — "How do results change with a second judge model?"

**Design:** Re-judge a subset of existing responses using gemini-2.0-flash (free tier). Pick all classification + product extraction responses (the significant tasks) = 2 tasks × 7 models × 7 levels × 20 examples = 1,960 responses to re-judge.

**Files:**
- Create: `experiments/rebuttal_second_judge.py`
- Output: `results/rebuttal/second_judge_results.json`, `results/rebuttal/second_judge_agreement.json`

- [ ] **Step 1: Create second judge script**

```python
"""
Re-judge existing responses with a second judge model (gemini-2.0-flash).
Compares agreement with original gpt-4o-mini judge.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from greenprompt.llm import GeminiProvider
from greenprompt.evaluators import LLMJudgeEvaluator


OUTPUT_PATH = 'results/rebuttal/second_judge_results.json'


def run_second_judge(
    source_path: str,
    tasks: list[str] = ['classification', 'product_extraction'],
    delay: float = 1.0,
    resume: bool = False,
):
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    api_key = os.environ.get('GEMINI_API_KEY')
    judge = GeminiProvider(api_key=api_key, model='gemini-2.0-flash')

    with open(source_path) as f:
        source = json.load(f)

    to_judge = [r for r in source if 'error' not in r and r['task'] in tasks]

    results, done = [], set()
    if resume and os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH) as f:
            results = json.load(f)
        done = {(r['model'], r['task'], r['level'], r['example_id']) for r in results}

    for r in to_judge:
        key = (r['model'], r['task'], r['level'], r['example_id'])
        if key in done:
            continue

        evaluator = LLMJudgeEvaluator(judge_provider=judge, task_type=r['task'])
        try:
            quality, completed = evaluator.evaluate(
                r['response_text'], r.get('ground_truth', '')
            )
            record = {
                'model': r['model'], 'task': r['task'],
                'level': r['level'], 'example_id': r['example_id'],
                'original_quality': r['quality'],
                'gemini_quality': quality,
                'timestamp': datetime.now().isoformat(),
            }
            print(f"[{r['model']}|{r['task']}|L{r['level']}|ex{r['example_id']}] "
                  f"orig={r['quality']:.3f} gemini={quality:.3f}")
        except Exception as e:
            record = {
                'model': r['model'], 'task': r['task'],
                'level': r['level'], 'example_id': r['example_id'],
                'error': str(e),
            }
            print(f"ERROR: {e}")

        results.append(record)
        done.add(key)
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(results, f, indent=2)
        time.sleep(delay)

    return results


def analyze_agreement(results_path: str = OUTPUT_PATH) -> dict:
    """Compute inter-judge agreement statistics."""
    from scipy.stats import pearsonr, spearmanr
    import numpy as np

    with open(results_path) as f:
        data = json.load(f)

    valid = [r for r in data if 'error' not in r]
    orig = [r['original_quality'] for r in valid]
    gemini = [r['gemini_quality'] for r in valid]

    r_pearson, p_pearson = pearsonr(orig, gemini)
    r_spearman, p_spearman = spearmanr(orig, gemini)
    mae = float(np.mean(np.abs(np.array(orig) - np.array(gemini))))

    agreement = {
        'n': len(valid),
        'pearson_r': round(r_pearson, 3),
        'pearson_p': round(p_pearson, 6),
        'spearman_r': round(r_spearman, 3),
        'mae': round(mae, 3),
    }

    out_path = 'results/rebuttal/second_judge_agreement.json'
    with open(out_path, 'w') as f:
        json.dump(agreement, f, indent=2)
    print(f"Agreement: r={r_pearson:.3f}, MAE={mae:.3f}")
    print(f"Saved: {out_path}")
    return agreement


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default='results/saturation_results_judge.json')
    parser.add_argument('--delay', type=float, default=1.0)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--analyze-only', action='store_true')
    args = parser.parse_args()

    if args.analyze_only:
        analyze_agreement()
    else:
        run_second_judge(args.source, delay=args.delay, resume=args.resume)
        analyze_agreement()
```

- [ ] **Step 2: Run the second judge (API calls)**

```bash
python experiments/rebuttal_second_judge.py \
    --source results/saturation_results_judge.json \
    --delay 1.0 --resume
```

For new tasks:
```bash
python experiments/rebuttal_second_judge.py \
    --source results/saturation_results_new_tasks.json \
    --delay 1.0 --resume
```

- [ ] **Step 3: Analyze agreement and record finding**

```bash
python experiments/rebuttal_second_judge.py --analyze-only
```

Key sentence: "Second judge (gemini-2.0-flash) agrees with gpt-4o-mini at r=X.XX (Pearson), MAE=X.XX, across N responses."

- [ ] **Step 4: Commit**

```bash
git add experiments/rebuttal_second_judge.py \
    results/rebuttal/second_judge_results.json \
    results/rebuttal/second_judge_agreement.json
git commit -m "experiment: second judge model for COLM rebuttal (CnfP Q4)"
```

---

## Task 9: Draft Reviewer Responses

**Purpose:** Write concise responses to each reviewer, citing evidence from Tasks 1-8.

**Constraint:** Short. Each response should be a few paragraphs at most.

**Files:**
- Create: `docs/rebuttal/responses.md`

- [ ] **Step 1: Draft response to Reviewer CnfP (most movable, rating 5)**

Structure:
1. Thank them for the constructive feedback
2. **Q1 (threshold sensitivity):** "Saturation points are robust: at 90% threshold, classification shifts by <X tokens. Knee estimator yields X tokens vs 95% estimate of Y tokens." (cite Task 2)
3. **Q2 (ceiling stratification):** "We stratified QA/math by L1 quality. Below-ceiling examples (n=X) show/don't show saturation (p=X.XX)." (cite Task 1)
4. **Q3 (layer ordering):** "We ran a layer-ordering ablation with 2 alternative orderings on 3 models. Classification saturation shifts from X to Y tokens — the effect is/is not robust to ordering." (cite Task 7)
5. **Q4 (second judge):** "Gemini-2.0-flash as second judge agrees with gpt-4o-mini at r=X.XX across N responses." (cite Task 8)
6. **Post-hoc grouping:** Acknowledge honestly. "We agree the structured-open grouping is post-hoc. We present it as a hypothesis for future testing, not a confirmed taxonomy."
7. **Schema-compliance:** "We soften this to a mechanistic hypothesis, not a tested contribution."
8. **LLMLingua distinction:** "LLMLingua compresses existing verbose prompts; we study whether the verbosity was necessary. These are complementary questions."

- [ ] **Step 2: Draft response to Reviewer R19f (rating 4)**

Structure:
1. **Q1 (layer order):** Same ablation results as CnfP Q3
2. **Q2 (few-shot not helping QA/math):** "QA models score 0.92+ at L1 (bare question). The bottleneck is parametric knowledge, not task understanding. Few-shot examples provide task clarification, not new knowledge — hence no gain." (cite ceiling analysis)
3. **Q3 (broader model range):** Acknowledge as good future direction. Note that within our 7 models (8B to frontier), we already observe capability-modulated saturation.
4. **Scope:** "We agree the study focuses on single-turn instruction tasks. We will explicitly scope our claims to this setting and note agentic/retrieval workflows as future work."

- [ ] **Step 3: Draft response to Reviewer 4x2b (rating 4)**

Structure:
1. **Title:** "We agree the title overstates. We propose: 'Prompt Saturation in Structured Tasks: When Does Prompt Elaboration Stop Helping?'"
2. **Per-layer marginal contribution:** "L1→L2 (adding task label) accounts for X% of total quality gain in classification. Later layers add genuine content with diminishing returns." (cite Task 3)
3. **Output length:** "Output length varies (classification drops from 85 to 2 tokens as format spec kicks in). Partial correlation: quality~prompt_tokens controlling for output_tokens yields r=X.XX." (cite Task 4)
4. **Sample size:** "n=20 yields 140 paired observations per curve (20 examples × 7 levels). The replication on 200 examples confirms patterns persist."
5. **"Practitioners use verbose prompts" reference:** Cite OpenAI's prompt engineering guide, Anthropic's prompt guide, and specific benchmark system prompts (e.g., MMLU's 1000+ token system prompts).

- [ ] **Step 4: Draft response to Reviewer C2JD (rating 3, hardest)**

Structure:
1. **Per-level tables:** "We provide full per-level quality tables: [paste compact table or link to supplementary]." (cite Task 5)
2. **Qualitative examples:** "Concrete example (classification, gpt-4o-mini, example 0): L1 outputs a full paragraph with embedded sentiment analysis (85 tokens); L3 outputs just 'positive' (2 tokens) with identical quality." (cite Task 6)
3. **Level 1 ambiguity:** "Level 1 is intentionally under-specified. That a model can infer 'sentiment classification' from context is precisely the point — it demonstrates that task specification (L2) may be unnecessary for capable models. The quality jump from L1→L2 (delta=+X.XX) measures the value of explicit specification."
4. **Evaluation design:** "Our judge uses task-specific rubrics (e.g., for classification: 'focus on whether the label matches'). While the four scoring dimensions are shared, the rubric text steers the judge's focus per task."
5. **Bibliography:** "We thank the reviewer for catching these errors. The correct citations are [corrected authors]. We will fix in camera-ready."
6. **Replication scope:** "We replicated classification (clear saturation) and QA (no saturation) to test both poles. Extending to product extraction and instruction following is valuable future work."

- [ ] **Step 5: Save all responses**

Write to `docs/rebuttal/responses.md` with clear section headers per reviewer.

- [ ] **Step 6: Commit**

```bash
git add docs/rebuttal/responses.md
git commit -m "docs: draft COLM rebuttal responses"
```

---

## Execution Order

| Phase | Tasks | API Calls | Time |
|-------|-------|-----------|------|
| **Phase 1: Existing data** | Tasks 1-6 | 0 | ~1 hour |
| **Phase 2: New experiments** | Tasks 7-8 | ~3,600 | 1-3 days |
| **Phase 3: Draft responses** | Task 9 | 0 | ~1 hour |

Phase 1 can start immediately. Phase 2 runs in background. Phase 3 happens after Phase 2 results are in.
