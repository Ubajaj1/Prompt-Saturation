"""Re-score stored product extraction and NER responses with strict, lenient, and content-presence evaluators.

Outputs:
  results/revision_analysis/rescore_product_extraction.csv
  results/revision_analysis/rescore_ner.csv
  results/revision_analysis/parse_path_breakdown.csv
  results/revision_analysis/rescore_summary.json
"""

import sys, json, csv, re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from greenprompt.evaluators import (
    ProductExtractionEvaluator,
    NERExtractionEvaluator,
    content_presence_score,
)
from experiments.prompting_strategies import BENCHMARK_EXAMPLES

OUT = ROOT / 'results' / 'revision_analysis'
OUT.mkdir(parents=True, exist_ok=True)


# ── Old strict evaluators (reimplemented to preserve original behavior) ──

def old_pe_parse(text):
    cleaned = re.sub(r'```(?:json)?\s*', '', text).strip().rstrip('`')
    match = re.search(r'\{[^}]+\}', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    result = {}
    fields = ['name', 'price', 'brand', 'category']
    for line in text.split('\n'):
        for field in fields:
            m = re.match(rf'{field}\s*:\s*(.+)', line.strip(), re.IGNORECASE)
            if m:
                result[field] = m.group(1).strip()
    return result if result else None


def old_pe_eval(response, ground_truth):
    try:
        gt = json.loads(ground_truth)
    except (json.JSONDecodeError, TypeError):
        return 0.0
    parsed = old_pe_parse(response)
    if not parsed:
        return 0.0
    matches = 0
    for field in ['name', 'price', 'brand', 'category']:
        if field in parsed and field in gt:
            ext, exp = str(parsed[field]), str(gt[field])
            if field == 'price':
                clean_e = re.sub(r'[$,]', '', ext.strip())
                clean_g = re.sub(r'[$,]', '', exp.strip())
                try:
                    ne = float(clean_e)
                    ng = float(clean_g)
                    ok = (str(int(ne)) if ne == int(ne) else str(ne)) == (str(int(ng)) if ng == int(ng) else str(ng))
                except ValueError:
                    ok = clean_e.lower() == clean_g.lower()
            elif field == 'name':
                ok = exp.lower() in ext.lower() or ext.lower() in exp.lower()
            else:
                ok = ext.lower().strip() == exp.lower().strip()
            if ok:
                matches += 1
    return matches / 4


def old_ner_parse(text):
    cleaned = re.sub(r'```(?:json)?\s*', '', text.strip()).rstrip('`')
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group())
        if isinstance(parsed, dict):
            return {k: [str(v).lower() for v in vs] if isinstance(vs, list) else [str(vs).lower()]
                    for k, vs in parsed.items()}
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def old_ner_eval(response, ground_truth):
    try:
        gt = json.loads(ground_truth)
    except (json.JSONDecodeError, TypeError):
        return 0.0
    extracted = old_ner_parse(response)
    if not extracted:
        return 0.0
    f1s = []
    for etype, gt_ents in gt.items():
        gt_set = {e.lower() for e in gt_ents}
        pred_set = {e.lower() for e in extracted.get(etype, [])}
        if not gt_set:
            continue
        tp = len(gt_set & pred_set)
        p = tp / len(pred_set) if pred_set else 0.0
        r = tp / len(gt_set)
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        f1s.append(f1)
    return sum(f1s) / len(f1s) if f1s else 0.0


def classify_parse_path(text, task):
    cleaned = re.sub(r'```(?:json)?\s*', '', text.strip()).rstrip('`')
    if re.search(r'\{[^}]*\}', cleaned, re.DOTALL):
        try:
            json.loads(re.search(r'\{.*\}', cleaned, re.DOTALL).group())
            return 'json'
        except (json.JSONDecodeError, AttributeError):
            pass
    if re.search(r'(?:^|\n)\s*[-*•]\s', text) or re.search(r'(?:^|\n)\s*\d+[.)]\s', text):
        return 'markdown_list'
    if re.search(r'\*\*[^*]+\*\*', text):
        return 'bold_keys'
    if re.search(r'\w+\s*:\s*.+', text):
        return 'plain_keyval'
    return 'prose'


# ── Product Extraction ──

new_pe = ProductExtractionEvaluator()
gt_pe = BENCHMARK_EXAMPLES['product_extraction']
data_pe = json.load(open(ROOT / 'results' / 'saturation_results_new_tasks.json'))
pe_entries = [r for r in data_pe if r['task'] == 'product_extraction' and 'response_text' in r]

rows_pe = []
for e in pe_entries:
    ex_id = e['example_id']
    if ex_id >= len(gt_pe):
        continue
    gt = gt_pe[ex_id]['ground_truth']
    resp = e['response_text']

    old_q = old_pe_eval(resp, gt)
    new_q, _ = new_pe.evaluate(resp, gt)
    cp = content_presence_score(resp, gt, 'product_extraction')
    judge_q = e.get('quality', None)
    parse_path = classify_parse_path(resp, 'product_extraction')

    rows_pe.append({
        'model': e['model'],
        'level': e['level'],
        'example_id': ex_id,
        'strict_quality': round(old_q, 4),
        'lenient_quality': round(new_q, 4),
        'content_presence': round(cp, 4),
        'judge_quality': round(judge_q, 4) if judge_q is not None else '',
        'parse_path': parse_path,
    })

with open(OUT / 'rescore_product_extraction.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows_pe[0].keys()))
    w.writeheader()
    w.writerows(rows_pe)

# ── NER ──

new_ner = NERExtractionEvaluator()
gt_ner = BENCHMARK_EXAMPLES['ner']
data_ner = json.load(open(ROOT / 'results' / 'rebuttal_v2' / 'ner_held_out.json'))
ner_entries = [r for r in data_ner if 'response_text' in r]

rows_ner = []
for e in ner_entries:
    ex_id = e['example_id']
    if ex_id >= len(gt_ner):
        continue
    gt = gt_ner[ex_id]['ground_truth']
    resp = e['response_text']

    old_q = old_ner_eval(resp, gt)
    new_q, _ = new_ner.evaluate(resp, gt)
    cp = content_presence_score(resp, gt, 'ner')
    stored_q = e.get('quality', None)
    parse_path = classify_parse_path(resp, 'ner')

    rows_ner.append({
        'model': e['model'],
        'level': e['level'],
        'example_id': ex_id,
        'strict_quality': round(old_q, 4),
        'lenient_quality': round(new_q, 4),
        'content_presence': round(cp, 4),
        'stored_quality': round(stored_q, 4) if stored_q is not None else '',
        'parse_path': parse_path,
    })

with open(OUT / 'rescore_ner.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows_ner[0].keys()))
    w.writeheader()
    w.writerows(rows_ner)

# ── Parse path breakdown ──

parse_rows = []
for task_name, rows in [('product_extraction', rows_pe), ('ner', rows_ner)]:
    for level in range(1, 8):
        level_rows = [r for r in rows if r['level'] == level]
        if not level_rows:
            continue
        paths = defaultdict(int)
        for r in level_rows:
            paths[r['parse_path']] += 1
        total = len(level_rows)
        parse_rows.append({
            'task': task_name,
            'level': level,
            'n': total,
            'json_pct': round(100 * paths.get('json', 0) / total, 1),
            'markdown_list_pct': round(100 * paths.get('markdown_list', 0) / total, 1),
            'bold_keys_pct': round(100 * paths.get('bold_keys', 0) / total, 1),
            'plain_keyval_pct': round(100 * paths.get('plain_keyval', 0) / total, 1),
            'prose_pct': round(100 * paths.get('prose', 0) / total, 1),
        })

with open(OUT / 'parse_path_breakdown.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(parse_rows[0].keys()))
    w.writeheader()
    w.writerows(parse_rows)

# ── Summary ──

summary = {}
for task_name, rows in [('product_extraction', rows_pe), ('ner', rows_ner)]:
    task_summary = {}
    for level in range(1, 8):
        level_rows = [r for r in rows if r['level'] == level]
        if not level_rows:
            continue
        task_summary[f'L{level}'] = {
            'strict': round(sum(r['strict_quality'] for r in level_rows) / len(level_rows), 4),
            'lenient': round(sum(r['lenient_quality'] for r in level_rows) / len(level_rows), 4),
            'content_presence': round(sum(r['content_presence'] for r in level_rows) / len(level_rows), 4),
            'n': len(level_rows),
        }
    summary[task_name] = task_summary

with open(OUT / 'rescore_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

# ── Print summary ──

for task_name in ['product_extraction', 'ner']:
    print(f"\n{'='*60}")
    print(f"  {task_name.upper()}")
    print(f"{'='*60}")
    print(f"{'Level':>6} | {'Strict':>8} | {'Lenient':>8} | {'Content':>8} | {'N':>4}")
    print(f"{'':->6}-+-{'':->8}-+-{'':->8}-+-{'':->8}-+-{'':->4}")
    for level in range(1, 8):
        s = summary[task_name].get(f'L{level}')
        if s:
            print(f"  L{level}   | {s['strict']:>8.3f} | {s['lenient']:>8.3f} | {s['content_presence']:>8.3f} | {s['n']:>4}")

print(f"\nFiles saved to {OUT}/")
