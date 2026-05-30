"""
Sub-8B model addition for rebuttal: tests whether the capability-modulated
saturation pattern (R19f Q3) extends to a model below our existing 8B floor.

Adds llama-3.2-3b-preview (Groq) on classification and product_extraction
using the same examples, prompts, and LLM judge (gpt-4o-mini) as the main
study, so results are directly comparable to llama-3.1-8b.

Output: results/rebuttal/sub8b_results.json (separate file; main-study
results in results/saturation_judge/ are not modified).

Usage:
    python experiments/rebuttal_sub8b.py
    python experiments/rebuttal_sub8b.py --resume   # if interrupted
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments.saturation_benchmark import (
    get_provider, run_saturation_benchmark, MODEL_CONFIGS,
)


MODEL = 'llama-3.2-3b'
TASKS = ['classification', 'product_extraction']
JUDGE_MODEL = 'gpt-4o-mini'
OUTPUT_PATH = 'results/rebuttal/sub8b_results.json'


def main():
    parser = argparse.ArgumentParser(
        description='Sub-8B saturation runner (rebuttal addition for R19f Q3)'
    )
    parser.add_argument('--resume', action='store_true',
                        help='Skip experiments already in the output file')
    parser.add_argument('--delay', type=float, default=2.5,
                        help='Seconds between Groq calls (default 2.5 for free-tier 30 RPM)')
    parser.add_argument('--examples', type=int, default=None,
                        help='Override examples per task (default: max available)')
    args = parser.parse_args()

    if MODEL not in MODEL_CONFIGS:
        print(f"Error: '{MODEL}' not in MODEL_CONFIGS. Add it to saturation_benchmark.py.")
        sys.exit(1)

    if not os.environ.get('HF_TOKEN'):
        print("Error: HF_TOKEN missing in environment / .env")
        sys.exit(1)
    if not os.environ.get('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY missing (needed for gpt-4o-mini judge)")
        sys.exit(1)

    _, target_provider = get_provider(MODEL)
    _, judge_provider = get_provider(JUDGE_MODEL)

    # Use all available examples per task; main-study uses 20.
    # classification has 30 available, product_extraction has 20.
    examples_per_task = args.examples if args.examples is not None else 30

    print(f"Model:    {MODEL} ({MODEL_CONFIGS[MODEL]['model']})")
    print(f"Tasks:    {TASKS}")
    print(f"Judge:    {JUDGE_MODEL}")
    print(f"Examples: up to {examples_per_task} per task (capped by source data)")
    print(f"Output:   {OUTPUT_PATH}")
    print(f"Delay:    {args.delay}s between calls")
    print()

    run_saturation_benchmark(
        providers=[(MODEL, target_provider)],
        tasks=TASKS,
        examples_per_task=examples_per_task,
        output_path=OUTPUT_PATH,
        delay_between_calls=args.delay,
        resume=args.resume,
        evaluator_type='llm_judge',
        judge_provider=judge_provider,
    )


if __name__ == '__main__':
    main()
