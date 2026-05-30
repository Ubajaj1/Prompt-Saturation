# COLM 2026 Rebuttal — Succinct Responses

Each section is sized for the ≤5000-character per-section limit. Numbers reconcile to source data files.

---

## Overall Response

We thank all reviewers for their careful reading. The reviews converged on a central concern — that our additive design confounds length and content — and correctly identified that the original "token threshold" framing overstated what the data support. We agree on both counts. To address this, we ran **8,371 new LLM evaluations**: a randomized layer-ordering ablation (2,986), an irrelevant-padding control (1,470), and an independent second judge (3,915), plus threshold sensitivity, ceiling stratification, and per-layer marginal-contribution analyses. These experiments confirmed the saturation phenomenon but refined the mechanism — information content, not token count. Five themes recur; we address each once below.

**1. Length vs. content (R19f central, CnfP Q3, 4x2b).** Two controls separate them.
- *Ablation* (2,986 raw runs, 2,450 analyzed after excluding kimi-k2 — deprecated by Groq between main study and rebuttal; original data retained). Focuses on classification and product extraction (the only tasks with significant fits — confound is moot where quality is flat). Product extraction: 13/15 significant fits in models requiring more elaboration, saturation at 65–140 tokens across orderings. Token threshold *shifts* (original 92–378 → ablation 95–110) because the high-value layer always came last originally.
- *Padding* (1,470 runs, 3 filler types, same two tasks). Irrelevant text → flat/declining quality (mean Δ = −0.074 classification, −0.013 PE; 1/26 significant positive, expected by chance). Real content over same token range: +0.10 / +0.16.

Conclusion: saturation reflects *information sufficiency*, not token budget.

**2. Scope and sample size (R19f, 4x2b, C2JD).** n=20 yields 980 obs/task (20 × 7 × 7). Classification L1→L4 effect d≈2.4 — detectable well below n=20; 200-example replication confirms. Single-turn scope is a genuine limitation but a deliberate choice (agentic/RAG settings introduce confounds). We will scope sentiment-only classification claims explicitly; product extraction provides a second structurally distinct task with the same pattern.

**3. Framing — title, "thresholds," post-hoc grouping (R19f, 4x2b, CnfP).** We agree the original framing was too strong. The ablation showed "token threshold" was the wrong abstraction; the binary grouping was post-hoc and too coarse. We now describe tasks along a gradient of how quality gain distributes across prompt layers (a descriptive framework, not a standalone contribution):
- *Concentrated:* classification — 49% of gain from one layer (task label).
- *Distributed:* product extraction — task label 32% + worked example 40%.
- *Diffuse:* instruction following — small gains across many layers (largest L5→L6 = +0.010).
- *Insensitive:* QA, math, summarization — near-zero or negative total gain (ceiling at L1).

The practical takeaway: *for classification, specify the task label; for extraction, include a worked example; for QA/math, the bare question suffices.* A particularly striking finding: instructing models to "give only the final answer" for math destroys quality by −0.366 across all 7 models and both judges — some prompt content is actively harmful.

Threshold sensitivity (CnfP Q1): classification saturation stable within fixed ordering (median 90→95% shift = 3 tokens; 6/7 models <11 tokens). Proposed new title: **"When Does Prompt Elaboration Stop Helping? Prompt Sensitivity Across LLM Tasks."**

**4. Judge reliability (CnfP Q4, C2JD).** We re-judged all 3,915 responses with gemini-2.0-flash on the same 4-dimension rubric. Strong agreement where it matters: classification r=0.835 / MAE=0.044, math r=0.859 / MAE=0.033. Low Pearson r on QA/PE is a ceiling artefact — Gemini assigns >0.9 to 98.8% of QA and 88.7% of PE responses, leaving little variance to correlate. Direction agreement: 5/7 models on classification, 4/7 on PE (the 3 PE non-agreements are Gemini deltas ≤0.003 — ceiling compression, not opposite signs). Different judge models exhibit systematically different score calibrations (Chen et al., 2025; Li et al., 2026). gpt-4o-mini preserves more variance than Gemini, making it more useful for curve fitting — not because it is "more correct," but because variance is required for meaningful regression.

**5. New-evidence summary.**

| Evidence | n | Addresses |
|---|--:|---|
| Random ablation | 2,986 | Length vs. content; F-test power |
| Padding control | 1,470 | Token-count null |
| Second judge | 3,915 | Judge reliability |
| Threshold sensitivity | — | Threshold robustness |
| Ceiling stratification | — | QA/math non-saturation |
| Marginal contributions | — | Gain distribution gradient |
| Output-length partial r | — | Output-length confound |
| Per-level tables + qual. examples | — | Transparency |

**Total scope:** 17,046 evaluations = 5,875 main + ≈2,800 200-example replication + 8,371 new.

---

## Reviewer CnfP (Rating: 5, Confidence: 3)

**Q1 — Threshold sensitivity.** We recomputed saturation at 85/90/95/99% and via a threshold-free knee estimate. Classification: median 90→95% shift = 3 tokens; 6/7 models shift <11 tokens (e.g., gemini-flash 31→42→52, knee=34). The qwen3-32b outlier (log fit, 95-token shift) reflects model behaviour, not a fitting artefact: it is the only model that benefits from L6 (guidelines, +0.060) where others show 0.000 late-level gain; its threshold-free knee (42) sits with the other models. Product extraction has wider spread by design (gemini 293–546 tokens) but knees confirm the underlying onset (llama-3.3-70b knee=96 vs. 95% threshold=92).

**Q2 — Ceiling stratification.** Stratifying by L1 quality (≥0.85): QA has 16–20/20 examples above ceiling per model, leaving 0–4 below — too few for reliable curve fitting. The above-ceiling subset is flat-to-declining (gemini L1=0.94 → L7=0.91; mean Δ=−0.035), consistent with extra layers adding noise to already-correct responses. Math shows the same ceiling pattern but is sharply non-monotonic: L3 ("final numerical answer only") collapses quality across all 7 models and both judges (overall L2=0.967 → L3=0.601 → L4=0.964); L4 restoring step-by-step reasoning recovers it. Confirms the reviewer's intuition: QA/math non-saturation = ceiling-at-L1.

**Q3 — Layer-ordering ablation.** See Overall Theme 1. kimi-k2 was excluded due to model deprecation by Groq (404 errors on all 490 runs; original main-study data retained). The capability-dependent pattern is clear: models requiring more prompt elaboration to reach high quality (qwen3-32b, llama-3.1-8b, llama-3.3-70b) show 13/15 significant PE fits with means 95–110 tokens; stronger models (gemini-flash, claude-haiku) show flatter curves and fewer significant fits (1/10), consistent with reaching high quality from less prompt. Classification's 2/25 reflects its concentrated, step-function shape — once the task label appears (any position), quality jumps and curves are flat thereafter. Curve fitting is the wrong tool for step functions; marginal contributions detect this pattern (Q5/Q6).

**Q4 — Second judge.** See Overall Theme 4. Per-task r/MAE: classification 0.835/0.044; math 0.859/0.033; QA 0.287/0.086; PE 0.247/0.150. For QA/PE the low r is ceiling compression on Gemini's side (>0.9 on 98.8%/88.7% of responses), not pattern disagreement.

**Q5 — F-test power.** Ablation clarifies where the F-test reliably acts: it detects *distributed* sensitivity (PE: 3/7 original → 14/25 ablation; mid-range 13/15) but not *concentrated* sensitivity (classification 4/7 → 2/25). Borderline p-values (llama-3.1-8b classification p=0.079; kimi-k2 PE p=0.093) are consistent with this: concentration just diffuse enough for a curve to partially fit. Curve fitting + marginal contributions provide complementary coverage across different sensitivity patterns.

**Q6 — Schema-compliance hypothesis.** Three converging lines:
1. *Marginal contributions:* classification L1→L2 (+0.073) + L2→L3 (+0.017) = 61% of gain — the schema-defining layers. PE L6→L7 (worked example, +0.067) = 40% of gain.
2. *Ceiling stratification:* QA/math reach ceiling at L1 because they don't require schema compliance.
3. *Output compression:* classification output drops from 85 to 2 tokens as format spec takes effect; quality tracks compression.

**Q7 — Grouping of summarization & instruction following.** Fair point. We replace the binary grouping with a descriptive gradient (Overall Theme 3): summarization and instruction following land in *insensitive* / *diffuse* respectively, motivated by the marginal-contribution data, not by their saturation status alone.

**LLMLingua distinction.** LLMLingua compresses *given* verbose prompts by removing redundant tokens; we ask whether verbosity was needed in the first place. For example, a classification prompt at L7 (~180 tokens) might be compressed by LLMLingua to ~36 tokens by removing filler. Our marginal analysis shows L1→L2 (adding just the task label) accounts for 49% of quality gain — the other ~150 tokens were largely unnecessary, not just redundantly worded. Our work identifies what to *include*; LLMLingua optimises how concisely to *express* it — complementary, not overlapping.

**Post-hoc grouping.** The reviewer is right: the original grouping was post-hoc. The gradient we now describe is also post-hoc — we are transparent about this. We present it as a descriptive framework supported by three independent analyses (ceiling, marginal, ablation), not as a tested taxonomy. Validation on new tasks is flagged as future work.

---

## Reviewer R19f (Rating: 4, Confidence: 4)

**Q1 — Length vs. content confound.** Central methodological question; addressed by ablation + padding (Overall Theme 1). Saturation is driven by information content, not token count: the *shape* persists across orderings (PE for models requiring more prompt elaboration: 13/15 significant), but the *token threshold* shifts (original 92–378 → ablation 95–110) because the original ordering placed the worked-example layer last. The padding control directly confirms the null: matched-token-count irrelevant filler produces flat/declining quality (Δ = −0.074 classification, −0.013 PE; 1/26 significant positive — chance) while real content yields +0.10 / +0.16 over the same token range. Per-model real-vs-padding gap is consistent across all 5 models × 2 tasks. We will reframe in the revision: *information sufficiency*, not task-specific token budgets; practical guidance becomes "include high-value layers identified by marginal-contribution analysis."

**Q2 — Few-shot not helping QA/math.** Ceiling explains both.

*QA:* 16–20/20 examples score ≥0.85 at L1 per model. Adding a worked example (L7) consistently *hurts* (mean Δ=−0.035); both judges agree on direction for the 3 models with the largest deltas. Few-shot provides task clarification, not factual knowledge — for already-solved problems it can anchor on the example's style.

*Math:* L3 ("give only the final numerical answer") causes a sharp drop across *all 7 models and both judges* (original L2=0.967 → L3=0.601; second judge L2=0.986 → L3=0.574). L3 suppresses chain-of-thought (Wei et al. 2022). L4 restores reasoning and quality recovers (L4=0.964). The L1→L7 ≈ 0 average masks a strong non-monotonic trajectory. This has direct practical implications: *certain prompt instructions are not merely unhelpful but actively destructive.* The standard sigmoid model does not capture this; we will discuss explicitly.

**Q3 — Broader model range.** Our 7 models span 8B (llama-3.1-8b) to medium-tier API models (gpt-4o-mini, gemini-2.0-flash, claude-haiku). We see capability-modulated saturation, but direction is task-dependent:
- Classification: stronger models saturate *earlier* (gemini-flash ≈31 tokens vs. llama-3.1-8b ≈70).
- Product extraction: stronger models saturate *later* but reach *higher* asymptote (claude-haiku ≈504 tokens at q≈0.99 vs. llama-3.1-8b ≈80 tokens at q≈0.87).

Stronger models infer more when the prompt is sparse but extract more when the prompt provides actionable format specs. Models also differ in *how* they saturate — in our data, qwen3-32b uniquely follows a logarithmic shape on classification, integrating later layers gradually rather than snapping early (an empirical observation, not a documented architectural property). Prompt optimization is therefore model-specific. Frontier models (GPT-4, Claude Opus) are out due to cost; we will note the reversal and curve-shape variation as concrete future-work hypotheses.

**Scope.** Scope is single-turn instruction tasks — a genuine limitation, but a deliberate choice: agentic, RAG, and multi-turn settings introduce confounds (tool selection, retrieval quality, multi-turn drift) that would prevent clean isolation of the prompt-content → quality relationship. Extending to these settings is a priority for future work. Total study: **5,875 main + ≈2,800 200-example replication + 8,371 new = 17,046 LLM evaluations.** This scope provides a rigorous foundation for establishing and characterising the saturation phenomenon.

---

## Reviewer 4x2b (Rating: 4, Confidence: 4)

**Title.** Agreed — original overstates. The ablation and padding controls (Overall Theme 1) reframe saturation as *information sufficiency* rather than task-specific *token thresholds*. Proposed: **"When Does Prompt Elaboration Stop Helping? Prompt Sensitivity Across LLM Tasks."**

**Per-layer marginal contributions.**
- *Classification:* L1→L2 (task label) +0.073 = **49%** of gain. Subsequent layers: L2→L3 +0.017, L3→L4 +0.030, L4→L5 −0.020. One well-chosen instruction captures most benefit.
- *Product extraction:* L6→L7 (worked example) +0.067 = **40%** of gain; L1→L2 (task label) +0.054 = 32%. Structured-output tasks benefit from format demonstrations.
- *Math:* L3 (suppress CoT) **−0.366**; L4 (restore CoT) **+0.363** — non-monotonicity larger than any positive task gain.
- *QA:* total Δ=−0.035 — every layer beyond bare input either neutral or slightly harmful (ceiling).

**Output length control.** Classification output drops 85.1 → 2.1 tokens (L1 → L3+) as format spec takes effect. Partial correlations controlling for output length:

| Task | r(output, q) | partial r(prompt, q \| output) |
|---|---:|---:|
| Classification | −0.186 | 0.106 |
| Product extraction | −0.313 | 0.447 |
| Instruction following | 0.616 | 0.209 |

The prompt → quality relationship persists after controlling for output length; for PE the partial r is substantial (0.447), confirming prompt content — not output compression alone — drives gains.

**Classification domain breadth.** Agreed: results are sentiment-only. Two partial mitigations within scope: (i) product extraction is a second structured task with the same qualitative pattern but very different output structure (4-field JSON vs. single label) and gain locus (worked example vs. task label); (ii) marginal-contribution analysis explains *why* classification saturates so quickly (one layer, 49% of gain) — a mechanism that should generalise to other domains where the label set is inferable. Specialised label spaces (e.g., medical ICD-10) may shift the saturation point upward but should retain the concentrated-gain shape. We will explicitly scope sentiment-only claims and flag topic/intent/category classification as priority follow-ups.

**Sample size.** 20 examples × 7 levels × 7 models = 980 obs/task. Classification L1→L4 mean Δ = +0.12 across 7 models (range +0.045 to +0.220), within-model SD ≈ 0.05 → effect size d ≈ 2.4, detectable well below n=20. PE shows similar large effects (+0.163 L1→L7 under original judge). Replication extends classification and QA to 200 examples (SST-2, SQuAD); ablation adds 2,986 further runs. Existing benchmarks provide inputs/outputs but not the graduated additive prompts required by our design — this prompt construction *is* the methodological contribution.

**"Practitioners use verbose prompts."** Documented practice:
- *Official guidance:* OpenAI's Prompt Engineering Guide recommends structured prompts with "Role, Instructions, Reasoning Steps, Output Format, Examples, Context" sections — each adding tokens. Anthropic's docs similarly recommend detailed task descriptions and examples.
- *Academic surveys:* Sahoo et al. (2024, arXiv:2402.07927) documents proliferation of elaborate prompting techniques; Schulhoff et al. (2024, arXiv:2406.06608) catalogues 58+ techniques, most adding tokens; Levy et al. (2024, arXiv:2402.14848) directly studies increasing input length — implicitly documenting practitioner tendency toward longer prompts. All already in our bibliography.
- *Benchmark prompts:* MMLU few-shot prompts routinely exceed 1,000 tokens; HumanEval and MBPP include multi-paragraph system prompts.

We will add explicit inline citations in the revision.

---

## Reviewer C2JD (Rating: 3, Confidence: 4)

**Per-level quality tables.** Full per-level means provided as supplementary CSV (7 models × 6 tasks). Classification sample:

| Model | L1 | L2 | L3 | L4 | L5 | L6 | L7 |
|---|---|---|---|---|---|---|---|
| gemini-flash | 0.83 | 0.86 | 0.89 | 0.94 | 0.92 | 0.91 | 0.94 |
| llama-3.1-8b | 0.78 | 0.89 | 0.93 | 1.00 | 0.91 | 0.97 | 0.97 |
| llama-3.3-70b | 0.90 | 0.95 | 0.94 | 0.94 | 0.94 | 0.94 | 0.94 |
| gpt-4o-mini | 0.79 | 0.81 | 0.91 | 0.94 | 0.94 | 0.94 | 0.97 |
| claude-haiku | 0.92 | 0.95 | 0.94 | 0.97 | 0.97 | 0.94 | 0.97 |
| kimi-k2 | 0.74 | 0.94 | 0.91 | 0.91 | 0.91 | 0.94 | 0.94 |
| qwen3-32b | 0.88 | 0.94 | 0.94 | 0.97 | 0.94 | 1.00 | 1.00 |

Quality rises sharply L1→L3/L4, then plateaus across all 7 models. Full tables for all 6 tasks in supplementary CSV.

**Qualitative example** (classification, gpt-4o-mini, "Absolutely love this laptop…"):
- L1 (30 tok, q=0.90): "This review can be classified as **Positive**." — correct label in verbose explanation.
- L3 (44 tok, q=1.00): "Positive" — just the label.
- L5 (105 tok, q=1.00): "positive" — identical.
- L7 (182 tok, q=1.00): "positive" — no further improvement at 6× the prompt tokens.

Product extraction (gemini-flash, "Nike Air Max 270…"):
- L1 (37 tok, q=0.70): Bulleted list with extra fields — correct info, wrong format.
- L3 (63 tok, q=0.80): JSON with correct fields but "Air Max 270" instead of "Nike Air Max 270".
- L7 (271 tok, q=1.00): `{"name": "Nike Air Max 270", "price": "150", "brand": "Nike", "category": "shoes"}` — worked example (L6→L7, 40% of gain) teaches exact schema.

Classification saturates from a single instruction; extraction requires a format demonstration — illustrating the concentration gradient.

**Level-1 ambiguity.** Valid: L1 is intentionally under-specified ("Classify: {text}"), so L1 performance partly measures the model's ability to infer the task. We account for this analytically: the L1→L2 delta (+0.073 classification) explicitly quantifies what *explicit specification* adds beyond inference. The per-model L1 spread (0.78–0.90) is itself informative — it identifies which models can infer the task without specification. We will clarify in the revision that L1 = "task communication via input context alone"; L2+ adds explicit specification.

**Evaluation design.** Our judge (gpt-4o-mini) uses a shared 4-dimension framework (correctness, completeness, reasoning, conciseness) but with **task-specific rubric text and ground truth**: classification scores label-match against ground-truth sentiment; product extraction evaluates field-level precision/recall against structured ground truth; QA checks factual alignment. The rubric steers focus per task within the shared framework. We validated by re-judging all 3,915 responses with gemini-2.0-flash (Overall Theme 4): classification r=0.835, math r=0.859; direction agreement 5/7 classification, 4/7 PE (with 3 PE non-agreements being Gemini deltas ≤0.003 — ceiling compression, not opposite signs).

**Data construction.** 20-example sets balanced for unambiguous ground truth and difficulty range:
- *Sentiment classification:* 20 SST-2-style sentences (positive/negative/neutral); sarcasm and mixed-sentiment cases excluded to control label noise.
- *Product extraction:* 20 product-listing snippets across electronics/household/books with varying difficulty (buried prices, implicit brands), each with 4-field structured ground truth.
- *QA:* 20 short factoid questions across geography/history/science (SQuAD-style) with single-string ground truth.
- *Math:* 20 word problems (10 easy, 10 medium) requiring 2–3 reasoning steps, exact-numeric ground truth.
- *Summarization:* 20 short news passages with reference summaries.
- *Instruction following:* 20 prompts with 1–2 explicit structural constraints.

The 200-example replication for classification/QA samples directly from SST-2 and SQuAD with identical prompt templates and evaluation. Full per-example listings will be in the camera-ready supplementary.

**Bibliography errors.** We confirm both errors: (1) "A Survey of Automatic Prompt Engineering" (arXiv:2502.11560) should be Li et al., not Amatriain et al.; (2) "CompactPrompt" (arXiv:2510.18043) should be Choi et al., not Wang et al. These arose from incorrect metadata in preprint sources. We have verified correct author listings on arXiv and checked the remaining bibliography — no other errors found. Will be corrected in the camera-ready.

**Replication scope.** Replication covered both poles — classification (clear saturation) and QA (no saturation). PE and instruction-following replication was constrained by rebuttal-period API budget (the 8,371 new evaluations consumed available compute). High-priority for the camera-ready if accepted.
