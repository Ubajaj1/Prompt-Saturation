# COLM 2026 Rebuttal — Succinct Responses

Each section is sized for the 5,000-character per-section limit. Numbers reconcile to source data files. All tables and figures are collected in the Appendix at the end.

---

## Overall Response

We thank all reviewers for their careful reading. The reviews converged on a central concern — that our additive design confounds length and content — and correctly identified that the original "token threshold" framing overstated what the data support. We agree on both counts. To address this, we ran **8,371 new LLM evaluations**: a randomized layer-ordering ablation (2,986), an irrelevant-padding control (1,470), and an independent second judge (3,915), plus threshold sensitivity, ceiling stratification, and per-layer marginal-contribution analyses. These experiments confirmed the saturation phenomenon but refined the mechanism — information content, not token count. Five themes recur; we address each once below.

**1. Length vs. content (R19f central, CnfP Q3, 4x2b).** We agree with R19f's stronger framing: the seven levels are *qualitatively different mechanisms* (task label, format spec, definitions, persona, guidelines, worked example), not length units. Our marginal-contribution analysis measures the quality delta between each adjacent level pair (e.g., L1→L2, L2→L3), isolating how much each mechanism contributes to overall quality gain rather than treating the levels as increments of length. Two additional controls disentangle length from content.

In the *ablation* (2,986 runs, 2,450 analyzed; kimi-k2 excluded due to Groq deprecation, though its recorded main-study outputs are retained), product extraction yielded 13/15 significant fits in mid-range models, with per-model mean saturation at 95–110 tokens (full range across orderings: 65–140). These ablation means are substantially lower than the original fixed-ordering estimates (92–378 tokens) because the original ordering always placed the most valuable layer (the worked example) last, delaying the quality bend to higher token counts.

In the *padding control* (1,470 runs, 3 filler types), irrelevant text produced flat or declining quality (mean delta of −0.074 for classification and −0.013 for product extraction; only 1 of 26 conditions showed a significant positive trend, consistent with chance). Real content over the same token range produced gains of +0.10 and +0.16. The real-content delta exceeded the padding delta for 9 of 10 model-task pairs, with the largest gaps in llama-3.1-8b classification (+0.190 vs. −0.161) and qwen3-32b product extraction (+0.220 vs. −0.038). We conclude that saturation reflects *information sufficiency*, not token budget.

**2. Scope and sample size (R19f, 4x2b, C2JD).** Each of our 20 examples is evaluated across 7 levels and 7 models, yielding 980 observations per task. The classification L1-to-L4 effect size is d=2.4, detectable well below n=20, and a 200-example replication confirms the main-study fits. Single-turn scope is a genuine limitation but a deliberate choice, as agentic and RAG settings introduce confounds that prevent clean isolation. We will scope sentiment-only classification claims explicitly; product extraction provides a second structurally distinct task with the same pattern.

**3. Framing — title, "thresholds," post-hoc grouping (R19f, 4x2b, CnfP).** We agree the original framing was too strong. The ablation showed that "token threshold" was the wrong abstraction, and the binary grouping was too coarse. We now describe tasks along a gradient of how quality gain distributes across prompt layers (a descriptive framework, not a standalone contribution): *concentrated* (classification — 49% of gain from one layer), *distributed* (product extraction — task label 32% + worked example 40%), *diffuse* (instruction following — small gains across many layers), and *insensitive* (QA, math, summarization — near-zero or negative total gain at ceiling from L1).

The practical takeaway is concrete: for classification, specify the task label; for extraction, include a worked example; for QA and math, the bare question suffices. A particularly striking finding is that instructing models to "give only the final answer" for math destroys quality by −0.366 across all 7 models and both judges — some prompt content is actively harmful. Threshold sensitivity analysis (CnfP Q1) confirms classification saturation is stable within a fixed ordering, with a median 90-to-95% shift of only 3 tokens. We propose a revised title: **"When Does Prompt Elaboration Stop Helping? Prompt Sensitivity Across LLM Tasks."**

**4. Judge reliability (CnfP Q4, C2JD).** We re-judged all 3,915 responses with gemini-2.0-flash using the same task-specific rubric. Agreement is strong where it matters most: classification r=0.835 with MAE=0.044, and math r=0.859 with MAE=0.033. The low Pearson r on QA and product extraction reflects ceiling compression rather than pattern disagreement — Gemini assigns scores above 0.9 to 98.8% of QA responses and 88.7% of product extraction responses, leaving little variance to correlate. Direction agreement holds for 5/7 models on classification and 4/7 on product extraction, where the 3 non-agreements involve Gemini deltas of 0.003 or less. As prior work has shown (Chen et al. 2025; Li et al. 2026), different LLM judges exhibit systematic calibration differences; gpt-4o-mini preserves more variance, making it more useful for curve fitting.

**5. New-evidence summary.** We conducted a randomized ablation (n=2,986), a padding control (n=1,470), a second-judge re-evaluation (n=3,915), and analyses of threshold sensitivity, ceiling stratification, marginal contributions, output-length partial correlations, and per-level quality tables with qualitative examples. **Total scope:** 17,378 evaluations across 5,875 main-study runs, approximately 2,800 replication runs, 8,371 new rebuttal runs, and 332 sub-8B experiments.

---

## Reviewer CnfP (Rating: 5, Confidence: 3)

**Q1 — Threshold sensitivity.** We recomputed saturation at 85/90/95/99% of the fitted asymptote and using a threshold-free knee estimator. For classification, 6 of 7 models show stable saturation points, with a median 90-to-95% shift of just 3 tokens and all but one model shifting by fewer than 11 tokens. The sole outlier is qwen3-32b, which follows a logarithmic rather than sigmoid trajectory and shifts by 95 tokens. This model uniquely benefits from the guidelines layer (L6), suggesting it integrates detailed instructions more gradually — though with a single model showing this pattern on a single task, we treat this as an observation requiring further study. Its threshold-free knee estimate (42 tokens) falls close to the other models, confirming similar saturation onset despite the different curve shape. Product extraction shows wider spread by design, but knees confirm onset at comparable scales (e.g., llama-3.3-70b knee=96 vs. 95% threshold=92).

**Q2 — Ceiling stratification.** Across models, 16–20 of 20 QA examples already score above 0.85 at L1, leaving too few below-ceiling examples for reliable curve fitting. The above-ceiling subset is flat-to-declining (e.g., gemini L1=0.94 declining to L7=0.91; mean delta=−0.035), consistent with extra layers adding noise to already-correct responses. Math shows the same ceiling pattern but is sharply non-monotonic: L3 ("give only the final numerical answer") collapses quality across all 7 models and both judges (L2=0.967 to L3=0.601 to L4=0.964), with L4's restoration of step-by-step reasoning recovering performance immediately. This confirms the reviewer's intuition that QA and math non-saturation is ceiling-at-L1.

**Q3 — Layer-ordering ablation.** The full ablation results are detailed in Overall Theme 1. Kimi-k2 was excluded because the model was deprecated by Groq between the main study and rebuttal, returning 404 errors on all 490 attempted runs; original main-study data is retained. The results confirm the capability-dependent pattern reported in Section 4.2 of the original paper: models requiring more prompt elaboration (qwen3-32b, llama-3.1-8b, llama-3.3-70b) show 13/15 significant product extraction fits with means of 95–110 tokens, while stronger models (gemini-flash, claude-haiku) show flatter curves with only 1/10 significant fits, consistent with reaching high quality from less prompt. Classification's 2/25 significant fits reflects its concentrated step-function shape — once the task label appears at any position, quality jumps and curves are flat thereafter. Curve fitting is the wrong tool for step functions; marginal contributions detect this pattern instead (see Q5/Q6).

**Q4 — Second judge.** Detailed in Overall Theme 4. Per-task agreement: classification r=0.835 with MAE=0.044, math r=0.859 with MAE=0.033, QA r=0.287 with MAE=0.086, product extraction r=0.247 with MAE=0.150. For QA and product extraction, the low r reflects ceiling compression on Gemini's side (scores above 0.9 for 98.8% and 88.7% of responses respectively), not pattern disagreement.

**Q5 — F-test power.** The reviewer is right that the borderline cases (llama-3.1-8b classification at p=0.079; kimi-k2 product extraction at p=0.093) are plausibly true positives. Under the gradient framework, these models are prompt-sensitive — marginal-contribution analysis confirms substantive L1-to-L7 deltas of +0.190 and +0.166 respectively, and the ablation reclassifies mid-range models as 13/15 significant for product extraction. We were wrong to leave these as ambiguous originally. The ablation also clarifies where the F-test reliably operates: it detects *distributed* sensitivity (product extraction rising from 3/7 to 14/25 significant) but not *concentrated* sensitivity (classification falling from 4/7 to 2/25). This is a tool-shape mismatch, not a power failure, and curve fitting plus marginal contributions are complementary.

**Q6 — Schema-compliance hypothesis.** Three converging lines of evidence, all post-hoc analyses on existing data rather than pre-registered confirmations. First, marginal contributions show that classification's two schema-defining layers (L1-to-L2 at +0.073 and L2-to-L3 at +0.017) account for 61% of total gain, while product extraction's worked example (L6-to-L7 at +0.067) accounts for 40%. Second, ceiling stratification shows that QA and math reach ceiling at L1 precisely because they do not require schema compliance. Third, classification output drops from 85 to 2 tokens as format specification takes effect, with quality tracking the compression.

**Q7 — Grouping of summarization and instruction following.** Fair point. We replace the binary grouping with the descriptive gradient described in Overall Theme 3, placing summarization as *insensitive* and instruction following as *diffuse*, motivated by their marginal-contribution profiles rather than saturation status alone.

**LLMLingua distinction.** LLMLingua operates at inference time per instance, compressing a written prompt by removing low-information tokens. Our work operates at authoring time per task, providing priors on which mechanisms yield gains before any specific instance is constructed. The two are complementary: author the right mechanisms (our contribution), then compress wording within them (LLMLingua). For classification, LLMLingua-2 might compress L7 from approximately 180 to 36 tokens, but our analysis shows that L1-to-L2 (adding roughly 5 tokens of task label) already captures 49% of the quality gain — the L7 elaboration was largely unnecessary content, not redundant wording.

**Post-hoc grouping.** The reviewer is right that the original grouping was post-hoc. The new gradient is also post-hoc, which we are transparent about — it is a descriptive framework supported by three independent analyses (ceiling stratification, marginal contributions, and ablation), not a tested taxonomy. Validation on new tasks is future work.

---

## Reviewer R19f (Rating: 4, Confidence: 4)

**Q1 — Length vs. content confound.** This is the central methodological question, addressed by the ablation and padding control detailed in Overall Theme 1. Saturation is driven by information content, not token count: the sigmoid shape persists across orderings for models requiring more prompt elaboration (13/15 significant for product extraction), but the token threshold shifts substantially (original 92–378 vs. ablation 95–110) because the original ordering placed the most valuable layer last. The padding control directly confirms the null hypothesis: matched-token-count irrelevant filler produces flat or declining quality (mean delta of −0.074 for classification, −0.013 for product extraction; only 1 of 26 conditions significant positive, consistent with chance), while real content yields gains of +0.10 and +0.16 over the same token range. The per-model real-vs-padding gap is consistent across all 5 models and both tasks (see Appendix, Table A2). We will reframe in the revision to emphasize *information sufficiency*, with practical guidance becoming "include the high-value layers identified by marginal-contribution analysis" rather than "trim after N tokens."

**Q2 — Few-shot not helping QA/math.** Ceiling effects explain both cases.

For QA, 16–20 of 20 examples per model score above 0.85 at L1. Adding a worked example (L7) consistently hurts (mean delta=−0.035), and both judges agree on direction for the 3 models with the largest deltas. Few-shot examples provide task clarification, not factual knowledge — for problems the model already solves correctly, they can anchor the response style rather than improve accuracy.

For math, L3 ("give only the final numerical answer") causes a sharp quality drop across all 7 models and both judges (original judge L2=0.967 to L3=0.601; second judge L2=0.986 to L3=0.574). L3 suppresses chain-of-thought reasoning (Wei et al. 2022), and L4's restoration of step-by-step reasoning recovers quality immediately (L4=0.964). Excluding L3, the remaining trajectory is flat (means ranging from 0.951 to 0.970; per-model range at most 0.060), so the no-saturation conclusion holds independent of the L3 anomaly. This finding has direct practical implications: certain prompt instructions are not merely unhelpful but actively destructive, and the standard sigmoid model does not capture this non-monotonicity.

**Q3 — Broader model range.** Our 7 models span 8B parameters (llama-3.1-8b) to medium-tier API models (gpt-4o-mini, gemini-2.0-flash, claude-haiku). We observe capability-modulated saturation that is task-dependent in direction: for classification, stronger models saturate earlier (gemini-flash at approximately 31 tokens vs. llama-3.1-8b at approximately 70), while for product extraction the pattern reverses — stronger models saturate later but reach higher asymptotic quality (claude-haiku at approximately 504 tokens and q=0.99 vs. llama-3.1-8b at approximately 80 tokens and q=0.87). Stronger models infer more from sparse prompts but also extract more from detailed format specifications.

To test whether this trend extends below 8B, we ran Llama-3.2-1B-Instruct on classification and product extraction using the same prompts and judge (332 runs). On classification, the 1B model starts lower (L1 q=0.467 vs. 8B's 0.780) and gains 1.58 times more from elaboration (delta=+0.300 vs. +0.190), but saturates at a lower ceiling (L7 q=0.767 vs. 0.970). On product extraction, the 1B model shows a dramatic floor effect — complete failure at L1–L2 (q=0.000), then a jump to 0.776 at L3 when format specs are introduced, plateauing at approximately 0.850. The 8B model already achieves 0.767 at L1, yielding an effect ratio of 8.72 times. The capability-modulated trend now extends monotonically from 1B through 8B, 32B, 70B, and API-tier: weaker models are more prompt-dependent but saturate at lower quality. The floor effects at 1B validate our original scope decision while confirming the predicted direction below 8B. Frontier models (GPT-4, Claude Opus) are excluded due to cost and flagged as future-work hypotheses.

The qwen3-32b logarithmic curve shape on classification is noted with an n=1 caveat — a single model on a single task cannot distinguish architectural properties from noise without further models.

**Scope and transfer to agentic/RAG.** Single-turn scope is deliberate, as agentic and RAG settings introduce confounds (tool selection, retrieval quality, multi-turn drift) that prevent clean isolation. Our mechanism-level findings yield concrete predictions rather than undifferentiated future work: the schema-compliance mechanism (40% of product extraction gain from one layer) predicts that a single well-specified tool-schema layer should suffice in agentic settings, while RAG settings introduce an orthogonal content-quality confound where saturation should depend on retrieval quality rather than prompt length. **Total study: 17,378 LLM evaluations.**

---

## Reviewer 4x2b (Rating: 4, Confidence: 4)

**Title.** We agree the original title overstates. The ablation and padding controls reframe saturation as *information sufficiency* rather than task-specific *token thresholds*. We propose: **"When Does Prompt Elaboration Stop Helping? Prompt Sensitivity Across LLM Tasks."**

**Per-layer marginal contributions.** For classification, L1-to-L2 (adding the task label) contributes +0.073 quality, accounting for 49% of total positive gain, with subsequent layers yielding diminishing returns (L2-to-L3 at +0.017, L3-to-L4 at +0.030, L4-to-L5 at −0.020). A single well-chosen instruction captures most of the quality benefit. For product extraction, the pattern differs: L6-to-L7 (the worked example) contributes +0.067 or 40% of gain, while L1-to-L2 (the task label) adds +0.054 or 32%. Structured-output tasks benefit more from format demonstrations. For math, L3's suppression of chain-of-thought causes a dramatic −0.366 quality drop, with L4's restoration recovering +0.363 — this non-monotonicity is larger than any positive task gain in the study. For QA, the total delta is −0.035, with every layer beyond bare input either neutral or slightly harmful.

**Output length control.** Classification output drops from 85.1 to 2.1 tokens as format specification takes effect. Partial correlations controlling for output length confirm that the prompt-to-quality relationship persists (see Appendix, Table A3). For product extraction, the partial r is substantial at 0.447, confirming that prompt content — not output compression alone — drives quality gains. We note that partial r assumes linearity, and classification's 85-to-2-token transition is quasi-discrete, so we report this as a first-order check rather than a definitive decomposition. Non-linear treatments (binning by output regime, restricting to L3+) yield the same qualitative conclusion.

**Classification domain breadth.** We agree that results are sentiment-only. Two partial mitigations exist within scope: product extraction is a second structured task with the same qualitative pattern but different output structure (4-field JSON vs. single label) and gain locus (worked example vs. task label), and the marginal-contribution analysis explains *why* classification saturates quickly (one layer, 49% of gain) — a mechanism that should generalize to other domains where the label set is inferable. Specialized label spaces (e.g., medical ICD-10) may shift the saturation point upward but should retain the concentrated-gain shape. We will explicitly scope sentiment-only claims and flag other classification domains as priority follow-ups.

**Sample size.** Our 20 examples yield 980 observations per task (20 examples times 7 levels times 7 models). The classification L1-to-L4 effect has a mean delta of +0.12 across 7 models (range +0.045 to +0.220) with within-model standard deviation of approximately 0.05, giving an effect size of d=2.4 — detectable well below n=20. Product extraction shows similarly large effects (+0.163 from L1 to L7). The 200-example replication extends classification and QA to SST-2 and SQuAD respectively, and the ablation adds 2,986 further runs. Existing benchmarks provide inputs and outputs but not the graduated additive prompts required by our design — this prompt construction is the methodological contribution.

**"Practitioners use verbose prompts."** This claim is grounded in documented practice. OpenAI's Prompt Engineering Guide recommends structured prompts with sections for Role, Instructions, Reasoning Steps, Output Format, Examples, and Context — each adding tokens. Anthropic's documentation similarly recommends detailed task descriptions and examples. Academic surveys document the same trend: Sahoo et al. (2024, arXiv:2402.07927) surveys elaborate prompting techniques, Schulhoff et al. (2024, arXiv:2406.06608) catalogues 58+ techniques that mostly add tokens, and Levy et al. (2024, arXiv:2402.14848) directly studies the effect of increasing input length. Benchmark prompts from MMLU, HumanEval, and MBPP routinely include extensive few-shot examples or multi-paragraph system prompts. All cited works are already in our bibliography; we will add explicit inline citations in the revision.

---

## Reviewer C2JD (Rating: 3, Confidence: 4)

**Per-level quality tables.** Full per-level means are provided as supplementary CSV covering all 7 models across 6 tasks. As shown in Appendix Table A1, classification quality rises sharply from L1 to L3–L4 and then plateaus across all 7 models. Full tables for all 6 tasks are included in the supplementary material.

**Qualitative example.** For classification (gpt-4o-mini, "Absolutely love this laptop..."), L1 (30 tokens, q=0.90) produces "This review can be classified as **Positive**" — a correct label embedded in verbose explanation. By L3 (44 tokens, q=1.00), the output is simply "Positive," and L7 (182 tokens, q=1.00) produces "positive" — no improvement despite 6 times more prompt tokens. For product extraction (gemini-flash, "Nike Air Max 270..."), L1 (37 tokens, q=0.70) produces a bulleted list in the wrong format, L3 (63 tokens, q=0.80) produces JSON but with "Air Max 270" instead of "Nike Air Max 270," and L7 (271 tokens, q=1.00) produces the correct four-field JSON. The worked example at L6-to-L7, which marginal analysis identifies as 40% of total gain, teaches the exact schema. Classification saturates from a single instruction; extraction requires a format demonstration.

**Level-1 ambiguity.** This is a valid point. L1 is intentionally under-specified (e.g., "Classify: {text}"), so L1 performance partly measures the model's ability to infer the task. We account for this analytically: the L1-to-L2 delta (+0.073 for classification) quantifies what explicit specification adds beyond inference. The per-model L1 spread (0.78 to 0.90) is itself informative, as it identifies which models can infer the task without specification. We will clarify in the revision that L1 represents "task communication via input context alone," with L2 onward adding explicit specification.

**Evaluation design.** The four dimensions are a shared output schema for cross-task comparability; the rubric text given to the judge is task-specific. QA emphasizes correctness and reference matching, classification emphasizes label match and direct labeling, product extraction emphasizes field-level accuracy and completeness of all 4 fields, math emphasizes final numerical answer match, and instruction following emphasizes constraint satisfaction. This implements what the reviewer suggested: genuinely different evaluation foci under a comparable reporting structure. The second judge (gemini-2.0-flash) used the identical task-specific rubric and confirms agreement on classification (r=0.835) and math (r=0.859), with direction agreement for 5/7 models on classification and 4/7 on product extraction.

**Data construction.** Twenty examples per task were assembled to balance unambiguous ground truth with difficulty range. Classification uses SST-2-style sentences with sarcasm and mixed sentiment excluded to control label noise. Product extraction uses product-listing snippets across electronics, household goods, and books, each with 4-field structured ground truth. QA uses factoid questions in SQuAD-style format. Math reasoning uses 20 word problems (10 easy, 10 medium, 2–3 steps) with exact numerical answers. Summarization uses short news passages with reference summaries, and instruction following uses prompts with 1–2 explicit structural constraints. The 200-example replication samples directly from SST-2 and SQuAD with identical prompt templates. Full per-example listings will be included in camera-ready supplementary material.

**Bibliography errors.** We confirm both errors: "A Survey of Automatic Prompt Engineering" (arXiv:2502.11560) should be Li et al., not Amatriain et al., and "CompactPrompt" (arXiv:2510.18043) should be Choi et al., not Wang et al. These arose from incorrect metadata in preprint sources. We have verified correct author listings on arXiv and checked the remaining bibliography with no other errors found.

**Replication scope.** Replication covered both poles — classification (saturation) and QA (no saturation). Product extraction and instruction following on external benchmarks were constrained by rebuttal API budget. The ablation (2,986 runs) and padding control (1,470 runs) provide partial replication for product extraction with new orderings and instantiations, preserving the L1-to-L7 effect direction (mid-range models 13/15 significant; +0.16 real delta vs. −0.013 padding delta). This is not a substitute for external-benchmark replication, but it does independently confirm the saturation pattern's robustness to prompt variation. Full replication on an external dataset such as Amazon-ESCI is high-priority for camera-ready if accepted.

---

## Appendix: Tables and Figures

### Table A1: Classification Per-Level Mean Quality (7 Models)

| Model | L1 | L2 | L3 | L4 | L5 | L6 | L7 |
|---|---|---|---|---|---|---|---|
| gemini-flash | 0.83 | 0.86 | 0.89 | 0.94 | 0.92 | 0.91 | 0.94 |
| llama-3.1-8b | 0.78 | 0.89 | 0.93 | 1.00 | 0.91 | 0.97 | 0.97 |
| llama-3.3-70b | 0.90 | 0.95 | 0.94 | 0.94 | 0.94 | 0.94 | 0.94 |
| gpt-4o-mini | 0.79 | 0.81 | 0.91 | 0.94 | 0.94 | 0.94 | 0.97 |
| claude-haiku | 0.92 | 0.95 | 0.94 | 0.97 | 0.97 | 0.94 | 0.97 |
| kimi-k2 | 0.74 | 0.94 | 0.91 | 0.91 | 0.91 | 0.94 | 0.94 |
| qwen3-32b | 0.88 | 0.94 | 0.94 | 0.97 | 0.94 | 1.00 | 1.00 |

Quality rises sharply from L1 to L3–L4 and then plateaus across all 7 models. Full tables for all 6 tasks are provided in the supplementary CSV.

### Table A2: Real vs. Padding Quality Deltas (L1 to L7)

| Model | Task | Real Delta | Padding Delta |
|---|---|:-:|:-:|
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

Real content consistently produces positive quality gains, while irrelevant padding produces flat or negative changes.

### Table A3: Output-Length Partial Correlations

| Task | r(output, quality) | partial r(prompt, quality given output) |
|---|:-:|:-:|
| Classification | −0.186 | 0.106 |
| Product extraction | −0.313 | 0.447 |
| Instruction following | 0.616 | 0.209 |

The prompt-to-quality relationship persists after controlling for output length across all three tasks.

### Table A4: Second Judge Agreement

| Task | n | Pearson r | MAE | Original Mean | Gemini Mean |
|---|---|:-:|:-:|:-:|:-:|
| Classification | 980 | 0.835 | 0.044 | 0.922 | 0.961 |
| Math reasoning | 978 | 0.859 | 0.033 | 0.910 | 0.927 |
| QA | 980 | 0.287 | 0.086 | 0.912 | 0.995 |
| Product extraction | 977 | 0.247 | 0.150 | 0.835 | 0.976 |

Strong agreement for classification and math (r > 0.83, MAE < 0.05). Low r for QA and product extraction reflects ceiling compression on the Gemini judge, not pattern disagreement.

### Table A5: New Evidence Summary

| Evidence | n | Addresses |
|---|:-:|---|
| Randomized layer-ordering ablation | 2,986 | Length vs. content; F-test power |
| Irrelevant-padding control | 1,470 | Token-count null hypothesis |
| Independent second judge | 3,915 | Judge reliability; evaluation design |
| Threshold sensitivity (85/90/95/99% + knee) | — | Threshold robustness |
| Ceiling stratification (QA/math) | — | Non-saturation interpretation |
| Per-layer marginal contributions | — | Gain distribution gradient |
| Output-length partial correlations | — | Output-length confound |
| Per-level quality tables + qualitative examples | — | Transparency |
| Sub-8B experiment (Llama-3.2-1B) | 332 | Capability-modulated saturation below 8B |
