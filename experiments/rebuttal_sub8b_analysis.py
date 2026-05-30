"""
Analyze sub-8B results and produce numbers directly usable in the rebuttal.

Reads:  results/rebuttal/sub8b_results.json
        results/saturation_judge/saturation_results.json (for llama-3.1-8b comparison)

Writes: results/rebuttal/sub8b_analysis.json
        Prints a markdown summary suitable for pasting into responses.md.

Usage:
    python experiments/rebuttal_sub8b_analysis.py
"""

import json
import os
import sys
from pathlib import Path
from statistics import mean, stdev


REPO = Path(__file__).parent.parent
SUB8B_PATH = REPO / 'results' / 'rebuttal' / 'sub8b_results.json'
MAIN_PATH = REPO / 'results' / 'saturation_judge' / 'saturation_results.json'
OUT_PATH = REPO / 'results' / 'rebuttal' / 'sub8b_analysis.json'

TASKS = ['classification', 'product_extraction']
LEVELS = list(range(1, 8))


def load(path: Path) -> list[dict]:
    if not path.exists():
        print(f"[warn] missing: {path}")
        return []
    return json.loads(path.read_text())


def per_level_means(records: list[dict], model: str, task: str) -> dict[int, float]:
    out: dict[int, list[float]] = {lvl: [] for lvl in LEVELS}
    for r in records:
        if r.get('model') != model or r.get('task') != task or 'error' in r:
            continue
        lvl = r.get('level')
        q = r.get('quality')
        if lvl in out and isinstance(q, (int, float)):
            out[lvl].append(q)
    return {lvl: (mean(vals) if vals else float('nan')) for lvl, vals in out.items()}


def per_level_tokens(records: list[dict], model: str, task: str) -> dict[int, float]:
    out: dict[int, list[int]] = {lvl: [] for lvl in LEVELS}
    for r in records:
        if r.get('model') != model or r.get('task') != task or 'error' in r:
            continue
        lvl = r.get('level')
        t = r.get('prompt_tokens')
        if lvl in out and isinstance(t, int):
            out[lvl].append(t)
    return {lvl: (mean(vals) if vals else float('nan')) for lvl, vals in out.items()}


def fmt(x: float, n: int = 3) -> str:
    if x != x:  # NaN
        return '—'
    return f"{x:.{n}f}"


def main():
    sub8b = load(SUB8B_PATH)
    main_data = load(MAIN_PATH)

    summary: dict = {'sub8b_model': 'llama-3.2-3b', 'tasks': {}}

    print('# Sub-8B sub-results (paste into rebuttal R19f Q3)\n')
    for task in TASKS:
        sub_q = per_level_means(sub8b, 'llama-3.2-3b', task)
        ref_q = per_level_means(main_data, 'llama-3.1-8b', task)
        sub_tok = per_level_tokens(sub8b, 'llama-3.2-3b', task)
        ref_tok = per_level_tokens(main_data, 'llama-3.1-8b', task)

        n_sub = sum(1 for r in sub8b
                    if r.get('model') == 'llama-3.2-3b'
                    and r.get('task') == task
                    and 'error' not in r)

        sub_l1 = sub_q.get(1, float('nan'))
        sub_l7 = sub_q.get(7, float('nan'))
        ref_l1 = ref_q.get(1, float('nan'))
        ref_l7 = ref_q.get(7, float('nan'))

        delta_sub = sub_l7 - sub_l1 if sub_l1 == sub_l1 and sub_l7 == sub_l7 else float('nan')
        delta_ref = ref_l7 - ref_l1 if ref_l1 == ref_l1 and ref_l7 == ref_l7 else float('nan')

        print(f'## {task}\n')
        print(f'| Level | llama-3.2-3b q | llama-3.1-8b q | sub-8B tok | 8B tok |')
        print(f'|---|--:|--:|--:|--:|')
        for lvl in LEVELS:
            print(
                f'| L{lvl} | {fmt(sub_q.get(lvl, float("nan")))} '
                f'| {fmt(ref_q.get(lvl, float("nan")))} '
                f'| {fmt(sub_tok.get(lvl, float("nan")), 0)} '
                f'| {fmt(ref_tok.get(lvl, float("nan")), 0)} |'
            )
        print()
        print(f'- N (sub-8B successful runs): {n_sub}')
        print(f'- L1→L7 Δ (llama-3.2-3b): {fmt(delta_sub)}')
        print(f'- L1→L7 Δ (llama-3.1-8b reference): {fmt(delta_ref)}')
        if delta_sub == delta_sub and delta_ref == delta_ref:
            ratio = delta_sub / delta_ref if delta_ref != 0 else float('nan')
            print(f'- Effect-size ratio (sub-8B / 8B): {fmt(ratio, 2)}')
        print()

        summary['tasks'][task] = {
            'sub8b_per_level_quality': {f'L{l}': sub_q[l] for l in LEVELS},
            'ref_per_level_quality': {f'L{l}': ref_q[l] for l in LEVELS},
            'sub8b_per_level_tokens': {f'L{l}': sub_tok[l] for l in LEVELS},
            'sub8b_l1_l7_delta': delta_sub,
            'ref_l1_l7_delta': delta_ref,
            'n_sub8b_runs': n_sub,
        }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(summary, indent=2, default=str))
    print(f'\n[saved] {OUT_PATH}')


if __name__ == '__main__':
    main()
