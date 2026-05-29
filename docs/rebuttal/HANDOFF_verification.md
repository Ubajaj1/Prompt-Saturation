# Rebuttal Verification — Handoff Notes

**Date:** 2026-05-29
**Purpose:** Hand off the fact-check of `docs/rebuttal/responses.md` and the coverage analysis vs `docs/rebuttal/reviews.md`. Lists (A) what was verified, (B) discrepancies to fix, (C) coverage gaps, (D) remaining tasks (overall-response section, restructure).

---

## Source-of-truth files (all under `results/rebuttal/` unless noted)

| File | Contents |
|------|----------|
| `random_ablation_results.json` | Raw ablation runs (list, **2986** records) |
| `random_ablation_analysis.json` | Per-model ablation summary (5 models analyzed) |
| `second_judge_results.json` | Raw second-judge re-evals (list, **3915**) |
| `second_judge_agreement.json` | Per-task Pearson r / MAE |
| `padding_control_results.json` | Raw padding runs (list, **1470**) |
| `padding_control_analysis.json` | Padding deltas + comparison_with_real |
| `threshold_sensitivity.json` | Saturation by 85/90/95/99% + knee |
| `ceiling_stratification.json` | QA/math below/above-ceiling fits |
| `marginal_contributions.json` | Per-layer deltas per task |
| `output_length.json` | Partial correlations |
| `per_level_quality.csv` | Per-level mean quality, 7 models × 6 tasks |
| `qualitative_examples.json` | C2JD qualitative samples |
| `../../results/saturation_combined/saturation_summary.csv` | Original (fixed-order) fits |
| `../../archive/results/saturation_results.json` | Main study raw (list, **4192** records) |

---

## A. VERIFIED CORRECT (numbers match source data)

- **Raw experiment counts:** ablation file = 2986 ✓, second judge = 3915 ✓, padding = 1470 ✓.
- **Second-judge per-task r / MAE** (Q4 table): classification r=0.835/MAE=0.044 ✓, math r=0.859/0.033 ✓, QA r=0.287/0.086 ✓, product extraction r=0.247/0.150 ✓. Orig/Gemini means all ✓ (class 0.922/0.961, math 0.910/0.927, QA 0.912/0.995, PE 0.835/0.976).
- **QA Gemini >0.9 = 98.8%** ✓ (actual 98.78%).
- **Ablation product-extraction table** (means/std/range/sig per model) — all 5 rows ✓. Mid-range significant = **13/15** ✓; stronger models **1/10** ✓.
- **Ablation classification = 2/25 significant** ✓.
- **Original PE significant fits = 3/7** (qwen p=0.0049, llama-3.3-70b p=0.0229, claude p=0.0047) ✓.
- **Threshold sensitivity:** gemini-flash classification 90%→31, 95%→42, 99%→52, knee 34 ✓. qwen3-32b log R²=0.753 ✓, 95-token shift ✓, knee 42 ✓. Median 90→95 shift ≈ 2.7 (~3 tokens) ✓. PE gemini 85%→293 / 99%→546 ✓. PE llama-3.3-70b knee 96 vs 95%=92 ✓.
- **Ceiling stratification:** QA above-ceiling n range 16–20 ✓, below-ceiling 0–4 ✓; gemini L1=0.94/L7=0.91 ✓, claude L1=0.92/L7=0.89 ✓. Math above-ceiling 17–19 ✓. QA mean delta −0.035 ✓.
- **Math L3 collapse:** L2=0.967→L3=0.601→L4=0.964 ✓; per-model L2→L3 drops span −0.267 to −0.420 ✓; second judge L2=0.986→L3=0.574 ✓.
- **Marginal contributions:** classification L1→L2 +0.073 = 49% ✓; schema layers (L1→L2 + L2→L3) = 61% ✓; PE L6→L7 +0.067 = 40% ✓, L1→L2 +0.054 = 32% ✓; math −0.366/+0.363 ✓; QA total ≈ −0.035 ✓; instr-following biggest L5→L6 +0.010 ✓; summarization biggest L2→L3 +0.004 ✓.
- **Output length partial-r table:** class −0.186/0.106 ✓, PE −0.313/0.447 ✓, instr 0.616/0.209 ✓. Class output 85→2 tokens ✓.
- **Per-level table (C2JD):** gemini-flash, llama-3.1-8b, llama-3.3-70b, gpt-4o-mini rows all ✓.
- **Qualitative example:** L1 30tok q0.90, L3 44tok q1.0, L5 105tok q1.0, L7 182tok q1.0 ✓.
- **Padding control:** mean Δ class −0.074 ✓, PE −0.013 ✓. Significant trends = 4 total (1 positive: claude-haiku class random_words r=0.79 p=0.034, Δ+0.029; 3 negative: llama-3.1-8b class, gemini-flash PE, qwen3-32b PE) ✓. The "1/26 positive, 3/26 negative" framing ✓. Per-model real-vs-padding Δ table (10 rows) — all ✓.
- **Borderline p-values:** llama-3.1-8b classification p=0.079 (doc says ~0.06 → see discrepancy #7), kimi-k2 PE p=0.093 (doc says ≈0.05 → discrepancy #7).

---

## B. DISCREPANCIES TO FIX (doc value ≠ source data)

1. **PE ablation total in CnfP Q5 (line ~78):** doc says "13/25 ablation significant". Actual total = **14/25** (mid-range 13/15 + gemini-flash 1/5). The "13/15" elsewhere is mid-range only and is correct; the "13/25" is wrong → should be **14/25**.

2. **Second-judge extraction ceiling (Q4, line ~72):** doc says Gemini assigns >0.9 to "97% of extraction responses". Actual = **88.7%**. Fix the percentage (mean 0.976 is correct).

3. **Direction agreement — product extraction (Q4 point (1), line ~70):** doc says "6 of 7 models show the same L1→L7 direction." Actual = **4/7** (disagreements: gpt-4o-mini, claude-haiku, kimi-k2 — Gemini gives ~0.000 delta at ceiling). Also C2JD "Evaluation Design" (line ~260) repeats "6/7 models on classification and 6/7 on product extraction" — actual **classification 5/7, PE 4/7**.

4. **"5 models × 7 examples (2,986 experiments)" (lines ~31, ~121, and totals):** The 2986 raw records **include kimi-k2** (490 records) → **6 models in the raw file**, but kimi was dropped from the analysis (only 5 models in `random_ablation_analysis.json`). Arithmetic: 5 perms × 5 models × 2 tasks × 7 ex × 7 levels = 2450 (not 2986); 6 models would be 2940. The "5 models × 7 examples = 2,986" equation is internally inconsistent. **Decide:** either (a) re-run analysis including kimi and say "6 models," or (b) keep 5-model analysis and recount the experiments actually used (~2450), or (c) state "2,986 raw runs across 6 models; analysis on the 5 models with complete data." Currently misleading.

5. **Threshold "5 of 7 models shift by <11 tokens" (line ~13):** actual = **6 of 7** (<11 tokens: all except qwen3-32b). Fix to 6 of 7.

6. **PE qwen knee "falls between its 85% (160) and 90% (245)" (line ~17):** qwen PE knee = **62**, which is **below** 160, not between 160 and 245. Statement is false → reword (knee is far below the threshold-based estimates, reflecting the log fit).

7. **Borderline p-values (CnfP Q5, line ~78):** doc says "llama-3.1-8b classification at p=0.06, kimi-k2 extraction at p≈0.05". Actual: llama-3.1-8b classification **p=0.079**, kimi-k2 PE **p=0.093**. Update both (CnfP's review quoted its own numbers; ours should match our data).

8. **Classification effect size (4x2b Sample Size, line ~209):** doc says "quality jump of +0.15 from L1 to L4". Actual mean L1→L4 across 7 models = **+0.12**. Either fix to +0.12 (d still large) or cite a specific model. (Per-model L1→L4 ranges +0.045 to +0.220.)

9. **"R² >0.93 for the sigmoid-fitted models" (line ~13):** Not all sigmoid classification fits exceed 0.93 — llama-3.1-8b sigmoid R²=0.866, claude-haiku sigmoid R²=0.646. Reword to "for the well-fit sigmoid models" or name them (gemini, llama-3.3-70b, kimi, gpt-4o-mini).

10. **Total scope arithmetic (header line 3 + Summary line 287):** Header says "8,371 new evaluations" (2986+3915+1470 = 8371 ✓). Summary "Total experimental scope: 14,284" = 5913+2986+3915+1470. But **main study raw file has 4192 records, not 5913**. The 5913 figure (7×6×7×20=5880 + replication) is not backed by the archive file I found (4192). **Verify the main-study N** against the actual paper / replication data before quoting 5913 and 14,284. R19f "Scope" (line 171) also quotes 5,913 and 12,814 — same dependency.

> Note items #4 and #10 are the biggest credibility risks (a reviewer can divide and check). Resolve the experiment-count story end-to-end and make every total reconcile.

---

## C. COVERAGE GAPS vs reviews.md (questions not fully answered)

1. **4x2b — additional classification domains:** Reviewer explicitly asks to extend beyond *sentiment* classification ("classification results are based solely on sentiment classification; extending this to additional classification domains would strengthen the argument"). **Not addressed anywhere.** Need a response (acknowledge + future work, or argue product-extraction already adds a second structured task).

2. **C2JD — data construction process:** Reviewer asks for "more information about the data construction process" and example details. Current "Replication Scope" / "Sample Size" only partly touch this. Add a short paragraph on how examples were sourced/constructed per task.

3. **C2JD — extend replication to product extraction & instruction following:** Partially addressed (budget caveat in "Replication Scope") but PE replication is now *partially run* per `padding-exp/ACCEPTANCE_ASSESSMENT.md` ("Product extraction replication at 200 examples"). **Check whether a 200-example PE replication exists** and fold it in if so — would directly close this gap.

All other review questions appear covered (R19f Q1–Q3 + scope; 4x2b title/marginal/output-length/practitioner-refs; CnfP Q1–Q7 + LLMLingua + post-hoc; C2JD per-level/qualitative/L1-ambiguity/eval-design/bibliography).

---

## D. REMAINING TASKS (user's explicit request)

1. **Write an "Overall Response / Common Themes" section FIRST**, before the per-reviewer answers. Synthesize the cross-cutting themes that recur across reviewers:
   - **Theme 1 — Length vs. content confound** (raised by R19f, 4x2b, CnfP): answer once with ablation + padding control, then reference from per-reviewer sections.
   - **Theme 2 — Scope / sample size / narrow tasks** (R19f, 4x2b, C2JD): n=20 rationale, replication, deliberate single-turn scope.
   - **Theme 3 — Framing overstated (title, "thresholds", post-hoc grouping)** (R19f, 4x2b, CnfP): the information-sufficiency reframing + sensitivity spectrum.
   - **Theme 4 — Judge reliability** (CnfP, C2JD): second judge.
   - **Theme 5 — New experiments summary** (the 8,371 new evals): keep the summary table, move it up.
   Then keep reviewer-wise sections but trim repetition (point back to the overall section).

2. **Apply the Section B fixes** to `responses.md`.

3. **Add Section C responses** (classification-domain breadth; data-construction detail; PE replication if data exists).

4. **Final pass:** make every experiment-count total reconcile (see #4, #10).

---

## Quick re-verification snippets

```bash
# raw counts
python3 -c "import json;[print(f, len(json.load(open('results/rebuttal/'+f)))) for f in ['random_ablation_results.json','second_judge_results.json','padding_control_results.json']]"

# second-judge direction agreement per task (recompute 4/7, 5/7, 5/7)
# ceiling/marginal/threshold: read the JSONs directly — all keyed by task→model
```
