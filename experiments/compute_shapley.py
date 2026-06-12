"""Compute Shapley-style per-mechanism attributions from the random ablation data.

Level 1 = bare prompt (no mechanisms). Levels 2-7 each add one mechanism
from perm_order. Marginal contribution of mechanism at position k is
avg_quality(level k+1) - avg_quality(level k).

Shapley value = average marginal contribution across all orderings.

Outputs:
  results/revision_analysis/shapley_values.csv
  results/revision_analysis/shapley_summary.json
"""

import json, csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'results' / 'revision_analysis'
OUT.mkdir(parents=True, exist_ok=True)

data = json.load(open(ROOT / 'results' / 'rebuttal' / 'random_ablation_results.json'))

# Group by (task, model, perm_id, level) → list of qualities
groups = defaultdict(list)
perm_orders = {}
for r in data:
    if 'quality' not in r:
        continue
    key = (r['task'], r['model'], r['perm_id'], r['level'])
    groups[key].append(r['quality'])
    perm_orders[(r['task'], r['model'], r['perm_id'])] = r['perm_order']

# Compute per-level average quality for each (task, model, perm)
level_avgs = {}
for (task, model, perm_id, level), qualities in groups.items():
    level_avgs[(task, model, perm_id, level)] = sum(qualities) / len(qualities)

# Compute marginal contributions
marginals = defaultdict(list)  # mechanism → list of (task, model, marginal)
rows = []

for (task, model, perm_id), order in perm_orders.items():
    for pos, mechanism in enumerate(order):
        level_after = pos + 2   # level 2 = after adding first mechanism
        level_before = pos + 1  # level 1 = base, or previous

        q_after = level_avgs.get((task, model, perm_id, level_after))
        q_before = level_avgs.get((task, model, perm_id, level_before))

        if q_after is not None and q_before is not None:
            marginal = q_after - q_before
            marginals[(task, mechanism)].append(marginal)
            rows.append({
                'task': task,
                'model': model,
                'perm_id': perm_id,
                'mechanism': mechanism,
                'position': pos + 1,
                'quality_before': round(q_before, 4),
                'quality_after': round(q_after, 4),
                'marginal': round(marginal, 4),
            })

# Save detailed marginals
with open(OUT / 'shapley_marginals.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# Compute Shapley values (average marginal per mechanism per task)
shapley = {}
shapley_rows = []
for (task, mechanism), margs in sorted(marginals.items()):
    sv = sum(margs) / len(margs)
    shapley[(task, mechanism)] = sv
    shapley_rows.append({
        'task': task,
        'mechanism': mechanism,
        'shapley_value': round(sv, 4),
        'n_observations': len(margs),
        'min_marginal': round(min(margs), 4),
        'max_marginal': round(max(margs), 4),
    })

with open(OUT / 'shapley_values.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(shapley_rows[0].keys()))
    w.writeheader()
    w.writerows(shapley_rows)

# Also compute canonical-order attribution for comparison
# Canonical order: task_label, format_spec, definitions, persona, edge_cases, example
canonical_order = ['task_label', 'format_spec', 'definitions', 'persona', 'edge_cases', 'example']
canonical_marginals = defaultdict(list)

# From the main study data
main_data = json.load(open(ROOT / 'results' / 'saturation_results_judge.json'))
for task in ['classification']:
    for model in set(r['model'] for r in main_data if r['task'] == task):
        for level in range(1, 7):
            prev_entries = [r for r in main_data if r['task'] == task and r['model'] == model and r['level'] == level]
            next_entries = [r for r in main_data if r['task'] == task and r['model'] == model and r['level'] == level + 1]
            if prev_entries and next_entries:
                q_prev = sum(r['quality'] for r in prev_entries) / len(prev_entries)
                q_next = sum(r['quality'] for r in next_entries) / len(next_entries)
                mechanism = canonical_order[level - 1] if level - 1 < len(canonical_order) else 'unknown'
                canonical_marginals[(task, mechanism)].append(q_next - q_prev)

# Print comparison
print("=" * 70)
print("  SHAPLEY VALUES vs CANONICAL-ORDER ATTRIBUTION")
print("=" * 70)

tasks_in_data = sorted(set(t for t, _ in shapley.keys()))
mechanisms = ['task_label', 'format_spec', 'definitions', 'persona', 'edge_cases', 'example']

for task in tasks_in_data:
    print(f"\n--- {task} ---")
    print(f"{'Mechanism':>15} | {'Shapley':>10} | {'Canonical':>10} | {'Diff':>10}")
    print(f"{'':->15}-+-{'':->10}-+-{'':->10}-+-{'':->10}")

    total_shapley = 0
    for m in mechanisms:
        sv = shapley.get((task, m), 0)
        total_shapley += sv

        cm_list = canonical_marginals.get((task, m), [])
        cm = sum(cm_list) / len(cm_list) if cm_list else float('nan')

        diff = sv - cm if cm == cm else float('nan')
        cm_str = f'{cm:>10.4f}' if cm == cm else f'{"N/A":>10}'
        diff_str = f'{diff:>+10.4f}' if diff == diff else f'{"":>10}'
        print(f"{m:>15} | {sv:>10.4f} | {cm_str} | {diff_str}")

    print(f"{'TOTAL':>15} | {total_shapley:>10.4f} |")

# Summary JSON
summary = {
    'shapley_values': {
        task: {m: round(shapley.get((task, m), 0), 4) for m in mechanisms}
        for task in tasks_in_data
    },
    'description': 'Average marginal contribution of each mechanism across all orderings (5 permutations × models)',
}

with open(OUT / 'shapley_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\nFiles saved to {OUT}/")
