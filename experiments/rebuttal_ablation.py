"""
Layer-ordering ablation for COLM rebuttal.

Tests whether saturation points change when prompt layers are reordered.

Usage:
    python experiments/rebuttal_ablation.py \
        --models gpt-4o-mini llama-3.3-70b gemini-flash \
        --tasks classification product_extraction \
        --delay 1.5 --resume

    python experiments/rebuttal_ablation.py --analyze-only
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

from greenprompt.llm import OpenAIProvider, GeminiProvider
from greenprompt.evaluators import LLMJudgeEvaluator
from experiments.saturation_benchmark import get_provider
from experiments.saturation_prompts import TASK_INPUT_KEY
from experiments.rebuttal_ablation_prompts import ABLATION_TEMPLATES
from experiments.prompting_strategies import BENCHMARK_EXAMPLES


OUTPUT_PATH = 'results/rebuttal/ablation_results.json'


def format_prompt(template: str, task: str, example: dict) -> str:
    placeholder = '{' + TASK_INPUT_KEY[task] + '}'
    return template.replace(placeholder, example['input'])


def _load_existing(resume: bool) -> tuple[list[dict], set[tuple]]:
    if not resume or not os.path.exists(OUTPUT_PATH):
        return [], set()
    try:
        with open(OUTPUT_PATH) as f:
            existing = json.load(f)
        done = {
            (r['model'], r['task'], r['ordering'], r['level'], r['example_id'])
            for r in existing if 'error' not in r
        }
        return existing, done
    except Exception:
        return [], set()


def _save(results: list[dict]) -> None:
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    tmp = OUTPUT_PATH + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(results, f, indent=2)
    os.replace(tmp, OUTPUT_PATH)


def run_ablation(
    model_names: list[str],
    tasks: list[str],
    delay: float = 1.5,
    resume: bool = False,
) -> list[dict]:
    results, done = _load_existing(resume)
    print(f"Resuming: {len(done)} done" if done else "Starting fresh run")

    gemini_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_key:
        print("Error: GEMINI_API_KEY required for LLM judge")
        sys.exit(1)
    judge_provider = GeminiProvider(api_key=gemini_key, model='gemini-2.0-flash')

    for model_name in model_names:
        _, provider = get_provider(model_name)

        for task in tasks:
            if task not in ABLATION_TEMPLATES:
                print(f"No ablation templates for {task}, skipping")
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
                                'model': model_name,
                                'task': task,
                                'ordering': ordering_name,
                                'level': level,
                                'example_id': ex_idx,
                                'prompt_tokens': response.input_tokens,
                                'output_tokens': response.output_tokens,
                                'response_text': response.text,
                                'quality': quality,
                                'completed': completed,
                                'timestamp': datetime.now().isoformat(),
                            }
                            print(f"{label} q={quality:.3f}")

                        except Exception as e:
                            record = {
                                'model': model_name,
                                'task': task,
                                'ordering': ordering_name,
                                'level': level,
                                'example_id': ex_idx,
                                'error': str(e),
                                'timestamp': datetime.now().isoformat(),
                            }
                            print(f"{label} ERROR: {e}")

                        results.append(record)
                        if 'error' not in record:
                            done.add(key)
                        _save(results)

                        if delay > 0:
                            time.sleep(delay)

    successful = len([r for r in results if 'error' not in r])
    print(f"\nDone. {successful} successful records.")
    return results


def analyze_ablation(results_path: str = OUTPUT_PATH) -> dict:
    """Compare saturation points across orderings."""
    import numpy as np
    import pandas as pd
    from experiments.saturation_analysis import fit_best_curve, null_model_ftest

    with open(results_path) as f:
        data = json.load(f)

    df = pd.DataFrame([r for r in data if 'error' not in r])
    if df.empty:
        print("No valid results to analyze.")
        return {}

    analysis = {}

    for task in sorted(df['task'].unique()):
        analysis[task] = {}
        for model in sorted(df['model'].unique()):
            analysis[task][model] = {}
            for ordering in sorted(df['ordering'].unique()):
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
                    'saturation_tokens': round(fit['saturation_tokens'], 1)
                    if not np.isnan(fit['saturation_tokens']) else None,
                    'r2': round(fit['r2'], 3),
                    'ftest_F': round(ftest['ftest_F'], 2)
                    if not np.isnan(ftest['ftest_F']) else None,
                    'ftest_p': round(ftest['ftest_p'], 4)
                    if not np.isnan(ftest['ftest_p']) else None,
                    'ftest_significant': ftest['ftest_significant'],
                    'quality_by_level': {
                        int(row['level']): round(row['mean_quality'], 3)
                        for _, row in agg.iterrows()
                    },
                }

    out_path = 'results/rebuttal/ablation_analysis.json'
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    print(f"Saved: {out_path}")

    print("\n=== Ablation Summary ===")
    for task, models in analysis.items():
        print(f"\n{task}:")
        for model, orderings in models.items():
            print(f"  {model}:")
            for ordering, stats in orderings.items():
                sig = "SIG" if stats['ftest_significant'] else "ns"
                sat = stats['saturation_tokens'] or 'N/A'
                print(f"    {ordering}: sat={sat}  p={stats['ftest_p']}  r2={stats['r2']}  {sig}")

    return analysis


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Layer-ordering ablation')
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
