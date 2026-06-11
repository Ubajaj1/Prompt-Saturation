"""
Backfill LLM judge scores for repeated_runs entries that were generated
without scoring (--evaluator none, i.e. Bedrock generation-only runs).

Reads repeated_runs.json, finds entries missing judge_scores, calls
gpt-4o-mini judge on each stored response_text, and updates the file
in-place with quality + judge_scores + completed fields.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from greenprompt.llm import OpenAIProvider
from greenprompt.evaluators import LLMJudgeEvaluator
from experiments.prompting_strategies import BENCHMARK_EXAMPLES

DATA = os.path.join(ROOT, "results", "rebuttal_v2", "repeated_runs.json")
DELAY = 0.5


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY required"); sys.exit(1)

    judge_provider = OpenAIProvider(api_key=api_key, model="gpt-4o-mini")

    with open(DATA) as f:
        records = json.load(f)

    to_score = [
        (i, r) for i, r in enumerate(records)
        if "judge_scores" not in r and r.get("response_text")
    ]
    print(f"Total records: {len(records)}, needing judge scores: {len(to_score)}")

    if not to_score:
        print("Nothing to do.")
        return

    for count, (idx, rec) in enumerate(to_score, 1):
        task = rec["task"]
        example_id = int(rec["example_id"])
        response_text = rec["response_text"]

        ex = BENCHMARK_EXAMPLES[task][example_id]
        ground_truth = ex.get("ground_truth")

        evaluator = LLMJudgeEvaluator(
            judge_provider=judge_provider, task_type=task
        )
        quality, completed = evaluator.evaluate(response_text, ground_truth)
        scores = evaluator.last_scores

        records[idx]["quality"] = quality
        records[idx]["completed"] = completed
        if scores is not None:
            records[idx]["judge_scores"] = scores

        label = f"[{rec['model']} | {task} | L{rec['level']} | ex{example_id} | run{rec.get('run_id',0)}]"
        judge_ok = "judge" if scores else "fallback"
        print(f"  {count}/{len(to_score)} {label} quality={quality:.3f} ({judge_ok})")

        if count % 50 == 0:
            _save(records)
            print(f"  -- checkpoint saved ({count}/{len(to_score)})")

        time.sleep(DELAY)

    _save(records)
    print(f"\nDone. Scored {len(to_score)} entries.")


def _save(records):
    tmp = DATA + ".tmp"
    with open(tmp, "w") as f:
        json.dump(records, f, indent=2)
    os.replace(tmp, DATA)


if __name__ == "__main__":
    main()
