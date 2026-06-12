# Paper Revision Plan — "When Does Prompt Elaboration Stop Helping?"

**Date:** 2026-06-12
**Review score:** 5/10 (Borderline Reject), Confidence 4/5
**Goal:** Address the two critical weaknesses + major issues to strengthen the paper

---

## Diagnosis: What We Found

### The Circularity Problem (Critical Weakness #1)

The reviewer claims the "87–95% concentration at the schema layer" is circular because models that extract correctly in prose get scored 0. Our investigation:

**Product Extraction:**

| Level | Heuristic | Judge | Parse Failures |
|-------|-----------|-------|----------------|
| L1    | 0.002     | 0.762 | 99%            |
| L2    | 0.000     | 0.816 | 100%           |
| L3    | 0.829     | 0.812 | 0%             |
| L4    | 0.878     | 0.831 | 0%             |

- `ProductExtractionEvaluator` has a fallback parser (JSON + `field: value` lines)
- But the fallback **misses** markdown bullets (`- **Name:** X`) which is 100% of L2 responses
- At L2, models extract all 4 fields correctly in `- **Product Name:** Sony WH-1000XM5` format
- The heuristic scores them **0.000** — pure parsing failure, not extraction failure
- The judge correctly scores them **0.816**

**NER:**

| Level | Heuristic | Judge  |
|-------|-----------|--------|
| L1    | 0.082     | (N/A)  |
| L2    | 0.126     | (N/A)  |
| L3    | 0.760     | (N/A)  |

- `NERExtractionEvaluator` is **JSON-only** — no fallback at all
- At L1-L2, models output `"The entities are: Apple, Tim Cook, Cupertino"` — correct, scored 0

**The paper plots judge scores** (Figure 1 caption: "Quality (LLM judge, normalised to [0,1])"), so the figure itself isn't circular. But the heuristic scores ARE used in the cross-evaluator validation (Sec 4.7, r=0.986 claim) and the reviewer computed concentration percentages from them.

### The Attribution Problem (Critical Weakness #2)

The 87/92/95% concentration numbers come from one fixed layer ordering. The paper already has 2,986 ablation runs with shuffled orders (`results/rebuttal/random_ablation_results.json`) but never computes order-independent (Shapley) attributions.

---

## Revision Steps

### Step 1: Fix ProductExtractionEvaluator (zero cost)

**File:** `greenprompt/evaluators.py`, `_parse_response()` method (line 229)

Current fallback regex: `re.match(rf'{field}\s*:\s*(.+)', line.strip(), re.IGNORECASE)`

This fails on:
- `- **Product Name:** Sony WH-1000XM5` (bullet + bold)
- `**name:** value` (bold wrapping)
- Prose: "The product is an iPhone 15 by Apple, priced at $999"

Fix: strip markdown artifacts before matching, add synonym support, add field-name variants (e.g., "Product Name" → "name").

### Step 2: Fix NERExtractionEvaluator (zero cost)

**File:** `greenprompt/evaluators.py`, `_parse_entities()` method (line 296)

Currently JSON-only. Add fallback parsing for:
- `PERSON: Tim Cook, Apple` (labeled lines)
- `- PERSON: Tim Cook` (bullet lists)
- `**PERSON:** Tim Cook` (bold labels)

### Step 3: Add content-presence baseline (zero cost)

Create a simple check: "is each gold field value present anywhere in the response text?" (case-insensitive string containment). This is the absolute floor — if the value appears in the text, the model extracted it regardless of format.

### Step 4: Re-score all stored responses (zero cost)

Re-evaluate all stored responses with:
1. **Strict** evaluator (current, for backward compatibility)
2. **Lenient** evaluator (fixed parser)
3. **Content-presence** check (value-in-text)

Data files:
- Product extraction: `results/saturation_results_new_tasks.json` (984 entries with `response_text`)
- NER: `results/rebuttal_v2/ner_held_out.json` (870 entries with `response_text`)
- Ground truth: `experiments/prompting_strategies.py` BENCHMARK_EXAMPLES

Output per level:
- Strict quality, Lenient quality, Content-presence score
- Parse-path breakdown (JSON / key-value / prose / fail)
- Per-model breakdown

### Step 5: Compute Shapley values (zero cost)

Data: `results/rebuttal/random_ablation_results.json` (2,986 entries)
Each entry: `{model, task, perm_id, perm_order, level, example_id, quality, ...}`

Algorithm:
- For each permutation, compute marginal delta at each position
- Attribute each delta to the mechanism name at that position
- Average each mechanism's marginal contribution across all orderings
- Output: per-mechanism Shapley values by task

Compare: canonical-order attribution vs Shapley attribution

### Step 6: Analysis report (zero cost)

Consolidate findings into `results/revision_analysis/`:
- `rescore_comparison.csv` — strict vs lenient vs content-presence by level
- `parse_path_breakdown.csv` — how each level's responses parse
- `shapley_values.csv` — per-mechanism order-averaged attributions
- `revision_summary.md` — narrative summary of what changed

### Step 7: Update paper text (zero cost)

Based on analysis results:
- Sec 3.4: describe lenient parser explicitly, report parse-path breakdown
- Sec 4.x: report Shapley attributions alongside canonical-order
- Sec 5: address format-compliance vs extraction-ability decomposition
- Add missing citations (Tam et al. 2024, Min et al. 2022, IFEval)
- Shorten abstract, fix placeholders, enlarge Figure 1
- Apply multiple comparison correction

---

## Data Inventory

| File | Entries | Has response_text? | Used for |
|------|---------|--------------------|---------| 
| `results/saturation_results_new_tasks.json` | 984 PE + 993 math | Yes | PE re-scoring |
| `results/rebuttal_v2/ner_held_out.json` | 870 | Yes | NER re-scoring |
| `results/rebuttal/random_ablation_results.json` | 2,986 | Yes | Shapley computation |
| `results/rebuttal_v2/heuristic_rescore.json` | 3,915 | No | Cross-evaluator comparison |
| `results/saturation_results_judge.json` | 3,936 | Yes | Original 4-task data |

Ground truth: `experiments/prompting_strategies.py` → `BENCHMARK_EXAMPLES`
