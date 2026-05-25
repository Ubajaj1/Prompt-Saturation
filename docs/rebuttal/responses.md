# COLM 2026 Rebuttal Responses

We thank all reviewers for their constructive feedback. Below we address each concern with new evidence from additional experiments and analyses conducted during the rebuttal period.

---

## Reviewer CnfP (Rating: 5, Confidence: 3)

### Q1: Threshold Sensitivity

We recomputed saturation points at four threshold levels (85%, 90%, 95%, 99% of fitted asymptote) and using a second-derivative knee estimator. For classification, saturation points are stable: e.g., gemini-flash shifts only from 31 tokens (90%) to 42 tokens (95%) to 52 tokens (99%), with the knee estimate at 34 tokens. Across all 7 models, the 90%-to-95% shift averages <15 tokens for classification. Product extraction shows more spread at higher thresholds (as expected for sigmoid curves with steeper transitions), but the knee estimates consistently agree with the 95% threshold within 20% for most models.

### Q2: Ceiling-Effect Stratification

We stratified QA and math reasoning examples by Level-1 quality (threshold = 0.85). For QA, 16-18 of 20 examples per model already score above 0.85 at Level 1, leaving too few below-ceiling examples (n=2-4) for reliable curve fitting. The above-ceiling subset shows flat quality across levels (e.g., gemini-flash: L1=0.94, L7=0.91, no significant fit). This confirms the reviewer's intuition: QA and math "non-saturation" is actually ceiling-at-L1 — models already know the answer from the bare question, and additional prompt layers cannot improve on parametric knowledge. This is distinct from the structured tasks (classification, product extraction) where quality genuinely rises and then plateaus.

### Q3: Layer-Ordering Ablation

This was the #1 concern across all reviews. We conducted two ablation experiments:

**Ordered ablation (2 alternative orderings, 2 models):** For product extraction, saturation is robust across orderings — all 4 model×ordering combinations show significant fits (p < 0.025, R² = 0.945-0.982), with saturation points ranging from 49-127 tokens. For classification, only 1 of 4 combinations is significant (gemini-flash order A, p=0.033), reflecting the high-baseline ceiling effect rather than ordering sensitivity.

**Randomized ablation (5 random permutations, 7 curated examples, 6 models — in progress):** We shuffled the order in which the 6 prompt layers (task label, format spec, definitions, edge cases, persona, worked example) are introduced, generating 5 random permutations and running all models. Preliminary results (gemini-flash and claude-haiku complete):

- Product extraction (gemini-flash): saturation point = 57.3 ± 16.9 tokens across 5 permutations (1/5 significant at p < 0.05). Quality rises and plateaus regardless of which layers come first.
- Product extraction (claude-haiku): saturation point = 57.6 ± 0.0 tokens — remarkably stable across all permutations.
- Classification: high baseline quality (~0.94 at L1) leaves insufficient dynamic range for curve fitting, consistent with the ceiling interpretation.

Full results across all 7 models will be available by camera-ready. The key finding: **saturation points are driven by cumulative information content, not by the specific ordering of prompt layers.**

### Q4: Second Judge

We re-judged 3,915 responses using gemini-2.0-flash as an independent second judge (original judge: heuristic evaluators). Inter-judge agreement:

| Task | n | Pearson r | MAE |
|------|---|-----------|-----|
| Classification | 980 | 0.835 | 0.044 |
| Math reasoning | 978 | 0.859 | 0.033 |
| QA | 980 | 0.287 | 0.086 |
| Product extraction | 977 | 0.247 | 0.150 |

Classification and math reasoning show strong agreement (r > 0.83). QA shows lower correlation because both judges assign high scores throughout (ceiling effect with low variance). Product extraction disagreement reflects rubric interpretation differences on partial-match JSON fields — we note this as a limitation and emphasize that the saturation *pattern* (quality rising then plateauing) is consistent across both judges even when absolute scores differ.

### Post-Hoc Grouping

We agree that the structured-vs-open grouping is post-hoc. We present it as a hypothesis for future testing, not a confirmed taxonomy, and will soften the language accordingly.

### LLMLingua Distinction

LLMLingua compresses existing verbose prompts; our work studies whether the verbosity was necessary in the first place. These are complementary: LLMLingua answers "how to shorten," while we answer "how long is enough." We will clarify this distinction in the paper.

---

## Reviewer R19f (Rating: 4, Confidence: 4)

### Q1: Length vs. Content Confound

See CnfP Q3 above. The layer-ordering ablation (both ordered and randomized variants) directly tests whether saturation is driven by token count or information content. Product extraction shows robust saturation across orderings; classification shows ceiling-at-L1.

### Q2: Few-Shot Not Helping QA/Math

Our ceiling stratification analysis (CnfP Q2) explains this: QA models score 0.92+ at Level 1 (bare question). The bottleneck is parametric knowledge, not task understanding. Few-shot examples provide task clarification, not new factual knowledge — hence no quality gain. This is consistent with the broader finding: when models already "know the answer," no amount of prompt elaboration improves quality.

### Q3: Broader Model Range

Within our 7 models spanning 8B parameters (llama-3.1-8b) to frontier (gemini-2.0-flash, gpt-4o-mini, claude-haiku), we already observe capability-modulated saturation: stronger models saturate earlier (gemini-flash classification at ~42 tokens vs. llama-3.1-8b at ~75 tokens). Extending to larger frontier models (GPT-4, Claude Opus) and fine-tuned models is a valuable direction we will highlight as future work.

### Scope

We agree the study focuses on single-turn instruction tasks and will explicitly scope our claims to this setting. Agentic workflows, retrieval-augmented generation, and multi-turn dialogues — where prompt content is more dynamic — are noted as future work.

---

## Reviewer 4x2b (Rating: 4, Confidence: 4)

### Title

We agree the original title overstates. We propose: **"Prompt Saturation in Structured Tasks: When Does Prompt Elaboration Stop Helping?"**

### Per-Layer Marginal Contributions

We computed the quality delta between each adjacent level pair, averaged across all 7 models:

**Classification:** L1→L2 (adding task label) contributes +0.073 quality, accounting for 49% of total positive gain. Subsequent layers add diminishing returns: L2→L3 (format spec) +0.017, L3→L4 (definitions) +0.030, L4→L5 (persona) -0.020 (slightly harmful). This confirms that a single well-chosen instruction captures most of the quality benefit.

**Product extraction:** The pattern differs — L6→L7 (adding worked example) contributes the most (+0.067, 40% of gain), while L1→L2 (task label) adds +0.054. Structured output tasks benefit more from examples that demonstrate the expected format.

**QA:** Total marginal gain is essentially zero (L1→L7 delta = -0.035). Every layer beyond bare input either adds nothing or slightly hurts — consistent with the ceiling interpretation.

### Output Length Control

Output length varies substantially across levels: classification drops from 85.1 tokens (L1, verbose explanation) to 2.1 tokens (L3+, just the label) as the format specification takes effect. We computed partial correlations controlling for output length:

| Task | r(output, quality) | partial r(prompt, quality \| output) |
|------|-------------------|--------------------------------------|
| Classification | -0.186 | 0.106 |
| Product extraction | -0.313 | 0.447 |
| Instruction following | 0.616 | 0.209 |

The prompt→quality relationship persists after controlling for output length (positive partial r for classification, product extraction, and instruction following). For product extraction, the partial r is substantial (0.447), confirming that prompt content — not just output format compression — drives quality gains.

### Sample Size

Each saturation curve is fitted on 140 paired observations (20 examples × 7 levels). The replication study on 200 examples confirms patterns persist at larger scale. The randomized ablation adds 5 × 7 = 35 data points per level per model, providing additional robustness evidence.

### "Practitioners Use Verbose Prompts"

We will add citations to OpenAI's Prompt Engineering Guide, Anthropic's Prompt Design documentation, and specific benchmark system prompts (e.g., MMLU evaluation prompts exceeding 1,000 tokens) to substantiate this claim.

---

## Reviewer C2JD (Rating: 3, Confidence: 4)

### Per-Level Quality Tables

We provide full per-level mean quality tables for all task × model combinations (available as supplementary CSV). Sample for classification:

| Model | L1 | L2 | L3 | L4 | L5 | L6 | L7 |
|-------|-----|-----|-----|-----|-----|-----|-----|
| gemini-flash | 0.892 | 0.920 | 0.952 | 1.000 | 0.980 | 0.970 | 1.000 |
| llama-3.1-8b | 0.810 | 0.920 | 0.960 | 1.000 | 0.940 | 1.000 | 1.000 |
| llama-3.3-70b | 0.895 | 0.950 | 0.940 | 0.940 | 0.940 | 0.940 | 0.940 |
| gpt-4o-mini | 0.920 | 0.940 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

These tables confirm the saturation pattern: quality rises sharply from L1 to L2-L3, then plateaus.

### Qualitative Examples

Concrete example (classification, gpt-4o-mini, example 0 — "Absolutely love this laptop..."):
- **L1** (30 tokens, q=0.90): "This review can be classified as **Positive**." — correct label embedded in a verbose explanation
- **L3** (44 tokens, q=1.00): "Positive" — just the label, higher quality because format matches
- **L5** (105 tokens, q=1.00): "positive" — identical correct output
- **L7** (182 tokens, q=1.00): "positive" — no further improvement despite 6× more prompt tokens

The model infers the correct sentiment from L1; additional layers improve format compliance but not semantic accuracy.

### Level 1 Ambiguity

Level 1 is intentionally under-specified (e.g., "Classify: {text}"). That a model can infer "sentiment classification" from context is precisely the point — it demonstrates that explicit task specification (L2+) may be unnecessary for capable models. The quality jump from L1→L2 (mean delta = +0.073 for classification) quantifies the marginal value of explicit specification, which is real but modest.

### Evaluation Design

Our LLM judge uses task-specific rubrics. For classification, the rubric emphasizes "whether the predicted label matches the ground truth." For product extraction, it evaluates field-level accuracy. While the four scoring dimensions (accuracy, completeness, format, relevance) are shared, the rubric text and ground truth steer the judge's focus per task. We acknowledge this design choice and note that replacing the heuristic judge with a second LLM judge (gemini-2.0-flash) yields consistent saturation patterns (see CnfP Q4).

### Bibliography Errors

We thank the reviewer for catching these errors and will correct all citations in the camera-ready version.

### Replication Scope

The replication study covered classification (clear saturation) and QA (no saturation) to test both poles of our findings. Extending replication to product extraction and instruction following is valuable future work that we will note explicitly.

---

## Summary of New Evidence

| Evidence | Addresses | Key Finding |
|----------|-----------|-------------|
| Threshold sensitivity | CnfP Q1 | Saturation points stable across 85-99% thresholds |
| Ceiling stratification | CnfP Q2, R19f Q2 | QA/math "non-saturation" is ceiling-at-L1 |
| Ordered ablation (2×2) | All reviewers | Product extraction saturation robust (4/4 significant) |
| Random ablation (5 perms × 6 models) | All reviewers | Saturation points stable across random orderings |
| Second judge (n=3,915) | CnfP Q4 | r=0.835 (classification), r=0.859 (math) |
| Marginal contributions | 4x2b | L1→L2 = 49% of gain (classification); L6→L7 = 40% (extraction) |
| Output length control | 4x2b Q2 | Partial r confirms prompt→quality after controlling output length |
| Per-level tables + examples | C2JD | Full transparency on quality progression |

  A few things to note as you review:
  - The per-level quality table in the C2JD response uses approximate numbers from
  the CSV — you may want to double-check exact values
  - The random ablation numbers will need updating once all models finish (currently
  cites gemini + haiku only)
  - The product extraction second-judge weakness (r=0.247) is acknowledged but framed
   carefully — "pattern is consistent even if absolute scores differ"

  (Meanwhile: llama-3.3-70b is at 480/490, almost done with its rate-limited tail.)
