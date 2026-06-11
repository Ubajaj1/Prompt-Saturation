"""
Fetch harder examples from public datasets for the difficulty-sensitivity experiment.
- Math: GSM8K (multi-step word problems, 5-8 reasoning steps)
- QA: HotpotQA (multi-hop reasoning questions)
- Instruction following: IFEval-inspired multi-constraint prompts

Output: experiments/hard_examples.json
"""
import json
import os
import random
import re
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(HERE, "hard_examples.json")

random.seed(42)


def fetch_hf_rows(dataset, config, split, offset, length):
    all_rows = []
    while len(all_rows) < length:
        batch = min(100, length - len(all_rows))
        url = (
            f"https://datasets-server.huggingface.co/rows"
            f"?dataset={dataset}&config={config}&split={split}"
            f"&offset={offset + len(all_rows)}&length={batch}"
        )
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        all_rows.extend(r["row"] for r in data["rows"])
    return all_rows


def fetch_gsm8k_hard(n=20):
    rows = fetch_hf_rows("openai/gsm8k", "main", "test", 0, 200)

    def count_steps(answer_text):
        return answer_text.count("<<")

    def extract_answer(answer_text):
        match = re.search(r"####\s*([\d,.\-]+)", answer_text)
        if match:
            return match.group(1).replace(",", "")
        return None

    candidates = []
    for row in rows:
        steps = count_steps(row["answer"])
        ans = extract_answer(row["answer"])
        if ans and steps >= 3:
            candidates.append({
                "input": row["question"],
                "ground_truth": ans,
                "difficulty": "hard",
                "source": "gsm8k",
                "reasoning_steps": steps,
            })

    candidates.sort(key=lambda x: x["reasoning_steps"], reverse=True)
    selected = candidates[:n]
    print(f"GSM8K: selected {len(selected)} examples, "
          f"step range: {selected[-1]['reasoning_steps']}-{selected[0]['reasoning_steps']}")
    for ex in selected:
        del ex["reasoning_steps"]
    return selected


def fetch_hotpotqa_hard(n=20):
    rows = fetch_hf_rows(
        "hotpotqa/hotpot_qa", "fullwiki", "validation", 0, 200
    )

    hard_rows = [r for r in rows if r.get("type") == "comparison" or r.get("level") == "hard"]
    if len(hard_rows) < n:
        hard_rows = rows[:n]

    random.shuffle(hard_rows)
    selected = []
    for row in hard_rows[:n]:
        selected.append({
            "input": row["question"],
            "ground_truth": row["answer"],
            "difficulty": "hard",
            "source": "hotpotqa",
        })
    print(f"HotpotQA: selected {len(selected)} hard/comparison examples")
    return selected


def make_hard_instruction_following(n=20):
    """Multi-constraint instruction following examples.
    Each has 2-3 constraints that our evaluator can check."""
    examples = [
        {
            "input": "List 5 benefits of renewable energy. Use bullet points. Each point must start with a verb. Keep total response under 100 words.",
            "constraints": ["bullet_points"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "Explain the water cycle in exactly 4 numbered steps. Each step must be one sentence only.",
            "constraints": ["numbered_list"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "In a single word, what programming paradigm treats computation as the evaluation of mathematical functions?",
            "constraints": ["single_word"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "Using bullet points, compare 3 database types (relational, document, graph). Each bullet must mention a specific use case. Do not exceed 80 words total.",
            "constraints": ["bullet_points"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "Create a numbered list of exactly 7 layers of the OSI model, from bottom to top. After each layer name, include its primary function in parentheses.",
            "constraints": ["numbered_list"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "Answer with one word only: what is the name for a data structure that follows Last-In-First-Out ordering?",
            "constraints": ["single_word"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "Using bullet points, list 6 principles of object-oriented programming. Each bullet must be exactly one sentence. Do not use the word 'class' anywhere.",
            "constraints": ["bullet_points"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "Write a numbered list of 5 steps to debug a memory leak in a web application. Each step must start with an imperative verb. Total response must be under 75 words.",
            "constraints": ["numbered_list"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "In one word, name the algorithmic technique where a problem is solved by breaking it into overlapping subproblems and storing their solutions.",
            "constraints": ["single_word"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "Using bullet points, describe 4 differences between TCP and UDP. Each bullet must contain exactly two sentences: one about TCP and one about UDP.",
            "constraints": ["bullet_points"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "Create a numbered list of exactly 5 steps for conducting a code review. Each step must include a potential pitfall to avoid in parentheses.",
            "constraints": ["numbered_list"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "In a single word, what type of software testing verifies that individual components work correctly in isolation?",
            "constraints": ["single_word"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "Using bullet points, list 5 security vulnerabilities from the OWASP Top 10. Each bullet must include the vulnerability name and a one-sentence mitigation strategy. Do not exceed 120 words.",
            "constraints": ["bullet_points"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "Write a numbered list of 4 steps to implement a CI/CD pipeline. Steps must be in chronological order. Each step must mention a specific tool by name.",
            "constraints": ["numbered_list"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "Answer in exactly one word: what is the term for a function that takes another function as an argument or returns a function?",
            "constraints": ["single_word"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "Using bullet points, explain 3 consistency models in distributed systems. Each bullet must define the model and give one real-world database that uses it. Keep response under 90 words.",
            "constraints": ["bullet_points"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "Create a numbered list of exactly 6 HTTP status codes. For each, provide the code number, name, and when it occurs. Each entry must be one line only.",
            "constraints": ["numbered_list"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "In one word only, what is the name of the design pattern that ensures a class has only one instance?",
            "constraints": ["single_word"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "Using bullet points, list 4 types of machine learning. Each bullet must include the type name, a one-sentence definition, and one example algorithm. Do not use more than 100 words total.",
            "constraints": ["bullet_points"],
            "ground_truth": None,
            "difficulty": "hard",
        },
        {
            "input": "Write a numbered list of 5 common git commands for collaboration. Each must include the command syntax and a scenario where you would use it. Do not exceed 100 words.",
            "constraints": ["numbered_list"],
            "ground_truth": None,
            "difficulty": "hard",
        },
    ]
    print(f"Instruction following: {len(examples)} hard multi-constraint examples")
    return examples[:n]


def main():
    print("Fetching harder examples from public datasets...\n")

    hard_examples = {
        "math_reasoning_hard": fetch_gsm8k_hard(20),
        "qa_hard": fetch_hotpotqa_hard(20),
        "instruction_following_hard": make_hard_instruction_following(20),
    }

    with open(OUTPUT, "w") as f:
        json.dump(hard_examples, f, indent=2)

    print(f"\nSaved to {OUTPUT}")
    for task, examples in hard_examples.items():
        print(f"  {task}: {len(examples)} examples")


if __name__ == "__main__":
    main()
