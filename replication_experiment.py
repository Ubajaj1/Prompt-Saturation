"""
Standalone replication experiment.

Matches the main saturation experiment pipeline as closely as possible while
restricting the setup to:
  - 2 models
  - 2 tasks
  - 2 examples per task by default

Uses local replication datasets instead of the original benchmark example pool.
"""

import argparse
import json
import os
import sys
import time
from csv import DictReader
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent
load_dotenv(REPO_ROOT / ".env")

sys.path.insert(0, str(REPO_ROOT))

from experiments.saturation_prompts import NUM_LEVELS, SATURATION_TEMPLATES, format_prompt
from greenprompt.evaluators import LLMJudgeEvaluator, get_evaluator
from greenprompt.llm import GroqProvider, LLMProvider, OpenAIProvider


TASKS = ["classification", "qa"]
SST2_PATH = REPO_ROOT / "replication-data" / "SST-2" / "dev.tsv"
QA_PATH = REPO_ROOT / "replication-data" / "dev-v1.1-qa-only.json"

MODEL_CONFIGS: dict[str, dict] = {
    "gpt-4o-mini": {
        "provider_cls": OpenAIProvider,
        "model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
    },
    "llama-3.1-8b": {
        "provider_cls": GroqProvider,
        "model": "llama-3.1-8b-instant",
        "env_key": "GROQ_API_KEY",
    },
}


def load_classification_examples(limit: int) -> list[dict]:
    examples = []
    with SST2_PATH.open("r", encoding="utf-8") as f:
        reader = DictReader(f, delimiter="\t")
        for row in reader:
            examples.append(
                {
                    "input": row["sentence"].strip(),
                    "ground_truth": "positive" if row["label"].strip() == "1" else "negative",
                }
            )
            if len(examples) == limit:
                break

    if len(examples) < limit:
        raise ValueError(f"Expected at least {limit} SST-2 examples in {SST2_PATH}")
    return examples


def load_qa_examples(limit: int) -> list[dict]:
    with QA_PATH.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    examples = []
    for qa in payload:
        question = qa.get("question", "").strip()
        answer = qa.get("answer", "").strip()
        if not question or not answer:
            continue
        examples.append({"input": question, "ground_truth": answer})
        if len(examples) == limit:
            break

    if len(examples) < limit:
        raise ValueError(f"Expected at least {limit} QA examples in {QA_PATH}")
    return examples


def load_examples(examples_per_task: int) -> dict[str, list[dict]]:
    return {
        "classification": load_classification_examples(examples_per_task),
        "qa": load_qa_examples(examples_per_task),
    }


def get_provider(model_name: str) -> tuple[str, LLMProvider]:
    cfg = MODEL_CONFIGS[model_name]
    api_key = os.environ.get(cfg["env_key"])
    if not api_key:
        raise ValueError(
            f"Missing env var '{cfg['env_key']}' for model '{model_name}'. "
            f"Add it to {REPO_ROOT / '.env'} or export it in your shell."
        )
    provider = cfg["provider_cls"](api_key=api_key, model=cfg["model"])
    return model_name, provider


def _load_existing(output_path: Path, resume: bool) -> tuple[list[dict], set[tuple]]:
    if not resume or not output_path.exists():
        return [], set()

    try:
        with output_path.open("r", encoding="utf-8") as f:
            existing = json.load(f)
        done = {
            (r["model"], r["task"], r["prompt_level"], r["example_id"])
            for r in existing
            if "error" not in r
        }
        return existing, done
    except Exception:
        return [], set()


def _save_results(results: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, output_path)


def save_summary(results: list[dict], csv_path: Path) -> None:
    rows = [r for r in results if "error" not in r]
    if not rows:
        pd.DataFrame(columns=["model", "task", "prompt_level", "mean_score"]).to_csv(
            csv_path, index=False
        )
        return

    summary = (
        pd.DataFrame(rows)
        .groupby(["model", "task", "prompt_level"], as_index=False)["score"]
        .mean()
        .rename(columns={"score": "mean_score"})
    )
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(csv_path, index=False)


def run_replication(
    providers: list[tuple[str, LLMProvider]],
    examples_by_task: dict[str, list[dict]],
    output_path: Path,
    delay_between_calls: float = 0.0,
    resume: bool = False,
    evaluator_type: str = "llm_judge",
    judge_provider: Optional[LLMProvider] = None,
) -> list[dict]:
    results, done = _load_existing(output_path, resume)

    print(
        f"Resuming: {len(done)} experiments already done"
        if resume and done
        else "Starting fresh run"
    )

    for model_name, provider in providers:
        for task in TASKS:
            templates = SATURATION_TEMPLATES[task]
            examples = examples_by_task[task]

            for level_idx, template in enumerate(templates, start=1):
                for example_idx, example in enumerate(examples):
                    key = (model_name, task, level_idx, example_idx)
                    if key in done:
                        print(f"[{model_name} | {task} | level {level_idx} | ex {example_idx + 1}] SKIP")
                        continue

                    prompt = format_prompt(template, task, example)
                    label = f"[{model_name} | {task} | level {level_idx} | ex {example_idx + 1}]"

                    try:
                        response = provider.generate(prompt, max_tokens=256)

                        if evaluator_type == "llm_judge":
                            if judge_provider is None:
                                raise ValueError("LLM judge evaluator requires a judge provider.")
                            evaluator = LLMJudgeEvaluator(judge_provider=judge_provider, task_type=task)
                        else:
                            evaluator = get_evaluator(task)

                        score, completed = evaluator.evaluate(
                            response.text,
                            example.get("ground_truth"),
                        )

                        judge_scores = (
                            evaluator.last_scores if hasattr(evaluator, "last_scores") else None
                        )

                        record = {
                            "model": model_name,
                            "task": task,
                            "example_id": example_idx,
                            "prompt_level": level_idx,
                            "level": level_idx,
                            "prompt_tokens": response.input_tokens,
                            "output_tokens": response.output_tokens,
                            "tokens": response.input_tokens + response.output_tokens,
                            "response": response.text,
                            "response_text": response.text,
                            "score": score,
                            "quality": score,
                            "completed": completed,
                            "timestamp": datetime.now().isoformat(),
                        }
                        if judge_scores is not None:
                            record["judge_scores"] = judge_scores

                        print(f"{label} score={score:.3f} tokens={record['tokens']}")
                    except Exception as e:
                        record = {
                            "model": model_name,
                            "task": task,
                            "example_id": example_idx,
                            "prompt_level": level_idx,
                            "level": level_idx,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat(),
                        }
                        print(f"{label} ERROR: {e}")

                    results.append(record)
                    if "error" not in record:
                        done.add(key)
                    _save_results(results, output_path)

                    if delay_between_calls > 0:
                        time.sleep(delay_between_calls)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Small replication experiment")
    parser.add_argument(
        "--models",
        nargs="+",
        default=list(MODEL_CONFIGS.keys()),
        choices=list(MODEL_CONFIGS.keys()),
    )
    parser.add_argument(
        "--examples",
        type=int,
        default=2,
        help="Number of examples per task to run",
    )
    parser.add_argument(
        "--output",
        default=str(REPO_ROOT / "results" / "replication_results.json"),
    )
    parser.add_argument(
        "--summary-output",
        default=str(REPO_ROOT / "results" / "replication_summary.csv"),
    )
    parser.add_argument("--delay", type=float, default=0.0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--evaluator",
        default="llm_judge",
        choices=["heuristic", "llm_judge"],
    )
    parser.add_argument(
        "--judge-model",
        default="gpt-4o-mini",
        help="Judge model to use for --evaluator llm_judge",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    summary_path = Path(args.summary_output)

    judge_provider = None
    if args.evaluator == "llm_judge":
        judge_model = args.judge_model
        if judge_model in MODEL_CONFIGS:
            _, judge_provider = get_provider(judge_model)
        else:
            openai_key = os.environ.get("OPENAI_API_KEY")
            if not openai_key:
                raise ValueError("--evaluator llm_judge requires OPENAI_API_KEY")
            judge_provider = OpenAIProvider(api_key=openai_key, model=judge_model)
        print(f"Judge model: {args.judge_model}")

    providers = [get_provider(m) for m in args.models]
    examples_by_task = load_examples(args.examples)
    total = len(args.models) * len(TASKS) * NUM_LEVELS * args.examples

    print(f"Models:    {args.models}")
    print(f"Tasks:     {TASKS}")
    print(f"Levels:    {NUM_LEVELS} per task")
    print(f"Examples:  {args.examples} per task")
    print(f"Evaluator: {args.evaluator}")
    print(f"Total:     {total} experiments\n")

    results = run_replication(
        providers=providers,
        examples_by_task=examples_by_task,
        output_path=output_path,
        delay_between_calls=args.delay,
        resume=args.resume,
        evaluator_type=args.evaluator,
        judge_provider=judge_provider,
    )

    save_summary(results, summary_path)
    print(f"\nSaved raw results to {output_path}")
    print(f"Saved summary to {summary_path}")


if __name__ == "__main__":
    main()
