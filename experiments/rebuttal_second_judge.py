"""
Re-judge existing responses with gemini-2.0-flash as a second judge.
Compares agreement with original gpt-4o-mini judge scores.

Usage:
    python experiments/rebuttal_second_judge.py --delay 1.0 --resume
    python experiments/rebuttal_second_judge.py --analyze-only
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

from greenprompt.llm import GeminiProvider
from greenprompt.evaluators import LLMJudgeEvaluator
from experiments.prompting_strategies import BENCHMARK_EXAMPLES


OUTPUT_PATH = 'results/rebuttal/second_judge_results.json'

SOURCE_FILES = [
    'results/saturation_results_judge.json',
    'results/saturation_results_new_tasks.json',
]

TASKS_TO_JUDGE = [
    'classification', 'product_extraction',
    'qa', 'math_reasoning',
]


def _load_source_records() -> list[dict]:
    """Load original results from all source files."""
    records = []
    for path in SOURCE_FILES:
        if not os.path.exists(path):
            continue
        with open(path) as f:
            data = json.load(f)
        records.extend(r for r in data if 'error' not in r)
    return records


def _get_ground_truth(task: str, example_id: int) -> str:
    """Look up ground truth from BENCHMARK_EXAMPLES."""
    examples = BENCHMARK_EXAMPLES.get(task, [])
    if example_id < len(examples):
        return examples[example_id].get('ground_truth', '')
    return ''


def _load_existing(resume: bool) -> tuple[list[dict], set[tuple]]:
    if not resume or not os.path.exists(OUTPUT_PATH):
        return [], set()
    try:
        with open(OUTPUT_PATH) as f:
            existing = json.load(f)
        done = {
            (r['model'], r['task'], r['level'], r['example_id'])
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


def run_second_judge(
    tasks: list[str] = TASKS_TO_JUDGE,
    delay: float = 1.0,
    resume: bool = False,
) -> list[dict]:
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY required")
        sys.exit(1)

    judge = GeminiProvider(api_key=api_key, model='gemini-2.0-flash')

    source = _load_source_records()
    to_judge = [r for r in source if r['task'] in tasks]
    print(f"Source records to re-judge: {len(to_judge)}")

    results, done = _load_existing(resume)
    print(f"Resuming: {len(done)} done" if done else "Starting fresh run")

    for r in to_judge:
        key = (r['model'], r['task'], r['level'], r['example_id'])
        if key in done:
            continue

        ground_truth = _get_ground_truth(r['task'], r['example_id'])
        evaluator = LLMJudgeEvaluator(judge_provider=judge, task_type=r['task'])
        label = f"[{r['model']}|{r['task']}|L{r['level']}|ex{r['example_id']}]"

        try:
            quality, completed = evaluator.evaluate(r['response_text'], ground_truth)
            record = {
                'model': r['model'],
                'task': r['task'],
                'level': r['level'],
                'example_id': r['example_id'],
                'original_quality': r['quality'],
                'gemini_quality': quality,
                'gemini_scores': evaluator.last_scores,
                'timestamp': datetime.now().isoformat(),
            }
            print(f"{label} orig={r['quality']:.3f} gemini={quality:.3f}")

        except Exception as e:
            record = {
                'model': r['model'],
                'task': r['task'],
                'level': r['level'],
                'example_id': r['example_id'],
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
    print(f"\nDone. {successful} successful re-judgments.")
    return results


def analyze_agreement(results_path: str = OUTPUT_PATH) -> dict:
    """Compute inter-judge agreement statistics."""
    import numpy as np
    from scipy.stats import pearsonr, spearmanr

    with open(results_path) as f:
        data = json.load(f)

    valid = [r for r in data if 'error' not in r]
    if not valid:
        print("No valid results to analyze.")
        return {}

    orig = np.array([r['original_quality'] for r in valid])
    gemini = np.array([r['gemini_quality'] for r in valid])

    r_pearson, p_pearson = pearsonr(orig, gemini)
    r_spearman, p_spearman = spearmanr(orig, gemini)
    mae = float(np.mean(np.abs(orig - gemini)))
    mean_diff = float(np.mean(gemini - orig))

    # Per-task agreement
    per_task = {}
    tasks = set(r['task'] for r in valid)
    for task in sorted(tasks):
        task_records = [r for r in valid if r['task'] == task]
        t_orig = np.array([r['original_quality'] for r in task_records])
        t_gemini = np.array([r['gemini_quality'] for r in task_records])
        t_r, _ = pearsonr(t_orig, t_gemini)
        t_mae = float(np.mean(np.abs(t_orig - t_gemini)))
        per_task[task] = {
            'n': len(task_records),
            'pearson_r': round(t_r, 3),
            'mae': round(t_mae, 3),
        }

    agreement = {
        'overall': {
            'n': len(valid),
            'pearson_r': round(r_pearson, 3),
            'pearson_p': round(p_pearson, 6),
            'spearman_r': round(r_spearman, 3),
            'mae': round(mae, 3),
            'mean_diff_gemini_minus_orig': round(mean_diff, 3),
        },
        'per_task': per_task,
    }

    out_path = 'results/rebuttal/second_judge_agreement.json'
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(agreement, f, indent=2)

    print(f"\n=== Inter-Judge Agreement ===")
    print(f"Overall: r={r_pearson:.3f} (p={p_pearson:.2e}), "
          f"Spearman={r_spearman:.3f}, MAE={mae:.3f}, "
          f"mean diff={mean_diff:+.3f}, n={len(valid)}")
    for task, stats in per_task.items():
        print(f"  {task}: r={stats['pearson_r']:.3f}, MAE={stats['mae']:.3f}, n={stats['n']}")
    print(f"Saved: {out_path}")

    return agreement


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Second judge evaluation')
    parser.add_argument('--tasks', nargs='+', default=TASKS_TO_JUDGE,
                        choices=['classification', 'product_extraction',
                                 'qa', 'math_reasoning', 'summarization',
                                 'instruction_following'])
    parser.add_argument('--delay', type=float, default=1.0)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--analyze-only', action='store_true')
    args = parser.parse_args()

    if args.analyze_only:
        analyze_agreement()
    else:
        run_second_judge(tasks=args.tasks, delay=args.delay, resume=args.resume)
        analyze_agreement()
