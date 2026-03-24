"""
Extract question/answer pairs from a SQuAD-format JSON file.

Usage:
    python scripts/extract_squad_qa.py input.json output.json
"""

import json
import sys
from pathlib import Path


def extract_pairs(input_path: Path) -> list[dict]:
    with input_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    pairs: list[dict] = []
    for article in payload.get("data", []):
        for paragraph in article.get("paragraphs", []):
            for qa in paragraph.get("qas", []):
                answers = qa.get("answers", [])
                if not answers:
                    continue
                question = qa.get("question", "").strip()
                answer = answers[0].get("text", "").strip()
                if not question or not answer:
                    continue
                pairs.append({"question": question, "answer": answer})
    return pairs


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python scripts/extract_squad_qa.py input.json output.json")

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    pairs = extract_pairs(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(pairs, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(pairs)} question/answer pairs to {output_path}")


if __name__ == "__main__":
    main()
