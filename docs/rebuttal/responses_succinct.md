# COLM 2026 Rebuttal — Succinct Responses

Each section is sized for the ≤5000-character per-section limit. Numbers reconcile to source data files.

---

## Overall Response

We thank all reviewers for their careful reading. The reviews converged on a central concern — that our additive design confounds length and content — and correctly identified that the original "token threshold" framing overstated what the data support. We agree on both counts. To address this, we ran **8,371 new LLM evaluations**: a randomized layer-ordering ablation (2,986), an irrelevant-padding control (1,470), and an independent second judge (3,915), plus threshold sensitivity, ceiling stratification, and per-layer marginal-contribution analyses. These experiments confirmed the saturation phenomenon but refined the mechanism — information content, not token count. Five themes recur; we address each once below.

**1. Length vs. content (R19f central, CnfP Q3, 4x2b).** We agree with R19f's stronger framing: the seven levels are *qualitatively different mechanisms* (task label, format spec, definitions, persona, guidelines, worked example), not length units. Marginal-contribution analysis treats each as a distinct mechanism; two controls disentangle length from content.
- *Ablation* (2,986 runs, 2,450 analyzed; kimi-k2 excluded — Groq deprecation, but recorded outputs are immutable so main-study data is retained). PE: 13/15 significant fits in mid-range models, saturation at 65–140 tokens across orderings. Token threshold *shifts* (orig 92–378 → ablation 95–110) because the high-value layer always came last originally.
- *Padding* (1,470 runs, 3 filler types). Irrelevant text → flat/declining quality (Δ = −0.074 cls, −0.013 PE; 1/26 sig positive = chance). Real content same token range: +0.10 / +0.16. Real Δ ≥ padding Δ for **9/10** model×task pairs. Largest gaps: llama-3.1-8b cls (+0.190 vs −0.161); qwen3-32b PE (+0.220 vs −0.038).

Conclusion: saturation reflects *information sufficiency*, not token budget.

**2. Scope and sample size (R19f, 4x2b, C2JD).** n=20 yields 980 obs/task (20 × 7 × 7). Classification L1→L4 effect d≈2.4 — detectable well below n=20; 200-example replication confirms. Single-turn scope is a genuine limitation but a deliberate choice (agentic/RAG settings introduce confounds). We will scope sentiment-only classification claims explicitly; product extraction provides a second structurally distinct task with the same pattern.

**3. Framing — title, "thresholds," post-hoc grouping (R19f, 4x2b, CnfP).** We agree the original framing was too strong. The ablation showed "token threshold" was the wrong abstraction; the binary grouping was post-hoc and too coarse. We now describe tasks along a gradient of how quality gain distributes across prompt layers (a descriptive framework, not a standalone contribution):
- *Concentrated:* classification — 49% of gain from one layer (task label).
- *Distributed:* product extraction — task label 32% + worked example 40%.
- *Diffuse:* instruction following — small gains across many layers (largest L5→L6 = +0.010).
- *Insensitive:* QA, math, summarization — near-zero or negative total gain (ceiling at L1).

The practical takeaway: *for classification, specify the task label; for extraction, include a worked example; for QA/math, the bare question suffices.* A particularly striking finding: instructing models to "give only the final answer" for math destroys quality by −0.366 across all 7 models and both judges — some prompt content is actively harmful.

Threshold sensitivity (CnfP Q1): classification saturation stable within fixed ordering (median 90→95% shift = 3 tokens; 6/7 models <11 tokens). Proposed new title: **"When Does Prompt Elaboration Stop Helping? Prompt Sensitivity Across LLM Tasks."**

**4. Judge reliability (CnfP Q4, C2JD).** Re-judged all 3,915 responses with gemini-2.0-flash on identical task-specific rubric. Strong agreement where it matters: cls r=0.835 / MAE=0.044, math r=0.859 / MAE=0.033. Low Pearson r on QA/PE is ceiling compression (Gemini >0.9 on 98.8% QA, 88.7% PE). Direction agreement: 5/7 cls, 4/7 PE (3 PE non-agreements are Gemini Δ ≤0.003). Different judges show systematic calibration differences (Chen et al. 2025; Li et al. 2026); gpt-4o-mini preserves more variance for curve fitting.

**5. New-evidence summary.** Random ablation (n=2,986; length vs. content + F-test power); padding control (1,470; token-count null); second judge (3,915; judge reliability); threshold sensitivity, ceiling stratification, marginal contributions, output-length partial r, per-level tables + qual. examples.

**Total scope:** 17,378 evaluations = 5,875 main + ≈2,800 200-example replication + 8,371 new + 332 sub-8B.

---

## Reviewer CnfP (Rating: 5, Confidence: 3)

**Q1 — Threshold sensitivity.** Saturation recomputed at 85/90/95/99% + threshold-free knee. Classification: median 90→95% shift = 3 tokens; 6/7 models <11 tokens. qwen3-32b outlier (log fit, 95-tok shift) reflects per-model trajectory — only model that benefits from L6 (n=1 caveat: single model, single task, cannot separate architecture from noise). Knee (42) sits with others. PE wider spread by design but knees confirm onset (llama-3.3-70b knee=96 vs. 95% threshold=92).

**Q2 — Ceiling stratification.** Stratifying by L1 quality (≥0.85): QA has 16–20/20 examples above ceiling per model, leaving 0–4 below — too few for reliable curve fitting. The above-ceiling subset is flat-to-declining (gemini L1=0.94 → L7=0.91; mean Δ=−0.035), consistent with extra layers adding noise to already-correct responses. Math shows the same ceiling pattern but is sharply non-monotonic: L3 ("final numerical answer only") collapses quality across all 7 models and both judges (overall L2=0.967 → L3=0.601 → L4=0.964); L4 restoring step-by-step reasoning recovers it. Confirms the reviewer's intuition: QA/math non-saturation = ceiling-at-L1.

**Q3 — Layer-ordering ablation.** See Overall Theme 1. kimi-k2 was excluded due to model deprecation by Groq (404 errors on all 490 runs; original main-study data retained). The capability-dependent pattern is clear: models requiring more prompt elaboration to reach high quality (qwen3-32b, llama-3.1-8b, llama-3.3-70b) show 13/15 significant PE fits with means 95–110 tokens; stronger models (gemini-flash, claude-haiku) show flatter curves and fewer significant fits (1/10), consistent with reaching high quality from less prompt. Classification's 2/25 reflects its concentrated, step-function shape — once the task label appears (any position), quality jumps and curves are flat thereafter. Curve fitting is the wrong tool for step functions; marginal contributions detect this pattern (Q5/Q6).

**Q4 — Second judge.** See Overall Theme 4. Per-task r/MAE: classification 0.835/0.044; math 0.859/0.033; QA 0.287/0.086; PE 0.247/0.150. For QA/PE the low r is ceiling compression on Gemini's side (>0.9 on 98.8%/88.7% of responses), not pattern disagreement.

**Q5 — F-test power.** The reviewer is right that the borderline cases (llama-3.1-8b classification p=0.079; kimi-k2 PE p=0.093) are plausibly true positives. Under the gradient framework these models are **prompt-sensitive** — marginal-contribution analysis confirms substantive L1→L7 deltas (llama-3.1-8b classification +0.190; kimi-k2 PE +0.166), and ablation reclassifies kimi-k2-style mid-range models as 13/15 significant for PE. We were wrong to leave these as ambiguous originally. Ablation also clarifies where the F-test reliably acts: it detects *distributed* sensitivity (PE: 3/7 → 14/25; mid-range 13/15) but not *concentrated* sensitivity (classification 4/7 → 2/25) — a tool-shape mismatch (smooth fit vs. step function), not a power failure. Curve fitting + marginal contributions are complementary.

**Q6 — Schema-compliance hypothesis.** Three converging lines, all post-hoc analyses on existing data (not pre-registered confirmations):
1. *Marginal contributions:* classification L1→L2 (+0.073) + L2→L3 (+0.017) = 61% of gain — the schema-defining layers. PE L6→L7 (worked example, +0.067) = 40% of gain.
2. *Ceiling stratification:* QA/math reach ceiling at L1 because they don't require schema compliance.
3. *Output compression:* classification output drops from 85 to 2 tokens as format spec takes effect; quality tracks compression.

**Q7 — Grouping of summarization & instruction following.** Fair point. We replace the binary grouping with a descriptive gradient (Overall Theme 3): summarization and instruction following land in *insensitive* / *diffuse* respectively, motivated by the marginal-contribution data, not by their saturation status alone.

**LLMLingua distinction.** Different lifecycle stages: LLMLingua (and LLMLingua-2's task-aware variant) operates **at inference time, per instance** — compresses a written prompt by removing low-information tokens. Our work operates **at authoring time, per task** — priors on which mechanisms yield gains *before* a specific instance is written. The two stack: author the right mechanisms (us), then compress wording (LLMLingua). For cls, LLMLingua-2 might compress L7 (~180 tok) to ~36 tok; our analysis shows L1→L2 (~5 tok of task label) captures 49% of gain — L7 elaboration was largely unnecessary content, not redundantly-worded.

**Post-hoc grouping.** Reviewer is right; the original grouping was post-hoc. The new gradient is also post-hoc (we are transparent) — a descriptive framework supported by three independent analyses (ceiling, marginal, ablation), not a tested taxonomy. Validation on new tasks is future work.

---

## Reviewer R19f (Rating: 4, Confidence: 4)

**Q1 — Length vs. content confound.** Central methodological question; addressed by ablation + padding (Overall Theme 1). Saturation is driven by information content, not token count: the *shape* persists across orderings (PE for models requiring more prompt elaboration: 13/15 significant), but the *token threshold* shifts (original 92–378 → ablation 95–110) because the original ordering placed the worked-example layer last. The padding control directly confirms the null: matched-token-count irrelevant filler produces flat/declining quality (Δ = −0.074 classification, −0.013 PE; 1/26 significant positive — chance) while real content yields +0.10 / +0.16 over the same token range. Per-model real-vs-padding gap is consistent across all 5 models × 2 tasks. We will reframe in the revision: *information sufficiency*, not task-specific token budgets; practical guidance becomes "include high-value layers identified by marginal-contribution analysis."

**Q2 — Few-shot not helping QA/math.** Ceiling explains both.

*QA:* 16–20/20 examples score ≥0.85 at L1 per model. Adding a worked example (L7) consistently *hurts* (mean Δ=−0.035); both judges agree on direction for the 3 models with the largest deltas. Few-shot provides task clarification, not factual knowledge — for already-solved problems it can anchor on the example's style.

*Math:* L3 ("give only the final numerical answer") causes a sharp drop across *all 7 models and both judges* (original L2=0.967 → L3=0.601; second judge L2=0.986 → L3=0.574). L3 suppresses chain-of-thought (Wei et al. 2022). L4 restores reasoning and quality recovers (L4=0.964). Excluding L3, the L1, L2, L4–L7 trajectory is flat (means: 0.951, 0.967, 0.964, 0.960, 0.954, 0.970; per-model range ≤0.060), so the no-saturation conclusion holds independent of the L3 anomaly. This has direct practical implications: *certain prompt instructions are not merely unhelpful but actively destructive.* The standard sigmoid model does not capture this; we will discuss explicitly.

**Q3 — Broader model range.** Our 7 models span 8B (llama-3.1-8b) to medium-tier API models (gpt-4o-mini, gemini-2.0-flash, claude-haiku). We see capability-modulated saturation, task-dependent in direction:
- Classification: stronger models saturate *earlier* (gemini-flash ≈31 tokens vs. llama-3.1-8b ≈70).
- PE: stronger models saturate *later* but reach *higher* asymptote (claude-haiku ≈504 tokens at q≈0.99 vs. llama-3.1-8b ≈80 tokens at q≈0.87).

*On weaker models — new sub-8B experiment.* We ran Llama-3.2-1B-Instruct (1B params) on classification and PE using the same prompts and judge (332 runs). Results confirm the predicted pattern: on classification, the 1B model starts lower (L1 q=0.467 vs. 8B's 0.780) and gains 1.58× more from elaboration (Δ=+0.300 vs. +0.190), but saturates at a lower ceiling (L7 q=0.767 vs. 0.970). On PE, the 1B model shows a dramatic floor effect — complete failure at L1–L2 (q=0.000), then jumps to 0.776 at L3 when format specs are introduced, plateauing at ~0.850; the 8B model is already at 0.767 from L1 (effect ratio: 8.72×). The capability-modulated trend now extends monotonically from 1B → 8B → 32B → 70B → API: weaker models are more prompt-dependent but saturate at lower quality. Floor effects at 1B are real (complete PE failure without format specs, non-monotonic classification), validating our original scope decision while confirming the direction below 8B. Frontier models (GPT-4, Claude Opus) out due to cost; flagged as future-work hypotheses.

Stronger models infer more when prompt is sparse, extract more when prompt provides actionable format specs. qwen3-32b uniquely follows a logarithmic shape on classification (n=1 caveat — single model, single task; cannot distinguish architectural property from noise without further models).

**Scope and transfer to agentic/RAG.** Single-turn instruction scope is a deliberate choice — agentic and RAG settings introduce confounds (tool selection, retrieval quality, multi-turn drift) that prevent clean isolation. But our mechanism-level findings yield concrete predictions: the schema-compliance mechanism (40% of PE gain in one layer) plausibly predicts that a single tool-call schema layer should suffice in agentic settings; RAG settings introduce an orthogonal content-quality confound where saturation should depend on retrieval quality, not prompt length. We frame these as scope-extending hypotheses, not undifferentiated future work. Total study: **5,875 main + ≈2,800 200-example replication + 8,371 new + 332 sub-8B = 17,378 LLM evaluations.**

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

The prompt → quality relationship persists after controlling for output length; for PE the partial r is substantial (0.447), confirming prompt content — not output compression alone — drives gains. Caveat: partial r assumes linearity; the classification 85→2-token output transition is quasi-discrete, so partial r is a first-order check, not a definitive decomposition. Non-linear treatments (binning by output regime, restricting to L3+) yield the same qualitative conclusion.

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

**Qualitative example** (cls, gpt-4o-mini, "Absolutely love this laptop…"): L1 (30 tok, q=0.90) "This review can be classified as **Positive**." → L3 (44 tok, q=1.00) "Positive" → L7 (182 tok, q=1.00) "positive" — no improvement at 6× prompt tokens. PE (gemini-flash, "Nike Air Max 270…"): L1 (37 tok, q=0.70) bulleted list, wrong format → L3 (63 tok, q=0.80) JSON but "Air Max 270" not "Nike Air Max 270" → L7 (271 tok, q=1.00) `{"name": "Nike Air Max 270", ...}` — worked example (L6→L7, 40% of gain) teaches exact schema. Classification saturates from a single instruction; extraction requires a format demonstration.

**Level-1 ambiguity.** Valid: L1 is intentionally under-specified ("Classify: {text}"), so L1 performance partly measures the model's ability to infer the task. We account for this analytically: the L1→L2 delta (+0.073 classification) explicitly quantifies what *explicit specification* adds beyond inference. The per-model L1 spread (0.78–0.90) is itself informative — it identifies which models can infer the task without specification. We will clarify in the revision that L1 = "task communication via input context alone"; L2+ adds explicit specification.

**Evaluation design.** The 4 dimensions are a shared *output schema* for cross-task comparability; the rubric *text* given to the judge is task-specific. Verbatim rubric directives (passed to both judges):
- *QA:* "Focus **heavily** on Correctness (does the answer match the reference?)..."
- *Classification:* "Focus on Correctness (does the classification match the reference label?). Conciseness rewards direct labeling..."
- *PE:* "Focus on Correctness (do the extracted fields match the reference values?). Completeness checks if all 4 fields (name, price, brand, category) are present..."
- *Math:* "Focus on Correctness (final numerical answer match)..."
- *Instr-following:* "Focus on Completeness (are all stated constraints satisfied?). Correctness checks format and structural adherence..."

This implements what the reviewer requested: QA emphasizes correctness/factual matching, PE emphasizes field-level accuracy, instruction-following emphasizes constraint satisfaction. The 4-dim scaffold is a reporting convenience, not a uniform criterion. Validated via second judge: cls r=0.835, math r=0.859; direction agreement 5/7 cls, 4/7 PE (3 PE non-agreements are Gemini deltas ≤0.003).

**Data construction.** 20 examples per task, balanced for unambiguous ground truth and difficulty range: cls = SST-2-style sentences (sarcasm/mixed excluded to control label noise); PE = product-listing snippets (electronics/household/books) with 4-field ground truth; QA = factoid questions (geography/history/science, SQuAD-style); math = 20 word problems (10 easy, 10 medium, 2–3-step) with exact-numeric ground truth; summarization = short news passages w/ reference summaries; instr-following = 1–2 explicit structural constraints. The 200-example replication (cls/QA) samples directly from SST-2/SQuAD with identical prompt templates. Full per-example listings in camera-ready supplementary.

**Bibliography errors.** We confirm both errors: (1) "A Survey of Automatic Prompt Engineering" (arXiv:2502.11560) should be Li et al., not Amatriain et al.; (2) "CompactPrompt" (arXiv:2510.18043) should be Choi et al., not Wang et al. These arose from incorrect metadata in preprint sources. We have verified correct author listings on arXiv and checked the remaining bibliography — no other errors found. Will be corrected in the camera-ready.

**Replication scope.** Replication covered both poles — classification (saturation) and QA (no saturation). PE/instr-following on external benchmarks constrained by rebuttal API budget. Partial mitigation: rebuttal ablation (2,986) + padding (1,470) runs target PE with new orderings and instantiations — PE L1→L7 direction preserved (mid-range 13/15 significant; +0.16 real vs. −0.013 padding). Not a substitute for external-benchmark replication (e.g., Amazon-ESCI); high-priority for camera-ready if accepted.
