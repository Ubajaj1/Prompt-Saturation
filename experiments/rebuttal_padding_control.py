"""
Irrelevant-padding control experiment for COLM rebuttal.

Tests whether saturation is driven by token count or information content.
Creates prompts padded with irrelevant filler text to match the token counts
of the real additive levels, while keeping only the bare task input as
meaningful content.

If quality stays flat with padding → saturation is about information content.
If quality rises with padding → there's a raw token-count effect.

This directly addresses R19f's central concern about the length-vs-content
confound and transforms an acknowledged limitation into empirical evidence.

Usage:
    # Run the padding control experiment
    python experiments/rebuttal_padding_control.py \
        --models gemini-flash llama-3.3-70b llama-3.1-8b qwen3-32b claude-haiku \
        --tasks classification product_extraction \
        --delay 2.0 --resume

    # Analyze results only (no API calls)
    python experiments/rebuttal_padding_control.py --analyze-only

    # Compare with real saturation data
    python experiments/rebuttal_padding_control.py --analyze-only --compare
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
from experiments.saturation_prompts import TASK_INPUT_KEY


OUTPUT_PATH = 'results/rebuttal/padding_control_results.json'
ANALYSIS_PATH = 'results/rebuttal/padding_control_analysis.json'

MAX_RETRIES = 5

# Use the same curated examples as the random ablation for comparability
CURATED_EXAMPLE_INDICES = {
    'classification': [0, 2, 8, 9, 14, 20, 28],
    'product_extraction': [1, 3, 8, 12, 14, 17, 18],
}

# ── Filler text blocks ──────────────────────────────────────────────────────
# These are semantically irrelevant to the tasks. We use multiple types to
# avoid any single filler accidentally helping (e.g., if a model somehow
# benefits from seeing certain words).

FILLER_BLOCKS = [
    # Block A: Geography trivia (irrelevant to sentiment/extraction)
    (
        "The Amazon River flows through nine countries in South America. "
        "Mount Kilimanjaro is the tallest peak in Africa at 5,895 meters. "
        "The Sahara Desert covers approximately 9.2 million square kilometers. "
        "Lake Baikal in Russia contains roughly 20 percent of the world's "
        "unfrozen surface fresh water. The Great Barrier Reef stretches over "
        "2,300 kilometers along the Australian coast."
    ),
    # Block B: Historical facts (irrelevant to sentiment/extraction)
    (
        "The printing press was invented by Johannes Gutenberg around 1440. "
        "The Roman Empire reached its greatest territorial extent under Emperor "
        "Trajan in 117 AD. The first successful powered flight by the Wright "
        "Brothers occurred on December 17, 1903. The construction of the Great "
        "Wall of China spanned multiple dynasties over approximately 2,000 years."
    ),
    # Block C: Science facts (irrelevant to sentiment/extraction)
    (
        "Water molecules consist of two hydrogen atoms and one oxygen atom. "
        "The speed of light in a vacuum is approximately 299,792 kilometers "
        "per second. Photosynthesis converts carbon dioxide and water into "
        "glucose and oxygen using sunlight. The human body contains roughly "
        "37.2 trillion cells. DNA was first isolated by Friedrich Miescher "
        "in 1869."
    ),
    # Block D: Cooking/food facts (irrelevant to sentiment/extraction)
    (
        "Saffron is the most expensive spice by weight, harvested from crocus "
        "flowers. Fermentation is a metabolic process that converts sugar to "
        "acids, gases, or alcohol. The Maillard reaction occurs between amino "
        "acids and reducing sugars when food is heated. Vanilla extract requires "
        "at least 35 percent alcohol content by FDA regulations."
    ),
    # Block E: Architecture facts (irrelevant to sentiment/extraction)
    (
        "The Parthenon in Athens was completed in 432 BC and features Doric "
        "columns. Flying buttresses were a key innovation of Gothic architecture "
        "allowing thinner walls and larger windows. The Burj Khalifa stands at "
        "828 meters making it the tallest building in the world. Frank Lloyd "
        "Wright designed Fallingwater in 1935 over a waterfall in Pennsylvania."
    ),
    # Block F: Music facts (irrelevant to sentiment/extraction)
    (
        "The piano has 88 keys spanning seven octaves plus a minor third. "
        "Johann Sebastian Bach composed over 1,000 works during his lifetime. "
        "The standard tuning frequency for the note A above middle C is 440 Hz. "
        "A symphony orchestra typically contains between 70 and 100 musicians "
        "divided into four sections: strings, woodwinds, brass, and percussion."
    ),
]

# ── Padding conditions ──────────────────────────────────────────────────────
# We test three types of padding to ensure robustness:
# 1. "irrelevant_facts" - coherent but task-irrelevant text (above blocks)
# 2. "repeated_filler" - repeated neutral phrase ("Note: additional context follows.")
# 3. "random_words" - shuffled common English words (no coherent meaning)

PADDING_TYPES = ['irrelevant_facts', 'repeated_filler', 'random_words']

# Common English words for the random_words condition
COMMON_WORDS = [
    "the", "of", "and", "to", "in", "is", "that", "for", "it", "was",
    "on", "are", "as", "with", "his", "they", "be", "at", "one", "have",
    "this", "from", "by", "hot", "word", "but", "what", "some", "we",
    "can", "out", "other", "were", "all", "there", "when", "up", "use",
    "your", "how", "said", "an", "each", "she", "which", "do", "their",
    "time", "if", "will", "way", "about", "many", "then", "them", "write",
    "would", "like", "so", "these", "her", "long", "make", "thing", "see",
    "him", "two", "has", "look", "more", "day", "could", "go", "come",
    "did", "number", "sound", "no", "most", "people", "my", "over", "know",
    "water", "than", "call", "first", "who", "may", "down", "side", "been",
    "now", "find", "head", "stand", "own", "page", "should", "country",
    "found", "answer", "school", "grow", "study", "still", "learn", "plant",
]


def _generate_filler(padding_type: str, target_words: int, seed: int = 0) -> str:
    """Generate filler text of approximately target_words length."""
    rng = random.Random(seed)

    if padding_type == 'irrelevant_facts':
        # Cycle through filler blocks until we reach target length
        text_parts = []
        word_count = 0
        block_idx = 0
        while word_count < target_words:
            block = FILLER_BLOCKS[block_idx % len(FILLER_BLOCKS)]
            text_parts.append(block)
            word_count += len(block.split())
            block_idx += 1
        full_text = " ".join(text_parts)
        # Trim to approximate target
        words = full_text.split()[:target_words]
        return " ".join(words)

    elif padding_type == 'repeated_filler':
        # Repeat a neutral phrase
        phrase = "Note: additional context follows for reference purposes."
        phrase_words = len(phrase.split())
        repeats = (target_words // phrase_words) + 1
        full_text = " ".join([phrase] * repeats)
        words = full_text.split()[:target_words]
        return " ".join(words)

    elif padding_type == 'random_words':
        # Random selection of common words (no coherent meaning)
        words = [rng.choice(COMMON_WORDS) for _ in range(target_words)]
        return " ".join(words)

    else:
        raise ValueError(f"Unknown padding type: {padding_type}")


def _estimate_tokens(text: str) -> int:
    """Rough token estimate (words * 1.3 for English text)."""
    return int(len(text.split()) * 1.3)


# ── Target token counts ─────────────────────────────────────────────────────
# These are the approximate mean token counts at each level from the original
# saturation experiment. We match these with padding.

# From the actual experiment results (mean prompt tokens per level across models):
# These are calibrated from results/rebuttal/random_ablation_results.json
TARGET_TOKENS_BY_TASK = {
    'classification': {
        1: 48,    # bare "Classify: {text}"
        2: 84,    # + task label
        3: 111,   # + format spec
        4: 155,   # + definitions
        5: 175,   # + edge cases
        6: 196,   # + role + guidelines
        7: 217,   # + worked example
    },
    'product_extraction': {
        1: 66,    # bare "Extract product info: {text}"
        2: 102,   # + field names
        3: 135,   # + JSON format
        4: 194,   # + field definitions
        5: 212,   # + role + edge cases
        6: 261,   # + detailed guidelines
        7: 300,   # + worked example
    },
}


def build_padded_prompts(
    task: str,
    padding_type: str,
    seed: int = 0,
) -> list[str]:
    """
    Build 7 prompt templates where:
    - L1 = bare input (same as real experiment — the baseline)
    - L2-L7 = bare input + irrelevant padding to match real token counts

    The key insight: L1 is identical to the real experiment. If padding
    doesn't help, quality should stay flat from L1 onward. If the real
    experiment shows quality rising from L1 to L4, but the padding control
    stays flat, then the quality gain is driven by information content,
    not token count.
    """
    targets = TARGET_TOKENS_BY_TASK[task]
    input_key = TASK_INPUT_KEY[task]

    # L1: bare input (identical to real experiment)
    if task == 'classification':
        bare = "Classify: {" + input_key + "}"
    elif task == 'product_extraction':
        bare = "Extract product info: {" + input_key + "}"
    else:
        bare = "{" + input_key + "}"

    templates = [bare]  # L1

    # L2-L7: bare input + padding to match token targets
    for level in range(2, 8):
        target_total = targets[level]
        # Subtract approximate tokens from the bare prompt + input
        # (input is ~20-40 tokens typically; bare instruction is ~5-10)
        padding_tokens_needed = max(target_total - targets[1], 10)
        # Convert tokens to approximate words (tokens ≈ words * 1.3)
        padding_words = int(padding_tokens_needed / 1.3)

        filler = _generate_filler(padding_type, padding_words, seed=seed + level)

        # Structure: bare task instruction + separator + filler + input
        if task == 'classification':
            template = (
                f"Classify: {{{input_key}}}\n\n"
                f"[Additional context: {filler}]"
            )
        elif task == 'product_extraction':
            template = (
                f"Extract product info: {{{input_key}}}\n\n"
                f"[Additional context: {filler}]"
            )
        else:
            template = (
                f"{{{input_key}}}\n\n"
                f"[Additional context: {filler}]"
            )

        templates.append(template)

    return templates


def format_prompt(template: str, task: str, example: dict) -> str:
    """Replace the task-specific placeholder with example['input']."""
    placeholder = '{' + TASK_INPUT_KEY[task] + '}'
    return template.replace(placeholder, example['input'])


# ── Rate limit handling ─────────────────────────────────────────────────────

def _parse_retry_after(error_msg: str) -> float | None:
    """Extract wait time from a rate-limit error message."""
    m = re.search(r'try again in (\d+)m([\d.]+)s', str(error_msg))
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    m = re.search(r'try again in ([\d.]+)s', str(error_msg))
    if m:
        return float(m.group(1))
    return None


def _call_with_retry(fn, label: str, max_retries: int = MAX_RETRIES):
    """Call fn() with exponential backoff on rate-limit errors."""
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
                wait += 2
            print(f"  {label} rate-limited, waiting {wait:.0f}s "
                  f"(attempt {attempt+1}/{max_retries})")
            time.sleep(wait)


# ── Runner ───────────────────────────────────────────────────────────────────

def _load_existing(resume: bool) -> tuple[list[dict], set[tuple]]:
    if not resume or not os.path.exists(OUTPUT_PATH):
        return [], set()
    try:
        with open(OUTPUT_PATH) as f:
            existing = json.load(f)
        done = {
            (r['model'], r['task'], r['padding_type'], r['level'], r['example_id'])
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


def run_padding_control(
    model_names: list[str],
    tasks: list[str],
    padding_types: list[str] = PADDING_TYPES,
    delay: float = 2.0,
    resume: bool = False,
) -> list[dict]:
    """Run the padding control experiment."""

    # Set up judge
    gemini_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_key:
        print("Error: GEMINI_API_KEY required for LLM judge")
        sys.exit(1)
    judge_provider = GeminiProvider(api_key=gemini_key, model='gemini-2.0-flash')

    results, done = _load_existing(resume)
    print(f"Resuming: {len(done)} done" if done else "Starting fresh run")

    # Calculate total
    total = 0
    for task in tasks:
        n_examples = len(CURATED_EXAMPLE_INDICES.get(task, list(range(7))))
        total += len(model_names) * len(padding_types) * 7 * n_examples
    print(f"Total experiments: {total}")
    print(f"Models: {model_names}")
    print(f"Tasks: {tasks}")
    print(f"Padding types: {padding_types}")
    print()

    for model_name in model_names:
        _, provider = get_provider(model_name)

        for task in tasks:
            all_examples = BENCHMARK_EXAMPLES[task]
            indices = CURATED_EXAMPLE_INDICES.get(task, list(range(7)))
            examples = [(i, all_examples[i]) for i in indices]

            for padding_type in padding_types:
                templates = build_padded_prompts(task, padding_type)

                for level_idx, template in enumerate(templates):
                    level = level_idx + 1

                    for ex_idx, example in examples:
                        key = (model_name, task, padding_type, level, ex_idx)
                        if key in done:
                            continue

                        prompt = format_prompt(template, task, example)
                        label = (f"[{model_name}|{task}|{padding_type}|"
                                 f"L{level}|ex{ex_idx}]")

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
                                'padding_type': padding_type,
                                'level': level,
                                'example_id': ex_idx,
                                'prompt_tokens': response.input_tokens,
                                'output_tokens': response.output_tokens,
                                'response_text': response.text,
                                'quality': quality,
                                'completed': completed,
                                'timestamp': datetime.now().isoformat(),
                            }
                            print(f"{label} q={quality:.3f} "
                                  f"tokens={response.input_tokens}")

                        except Exception as e:
                            record = {
                                'model': model_name,
                                'task': task,
                                'padding_type': padding_type,
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

def analyze_padding_control(
    results_path: str = OUTPUT_PATH,
    compare_with_real: bool = False,
) -> dict:
    """
    Analyze the padding control results.

    Key question: Does quality increase with padding (token count effect)
    or stay flat (information content drives saturation)?
    """
    import numpy as np
    import pandas as pd
    from scipy import stats as scipy_stats

    with open(results_path) as f:
        data = json.load(f)

    df = pd.DataFrame([r for r in data if 'error' not in r])
    if df.empty:
        print("No valid results to analyze.")
        return {}

    analysis = {
        'summary': {},
        'per_task': {},
        'statistical_tests': {},
    }

    for task in sorted(df['task'].unique()):
        task_df = df[df['task'] == task]
        analysis['per_task'][task] = {}

        for model in sorted(task_df['model'].unique()):
            model_df = task_df[task_df['model'] == model]
            analysis['per_task'][task][model] = {}

            for padding_type in sorted(model_df['padding_type'].unique()):
                sub = model_df[model_df['padding_type'] == padding_type]

                # Aggregate by level
                agg = (sub.groupby('level')
                       .agg(
                           mean_quality=('quality', 'mean'),
                           std_quality=('quality', 'std'),
                           mean_tokens=('prompt_tokens', 'mean'),
                           n=('quality', 'count'),
                       )
                       .reset_index()
                       .sort_values('level'))

                qualities = agg['mean_quality'].values
                tokens = agg['mean_tokens'].values

                # Test: is there a significant trend?
                # Spearman correlation between level and quality
                if len(qualities) >= 3:
                    spearman_r, spearman_p = scipy_stats.spearmanr(
                        agg['level'].values, qualities
                    )
                else:
                    spearman_r, spearman_p = 0.0, 1.0

                # Linear regression slope
                if len(qualities) >= 3:
                    slope, intercept, r_value, p_value, std_err = (
                        scipy_stats.linregress(tokens, qualities)
                    )
                else:
                    slope, intercept, r_value, p_value, std_err = (
                        0, 0, 0, 1, 0
                    )

                # Quality delta L1 to L7
                l1_quality = float(qualities[0]) if len(qualities) > 0 else None
                l7_quality = float(qualities[-1]) if len(qualities) > 0 else None
                delta = (l7_quality - l1_quality) if (
                    l1_quality is not None and l7_quality is not None
                ) else None

                analysis['per_task'][task][model][padding_type] = {
                    'quality_by_level': {
                        int(row['level']): round(float(row['mean_quality']), 4)
                        for _, row in agg.iterrows()
                    },
                    'tokens_by_level': {
                        int(row['level']): round(float(row['mean_tokens']), 1)
                        for _, row in agg.iterrows()
                    },
                    'l1_quality': round(l1_quality, 4) if l1_quality else None,
                    'l7_quality': round(l7_quality, 4) if l7_quality else None,
                    'quality_delta_l1_l7': round(delta, 4) if delta else None,
                    'spearman_r': round(float(spearman_r), 4),
                    'spearman_p': round(float(spearman_p), 4),
                    'linear_slope': round(float(slope), 6),
                    'linear_r2': round(float(r_value**2), 4),
                    'linear_p': round(float(p_value), 4),
                    'trend_significant': bool(spearman_p < 0.05),
                }

    # Aggregate summary across all padding types and models
    for task in sorted(df['task'].unique()):
        task_df = df[df['task'] == task]

        # Overall: is there ANY significant trend with padding?
        all_deltas = []
        all_significant = []

        for model in task_df['model'].unique():
            for pt in task_df['padding_type'].unique():
                entry = analysis['per_task'][task].get(model, {}).get(pt, {})
                if entry and entry.get('quality_delta_l1_l7') is not None:
                    all_deltas.append(entry['quality_delta_l1_l7'])
                    all_significant.append(entry['trend_significant'])

        analysis['summary'][task] = {
            'mean_delta_across_conditions': round(
                float(np.mean(all_deltas)), 4
            ) if all_deltas else None,
            'std_delta_across_conditions': round(
                float(np.std(all_deltas)), 4
            ) if all_deltas else None,
            'num_significant_trends': sum(all_significant),
            'total_conditions': len(all_significant),
            'pct_significant': round(
                sum(all_significant) / len(all_significant) * 100, 1
            ) if all_significant else 0,
        }

    # Compare with real saturation data if requested
    if compare_with_real:
        analysis['comparison_with_real'] = _compare_with_real(df, analysis)

    # Save
    os.makedirs(os.path.dirname(ANALYSIS_PATH), exist_ok=True)
    with open(ANALYSIS_PATH, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    print(f"Saved: {ANALYSIS_PATH}")

    # Print summary
    print(f"\n{'='*70}")
    print("PADDING CONTROL EXPERIMENT RESULTS")
    print(f"{'='*70}")
    print("\nKey question: Does irrelevant padding improve quality?")
    print("(If NO → saturation is driven by information content, not token count)")
    print()

    for task, summary in analysis['summary'].items():
        print(f"  {task.upper()}:")
        delta = summary['mean_delta_across_conditions']
        delta_str = f"{delta:+.4f}" if delta is not None else "N/A"
        print(f"    Mean quality delta (L1→L7 with padding): {delta_str}")
        print(f"    Significant trends: {summary['num_significant_trends']}"
              f"/{summary['total_conditions']} conditions")
        print()

    return analysis


def _compare_with_real(padding_df, padding_analysis: dict) -> dict:
    """Compare padding control results with real saturation results."""
    import numpy as np
    import pandas as pd

    comparison = {}

    # Load real results
    real_paths = [
        'results/saturation_results_judge.json',
        'results/saturation_results_new_tasks.json',
    ]
    real_records = []
    for path in real_paths:
        if os.path.exists(path):
            with open(path) as f:
                real_records.extend([r for r in json.load(f) if 'error' not in r])

    if not real_records:
        print("Warning: No real saturation results found for comparison.")
        return comparison

    real_df = pd.DataFrame(real_records)

    for task in padding_df['task'].unique():
        comparison[task] = {}

        for model in padding_df[padding_df['task'] == task]['model'].unique():
            # Real data: quality by level
            real_sub = real_df[
                (real_df['task'] == task) & (real_df['model'] == model)
            ]
            if real_sub.empty:
                continue

            real_agg = (real_sub.groupby('level')
                        .agg(mean_quality=('quality', 'mean'))
                        .reset_index().sort_values('level'))

            real_l1 = float(real_agg[real_agg['level'] == 1]['mean_quality'].iloc[0])
            real_l7 = float(real_agg[real_agg['level'] == 7]['mean_quality'].iloc[0])
            real_delta = real_l7 - real_l1

            # Padding data: average across padding types
            padding_deltas = []
            for pt in padding_df['padding_type'].unique():
                entry = (padding_analysis.get('per_task', {})
                         .get(task, {}).get(model, {}).get(pt, {}))
                if entry and entry.get('quality_delta_l1_l7') is not None:
                    padding_deltas.append(entry['quality_delta_l1_l7'])

            mean_padding_delta = (
                float(np.mean(padding_deltas)) if padding_deltas else None
            )

            comparison[task][model] = {
                'real_delta_l1_l7': round(real_delta, 4),
                'padding_delta_l1_l7': round(mean_padding_delta, 4)
                if mean_padding_delta is not None else None,
                'difference': round(real_delta - mean_padding_delta, 4)
                if mean_padding_delta is not None else None,
                'interpretation': (
                    'Content drives quality (real >> padding)'
                    if (mean_padding_delta is not None and
                        real_delta > mean_padding_delta + 0.03)
                    else 'Token count may contribute'
                    if (mean_padding_delta is not None and
                        mean_padding_delta > 0.03)
                    else 'Both flat (ceiling effect)'
                ),
            }

    return comparison


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Irrelevant-padding control experiment'
    )
    parser.add_argument(
        '--models', nargs='+',
        default=['gemini-flash', 'llama-3.3-70b', 'llama-3.1-8b',
                 'qwen3-32b', 'claude-haiku'],
        help='Models to test',
    )
    parser.add_argument(
        '--tasks', nargs='+',
        default=['classification', 'product_extraction'],
        help='Tasks to test',
    )
    parser.add_argument(
        '--padding-types', nargs='+',
        default=PADDING_TYPES,
        choices=PADDING_TYPES,
        help='Types of padding to use',
    )
    parser.add_argument('--delay', type=float, default=2.0)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--analyze-only', action='store_true')
    parser.add_argument(
        '--compare', action='store_true',
        help='Compare with real saturation results (use with --analyze-only)',
    )
    args = parser.parse_args()

    if args.analyze_only:
        analyze_padding_control(compare_with_real=args.compare)
    else:
        run_padding_control(
            model_names=args.models,
            tasks=args.tasks,
            padding_types=args.padding_types,
            delay=args.delay,
            resume=args.resume,
        )
        analyze_padding_control(compare_with_real=True)


if __name__ == '__main__':
    main()
