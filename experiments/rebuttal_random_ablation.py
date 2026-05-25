"""
Randomized layer-ordering ablation for COLM rebuttal.

Instead of hand-picking 2 orderings, generates K random permutations of
layers 2-7 (L1=bare is always first). Each layer is a modular text block
that can appear in any position.

Reports distribution of saturation points across permutations.

Usage:
    python experiments/rebuttal_random_ablation.py \
        --models gemini-flash llama-3.3-70b llama-3.1-8b qwen3-32b kimi-k2 \
                 gpt-4o-mini claude-haiku \
        --num-permutations 5 --delay 2.0 --resume

    python experiments/rebuttal_random_ablation.py --analyze-only
"""

import argparse
import json
import os
import re
import sys
import time
import random
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from greenprompt.llm import GeminiProvider
from greenprompt.evaluators import LLMJudgeEvaluator
from experiments.saturation_benchmark import get_provider
from experiments.prompting_strategies import BENCHMARK_EXAMPLES


OUTPUT_PATH = 'results/rebuttal/random_ablation_results.json'
PERMUTATIONS_PATH = 'results/rebuttal/random_ablation_permutations.json'

CURATED_EXAMPLE_INDICES = {
    'classification': [0, 2, 8, 9, 14, 20, 28],
    'product_extraction': [1, 3, 8, 12, 14, 17, 18],
}

MAX_RETRIES = 5

# ── Modular layer blocks ────────────────────────────────────────────────────
# Each block is self-contained text that can appear in any order.
# Blocks are combined with double newlines between them.

LAYER_BLOCKS = {
    'classification': {
        'task_label': (
            "Task: Classify the sentiment as positive, negative, or neutral."
        ),
        'format_spec': (
            "Format: Respond with ONLY one word — positive, negative, or neutral. "
            "Do not include explanations."
        ),
        'definitions': (
            "Definitions:\n"
            "- positive: overall favorable, optimistic, praising, or satisfied tone\n"
            "- negative: overall unfavorable, critical, pessimistic, or dissatisfied tone\n"
            "- neutral: balanced, factual, or no clear sentiment"
        ),
        'edge_cases': (
            "Edge cases: If the text contains mixed sentiment, choose the dominant tone. "
            "If equally mixed, classify as neutral. "
            "Take text at face value; do not attempt sarcasm detection."
        ),
        'persona': (
            "Role: You are a sentiment classification expert. "
            "Base your judgment on the overall tone of the text, not individual words."
        ),
        'example': (
            "Example:\n"
            "Text: The product works great and I'm very happy with my purchase.\n"
            "Label: positive"
        ),
    },
    'product_extraction': {
        'task_label': (
            "Task: Extract the product name, price, brand, and category from the text."
        ),
        'format_spec': (
            "Format: Return ONLY valid JSON with keys: name, price, brand, category. "
            "No extra text."
        ),
        'definitions': (
            "Field definitions:\n"
            "- name: the full product name as stated in the text\n"
            "- price: numeric value only — strip currency symbols and commas\n"
            "- brand: the manufacturer or brand name, not the retailer\n"
            "- category: a single general product type (e.g., 'laptop', 'headphones')"
        ),
        'edge_cases': (
            "Edge cases: If price is written in words, convert to digits. "
            "If brand appears only in the product name, extract it from there. "
            "If a field cannot be determined, use \"unknown\"."
        ),
        'persona': (
            "Role: You are a product data specialist. "
            "Extract information precisely as stated in the text."
        ),
        'example': (
            "Example:\n"
            "Text: The new Bose SoundLink Flex portable speaker offers 12 hours of "
            "battery life and IP67 waterproofing. Now available for $149.00.\n"
            "Output: {\"name\": \"Bose SoundLink Flex\", \"price\": \"149\", "
            "\"brand\": \"Bose\", \"category\": \"speaker\"}"
        ),
    },
}

BARE_PROMPTS = {
    'classification': "Classify: {text}",
    'product_extraction': "Extract product info: {product_text}",
}

INTRO_PROMPTS = {
    'classification': "Classify the following text.",
    'product_extraction': "Extract product information from the following text.",
}

INPUT_KEYS = {
    'classification': 'text',
    'product_extraction': 'product_text',
}

BLOCK_NAMES = ['task_label', 'format_spec', 'definitions', 'edge_cases', 'persona', 'example']


def _parse_retry_after(error_msg: str) -> float | None:
    """Extract wait time in seconds from a Groq 429 error message."""
    m = re.search(r'try again in (\d+)m([\d.]+)s', str(error_msg))
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    m = re.search(r'try again in ([\d.]+)s', str(error_msg))
    if m:
        return float(m.group(1))
    return None


def _call_with_retry(fn, label: str, max_retries: int = MAX_RETRIES):
    """Call fn() with exponential backoff on rate-limit (429) errors."""
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as e:
            err = str(e)
            if '429' not in err or 'insufficient_quota' in err:
                raise
            if attempt == max_retries:
                raise
            wait = _parse_retry_after(err)
            if wait is None:
                wait = min(30 * (2 ** attempt), 600)
            else:
                wait += 2  # small buffer
            print(f"  {label} rate-limited, waiting {wait:.0f}s (attempt {attempt+1}/{max_retries})")
            time.sleep(wait)


# ── Prompt construction ─────────────────────────────────────────────────────

def build_prompts_for_permutation(
    task: str,
    permutation: list[str],
) -> list[str]:
    """
    Build 7 additive prompt templates for a given layer permutation.

    L1 = bare input
    L2 = intro + perm[0] + input
    L3 = intro + perm[0] + perm[1] + input
    ...
    L7 = intro + all 6 blocks in permuted order + input
    """
    blocks = LAYER_BLOCKS[task]
    input_key = INPUT_KEYS[task]
    bare = BARE_PROMPTS[task]
    intro = INTRO_PROMPTS[task]

    templates = [bare]  # L1

    for level in range(1, 7):  # L2 through L7
        included = permutation[:level]
        sections = [intro]
        for block_name in included:
            sections.append(blocks[block_name])
        sections.append(f"Text: {{{input_key}}}" if task == 'classification'
                        else f"{{{input_key}}}")
        templates.append("\n\n".join(sections))

    return templates


def generate_permutations(n: int, seed: int = 42) -> list[list[str]]:
    """Generate n unique random permutations of the 6 layer block names."""
    rng = random.Random(seed)
    seen = set()
    perms = []

    while len(perms) < n:
        p = BLOCK_NAMES.copy()
        rng.shuffle(p)
        key = tuple(p)
        if key not in seen:
            seen.add(key)
            perms.append(p)

    return perms


def format_prompt(template: str, task: str, example: dict) -> str:
    placeholder = '{' + INPUT_KEYS[task] + '}'
    return template.replace(placeholder, example['input'])


# ── Runner ───────────────────────────────────────────────────────────────────

def _load_existing(resume: bool) -> tuple[list[dict], set[tuple]]:
    if not resume or not os.path.exists(OUTPUT_PATH):
        return [], set()
    try:
        with open(OUTPUT_PATH) as f:
            existing = json.load(f)
        done = {
            (r['model'], r['task'], r['perm_id'], r['level'], r['example_id'])
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


def run_random_ablation(
    model_names: list[str],
    tasks: list[str],
    num_permutations: int = 5,
    seed: int = 42,
    delay: float = 1.5,
    resume: bool = False,
) -> list[dict]:
    # Generate and save permutations (deterministic seed for reproducibility)
    permutations = generate_permutations(num_permutations, seed=seed)

    os.makedirs(os.path.dirname(PERMUTATIONS_PATH), exist_ok=True)
    perm_record = {
        'seed': seed,
        'num_permutations': num_permutations,
        'permutations': {f'perm_{i}': p for i, p in enumerate(permutations)},
    }
    with open(PERMUTATIONS_PATH, 'w') as f:
        json.dump(perm_record, f, indent=2)
    print(f"Saved {num_permutations} permutations to {PERMUTATIONS_PATH}")
    for i, p in enumerate(permutations):
        print(f"  perm_{i}: {' → '.join(p)}")

    # Set up judge
    gemini_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_key:
        print("Error: GEMINI_API_KEY required for LLM judge")
        sys.exit(1)
    judge_provider = GeminiProvider(api_key=gemini_key, model='gemini-2.0-flash')

    results, done = _load_existing(resume)
    print(f"\nResuming: {len(done)} done" if done else "Starting fresh run")

    num_examples = len(CURATED_EXAMPLE_INDICES.get(tasks[0], list(range(7))))
    total = len(model_names) * len(tasks) * num_permutations * 7 * num_examples
    print(f"Total experiments: {total}")

    for model_name in model_names:
        _, provider = get_provider(model_name)

        for task in tasks:
            all_examples = BENCHMARK_EXAMPLES[task]
            indices = CURATED_EXAMPLE_INDICES.get(task, list(range(7)))
            examples = [(i, all_examples[i]) for i in indices]

            for perm_idx, perm in enumerate(permutations):
                perm_id = f'perm_{perm_idx}'
                templates = build_prompts_for_permutation(task, perm)

                for level_idx, template in enumerate(templates):
                    level = level_idx + 1

                    for ex_idx, example in examples:
                        key = (model_name, task, perm_id, level, ex_idx)
                        if key in done:
                            continue

                        prompt = format_prompt(template, task, example)
                        label = f"[{model_name}|{task}|{perm_id}|L{level}|ex{ex_idx}]"

                        try:
                            response = _call_with_retry(
                                lambda: provider.generate(prompt, max_tokens=512),
                                label,
                            )
                            evaluator = LLMJudgeEvaluator(
                                judge_provider=judge_provider, task_type=task,
                            )
                            quality, completed = _call_with_retry(
                                lambda: evaluator.evaluate(
                                    response.text, example.get('ground_truth'),
                                ),
                                f"{label} judge",
                            )
                            record = {
                                'model': model_name,
                                'task': task,
                                'perm_id': perm_id,
                                'perm_order': perm,
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
                                'perm_id': perm_id,
                                'perm_order': perm,
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


# ── Analysis ─────────────────────────────────────────────────────────────────

def analyze_random_ablation(results_path: str = OUTPUT_PATH) -> dict:
    """Analyze saturation points across random permutations."""
    import numpy as np
    import pandas as pd
    from experiments.saturation_analysis import fit_best_curve, null_model_ftest

    with open(results_path) as f:
        data = json.load(f)

    df = pd.DataFrame([r for r in data if 'error' not in r])
    if df.empty:
        print("No valid results.")
        return {}

    # Also load original results for comparison
    original_sats = {}
    for src in ['results/saturation_results_judge.json', 'results/saturation_results_new_tasks.json']:
        if not os.path.exists(src):
            continue
        orig_df = pd.DataFrame([r for r in json.load(open(src)) if 'error' not in r])
        for task in df['task'].unique():
            for model in df['model'].unique():
                sub = orig_df[(orig_df['task'] == task) & (orig_df['model'] == model)]
                if sub.empty:
                    continue
                agg = (sub.groupby('level')
                       .agg(mean_quality=('quality', 'mean'),
                            mean_tokens=('prompt_tokens', 'mean'))
                       .reset_index().sort_values('level'))
                tokens = agg['mean_tokens'].values.astype(float)
                quality = agg['mean_quality'].values.astype(float)
                fit = fit_best_curve(tokens, quality)
                ftest = null_model_ftest(tokens, quality, fit)
                if ftest['ftest_significant']:
                    original_sats[(model, task)] = fit['saturation_tokens']

    analysis = {}

    for task in sorted(df['task'].unique()):
        analysis[task] = {}

        for model in sorted(df['model'].unique()):
            perm_results = []

            for perm_id in sorted(df['perm_id'].unique()):
                sub = df[(df['task'] == task) & (df['model'] == model) &
                         (df['perm_id'] == perm_id)]
                if sub.empty:
                    continue

                agg = (sub.groupby('level')
                       .agg(mean_quality=('quality', 'mean'),
                            mean_tokens=('prompt_tokens', 'mean'))
                       .reset_index().sort_values('level'))

                tokens = agg['mean_tokens'].values.astype(float)
                quality = agg['mean_quality'].values.astype(float)

                fit = fit_best_curve(tokens, quality)
                ftest = null_model_ftest(tokens, quality, fit)

                perm_order = sub['perm_order'].iloc[0]
                if isinstance(perm_order, str):
                    perm_order = json.loads(perm_order)

                perm_results.append({
                    'perm_id': perm_id,
                    'perm_order': perm_order,
                    'saturation_tokens': fit['saturation_tokens'],
                    'r2': fit['r2'],
                    'ftest_p': ftest['ftest_p'],
                    'ftest_significant': ftest['ftest_significant'],
                })

            if not perm_results:
                continue

            sat_values = [p['saturation_tokens'] for p in perm_results
                          if not np.isnan(p['saturation_tokens'])]
            sig_count = sum(1 for p in perm_results if p['ftest_significant'])

            orig_sat = original_sats.get((model, task))

            analysis[task][model] = {
                'num_permutations': len(perm_results),
                'num_significant': sig_count,
                'saturation_mean': round(float(np.mean(sat_values)), 1) if sat_values else None,
                'saturation_std': round(float(np.std(sat_values)), 1) if sat_values else None,
                'saturation_min': round(float(np.min(sat_values)), 1) if sat_values else None,
                'saturation_max': round(float(np.max(sat_values)), 1) if sat_values else None,
                'original_saturation': round(orig_sat, 1) if orig_sat else None,
                'per_permutation': perm_results,
            }

    out_path = 'results/rebuttal/random_ablation_analysis.json'
    with open(out_path, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)

    print(f"\n{'='*70}")
    print("RANDOMIZED LAYER-ORDERING ABLATION RESULTS")
    print(f"{'='*70}")
    for task, models in analysis.items():
        print(f"\n{'─'*40}")
        print(f"  {task.upper()}")
        print(f"{'─'*40}")
        print(f"  {'Model':<20s} {'Original':>8s} {'Mean±Std':>12s} {'Range':>14s} {'Sig':>5s}")
        for model, stats in models.items():
            orig = f"{stats['original_saturation']:.0f}" if stats['original_saturation'] else "n/s"
            if stats['saturation_mean'] is not None:
                mean_std = f"{stats['saturation_mean']:.0f}±{stats['saturation_std']:.0f}"
                rng = f"[{stats['saturation_min']:.0f}, {stats['saturation_max']:.0f}]"
            else:
                mean_std = "N/A"
                rng = "N/A"
            sig = f"{stats['num_significant']}/{stats['num_permutations']}"
            print(f"  {model:<20s} {orig:>8s} {mean_std:>12s} {rng:>14s} {sig:>5s}")

    print(f"\nSaved: {out_path}")
    return analysis


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Randomized layer-ordering ablation')
    parser.add_argument('--models', nargs='+',
                        default=['gemini-flash', 'gpt-4o-mini', 'claude-haiku',
                                 'llama-3.3-70b', 'llama-3.1-8b', 'qwen3-32b',
                                 'kimi-k2'])
    parser.add_argument('--tasks', nargs='+',
                        default=['classification', 'product_extraction'])
    parser.add_argument('--num-permutations', type=int, default=5)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--delay', type=float, default=1.5)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--analyze-only', action='store_true')
    args = parser.parse_args()

    if args.analyze_only:
        analyze_random_ablation()
    else:
        run_random_ablation(
            model_names=args.models,
            tasks=args.tasks,
            num_permutations=args.num_permutations,
            seed=args.seed,
            delay=args.delay,
            resume=args.resume,
        )
        analyze_random_ablation()
