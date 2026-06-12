# Revision Analysis Summary

**Date:** 2026-06-12
**Purpose:** Address the two critical reviewer concerns (format-compliance circularity + order-dependent attribution)

---

## 1. Format-Compliance Circularity Analysis

### Problem
The old heuristic evaluator could only parse JSON responses (and plain `field: value` lines for product extraction). At L1-L2, models respond in markdown (bullets, bold keys), which the parser scored as 0. This created an artificial quality cliff at L3 (the format-spec layer that tells models to use JSON).

### Fix
Built a lenient evaluator that strips markdown artifacts (bullets, bold, numbered lists) and handles field-name synonyms ("Product Name" → "name", "Type" → "category", etc.). Also built a content-presence baseline that simply checks if gold values appear anywhere in the response text.

### Results: Product Extraction

| Level | Old Strict | New Lenient | Content-Presence | Parse Format |
|-------|-----------|------------|-----------------|-------------|
| L1    | **0.002** | **0.539**  | **0.868**       | 94% markdown |
| L2    | **0.000** | **0.932**  | **0.923**       | 86% markdown |
| L3    | 0.829     | 0.921      | 0.873           | 100% JSON    |
| L4    | 0.878     | 0.941      | 0.935           | 99% JSON     |
| L5    | 0.888     | 0.939      | 0.932           | 100% JSON    |
| L6    | 0.929     | 0.943      | 0.936           | 100% JSON    |
| L7    | 0.905     | 0.912      | 0.901           | 100% JSON    |

**Key finding:** Under the old strict evaluator, L2→L3 appeared as a 0.000→0.829 cliff (the "schema gating" signal). Under the lenient evaluator, L2→L3 is 0.932→0.921 — **the step disappears entirely**. Content-presence confirms: 87-93% of gold values are present in the text at every level. The cliff was a parsing artifact.

The real step is **L1→L2** (0.539→0.932): telling the model *which fields to extract* matters enormously. The format instruction at L3 adds nothing once field names are known.

### Results: NER

| Level | Old Strict | New Lenient | Content-Presence |
|-------|-----------|------------|-----------------|
| L1    | **0.000** | **0.317**  | **0.876**       |
| L2    | **0.000** | **0.727**  | **0.938**       |
| L3    | 0.846     | 0.846      | 0.913           |
| L4    | 0.870     | 0.870      | 0.934           |
| L5    | 0.908     | 0.908      | 0.988           |
| L6    | 0.917     | 0.917      | 0.992           |
| L7    | 0.899     | 0.899      | 0.988           |

Same pattern: the old evaluator's 0→0.846 cliff at L3 was a JSON-parsing artifact. Content-presence shows 88-94% of gold entities are present in L1-L2 responses. The NER evaluator's lenient parsing still has gaps (39% parse failures at L1 because models list entities without type labels), but the content-presence check confirms the information IS there.

### Interpretation for the Paper

The "schema gating" story changes fundamentally:
- **Old story (circular):** "87-95% of quality concentrates at the format layer"
- **New story (genuine):** "The critical information is *field specification* (which fields/entities to extract), not *output format* (JSON vs prose). Once field names are known, quality is already high regardless of format."

This is a **stronger and more interesting** finding than the original claim.

---

## 2. Shapley Attribution Analysis

### Problem
The canonical 87/92/95% attribution numbers come from one fixed layer ordering. Attribution is order-dependent by construction.

### Method
Used 2,986 ablation runs with 5 different layer orderings. Re-scored all responses with the lenient evaluator. Computed each mechanism's average marginal contribution across all orderings (Shapley values).

### Results

**Classification (Shapley values, lenient evaluator):**

| Mechanism    | Shapley | % of total |
|-------------|---------|-----------|
| edge_cases   | +0.063  | 64.7%     |
| definitions  | +0.040  | 41.2%     |
| example      | +0.029  | 29.4%     |
| task_label   | +0.023  | 23.5%     |
| **format_spec** | **-0.034** | **-35.3%** |
| persona      | -0.023  | -23.5%    |

**format_spec has NEGATIVE Shapley for classification** — it slightly hurts quality. The most valuable mechanisms are edge_cases and definitions. This makes sense: classification needs clear label definitions, not a format spec.

**Product Extraction (Shapley values, lenient evaluator):**

| Mechanism    | Shapley | % of total |
|-------------|---------|-----------|
| **format_spec** | **+0.296** | **80.2%** |
| definitions  | +0.059  | 15.9%     |
| task_label   | +0.036  | 9.7%      |
| edge_cases   | +0.020  | 5.4%      |
| persona      | -0.006  | -1.6%     |
| example      | -0.036  | -9.7%     |

format_spec dominates for product extraction even under order-averaged attribution. **But its contribution is position-dependent:**

| Position | format_spec marginal | n  |
|----------|--------------------|----|
| 1 (first)  | +0.407           | 10 |
| 2 (second) | +0.329           | 10 |
| 6 (last)   | +0.007           |  5 |

When format_spec appears after other mechanisms, its marginal contribution drops to near-zero. This confirms the reviewer's insight: the format layer isn't special — **whichever mechanism first resolves the output schema captures the gain**.

### Interpretation for the Paper

The attribution story depends on the task:
- **Classification:** Format spec is unnecessary or slightly harmful. Definitions and edge-case handling matter.
- **Product Extraction:** Format spec genuinely helps, but only because it's typically the first mechanism that clarifies the output structure. Any mechanism that conveys the schema would have the same effect.

This is more nuanced and more useful than "87-95% at the schema layer."

---

## 3. Parse-Path Breakdown (for Sec 3.4 revision)

| Task | Level | JSON% | Markdown List% | Bold Keys% | Plain KV% | Prose% |
|------|-------|-------|---------------|-----------|----------|--------|
| PE   | L1    | 0     | 94            | 4         | 2        | 0      |
| PE   | L2    | 0     | 86            | 14        | 0        | 0      |
| PE   | L3    | 100   | 0             | 0         | 0        | 0      |
| NER  | L1    | 0     | 91            | 3         | 0        | 6      |
| NER  | L2    | 0     | 98            | 2         | 0        | 0      |
| NER  | L3    | 89    | 0             | 0         | 0        | 11     |

Without a format instruction, models default to markdown lists (86-98% of responses). After the format instruction (L3+), they switch to JSON (89-100%). The old strict evaluator only understood JSON — creating the artificial cliff.

---

## 4. Revised Paper Claims

### What survives
1. **Structured tasks saturate** — still true under lenient scoring. The saturation curves are real.
2. **The field-specification layer is critical** — L1→L2 step is genuine and large.
3. **Open-ended tasks don't saturate** — unaffected by this analysis.
4. **Model×strategy interaction** — unaffected.
5. **Pre-registered NER prediction** — still confirmed.

### What changes
1. **"87-95% concentration at the schema layer"** → reframe as "field specification captures most of the gain; format compliance adds a small additional bonus."
2. **Heuristic vs judge r=0.986** → this correlation was between two evaluators that both penalize non-JSON responses. The lenient heuristic tells a different story at L1-L2.
3. **Attribution percentages** → report Shapley values alongside canonical-order attribution, noting the order-dependence.

### What to add
1. Three-evaluator comparison table (strict / lenient / content-presence)
2. Parse-path breakdown per level
3. Shapley values with positional analysis
4. Explicit statement that the lenient evaluator parses markdown, not just JSON
5. Missing citations: Tam et al. 2024, Min et al. 2022, IFEval

---

## Files Generated

| File | Description |
|------|-------------|
| `rescore_product_extraction.csv` | Per-entry strict/lenient/content-presence scores (977 rows) |
| `rescore_ner.csv` | Per-entry strict/lenient/content-presence scores (700 rows) |
| `rescore_summary.json` | Level-averaged comparison |
| `parse_path_breakdown.csv` | Response format distribution per level |
| `shapley_values.csv` | Per-mechanism Shapley values |
| `shapley_marginals.csv` | Per-permutation marginal contributions |
| `shapley_summary.json` | Full Shapley results with positional breakdown |
