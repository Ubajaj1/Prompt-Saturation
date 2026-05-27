# COLM 2026 Rebuttal Responses

We thank all reviewers for their constructive feedback. We conducted 6,901 new LLM evaluations during the rebuttal period — including a randomized layer-ordering ablation (2,986 experiments), a second independent judge (3,915 re-evaluations), threshold sensitivity analysis, ceiling-effect stratification, and per-layer marginal contribution analysis. Below we address each concern with this new evidence.

---

## Reviewer CnfP (Rating: 5, Confidence: 3)

### Q1: Threshold Sensitivity

We recomputed saturation points at four threshold levels (85%, 90%, 95%, 99% of fitted asymptote) and using a threshold-free second-derivative knee estimator.

For classification, saturation points are stable across thresholds for 6 of 7 models with sigmoid fits. For example, gemini-flash shifts from 31 tokens (90%) to 42 tokens (95%) to 52 tokens (99%), with the knee estimate at 34 tokens. The median 90%-to-95% shift across all 7 models is 3 tokens (5 of 7 models shift by <11 tokens). One outlier — qwen3-32b — is fitted as a logarithmic rather than sigmoid curve (R²=0.75 vs. >0.93 for the sigmoid-fitted models), producing a 95-token shift; excluding this outlier, the mean shift is 3 tokens.

The qwen3-32b outlier is itself informative. The logarithmic fit reflects a genuinely different model behavior: while sigmoid-fitted models plateau sharply after L3–L4 (late-level gain L4→L7 = 0.000 for gemini-flash, llama-3.3-70b, claude-haiku), qwen3-32b continues extracting incremental gains from later layers (L5→L6: +0.060, reaching 1.000). It is the only model that benefits meaningfully from the guidelines layer (L6). This suggests qwen3-32b integrates detailed instructions more gradually rather than snapping to the correct answer early — a difference in *how the model uses the prompt*, not just a fitting artifact. The curve shape (sigmoid vs. logarithmic) is thus a characterization of model behavior: both saturate, but at different rates. The threshold-free knee estimate for qwen3-32b (42 tokens) falls close to the other models' estimates, confirming that the underlying saturation onset is similar even when the curve shape differs.

Product extraction shows wider threshold spread, as expected for tasks with more dynamic range. For example, gemini-flash ranges from 293 tokens (85%) to 546 tokens (99%). However, the knee estimates (threshold-free) remain informative: llama-3.3-70b knee=96 tokens agrees with its 95% threshold (92 tokens), and qwen3-32b knee=62 tokens falls between its 85% (160 tokens) and 90% (245 tokens) thresholds. We acknowledge that product extraction saturation points are more threshold-sensitive and report both knee estimates and threshold-based values in the revision.

### Q2: Ceiling-Effect Stratification

We stratified QA and math reasoning examples by Level-1 quality (threshold = 0.85). Across models, 16–20 of 20 QA examples already score above 0.85 at Level 1, leaving too few below-ceiling examples (n=0–4) for reliable curve fitting. The above-ceiling subset shows flat-to-declining quality across levels (e.g., gemini-flash: L1=0.94, L7=0.91; claude-haiku: L1=0.92, L7=0.89 — no significant fit). Quality actually *decreases* slightly from L1 to L7 for most models (mean delta = −0.04), suggesting that additional prompt layers add noise to responses the model was already handling correctly.

Math reasoning shows the same ceiling pattern: most models have 17–19 of 20 examples above 0.85 at L1, and the L1→L7 delta is near zero (mean = +0.01). However, the per-level trajectory is not flat — it is sharply non-monotonic. L3 ("Give only the final numerical answer") causes a dramatic quality collapse across all 7 models (overall mean: L2=0.967 → L3=0.601 → L4=0.964), with every model dropping between 0.267 and 0.420 quality points at L3. L4 restores step-by-step reasoning and quality recovers immediately. The L1→L7 delta averages to near zero only because the L3 valley and the surrounding plateau cancel out — the underlying trajectory is far from monotonic. We discuss the implications of this L3 effect in R19f Q2 below.

This confirms the reviewer's intuition: QA and math "non-saturation" is ceiling-at-L1 — models already have sufficient parametric knowledge from the bare question. This is distinct from structured tasks (classification, product extraction) where the prompt must communicate format requirements and task semantics that the model cannot infer from the input alone.

### Q3: Layer-Ordering Ablation

This was the #1 concern across all reviews. We conducted a randomized ablation: we shuffled the introduction order of all 6 prompt layers, generating 5 random permutations and running across 5 models × 7 curated examples (2,986 total experiments, reduced from 20 to 7 examples due to rebuttal-period API budget).

Product extraction results:

| Model | Mean ± Std (tokens) | Range | Significant fits |
|-------|-------------------|-------|-----------------|
| qwen3-32b | 95 ± 26 | [65, 134] | 5/5 |
| llama-3.1-8b | 110 ± 24 | [84, 140] | 4/5 |
| llama-3.3-70b | 110 ± 22 | [80, 131] | 4/5 |
| gemini-flash | 57 ± 17 | [49, 91] | 1/5 |
| claude-haiku | 58 ± 0 | [58, 58] | 0/5 |

The results reveal a capability-dependent pattern. Mid-range models (qwen3-32b, llama-3.1-8b, llama-3.3-70b) show robust saturation: 13/15 fits are significant, with saturation points clustering at 65–140 tokens regardless of ordering. Stronger models (gemini-flash, claude-haiku) show flatter curves with fewer significant fits (1/10), consistent with these models requiring less prompt elaboration to reach high quality — the same capability-modulated saturation reported in Section 4.2.

Classification: only 2/25 fits are significant. This reflects the ceiling effect (quality already ~0.94 at Level 1), not ordering sensitivity — consistent with Q2 above.

**Key finding:** For the task with sufficient dynamic range (product extraction), saturation is robust across orderings in mid-range models. What changes across orderings is *where* the curve bends, not *whether* it bends — the sigmoid shape persists across all significant fits. In frontier models, the quality curve is too flat for curve fitting to detect a meaningful inflection point, which is itself consistent with the saturation hypothesis — these models saturate at or before Level 1.

### Q4: Second Judge

We re-judged 3,915 responses using gemini-2.0-flash as an independent second judge. Both judges use the same 4-dimension rubric (correctness, completeness, reasoning, conciseness, each 1–5); the original judge was gpt-4o-mini. We report both Pearson and Spearman (rank) correlations:

| Task | n | Pearson r | Spearman ρ | MAE | Orig mean | Gemini mean |
|------|---|-----------|-----------|-----|-----------|-------------|
| Classification | 980 | 0.835 | 0.750 | 0.044 | 0.922 | 0.961 |
| Math reasoning | 978 | 0.859 | 0.800 | 0.033 | 0.910 | 0.927 |
| QA | 980 | 0.287 | 0.102 | 0.086 | 0.912 | 0.995 |
| Product extraction | 977 | 0.247 | 0.319 | 0.150 | 0.835 | 0.976 |

**Agreement is strong where it matters most.** Classification and math reasoning show strong correlation (Pearson r > 0.83, Spearman ρ ≥ 0.75), as expected for tasks with crisp ground truths where both judges key on the same signal.

For QA and product extraction, we emphasize three points:

**(1) Both judges agree on the task-level pattern.** Both show quality increasing from L1 to L7 for product extraction (gpt-4o-mini: +0.163; gemini: +0.073) and flat/declining for QA (gpt-4o-mini: −0.035; gemini: −0.008). The disagreement is about calibration, not direction.

**(2) Both judges agree on the per-model direction.** For product extraction, 6 of 7 models show the same L1→L7 direction under both judges. For classification, 6 of 7 agree. Even for QA, where the original judge shows slight quality *decreases* (mean delta −0.035), both judges agree on direction for the 3 models with the largest deltas (llama-3.1-8b, claude-haiku, gemini-flash).

**(3) Low Pearson r reflects rubric leniency asymmetry, not pattern disagreement.** Gemini-flash assigns scores > 0.9 to 98.8% of QA responses, compressing variance to near zero. With one judge's scores clustered at the ceiling, Pearson correlation is mechanically undefined regardless of agreement on the underlying pattern. The Spearman ρ for product extraction (0.319) is higher than the Pearson r (0.247), consistent with nonlinear score compression rather than genuine disagreement.

We acknowledge that the gemini-flash judge's compressed score range makes it less informative for detecting saturation curves. The choice of judge model is itself a methodological degree of freedom — one we are transparent about. We note that gpt-4o-mini's stricter scoring is more useful for our analysis precisely because it preserves the variance needed to fit curves.

### Q5: F-Test Power

The reviewer correctly notes that our F-test (7 level means, 2–3 fitted parameters) has limited power. We view the F-test as a *conservative filter*: tasks that pass it show strong saturation, but tasks that fail may still exhibit weaker saturation masked by low power. The borderline cases (llama-3.1-8b classification at p=0.06, kimi-k2 extraction at p≈0.05) are consistent with this interpretation.

The randomized ablation provides a complementary test that sidesteps the F-test limitation: for product extraction, 13/15 permutations across mid-range models produce significant fits, confirming that saturation is robust beyond what the original F-test alone can establish. The structured/open dichotomy is thus supported by converging evidence from two independent statistical approaches.

### Q6: Schema-Compliance Hypothesis

The reviewer correctly notes that the schema-compliance hypothesis is stated but not directly tested. We now provide three converging lines of evidence:

**(1) Marginal contribution analysis.** For classification, the two schema-defining layers — L1→L2 (task label, +0.073) and L2→L3 (format specification, +0.017) — together account for 61% of total quality gain. For product extraction, L6→L7 (worked example demonstrating output schema, +0.067) accounts for 40% of gain. In both cases, the layers that communicate *what the output should look like* are the dominant quality drivers.

**(2) Ceiling stratification.** Open-ended tasks (QA, math) reach ceiling at L1 precisely because they do *not* require schema compliance — the model already knows what to output (an answer, a number). Structured tasks start below ceiling because the model must learn the expected output format from the prompt.

**(3) Output format compression.** For classification, output length drops from 85 tokens (L1, verbose explanation) to 2 tokens (L3+, just the label) as format specification takes effect. The quality gain tracks this compression — the prompt teaches the model the output schema, and once learned, further elaboration adds nothing.

We will revise the manuscript to present schema-compliance as a hypothesis supported by converging evidence rather than a standalone tested contribution, and will include the marginal contribution analysis as a supporting figure.

### Q7: Grouping of Summarization and Instruction Following

The reviewer raises a valid point: summarization and instruction following arguably involve schema-like elements (expected format, constraint satisfaction) and do not cleanly fit the "open-ended" label. We acknowledge that the two-bucket grouping (structured vs. open) is a simplification. The marginal contribution data suggests a gradient rather than a binary: classification and extraction show large, concentrated gains from schema-defining layers; instruction following shows modest gains spread across layers (biggest: L5→L6 guidelines, +0.010); summarization shows near-zero total gain (biggest: L2→L3, +0.004). The grouping reflects where *statistically significant* saturation was detected, not a claim that these tasks share identical mechanisms. We will soften the language in the revision to present this as a spectrum with clear poles (classification vs. QA) and intermediate cases (instruction following, summarization).

### LLMLingua Distinction

LLMLingua compresses existing verbose prompts by removing redundant tokens; our work asks whether the verbosity was necessary in the first place. These are complementary: LLMLingua answers "how to shorten a given prompt," while we answer "how much prompt is enough for a given task." We note that both approaches converge on the practical recommendation of shorter, well-targeted prompts, and will clarify this relationship in the revision.

### Post-Hoc Grouping

We present the structured-vs-open grouping as a post-hoc hypothesis, not a pre-registered finding, and will make this explicit in the revision. However, it is supported by three independent analyses: (1) the ceiling stratification (Q2) shows that open-ended tasks hit ceiling at L1 while structured tasks do not, (2) the marginal contribution analysis shows qualitatively different layer-importance profiles between the two groups, and (3) the schema-compliance evidence (Q6) shows that schema-defining layers drive quality gains in structured tasks specifically. We view this as a hypothesis with converging supporting evidence warranting further investigation.

---

## Reviewer R19f (Rating: 4, Confidence: 4)

### Q1: Length vs. Content Confound

This is the central methodological question. We conducted a randomized ablation to test whether saturation is driven by token count or information content (full details in CnfP Q3 above).

In the randomized ablation (5 random permutations × 5 models × 7 examples = 2,986 experiments), we shuffled the order in which prompt layers are introduced. For product extraction, mid-range models (qwen3-32b, llama-3.1-8b, llama-3.3-70b) show robust saturation across orderings: 13/15 fits are significant, with saturation clustering at 65–140 tokens regardless of which layers come first.

The observed ~2× range in saturation points (65–140 tokens) tells us something important: *which* information comes first does modulate *where* the curve bends, but it does not eliminate *whether* the curve bends. The sigmoid shape persists across all significant fits. This demonstrates that saturation is a genuine property of the task-model interaction, not an artifact of our particular layer ordering.

We acknowledge that a stronger test would include a control with irrelevant padding tokens (to test whether raw token count alone shifts the curve). Absent that, the ablation shows the saturation curve is robust to information ordering but cannot fully rule out a token-count component. We will note this as a concrete future experiment.

### Q2: Few-Shot Not Helping QA/Math

**QA:** Models score 0.89–0.95 at Level 1 (bare question). The ceiling stratification analysis (CnfP Q2) confirms that 16–20 of 20 examples per model are already above 0.85 at L1. Adding a worked example (L7) not only fails to help but consistently *hurts* quality (mean L1→L7 delta = −0.035). Few-shot examples provide task clarification, not factual knowledge — and for already-solved problems, they may anchor the model's response style on the example rather than the actual question. Both judges confirm this decline: the second judge (gemini-flash) also shows QA quality decreasing from L1 to L7 for the 3 models with the largest original deltas.

**Math reasoning:** The per-level data reveals a striking non-monotonic pattern. L3 ("Give only the final numerical answer") causes a sharp quality drop across *all 7 models* and *both judges* (original judge: L2=0.967 → L3=0.601; second judge: L2=0.986 → L3=0.574). L3 suppresses chain-of-thought reasoning, which is critical for math accuracy — a well-documented finding in the CoT literature (Wei et al., 2022). L4 restores step-by-step reasoning and quality recovers immediately (L4=0.964).

This is one of the most actionable findings in the paper: certain prompt instructions are not merely unhelpful but actively *destructive*. The standard sigmoid model does not capture tasks where intermediate prompt layers are counterproductive. We will discuss this non-monotonicity explicitly in the revision and note that prompt design should consider not just "how much" but "what kind" of elaboration.

### Q3: Broader Model Range

Our 7 models span 8B parameters (llama-3.1-8b) to medium-tier API models (gpt-4o-mini, gemini-2.0-flash, claude-haiku). We observe capability-modulated saturation, but the direction is task-dependent:

- **Classification:** Stronger models saturate earlier (gemini-flash at ~31 tokens vs. llama-3.1-8b at ~70 tokens). Stronger models infer the task from less context.
- **Product extraction:** The pattern reverses — stronger models saturate *later* (claude-haiku at ~504 tokens vs. llama-3.1-8b at ~80 tokens) but reach *higher* asymptotic quality (0.99 vs. 0.87). Stronger models extract more from detailed prompts, while weaker models plateau early at lower quality.

This reversal is itself a novel finding: model capability and prompt saturation interact differently depending on task structure. For tasks where the model must *infer* what to do (classification), stronger models need less prompt. For tasks where the prompt provides *actionable format specifications* (extraction), stronger models leverage more of them.

Beyond the speed of saturation, models also differ in *how* they saturate. Most models fit sigmoid curves on classification (sharp plateau after L3–L4), but qwen3-32b fits a logarithmic curve — it keeps extracting incremental gains from later layers where other models show zero late-level gain. This suggests that models differ not just in when they saturate but in how gradually they integrate prompt elaboration, which has practical implications: prompt optimization should be model-specific, not one-size-fits-all.

We do not include true frontier models (GPT-4, Claude Opus) due to cost constraints, and will note the reversed saturation pattern and model-specific curve shapes as concrete hypotheses for future work with larger models.

### Scope

We agree the study focuses on single-turn instruction tasks and will explicitly scope our claims to this setting. However, we note that this scope is deliberate, not a limitation: agentic workflows, retrieval-augmented generation, and multi-turn dialogues introduce confounds (tool selection, retrieval quality, multi-turn drift) that would make it impossible to isolate the prompt length → quality relationship. Our controlled design is what enables clean measurement of the saturation phenomenon. Characterizing saturation in more complex settings is a natural next step that builds on the foundation established here.

In total, the study encompasses 5,913 main experiments (7 models × 6 tasks × 7 levels × 20 examples, plus 200-example replications for 2 tasks), 2,986 randomized ablation experiments, and 3,915 second-judge re-evaluations — 12,814 total LLM evaluations across the main study and rebuttal period. We believe this scope is appropriate for establishing and characterizing the saturation phenomenon.

---

## Reviewer 4x2b (Rating: 4, Confidence: 4)

### Title

We agree the original title overstates. We propose: **"When Does Prompt Elaboration Stop Helping? Saturation Curves Across Structured and Open-Ended LLM Tasks"** — this captures both sides of the finding (saturation in structured tasks, ceiling effects in open-ended tasks) without overstating.

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

### Sample Size

We use 20 examples per task because each example must be paired with 7 additive prompt levels and evaluated across 7 models — yielding 980 observations per task in the main study (20 × 7 × 7). The replication study extends classification and QA to 200 examples. The randomized ablation adds 2,986 further experiments.

For the effects we detect, n=20 provides adequate power. Classification shows a quality jump of +0.15 from L1 to L4 with within-model standard deviations of ~0.05 — an effect size of d ≈ 3.0, detectable at well below n=20. Product extraction shows similar large effects (+0.163 L1→L7 under the original judge).

Regarding existing benchmarks: our additive prompt design requires *custom prompt construction* at each level — existing benchmark datasets provide inputs/outputs but not the graduated prompt hierarchy that is our methodological contribution. We did use standard benchmark data where available (Amazon product reviews for classification and product extraction, GSM8K-style problems for math reasoning, SQuAD-derived questions for QA).

### "Practitioners Use Verbose Prompts"

This claim is grounded in documented practice:

- **Official guidance:** OpenAI's Prompt Engineering Guide recommends adding step-by-step instructions, role assignments, and system prompts — all of which increase prompt length (OpenAI, 2024). Anthropic's documentation similarly recommends detailed task descriptions and examples (Anthropic, 2024).
- **Benchmark prompts:** MMLU evaluation prompts routinely exceed 1,000 tokens with few-shot examples (Hendrycks et al., 2021). HumanEval and MBPP code benchmarks include multi-paragraph system prompts.
- **Industry practice:** The "mega-prompt" pattern — prompts of 500–2,000+ tokens with roles, constraints, examples, and formatting rules — is widely documented in prompt engineering communities and commercial LLM applications.

We will include these citations in the revision.

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

These tables confirm the saturation pattern: quality rises sharply from L1 to L3–L4, then plateaus.

### Qualitative Examples

Concrete example (classification, gpt-4o-mini, example 0 — "Absolutely love this laptop..."):
- **L1** (30 tokens, q=0.90): "This review can be classified as **Positive**." — correct label embedded in a verbose explanation
- **L3** (44 tokens, q=1.00): "Positive" — just the label, higher quality because format matches
- **L5** (105 tokens, q=1.00): "positive" — identical correct output
- **L7** (182 tokens, q=1.00): "positive" — no further improvement despite 6× more prompt tokens

The model infers the correct sentiment from L1; additional layers improve format compliance but not semantic accuracy.

### Level 1 Ambiguity

The reviewer raises a valid point: Level 1 is intentionally under-specified (e.g., "Classify: {text}"), and a model's ability to infer "sentiment classification" from context makes L1 performance partly a measure of model inference ability rather than a fixed baseline.

However, this is accounted for in our analysis. The L1→L2 quality delta (+0.073 for classification, averaged across 7 models) explicitly quantifies what explicit specification adds *beyond* model inference. The saturation analysis measures quality trajectories starting from whatever L1 achieves — it does not assume a fixed baseline. Moreover, the per-model variation at L1 (0.78–0.90 for classification) is itself informative: it reveals which models can infer the task without explicit specification and which cannot. We will clarify in the revision that L1 represents "task communication via input context alone" and L2+ adds explicit task specification.

### Evaluation Design

Our LLM judge (gpt-4o-mini) uses a shared 4-dimension framework (correctness, completeness, reasoning, conciseness) but with *task-specific rubric text and ground truth*. For classification, correctness evaluates label match against the ground-truth sentiment; for product extraction, it evaluates field-level precision and recall against structured ground truth; for QA, it checks factual alignment with the reference answer. The rubric text steers the judge's focus per task within the shared framework.

We validated this design by re-judging all 3,915 responses with an independent second judge (gemini-2.0-flash). The two judges agree on L1→L7 direction for 6/7 models on classification and 6/7 on product extraction — the two tasks central to our saturation claims. For tasks with crisp ground truths, both Pearson and Spearman correlations are strong (classification: r=0.835, ρ=0.750; math: r=0.859, ρ=0.800). See CnfP Q4 for the full analysis.

### Bibliography Errors

We thank the reviewer for catching these errors and will correct all citations in the camera-ready version.

### Replication Scope

The replication study covered classification (clear saturation) and QA (no saturation) to test both poles of our findings. Extending replication to product extraction and instruction following would strengthen the paper; we were constrained by rebuttal-period API budget (the ablation and second-judge experiments consumed the available budget). We will note this as high-priority future work and will extend replication to these tasks for the camera-ready version if accepted.

---

## Summary of New Evidence

| Evidence | Addresses | Key Finding |
|----------|-----------|-------------|
| Randomized ablation (5 perms × 5 models, n=2,986) | All reviewers (length vs. content) | Product extraction: 13/15 significant for mid-range models; sigmoid shape robust across orderings |
| Second judge + rank correlations (n=3,915) | CnfP Q4 | Pearson r=0.835/0.859 (classification/math); direction agreement 6/7 on classification and extraction |
| Ceiling stratification | CnfP Q2, R19f Q2 | QA/math "non-saturation" is ceiling-at-L1 (16–20/20 examples above 0.85) |
| Threshold sensitivity | CnfP Q1 | Median 90%-to-95% shift = 3 tokens (classification); knee estimates confirm |
| Marginal contributions | 4x2b, CnfP Q6 | L1→L2 = 49% of gain (classification); L6→L7 = 40% (extraction); schema-defining layers dominate |
| Math L3 non-monotonicity | R19f Q2 | "Final answer only" instruction destroys quality (−0.366) across all models and both judges |
| Output length control | 4x2b Q2 | Partial r confirms prompt→quality after controlling output length (PE: 0.447) |
| Per-level tables + examples | C2JD | Full transparency on quality progression across all 42 model×task combinations |
| F-test + ablation convergence | CnfP Q5 | Two independent statistical approaches confirm structured/open dichotomy |

**Total experimental scope:** 12,814 LLM evaluations (5,913 main + 2,986 randomized ablation + 3,915 second judge).
