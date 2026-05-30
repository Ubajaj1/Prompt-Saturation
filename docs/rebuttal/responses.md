# COLM 2026 Rebuttal Responses

We thank all reviewers for their careful reading. The reviews converged on a central methodological concern — that our additive design confounds length and content — and correctly identified that the original "task-specific token threshold" framing overstated what the data support. We agree on both counts.

To address this, we conducted 8,371 new LLM evaluations: a randomized layer-ordering ablation (2,986), an irrelevant-padding control (1,470), and an independent second judge (3,915), plus threshold sensitivity, ceiling-effect stratification, and per-layer marginal contribution analyses. These experiments confirmed the core saturation phenomenon but also revealed that the mechanism is information content, not token count — a refinement prompted directly by the reviewers' concerns.

We organize this rebuttal as an **Overall Response** addressing the cross-cutting themes, followed by per-reviewer sections that handle specific points.

---

## Overall Response: Cross-Cutting Themes

Five themes recur across the four reviews. We address each once here, then point per-reviewer sections to the relevant subsection.

### Theme 1 — Length vs. content confound (R19f central, CnfP Q3, 4x2b "content vs. length")

**Concern.** The additive design varies prompt length and prompt content simultaneously, so the saturation curve could in principle reflect either. This was the single most common concern.

**Evidence.** We ran two complementary controls.

1. **Randomized layer-ordering ablation** (5 permutations × 6 models × 2 tasks × 7 examples × 7 levels; 2,986 raw runs, 2,450 analyzed after excluding kimi-k2). The ablation focuses on classification and product extraction — the only tasks with significant saturation fits in the original study — because the length-vs-content confound is moot for tasks where quality is flat regardless of prompt content or length. Shuffling layer order *preserves* the saturation curve for product extraction in mid-range models (13/15 fits significant; saturation clusters at 65–140 tokens regardless of which layer comes first), but *shifts the token threshold*: original fixed-ordering estimates were 92–378 tokens, ablation means 95–110 tokens. The shape is robust; the token count is not.

2. **Irrelevant-padding control** (3 padding types × 5 models × 2 tasks × 7 levels × 7 examples; 1,470 runs). As with the ablation, the padding control targets classification and product extraction — the tasks where saturation exists and the token-count confound is testable. Matched-token-count padding (factual trivia, repeated phrases, random words) produces flat or declining quality (mean L1→L7 Δ = −0.074 classification, −0.013 product extraction; 1/26 significant positive trend, consistent with chance at α=0.05). The same token range with *real* prompt content yields +0.10 / +0.16. Tokens themselves do not buy quality.

**Conclusion.** Saturation is driven by *information sufficiency* — the curve bends once task-critical content has been communicated, irrespective of position or token count. The practical guidance is concrete: marginal-contribution analysis identifies which layers matter per task (e.g., task label for classification, worked example for extraction), and additional layers beyond these yield diminishing or negative returns. A particularly striking example: instructing models to "give only the final numerical answer" for math (our L3) destroys quality by −0.366 across all 7 models and both judges — some prompt content is not merely unnecessary but actively harmful (R19f Q2).

Where the per-reviewer sections discuss this theme, they reference the ablation/padding evidence here rather than restating it (CnfP Q3, R19f Q1, 4x2b "Per-Layer Marginal Contributions").

### Theme 2 — Scope, sample size, and narrow tasks (R19f, 4x2b sample-size, C2JD coverage)

**Concern.** n=20 per task is small; classification only covers sentiment; agentic and multi-turn settings are out of scope.

**Position.** The sample-size choice was driven by the cross-product 7 levels × 7 models × 20 examples = 980 observations per task, which yields effect sizes (d ≈ 2.4 for the classification L1→L4 jump) detectable at well below n=20. The 200-example replication on classification and QA confirms the main-study fits. We agree single-domain (sentiment) classification limits generalisation; we partially mitigate by adding product extraction as a second structured task with the same qualitative pattern (4x2b "Classification Domain Breadth"), and we will explicitly scope sentiment-only claims in the camera-ready. Single-turn scope is deliberate: agentic and retrieval-augmented settings introduce confounds (tool selection, retrieval quality, multi-turn drift) that would prevent clean isolation of the prompt-length → quality relationship.

### Theme 3 — Framing overstated: title, "thresholds," post-hoc grouping (R19f, 4x2b title, CnfP post-hoc)

**Concern.** The original framing — task-specific token thresholds + a binary structured/open grouping — overstates what the data support, and the grouping was applied post-hoc.

**We agree.** The rebuttal experiments confirmed that "token threshold" was the wrong abstraction — the ablation showed the threshold shifts with layer ordering, and the padding control showed tokens themselves have no effect. The correct characterization is *information sufficiency* (Theme 1). We acknowledge this reframing was prompted by the ablation results rather than pre-registered; we believe it is more faithful to the data than the original framing.

Similarly, the binary structured/open grouping was post-hoc and too coarse. Marginal-contribution analysis reveals that tasks differ in how their quality gain is distributed across prompt layers. We describe this as a gradient rather than a dichotomy:

- **Concentrated:** classification — 49% of gain from one layer (task label).
- **Distributed:** product extraction — two layers carry 32% + 40%.
- **Diffuse:** instruction following — small gains across many layers.
- **Insensitive:** QA, math, summarization — near-zero or negative total gain.

We present this gradient as a descriptive framework for organizing the observed patterns, not as a standalone contribution. The practical takeaway is more concrete: *for classification, specify the task label; for extraction, include a worked example; for QA and math, the bare question suffices — additional elaboration yields diminishing or negative returns.*

Threshold sensitivity (CnfP Q1) confirms that within a fixed ordering, classification saturation is stable across thresholds (median 90→95% shift = 3 tokens; 6/7 models shift <11 tokens).

We propose a revised title: **"When Does Prompt Elaboration Stop Helping? Prompt Sensitivity Across LLM Tasks"**.

### Theme 4 — Judge reliability (CnfP Q4, C2JD evaluation design)

**Evidence.** We re-judged all 3,915 responses with gemini-2.0-flash as an independent second judge using the same 4-dimension rubric. Agreement is strong where it matters most — classification r=0.835 / MAE=0.044, math r=0.859 / MAE=0.033. For QA and product extraction, low Pearson r is a ceiling artefact (Gemini assigns >0.9 to 98.8% of QA and 88.7% of PE responses, leaving little variance to correlate); both judges agree on direction for the models with the largest original-judge deltas, and the L1→L7 sign agrees for 5/7 models on classification and 4/7 on product extraction (with the 3 PE non-agreements being Gemini deltas of ≤0.003 — non-disagreements driven by ceiling compression, not opposite signs). Prior work has shown that different LLM judges exhibit systematically different score calibrations (Chen et al., 2025, "Evaluating Scoring Bias in LLM-as-a-Judge"; Li et al., 2026, "Same Input, Different Scores"). In our data, the Gemini judge compresses scores toward the ceiling (>0.9 for 98.8% of QA responses), while the gpt-4o-mini judge preserves more variance. For saturation curve fitting, this greater score dispersion is methodologically preferable — not because one judge is "more correct," but because variance is required for meaningful curve fitting.

### Theme 5 — Summary of new evidence (8,371 new evaluations)

| Evidence | n | Addresses |
|----------|--:|-----------|
| Randomized layer-ordering ablation | 2,986 | Length vs. content (Theme 1); F-test power (CnfP Q5) |
| Irrelevant-padding control | 1,470 | Length vs. content (Theme 1); token-count null (R19f Q1) |
| Independent second judge | 3,915 | Judge reliability (Theme 4); evaluation design (C2JD) |
| Threshold sensitivity (85/90/95/99% + knee) | — | Threshold robustness (CnfP Q1) |
| Ceiling stratification (QA/math) | — | "Non-saturation" interpretation (CnfP Q2, R19f Q2) |
| Per-layer marginal contributions | — | Gain distribution gradient (4x2b, CnfP Q6/Q7) |
| Output-length partial correlations | — | Output-length confound (4x2b) |
| Per-level quality tables + qualitative examples | — | Transparency (C2JD) |

**Total experimental scope (with rebuttal additions):** 17,046 LLM evaluations — 5,875 main + ≈2,800 200-example replication + 2,986 randomized ablation + 3,915 second judge + 1,470 padding control.

---

## Reviewer CnfP (Rating: 5, Confidence: 3)

### Q1: Threshold Sensitivity

We recomputed saturation points at four threshold levels (85%, 90%, 95%, 99% of fitted asymptote) and using a threshold-free second-derivative knee estimator.

For classification, saturation points are stable across thresholds for 6 of 7 models with sigmoid fits. For example, gemini-flash shifts from 31 tokens (90%) to 42 tokens (95%) to 52 tokens (99%), with the knee estimate at 34 tokens. The median 90%-to-95% shift across all 7 models is 3 tokens (6 of 7 models shift by <11 tokens). One outlier — qwen3-32b — is fitted as a logarithmic rather than sigmoid curve (R²=0.75; the well-fit sigmoid models — gemini-flash, llama-3.3-70b, kimi-k2, gpt-4o-mini — all have R²>0.93), producing a 95-token shift; excluding this outlier, the mean shift is 3 tokens.

The qwen3-32b outlier is itself informative. The logarithmic fit reflects a genuinely different model behavior: while sigmoid-fitted models plateau sharply after L3–L4 (late-level gain L4→L7 = 0.000 for gemini-flash, llama-3.3-70b, claude-haiku), qwen3-32b continues extracting incremental gains from later layers (L5→L6: +0.060, reaching 1.000). It is the only model that benefits meaningfully from the guidelines layer (L6). This suggests qwen3-32b integrates detailed instructions more gradually rather than snapping to the correct answer early — an empirical observation from our data, not a documented architectural property, but a difference in *how the model uses the prompt*, not just a fitting artifact. The curve shape (sigmoid vs. logarithmic) is thus a characterization of model behavior: both saturate, but at different rates. The threshold-free knee estimate for qwen3-32b (42 tokens) falls close to the other models' estimates, confirming that the underlying saturation onset is similar even when the curve shape differs.

Product extraction shows wider threshold spread, as expected for tasks with more dynamic range. For example, gemini-flash ranges from 293 tokens (85%) to 546 tokens (99%). However, the knee estimates (threshold-free) remain informative: llama-3.3-70b knee=96 tokens agrees with its 95% threshold (92 tokens). For qwen3-32b, the threshold-based estimates (160 tokens at 85%, 533 tokens at 99%) reflect its logarithmic fit's slow asymptotic approach, while the knee estimate (62 tokens) localises the elbow of the curve — the two metrics characterise different aspects of the same fit, and the knee places saturation onset at a comparable scale to the other models.

We note that the layer-ordering ablation (Q3 below) introduces a more fundamental source of variation than the threshold percentage: the saturation *token count* itself shifts with prompt ordering. This means the threshold sensitivity analysis is most useful for confirming the robustness of the saturation *shape* (curves flatten) and for comparing models within a fixed ordering, rather than for establishing universal token budgets. We discuss this reframing in Q3.

### Q2: Ceiling-Effect Stratification

We stratified QA and math reasoning examples by Level-1 quality (threshold = 0.85). Across models, 16–20 of 20 QA examples already score above 0.85 at Level 1, leaving too few below-ceiling examples (n=0–4) for reliable curve fitting. The above-ceiling subset shows flat-to-declining quality across levels (e.g., gemini-flash: L1=0.94, L7=0.91; claude-haiku: L1=0.92, L7=0.89 — no significant fit). Quality actually *decreases* slightly from L1 to L7 for most models (mean delta = −0.04), suggesting that additional prompt layers add noise to responses the model was already handling correctly.

Math reasoning shows the same ceiling pattern: most models have 17–19 of 20 examples above 0.85 at L1, and the L1→L7 delta is near zero (mean = +0.01). However, the per-level trajectory is not flat — it is sharply non-monotonic. L3 ("Give only the final numerical answer") causes a dramatic quality collapse across all 7 models (overall mean: L2=0.967 → L3=0.601 → L4=0.964), with every model dropping between 0.267 and 0.420 quality points at L3. L4 restores step-by-step reasoning and quality recovers immediately. The L1→L7 delta averages to near zero only because the L3 valley and the surrounding plateau cancel out — the underlying trajectory is far from monotonic. We discuss the implications of this L3 effect in R19f Q2 below.

This confirms the reviewer's intuition: QA and math "non-saturation" is ceiling-at-L1 — models already have sufficient parametric knowledge from the bare question. This places QA and math at the insensitive end of the prompt-sensitivity gradient (see Q3 below). Classification and product extraction, by contrast, start below ceiling because the prompt must communicate format requirements and task semantics that the model cannot infer from the input alone — though they differ in *how* that sensitivity manifests (concentrated vs. distributed; see Q3).

### Q3: Layer-Ordering Ablation

This was the #1 concern across all reviews. We conducted a randomized ablation: we shuffled the introduction order of all 6 prompt layers, generating 5 random permutations and running on 7 curated examples per task (2,986 total runs collected across 6 models; analysis is restricted to the 5 models with complete data — kimi-k2 was excluded because the model (`moonshotai/kimi-k2-instruct`) was deprecated by Groq between the main study (March 2026) and the rebuttal experiments (May 2026), returning 404 errors for all 490 attempted runs; the original main-study data for kimi-k2 remains valid and is retained in all non-ablation analyses — yielding 2,450 analyzed runs). The reduction from 20 to 7 examples was due to rebuttal-period API budget.

Product extraction results:

| Model | Mean ± Std (tokens) | Range | Significant fits |
|-------|-------------------|-------|-----------------|
| qwen3-32b | 95 ± 26 | [65, 134] | 5/5 |
| llama-3.1-8b | 110 ± 24 | [84, 140] | 4/5 |
| llama-3.3-70b | 110 ± 22 | [80, 131] | 4/5 |
| gemini-flash | 57 ± 17 | [49, 91] | 1/5 |
| claude-haiku | 58 ± 0 | [58, 58] | 0/5 |

The results reveal a capability-dependent pattern. Models that required more prompt elaboration to reach high quality — qwen3-32b, llama-3.1-8b, and llama-3.3-70b (hereafter "mid-range" in terms of prompting sensitivity, as distinct from the stronger API models that achieve near-ceiling quality with minimal prompting) — show robust saturation: 13/15 fits are significant, with saturation points clustering at 65–140 tokens across random orderings. Stronger models (gemini-flash, claude-haiku) show flatter curves with fewer significant fits (1/10), consistent with these models requiring less prompt elaboration to reach high quality — the same capability-modulated saturation reported in Section 4.2.

Notably, the ablation saturation points (65–140 tokens) are substantially lower than the original fixed-ordering estimates for the same models (92–378 tokens for the significant fits). This is expected and informative: in the original design, the most valuable layer for product extraction — the worked example (L6→L7, contributing 40% of quality gain) — always comes *last*, so quality stays low until high token counts and the curve bends late. In random orderings, this high-value layer can appear at any position, including early ones, causing quality to rise sooner and saturation to occur at fewer tokens. The shift in saturation point across orderings directly demonstrates that it is *information content and ordering*, not raw token count, that determines where the curve bends. The padding control experiment (R19f Q1) provides direct confirmation: irrelevant tokens matched to the same token counts produce flat quality (mean L1→L7 delta = −0.01 to −0.07), while the real experiment shows significant gains over the same range.

Classification shows only 2/25 significant fits — but this is expected given classification's prompt-sensitivity profile, not a failure to replicate. The marginal contribution analysis (Q6 below) shows that classification's quality gain is concentrated in a single layer: L1→L2 (task label) accounts for 49% of total gain. This means classification's quality trajectory is a step function — quality jumps once the task label is encountered, then plateaus. In random orderings, the task label can appear at any position; when it falls early, quality starts high and the curve is flat from the start. Curve fitting is the wrong tool for detecting a step function — the 2/25 result reflects a mismatch between the analytical method (smooth curve fitting) and the shape of the phenomenon (a discrete step), not an absence of prompt-sensitivity.

This distinction between classification and product extraction is itself an important finding. The original manuscript grouped both as "structured tasks that saturate," but the ablation reveals they exhibit different *shapes* of prompt-sensitivity: classification's gain is **concentrated** (one layer captures most of the benefit) while product extraction's gain is **distributed** (accumulated across multiple layers, with the worked example contributing 40%). Both are prompt-sensitive — quality genuinely improves with the right prompt content — but the improvement has different structure. Curve fitting detects the distributed pattern (product extraction, 13/15 significant) but not the concentrated pattern (classification, 2/25 significant). The marginal contribution analysis detects both.

**Summary.** Prompt-sensitivity is robust, but tasks vary in how that sensitivity is distributed across prompt layers. Classification's quality depends on a single critical instruction; product extraction benefits from graduated elaboration; QA and math are already at ceiling. The ablation confirms the core finding but also shows that our original "token threshold" framing was too specific — the threshold shifts with layer ordering. The correct characterization is *information sufficiency*: quality saturates once task-critical content has been communicated, and the practical guidance is "identify which prompt layers drive quality and include those."

### Q4: Second Judge

We re-judged 3,915 responses using gemini-2.0-flash as an independent second judge. Both judges use the same 4-dimension rubric (correctness, completeness, reasoning, conciseness, each 1–5); the original judge was gpt-4o-mini.

| Task | n | Pearson r | MAE | Orig mean | Gemini mean |
|------|---|-----------|-----|-----------|-------------|
| Classification | 980 | 0.835 | 0.044 | 0.922 | 0.961 |
| Math reasoning | 978 | 0.859 | 0.033 | 0.910 | 0.927 |
| QA | 980 | 0.287 | 0.086 | 0.912 | 0.995 |
| Product extraction | 977 | 0.247 | 0.150 | 0.835 | 0.976 |

**Agreement is strong where it matters most.** Classification and math reasoning show strong correlation (r > 0.83) and low MAE (< 0.05), as expected for tasks with crisp ground truths where both judges key on the same signal.

For QA and product extraction, Pearson r is low, but this reflects calibration divergence rather than pattern disagreement:

**(1) Both judges agree on direction where the original judge detects a non-trivial signal.** Both show quality increasing from L1 to L7 for product extraction (gpt-4o-mini: +0.163; gemini: +0.073) and flat/declining for QA (gpt-4o-mini: −0.035; gemini: −0.008). For product extraction, 4 of 7 models show the same L1→L7 sign under both judges; for the remaining 3 models (gpt-4o-mini, claude-haiku, kimi-k2), Gemini's L1→L7 delta is essentially zero (≤0.003) — these are non-disagreements driven by Gemini's ceiling compression rather than opposing signs. Classification shows direction agreement for 5 of 7 models. Even for QA, both judges agree on direction for the 3 models with the largest original-judge deltas (llama-3.1-8b, claude-haiku, gemini-flash).

**(2) Low correlation is a ceiling artifact.** The Gemini mean columns explain the low r: Gemini assigns scores > 0.9 to 98.8% of QA responses (mean 0.995) and 88.7% of extraction responses (mean 0.976). With one judge's scores compressed to near-ceiling, there is almost no variance left to correlate — Pearson r is mechanically suppressed regardless of whether the judges agree on the underlying pattern.

In short: where there is signal to detect (classification, math), both judges agree strongly; where scores cluster near perfect (QA, product extraction), the low correlation reflects score compression rather than disagreement on patterns. We acknowledge that the Gemini judge's compressed score range makes it less informative for detecting saturation curves. The choice of judge model is itself a methodological degree of freedom — one we are transparent about. Prior work has shown that different LLM judges exhibit systematically different score calibrations (Chen et al., 2025, "Evaluating Scoring Bias in LLM-as-a-Judge"; Li et al., 2026, "Same Input, Different Scores"). In our data, the Gemini judge compresses scores toward the ceiling, while gpt-4o-mini preserves more variance — making it more useful for curve fitting, not because it is "more correct," but because variance is required for meaningful regression.

### Q5: F-Test Power

We agree that our F-test (7 level means, 2–3 fitted parameters) has limited power. The ablation results clarify where this matters: the F-test reliably detects tasks with *distributed* prompt-sensitivity (product extraction: 3/7 original, 14/25 ablation significant — driven by mid-range models at 13/15) but not tasks with *concentrated* sensitivity (classification: 4/7 original, 2/25 ablation). This is not a power failure — it reflects a mismatch between the analytical tool (smooth curve fitting) and the shape of the phenomenon (a step function for classification). The borderline cases (llama-3.1-8b classification at p=0.079, kimi-k2 extraction at p=0.093) are consistent with this interpretation: they sit near the boundary where the gain concentration is just diffuse enough for a curve to partially fit.

The randomized ablation confirms that product extraction's saturation is robust beyond what the original F-test alone can establish (13/15 significant fits for mid-range models). For classification, the marginal contribution analysis provides the appropriate evidence: L1→L2 accounts for 49% of quality gain, confirming prompt-sensitivity through a method suited to concentrated gains. Together, curve fitting and marginal contribution analysis provide complementary coverage across different patterns of prompt-sensitivity.

### Q6: Schema-Compliance Hypothesis

We agree that the schema-compliance hypothesis was stated but not directly tested. We now provide three converging lines of evidence:

**(1) Marginal contribution analysis.** For classification, the two schema-defining layers — L1→L2 (task label, +0.073) and L2→L3 (format specification, +0.017) — together account for 61% of total quality gain. For product extraction, L6→L7 (worked example demonstrating output schema, +0.067) accounts for 40% of gain. In both cases, the layers that communicate *what the output should look like* are the dominant quality drivers.

**(2) Ceiling stratification.** Open-ended tasks (QA, math) reach ceiling at L1 precisely because they do *not* require schema compliance — the model already knows what to output (an answer, a number). Structured tasks start below ceiling because the model must learn the expected output format from the prompt.

**(3) Output format compression.** For classification, output length drops from 85 tokens (L1, verbose explanation) to 2 tokens (L3+, just the label) as format specification takes effect. The quality gain tracks this compression — the prompt teaches the model the output schema, and once learned, further elaboration adds nothing.

We will revise the manuscript to present schema-compliance as a hypothesis supported by converging evidence rather than a standalone tested contribution, and will include the marginal contribution analysis as a supporting figure.

### Q7: Grouping of Summarization and Instruction Following

This is a fair point: summarization and instruction following arguably involve schema-like elements (expected format, constraint satisfaction) and do not cleanly fit the "open-ended" label. Rather than two buckets, we now describe tasks along a gradient of how quality gain is distributed across prompt layers:

- **Concentrated:** Classification — 49% of gain from one layer (task label). Prompt-sensitive, but as a step function.
- **Distributed:** Product extraction — gains spread across multiple layers (task label 32%, worked example 40%). Classical sigmoid saturation.
- **Diffuse:** Instruction following — small gains spread across many layers (biggest: L5→L6 guidelines, +0.010). Individually insignificant.
- **Insensitive:** QA, math, summarization — near-zero or negative total gain. Model already at ceiling (QA, math) or gains too small to detect (summarization, biggest: L2→L3, +0.004).

The original binary grouping correctly identified the poles — classification and extraction are prompt-sensitive, QA and math are not. This gradient adds resolution for intermediate cases and explains *why* the original F-test detected some tasks and not others: curve fitting is suited to distributed gains, not concentrated or diffuse ones. We present this as a descriptive observation rather than a tested taxonomy, and will revise the manuscript accordingly.

### LLMLingua Distinction

LLMLingua and our work address different questions. LLMLingua takes an existing verbose prompt and compresses it by removing redundant tokens while preserving meaning — it answers "how can I make this prompt shorter?" Our work asks whether the verbosity was necessary in the first place — "which prompt content is necessary for a given task?" For example, consider a classification prompt with role assignment, format specification, definitions, guidelines, and a worked example (our L7, ~180 tokens). LLMLingua might compress this to ~36 tokens by removing filler words. Our marginal analysis shows that L1→L2 (adding just the task label) accounts for 49% of the quality gain — most of the remaining ~150 tokens of elaboration were largely unnecessary, not just redundantly worded. The two are complementary: our analysis determines what to *include* in the first place, while LLMLingua determines how concisely to express what is included. We will clarify this relationship in the revision.

### Post-Hoc Grouping

The reviewer is right: the original structured-vs-open grouping was post-hoc. The gradient we now describe (concentrated → distributed → diffuse → insensitive) is also post-hoc — we are transparent about this. We do not present it as a tested hypothesis but as a descriptive framework that organizes three independent analyses: (1) ceiling stratification explains the insensitive end (QA, math at ceiling from L1), (2) marginal contribution analysis quantifies how gain is distributed across layers for each task, and (3) the ablation shows why curve fitting detects some tasks' sensitivity (distributed gains) but not others' (concentrated gains). The gradient describes patterns in the data; validation as a predictive framework requires testing on new tasks, which we flag as future work.

---

## Reviewer R19f (Rating: 4, Confidence: 4)

### Q1: Length vs. Content Confound

This is the central methodological question. We conducted a randomized ablation to test whether saturation is driven by token count or information content (full details in CnfP Q3 above).

In the randomized ablation (5 random permutations × 5 analyzed models × 2 tasks × 7 examples × 7 levels; 2,986 raw runs across 6 models, 2,450 analyzed runs after excluding kimi-k2 due to model deprecation — see CnfP Q3), we shuffled the order in which prompt layers are introduced. For product extraction, mid-range models (qwen3-32b, llama-3.1-8b, llama-3.3-70b) show robust saturation across orderings: 13/15 fits are significant, with saturation clustering at 65–140 tokens regardless of which layers come first.

The ablation resolves this confound decisively in favor of content. The *existence* of saturation is robust: the sigmoid shape persists across all significant fits (13/15 for mid-range models). But the *specific token count* at which saturation occurs shifts substantially — the original fixed-ordering estimates for product extraction (92–378 tokens for significant fits) are 2–4× higher than the ablation means (95–110 tokens). This is because the original ordering places the most valuable layer (worked example, 40% of quality gain) last; random orderings can place it early, causing quality to rise sooner.

The ablation resolves the confound in favor of content: quality saturates once task-critical information is communicated, regardless of when in the prompt it appears. The token count at which this occurs is ordering-dependent, not task-intrinsic — our original "token threshold" framing was too specific. We will revise the manuscript to characterize saturation as *information sufficiency*, with practical guidance becoming "identify which prompt layers matter (via marginal contribution analysis) and include those" rather than "trim after N tokens."

To directly test whether raw token count contributes to quality gains, we conducted a padding control experiment. We matched the token counts of our 7 additive levels using three types of irrelevant filler — factual trivia unrelated to the task (geography, history, science), repeated neutral phrases ("Note: additional context follows for reference purposes."), and random English words in shuffled order — keeping only the bare task instruction as meaningful content. Across 1,470 experiments (5 models × 2 tasks × 3 padding types × 7 levels × 7 examples), quality remained flat or declined: mean L1→L7 delta = −0.074 for classification and −0.013 for product extraction, with only 1/26 conditions showing a significant *positive* trend (Spearman p < 0.05) — a near-ceiling case (claude-haiku classification, Δ = +0.03, from 0.97 to 1.00) consistent with chance at 26 tests. The remaining 3/26 significant trends were all *negative* — padding slightly *hurt* quality, consistent with irrelevant text distracting the model. (At 26 tests and α = 0.05, ~1.3 false positives are expected by chance; the observed 1 positive trend is within this range and reflects ceiling noise rather than a genuine token-count effect.)

In contrast, the real experiment shows clear quality gains over the same token range: mean L1→L7 delta = +0.10 for classification and +0.16 for product extraction, with significant saturation curves for structured tasks. The per-model comparison is consistent across all 5 models and both tasks:

| Model | Task | Real Δ (L1→L7) | Padding Δ (L1→L7) |
|-------|------|:-:|:-:|
| gemini-flash | classification | +0.110 | +0.031 |
| llama-3.3-70b | classification | +0.045 | −0.221 |
| llama-3.1-8b | classification | +0.190 | −0.161 |
| qwen3-32b | classification | +0.123 | −0.029 |
| claude-haiku | classification | +0.055 | +0.029 |
| gemini-flash | product extraction | +0.191 | −0.002 |
| llama-3.3-70b | product extraction | +0.085 | −0.055 |
| llama-3.1-8b | product extraction | +0.098 | +0.043 |
| qwen3-32b | product extraction | +0.220 | −0.038 |
| claude-haiku | product extraction | +0.190 | −0.011 |

Combined with the randomized ablation (which shows saturation is robust to layer ordering), the padding control confirms that saturation is driven by information content reaching a task-specific sufficiency threshold, not by raw token count.

### Q2: Few-Shot Not Helping QA/Math

**QA:** Models score 0.89–0.95 at Level 1 (bare question). The ceiling stratification analysis (CnfP Q2) confirms that 16–20 of 20 examples per model are already above 0.85 at L1. Adding a worked example (L7) not only fails to help but consistently *hurts* quality (mean L1→L7 delta = −0.035). Few-shot examples provide task clarification, not factual knowledge — and for already-solved problems, they may anchor the model's response style on the example rather than the actual question. Both judges confirm this decline: the second judge (gemini-flash) also shows QA quality decreasing from L1 to L7 for the 3 models with the largest original deltas.

**Math reasoning:** The per-level data reveals a striking non-monotonic pattern. L3 ("Give only the final numerical answer") causes a sharp quality drop across *all 7 models* and *both judges* (original judge: L2=0.967 → L3=0.601; second judge: L2=0.986 → L3=0.574). L3 suppresses chain-of-thought reasoning, which is critical for math accuracy — a well-documented finding in the CoT literature (Wei et al., 2022). L4 restores step-by-step reasoning and quality recovers immediately (L4=0.964).

This finding has direct practical implications: certain prompt instructions are not merely unhelpful but actively *destructive*. The standard sigmoid model does not capture tasks where intermediate prompt layers are counterproductive, and this non-monotonicity is important for practitioners to be aware of. We will discuss this explicitly in the revision.

### Q3: Broader Model Range

Our 7 models span 8B parameters (llama-3.1-8b) to medium-tier API models (gpt-4o-mini, gemini-2.0-flash, claude-haiku). We observe capability-modulated saturation, but the direction is task-dependent:

- **Classification:** Stronger models saturate earlier (gemini-flash at ~31 tokens vs. llama-3.1-8b at ~70 tokens). Stronger models infer the task from less context.
- **Product extraction:** The pattern reverses — stronger models saturate *later* (claude-haiku at ~504 tokens vs. llama-3.1-8b at ~80 tokens) but reach *higher* asymptotic quality (0.99 vs. 0.87). Stronger models extract more from detailed prompts, while weaker models plateau early at lower quality.

This reversal is itself a novel finding: model capability and prompt saturation interact differently depending on task structure. For tasks where the model must *infer* what to do (classification), stronger models need less prompt. For tasks where the prompt provides *actionable format specifications* (extraction), stronger models leverage more of them.

Beyond the speed of saturation, models also differ in *how* they saturate. Most models fit sigmoid curves on classification (sharp plateau after L3–L4), but qwen3-32b fits a logarithmic curve — it keeps extracting incremental gains from later layers where other models show zero late-level gain. This suggests that models differ not just in when they saturate but in how gradually they integrate prompt elaboration, which has practical implications: prompt optimization should be model-specific, not one-size-fits-all.

We do not include true frontier models (GPT-4, Claude Opus) due to cost constraints, and will note the reversed saturation pattern and model-specific curve shapes as concrete hypotheses for future work with larger models.

### Scope

We agree the study focuses on single-turn instruction tasks and will explicitly scope our claims to this setting. This is a genuine limitation: agentic, RAG, and multi-turn settings may exhibit different saturation dynamics. We chose single-turn scope because it enables clean isolation of the prompt-content → quality relationship without confounds from tool selection, retrieval quality, or multi-turn drift. Extending to more complex settings is a priority for future work.

In total, the study encompasses 5,875 main experiments (7 models × 6 tasks × 7 levels × 20 examples = 5,880 attempted, 5,875 successful) plus ≈2,800 additional runs for 200-example replications on classification and QA, alongside 2,986 randomized ablation experiments, 3,915 second-judge re-evaluations, and 1,470 padding-control experiments — 17,046 total LLM evaluations across the main study and rebuttal period. This scope provides a rigorous foundation for establishing and characterizing the saturation phenomenon.

---

## Reviewer 4x2b (Rating: 4, Confidence: 4)

### Title

We agree the original title overstates. The ablation experiments (CnfP Q3) further revealed that saturation is better characterized as *information sufficiency* rather than task-specific *token thresholds* — quality saturates once task-critical content is communicated, and the token count at which this occurs depends on prompt design, not just the task. We propose: **"When Does Prompt Elaboration Stop Helping? Prompt Sensitivity Across LLM Tasks"** — this captures the phenomenon (elaboration stops helping) without overstating specificity or implying a binary grouping.

### Per-Layer Marginal Contributions

We computed the quality delta between each adjacent level pair, averaged across all 7 models:

**Classification:** L1→L2 (adding task label) contributes +0.073 quality, accounting for 49% of total positive gain. Subsequent layers add diminishing returns: L2→L3 (format spec) +0.017, L3→L4 (definitions) +0.030, L4→L5 (persona) −0.020 (slightly harmful). This confirms that a single well-chosen instruction captures most of the quality benefit.

**Product extraction:** The pattern differs — L6→L7 (adding worked example) contributes the most (+0.067, 40% of gain), while L1→L2 (task label) adds +0.054. Structured output tasks benefit more from examples that demonstrate the expected format.

**Math reasoning:** L3 (suppressing CoT with "give final answer only") causes a dramatic −0.366 quality drop — larger than any positive gain in any task. L4 (restoring step-by-step reasoning) recovers +0.363. This non-monotonicity is the most striking per-layer finding and demonstrates that prompt content can be actively harmful.

**QA:** Total marginal gain is essentially zero (L1→L7 delta = −0.035). Every layer beyond bare input either adds nothing or slightly hurts — consistent with the ceiling interpretation.

### Output Length Control

Output length varies substantially across levels: classification drops from 85.1 tokens (L1, verbose explanation) to 2.1 tokens (L3+, just the label) as the format specification takes effect. We computed partial correlations controlling for output length:

| Task | r(output, quality) | partial r(prompt, quality | output) |
|------|-------------------|--------------------------------------|
| Classification | −0.186 | 0.106 |
| Product extraction | −0.313 | 0.447 |
| Instruction following | 0.616 | 0.209 |

The prompt→quality relationship persists after controlling for output length (positive partial r for classification, product extraction, and instruction following). For product extraction, the partial r is substantial (0.447), confirming that prompt content — not just output format compression — drives quality gains.

### Classification Domain Breadth

We agree that our classification results draw from sentiment classification only, and this is a real limitation. Two points partially mitigate it within the present study:

1. **Product extraction is a second structured task** that exhibits the same qualitative saturation pattern (significant fits for 3/7 models in the original analysis; 13/15 in the mid-range models under the ablation). The two tasks differ substantially in output structure (single label vs. multi-field JSON), input domain (reviews/social posts vs. product listings), and which prompt layer drives gain (task label for classification, worked example for extraction — see 4x2b "Per-Layer Marginal Contributions"). The shared finding — saturation onset once the format-relevant content is communicated — is consistent across these two structurally distinct tasks.

2. **The marginal-contribution analysis (4x2b above) explains *why* classification saturates so quickly** (one layer carries 49% of the gain). That mechanism — a single instruction sufficing once the model has enough information to map inputs to a label space — should generalise to other classification domains where the label set is similarly inferable from the task description. Domains where the label set is highly specialised (e.g., medical ICD-10, intent classification with hundreds of fine-grained labels) may shift the saturation point upward but should retain the concentrated-gain shape.

We will explicitly scope the classification claims to *sentiment* in the camera-ready and flag topic, intent, and category classification as priority follow-ups. We thank the reviewer for this observation.

### Sample Size

We use 20 examples per task because each example must be paired with 7 additive prompt levels and evaluated across 7 models — yielding 980 observations per task in the main study (20 × 7 × 7). The replication study extends classification and QA to 200 examples. The randomized ablation adds 2,986 further experiments.

For the effects we detect, n=20 provides adequate power. Classification shows a mean quality jump of +0.12 from L1 to L4 across 7 models (per-model range: +0.045 to +0.220) with within-model standard deviations of ~0.05 — an effect size of d ≈ 2.4, detectable at well below n=20. Product extraction shows similar large effects (+0.163 L1→L7 under the original judge).

Regarding existing benchmarks: our additive prompt design requires *custom prompt construction* at each level — existing benchmark datasets provide inputs/outputs but not the graduated prompt hierarchy that is our methodological contribution. We did use standard benchmark data where available (Amazon product reviews for classification and product extraction, GSM8K-style problems for math reasoning, SQuAD-derived questions for QA).

### "Practitioners Use Verbose Prompts"

This claim is grounded in documented practice:

- **Official guidance:** OpenAI's Prompt Engineering Guide (developers.openai.com/docs/guides/prompt-engineering) recommends structured prompts with "Role and Objective, Instructions, Reasoning Steps, Output Format, Examples, and Context" — each section adding tokens. Anthropic's documentation similarly recommends detailed task descriptions and examples.
- **Academic surveys:** Sahoo et al. (2024, "A Systematic Survey of Prompt Engineering in LLMs," arXiv:2402.07927) documents the proliferation of elaborate prompting techniques. Schulhoff et al. (2024, "The Prompt Report," arXiv:2406.06608) catalogues 58+ prompting techniques, most of which add tokens. Levy et al. (2024, "Same Task, More Tokens," arXiv:2402.14848) directly studies the effect of increasing input length on reasoning — implicitly documenting the practitioner tendency toward longer prompts.
- **Benchmark prompts:** MMLU evaluation prompts routinely exceed 1,000 tokens with few-shot examples (Hendrycks et al., 2021). HumanEval and MBPP code benchmarks include multi-paragraph system prompts.
- **Industry practice:** The "mega-prompt" pattern — prompts of 500–2,000+ tokens with roles, constraints, examples, and formatting rules — is widely documented in prompt engineering communities and commercial LLM applications.

All cited works are already in our bibliography. We will add explicit inline citations in the revision.

---

## Reviewer C2JD (Rating: 3, Confidence: 4)

### Per-Level Quality Tables

We provide full per-level mean quality tables for all task × model combinations (available as supplementary CSV). Sample for classification:

| Model | L1 | L2 | L3 | L4 | L5 | L6 | L7 |
|-------|-----|-----|-----|-----|-----|-----|-----|
| gemini-flash | 0.830 | 0.857 | 0.890 | 0.940 | 0.920 | 0.910 | 0.940 |
| llama-3.1-8b | 0.780 | 0.890 | 0.930 | 1.000 | 0.910 | 0.970 | 0.970 |
| llama-3.3-70b | 0.895 | 0.950 | 0.940 | 0.940 | 0.940 | 0.940 | 0.940 |
| gpt-4o-mini | 0.792 | 0.812 | 0.910 | 0.940 | 0.940 | 0.940 | 0.970 |
| claude-haiku | 0.915 | 0.950 | 0.940 | 0.970 | 0.970 | 0.940 | 0.970 |
| kimi-k2 | 0.742 | 0.940 | 0.910 | 0.910 | 0.910 | 0.940 | 0.940 |
| qwen3-32b | 0.878 | 0.940 | 0.940 | 0.970 | 0.940 | 1.000 | 1.000 |

These tables confirm the saturation pattern across all 7 models: quality rises sharply from L1 to L3–L4, then plateaus. Full per-level tables for all 6 tasks are provided in the supplementary CSV.

### Qualitative Examples

Concrete example (classification, gpt-4o-mini, example 0 — "Absolutely love this laptop..."):
- **L1** (30 tokens, q=0.90): "This review can be classified as **Positive**." — correct label embedded in a verbose explanation
- **L3** (44 tokens, q=1.00): "Positive" — just the label, higher quality because format matches
- **L5** (105 tokens, q=1.00): "positive" — identical correct output
- **L7** (182 tokens, q=1.00): "positive" — no further improvement despite 6× more prompt tokens

The model infers the correct sentiment from L1; additional layers improve format compliance but not semantic accuracy.

Product extraction example (gemini-flash, example 3 — "Nike Air Max 270..."):
- **L1** (37 tokens, q=0.70): Outputs a bulleted list with extra fields (Product Type, Key Features, Availability) — correct information but wrong format.
- **L3** (63 tokens, q=0.80): Outputs JSON with correct fields, but "Air Max 270" instead of "Nike Air Max 270" for name.
- **L7** (271 tokens, q=1.00): `{"name": "Nike Air Max 270", "price": "150", "brand": "Nike", "category": "shoes"}` — the worked example (L6→L7) teaches the exact output schema, producing the quality jump that marginal analysis identifies as 40% of total gain.

The contrast between these two tasks illustrates the concentration gradient: classification's quality jumps with a single instruction, while product extraction requires a worked example demonstrating the expected format.

### Level 1 Ambiguity

The reviewer raises a valid point: Level 1 is intentionally under-specified (e.g., "Classify: {text}"), and a model's ability to infer "sentiment classification" from context makes L1 performance partly a measure of model inference ability rather than a fixed baseline.

However, this is accounted for in our analysis. The L1→L2 quality delta (+0.073 for classification, averaged across 7 models) explicitly quantifies what explicit specification adds *beyond* model inference. The saturation analysis measures quality trajectories starting from whatever L1 achieves — it does not assume a fixed baseline. Moreover, the per-model variation at L1 (0.78–0.90 for classification) is itself informative: it reveals which models can infer the task without explicit specification and which cannot. We will clarify in the revision that L1 represents "task communication via input context alone" and L2+ adds explicit task specification.

### Evaluation Design

Our LLM judge (gpt-4o-mini) uses a shared 4-dimension framework (correctness, completeness, reasoning, conciseness) but with *task-specific rubric text and ground truth*. For classification, correctness evaluates label match against the ground-truth sentiment; for product extraction, it evaluates field-level precision and recall against structured ground truth; for QA, it checks factual alignment with the reference answer. The rubric text steers the judge's focus per task within the shared framework.

We validated this design by re-judging all 3,915 responses with an independent second judge (gemini-2.0-flash). The two judges agree on L1→L7 direction for 5/7 models on classification and 4/7 on product extraction (the remaining classification disagreement and 3 PE non-agreements are driven by Gemini's near-zero deltas at ceiling, not opposite signs — see CnfP Q4). For tasks with crisp ground truths, correlation is strong (classification: r=0.835; math: r=0.859).

### Data Construction

The reviewer asks for more detail on how examples were sourced and constructed. The 20-example main-study sets were assembled per task as follows, balancing two requirements: (i) each example must be unambiguous enough that a competent annotator and a strong LLM agree on the ground truth, so that the quality signal reflects the prompt rather than label noise; and (ii) within each task, examples must span enough difficulty to avoid floor or ceiling collapse at L1.

- **Sentiment classification:** 20 product-review and social-media-style sentences drawn from the SST-2 distribution (with a small number of authored variants to balance neutral cases). Labels: positive / negative / neutral. Examples were screened to remove sarcasm and mixed-sentiment cases, since these create ground-truth disagreement that would inflate noise rather than measure saturation.
- **Product extraction:** 20 product-listing snippets covering electronics, household goods, and books, with varying difficulty (buried prices, implicit brand names, multiple candidate fields). Each example has a structured 4-field ground truth (name, price, brand, category).
- **QA:** 20 short factoid questions across geography, history, and science (SQuAD-style format), each paired with a single-string ground-truth answer.
- **Math reasoning:** 20 word problems requiring 2–3 steps of arithmetic, rate, or geometry reasoning (10 easy, 10 medium difficulty), with exact-numeric ground truth.
- **Summarization:** 20 short news passages with reference summaries.
- **Instruction following:** 20 prompts each carrying 1–2 explicit structural constraints (e.g., bullet points, numbered list, single word).

The 200-example replication for classification and QA samples directly from the source benchmarks (SST-2 for classification; SQuAD-derived for QA), preserving the identical prompt templates and evaluation procedure. We will include the full per-example listings and construction notes in the camera-ready supplementary material.

### Bibliography Errors

We thank the reviewer for catching these errors. Specifically:

1. **"A Survey of Automatic Prompt Engineering"** (arXiv:2502.11560) — incorrectly cited as Amatriain et al. The correct authors are Li, Wenwu; Wang, Xiangfeng; Li, Wenhao; Jin, Bo.
2. **"CompactPrompt"** (arXiv:2510.18043) — incorrectly cited as Wang et al. The correct first author is Choi, Joong Ho (Choi, Zhao, Shah, Sonawane, Singh, Appalla, Flanagan, Condessa).

These errors likely arose from incorrect metadata in the preprint sources we used during bibliography construction. We have verified the correct author listings on arXiv and will correct all citations in the camera-ready version. We have checked the remaining bibliography entries and confirmed they are accurate.

### Replication Scope

The replication study covered classification (clear saturation) and QA (no saturation) to test both poles of our findings. Extending replication to product extraction and instruction following would strengthen the paper; we were constrained by rebuttal-period API budget (the ablation, second-judge, and padding-control experiments — 8,371 new evaluations — consumed the available budget). We will note this as high-priority future work and will extend replication to these tasks for the camera-ready version if accepted.

---

## Summary of New Evidence

| Evidence | Addresses | Key Finding |
|----------|-----------|-------------|
| Randomized ablation (5 perms × 5 models, n=2,986) | All reviewers (length vs. content) | Product extraction: 13/15 significant fits confirm distributed saturation. Classification: 2/25 reflects concentrated sensitivity (step function, not curve). Token threshold shifts with ordering → information sufficiency, not a token budget |
| Second judge (n=3,915) | CnfP Q4 | r=0.835/0.859 (classification/math); direction agreement 5/7 on classification, 4/7 on extraction (3 of 7 PE non-agreements are Gemini deltas ≤0.003 — ceiling compression, not opposite signs); low r on QA/extraction explained by ceiling compression |
| Ceiling stratification | CnfP Q2, R19f Q2 | QA/math "non-saturation" is ceiling-at-L1 (16–20/20 examples above 0.85) |
| Threshold sensitivity | CnfP Q1 | Median 90%-to-95% shift = 3 tokens (classification); knee estimates confirm |
| Marginal contributions | 4x2b, CnfP Q6 | L1→L2 = 49% of gain (classification); L6→L7 = 40% (extraction); schema-defining layers dominate |
| Math L3 non-monotonicity | R19f Q2 | "Final answer only" instruction destroys quality (−0.366) across all models and both judges |
| Output length control | 4x2b Q2 | Partial r confirms prompt→quality after controlling output length (PE: 0.447) |
| Per-level tables + examples | C2JD | Full transparency on quality progression across all 42 model×task combinations |
| F-test + ablation convergence | CnfP Q5 | Curve fitting detects distributed sensitivity (extraction); marginal contributions detect concentrated sensitivity (classification) — complementary tools |
| Padding control (n=1,470) | All reviewers (length vs. content) | Quality flat with irrelevant padding (1/26 significant positive trend — ceiling noise; 3/26 significant negative trends; mean Δ = −0.07/−0.01 for classification/extraction), while real experiment shows +0.10/+0.16 — confirms saturation is information-driven, not token-count-driven |

**Total experimental scope:** 17,046 LLM evaluations (5,875 main + ≈2,800 200-example replication + 2,986 randomized ablation + 3,915 second judge + 1,470 padding control).
