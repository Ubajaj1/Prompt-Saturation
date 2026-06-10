# Review: "When Does Prompt Elaboration Stop Helping? A Controlled Study of Prompt Sensitivity Across LLM Tasks"

**Venue:** ACML 2026  
**Reviewer Confidence:** 3/5

---

### 1. PAPER SUMMARY

This paper investigates when adding more elaboration to LLM prompts stops improving response quality. The authors construct seven strictly additive prompt levels for six tasks (classification, product extraction, QA, math reasoning, summarisation, instruction following), where each level appends exactly one new prompt mechanism (task label, format spec, definitions, persona, guidelines, worked example). They evaluate 7–8 LLMs across 17,378 total evaluations, fitting saturation curves to quality-vs-token data. Two controls — a randomised layer-ordering ablation (2,986 runs) and an irrelevant-padding experiment (1,470 runs) — disentangle information content from raw token count. The main finding is that quality saturates based on *information sufficiency*, not token count, and that tasks vary along a four-level "prompt-sensitivity gradient" from concentrated (classification) to insensitive (QA, math).

---

### 2. STRENGTHS

- **S1 (Novelty & Originality):** The additive prompt-level methodology — where each template is a strict superset of the previous, isolating the contribution of one mechanism at a time — is a clean and well-motivated experimental design. The idea of systematically layering prompt components and measuring marginal returns per layer is, to my knowledge, novel in this form and genuinely useful for the prompt engineering community.

- **S3 (Empirical Rigor — Controls):** The two complementary controls are the strongest part of the paper. The randomised layer-ordering ablation directly tests whether saturation is driven by information content versus token position, and the irrelevant-padding control provides a clean null-hypothesis test against "more tokens = better." Together these controls elevate the work above a simple observational study. The padding result — 1/26 conditions significant, with many negative deltas — is convincing.

- **S3 (Empirical Rigor — Scale):** The total experimental scope of 17,378 evaluations across 8 models, 6 tasks, and multiple experimental conditions is substantial. The 200-example replication on SST-2 and SQuAD strengthens external validity for the two endpoint tasks.

- **S4 (Significance & Impact):** The practical guidelines in Section 5.4 — e.g., for classification just specify the task label (~50 tokens); for structured extraction include a worked example; for QA the bare question suffices — are concrete and actionable. The math L3 finding (suppressing chain-of-thought destroys quality by −0.366) is a genuinely useful negative result.

- **S2 (Technical Soundness — Ceiling Analysis):** The ceiling stratification analysis in Section 4.5, explaining *why* QA and math appear insensitive (16–20 of 20 examples already above 0.85 at L1), is an important piece of detective work that prevents the reader from drawing a wrong conclusion about those tasks.

- **S5 (Clarity):** The paper is generally well-written. The full prompt walkthroughs in Appendices D and E, showing exact prompts and model responses at each level, are excellent for reproducibility and intuition-building.

---

### 3. WEAKNESSES

#### W-EXP: Experimental / Empirical Issues

- **[CRITICAL] Extremely small per-condition sample size (n=20 examples).** The entire main study uses only 20 curated examples per task. With 7 level means per curve, each data point is a mean of just 20 observations. This is insufficient for reliable curve fitting — the authors themselves acknowledge the F-test has "limited power" with n=7 data points per curve (Section 5.6). Of 42 (model, task) pairs, only 10 achieve significance at p < 0.05 (Table 4/9). The fact that the majority of curves are *not* significant severely limits what can be concluded. The 200-example replication on only 2 of 6 tasks is a partial mitigation but not a substitute for a properly powered main study. **Why it matters:** With 20 examples, a single outlier example can shift the level mean substantially, and the fitted saturation points have extremely wide bootstrap CIs (e.g., [29, 147] for gemini-flash classification, a 5× range). The paper's core quantitative claims — specific saturation token counts, the prompt-sensitivity gradient categories — rest on noisy estimates. **Fix:** Run the full 6-task study with at least 100–200 examples per task. The 200-example replication shows this is feasible and should have been the main study.

- **[CRITICAL] LLM-as-judge is the sole evaluation method for the main study.** All quality scores come from gpt-4o-mini, with gemini-2.0-flash as a secondary judge. Both are LLM judges. The heuristic validation (Pearson r=0.986) is mentioned in one sentence but details are scant — which heuristics, on how many examples, for which tasks? The inter-judge agreement is poor for product extraction (r=0.247, MAE=0.150) and QA (r=0.287, MAE=0.086), which the authors attribute to "ceiling compression." But product extraction is one of the two tasks where saturation is *most pronounced*, making unreliable judging in exactly that condition a serious concern. **Why it matters:** If the judge scores are unreliable for the tasks where the paper claims the strongest signal, the saturation curves and their fitted parameters inherit that unreliability. The authors cannot simultaneously claim strong saturation signal in product extraction *and* dismiss the poor inter-judge agreement as mere ceiling compression. **Fix:** Report the heuristic evaluator results as the primary metric for tasks where ground-truth matching is feasible (classification, product extraction, QA, math). Use LLM judges only for tasks without clean heuristics (summarisation, instruction following), or at minimum report both and discuss discrepancies.

- **[MAJOR] Curated, non-standard evaluation examples.** The 20 examples per task are described as "curated" with no detail on the curation process, selection criteria, or potential biases introduced. For classification the text says "product reviews and social media posts" but does not specify the source or how they were selected. The paper uses SST-2 and SQuAD only for the replication, not the main study. **Why it matters:** Curated examples may not represent the difficulty distribution of real tasks. If the 20 examples are mostly easy, then all models reach ceiling quickly and the "insensitive" finding for QA/math is an artifact of task difficulty, not prompt sensitivity. The ceiling analysis in Section 4.5 actually confirms this — 16–20 of 20 QA examples are above 0.85 at L1 — but this raises the question of whether more difficult examples would reveal sensitivity. **Fix:** Use established benchmarks throughout (not just in replication), or at minimum, stratify examples by difficulty and report saturation curves per difficulty stratum.

- **[MAJOR] No repetition / no error bars on individual runs.** Each (model, task, level, example) combination appears to be evaluated exactly once — there is no mention of multiple runs per condition. LLMs are stochastic; with default temperature settings, the same prompt can produce different outputs. **Why it matters:** Without repeated runs, the observed quality at each level conflates prompt-level effects with sampling noise. **Fix:** Run each condition 3–5 times and report standard errors.

#### W-NOV: Novelty Concerns

- **[MAJOR] The core finding is somewhat intuitive and partially known.** The claim that "information sufficiency, not token count, drives quality" is, at a high level, unsurprising — it would be strange if *irrelevant* tokens helped. The more novel contribution is the *quantification* of where saturation occurs per task and the prompt-sensitivity gradient, but as argued above, the quantitative estimates are unreliable due to the small sample. The prompt compression literature (LLMLingua, LLMLingua-2) already demonstrates that many prompt tokens are expendable, which implicitly shows that information content — not token count — is what matters. **Why it matters:** The conceptual contribution is modest if the quantitative contribution is not robust. **Fix:** The novelty is in the methodology and the gradient taxonomy, which would be strengthened by more robust estimates and validation on additional tasks.

#### W-TECH: Technical Soundness Issues

- **[MAJOR] The "prompt-sensitivity gradient" is a post-hoc taxonomy, not a tested framework.** The four categories (concentrated, distributed, diffuse, insensitive) are assigned based on observing the marginal contribution profiles of 6 tasks. The paper acknowledges this is "a post-hoc descriptive framework... not a pre-registered taxonomy" (Section 5.6). With only 6 tasks, each category has 1–2 members. **Why it matters:** A taxonomy with 4 categories for 6 data points has essentially no predictive power. It is unclear whether a new task would be classifiable ex ante, which limits the framework's utility. **Fix:** Either (a) validate the taxonomy on held-out tasks, or (b) present it explicitly as a descriptive observation rather than a framework, and moderate the claims accordingly.

- **[MAJOR] Curve fitting with n=7 points.** Fitting 3–4 parameter models (logarithmic or sigmoid) to 7 data points leaves only 3–4 residual degrees of freedom. The F-test against a flat null with these degrees of freedom has very low power, as the authors note. But the paper still reports and interprets T* (saturation token count) values from non-significant fits (e.g., the heatmap in Figure 3 shows T* values for all 42 pairs including non-significant ones). **Why it matters:** Reporting and visualising T* from non-significant fits conflates noise with signal and is misleading. **Fix:** Clearly distinguish significant from non-significant fits in all figures. Omit or grey-out T* values from non-significant curves in the heatmap (partially done but inconsistently).

#### W-CLA: Clarity & Presentation Issues

- **[MAJOR] Figure 2 is a placeholder.** The marginal contribution figure — arguably the most important visualization for the prompt-sensitivity gradient — is a "[TODO: Marginal contribution figure]" box. This is unacceptable for a submission and suggests the paper was submitted in an incomplete state. **Why it matters:** The marginal contribution analysis is one of the paper's key contributions, and the reader must reconstruct it entirely from text. **Fix:** Include the actual figure.

- **[MINOR] Inconsistent model count claims.** The abstract says "seven large language models" and "seven additive prompt-elaboration levels." The methodology section (3.3) says "eight LLMs" (Table 2 lists 8). The abstract also says the main study spans "seven" models — this appears to be because Llama-3.2-1B only runs two tasks, but the distinction is unclear. **Fix:** Be precise: "eight models, seven of which run all six tasks."

- **[MINOR] The quality metric q = Σsᵢ/20 is a peculiar aggregation.** Summing four 1–5 subscores and dividing by 20 to get q ∈ [0,1] obscures which quality dimensions drive the saturation signal. A response that is correct but verbose might score the same as one that is concise but incomplete. **Fix:** Report per-dimension saturation curves, or at minimum discuss which dimensions drive the aggregate.

#### W-REL: Related Work & Positioning Issues

- **[MAJOR] Missing critical related work on prompt sensitivity.** The paper cites Webson & Pavlick (2022) and Mizrahi et al. (2024) but entirely omits **ProSA** (Zhuo et al., EMNLP Findings 2024), which directly addresses assessing and understanding prompt sensitivity in LLMs with a dedicated sensitivity metric (PromptSensiScore). The paper also omits **"Revisiting Prompt Sensitivity in Large Language Models for Text Classification"** (arxiv 2602.04297, 2026), which studies prompt sensitivity specifically for classification — one of this paper's two core tasks with significant saturation. **Why it matters:** These works study the same phenomenon (prompt sensitivity) from complementary angles. Failing to engage with them weakens the related work positioning. **Fix:** Discuss ProSA and the 2026 classification sensitivity paper, explaining how this work's additive elaboration design differs from their paraphrase-based sensitivity studies.

#### W-REP: Reproducibility Issues

- **[MINOR] API model versioning.** Four models (gemini-2.0-flash, kimi-k2, gpt-4o-mini, claude-haiku-4-5) have undisclosed parameter counts and are accessed through APIs. The paper notes kimi-k2 was deprecated between the main study and ablation. API models can be silently updated, making exact reproduction impossible. **Fix:** Record and report model version strings/dates. The kimi-k2 deprecation is honestly discussed, which is appreciated.

---

### 4. QUESTIONS FOR THE AUTHORS

1. **Why not use standard benchmarks for the main study?** You demonstrate feasibility with SST-2 and SQuAD in the replication. Using 20 curated examples when established benchmarks exist for 5 of your 6 tasks is a puzzling design choice. What was the rationale?

2. **How do heuristic evaluator results compare to LLM judge results per-level?** You report Pearson r=0.986 overall, but do the heuristic and judge scores agree on the *shape* of the saturation curve (not just overall correlation)? If the heuristic evaluator shows the same saturation pattern, that would substantially strengthen the claims.

3. **For the ceiling analysis (Section 4.5), what happens if you evaluate only the below-ceiling examples?** You note 16–20 of 20 QA examples score above 0.85 at L1. If you restrict to the remaining 0–4 examples, is there evidence of prompt sensitivity? If yes, the "insensitive" classification may be an artifact of easy examples rather than a task-level property.

4. **Can you quantify the inter-annotator agreement for your curated examples?** Were the 20 examples per task selected by one person or validated by multiple? Is there a principled difficulty distribution?

5. **Have you considered a within-example analysis?** Rather than averaging across 20 examples, fitting per-example saturation curves would reveal whether saturation is a property of the task or varies by example difficulty.

6. **Why was the marginal contribution figure (Figure 2) not included?** Is this an oversight in the submission, or is the analysis incomplete?

---

### 5. MISSING REFERENCES

- **Zhuo et al. (2024). "ProSA: Assessing and Understanding the Prompt Sensitivity of LLMs." Findings of EMNLP 2024.** Directly studies prompt sensitivity with a dedicated metric; the comparison between their paraphrase-based sensitivity and the authors' elaboration-based sensitivity would be informative.

- **"Revisiting Prompt Sensitivity in Large Language Models for Text Classification" (arXiv 2602.04297, 2026).** Studies prompt sensitivity specifically for text classification, the paper's strongest saturation task.

- **Sclar et al. (2024). "Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design." ICLR 2024.** Studies how minor prompt formatting choices (separator, casing) affect performance — relevant to disentangling content from formatting effects.

- **Voronov et al. (2024). "Mind Your Format: Towards Consistent Evaluation of In-Context Learning Improvements." arXiv 2401.06766.** Relevant to the format specification layers and how formatting choices affect evaluation.

---

### 6. MINOR ISSUES & TYPOS

- Figure 2 is a placeholder "[TODO: Marginal contribution figure]" — this must be included.
- The abstract says "seven large language models" but the study uses eight (Table 2).
- Table 1 caption says "not homogeneous units of length" which is important but could be stated more prominently.
- Section 3.8 says "5 models × 2 tasks × 3 padding types × 7 levels × 7 examples" = 1,470, but this is confusing because the main study uses 20 examples per task. The 7 examples here presumably come from the curated ablation set but this should be clarified.
- The paper switches between "prompt-sensitivity gradient" and "prompt sensitivity gradient" (with and without hyphen).

---

### 7. LIMITATIONS & FUTURE WORK ASSESSMENT

The limitations section (5.6) is commendably thorough and honest. The authors correctly identify: low statistical power, narrow classification domain (sentiment only), single-turn scope, English-only, the kimi-k2 deprecation, and the post-hoc nature of the gradient taxonomy. This is one of the better limitations sections I have reviewed — the authors clearly understand the boundaries of their claims.

However, two significant limitations are under-discussed: (1) the reliance on LLM-as-judge and the poor inter-judge agreement on product extraction/QA, and (2) the curated (non-standard) evaluation examples. The future work section is reasonable — extending to code generation, data-to-text, multi-turn, and mechanistic interpretability are all natural directions — but the most impactful near-term improvement would be a properly powered study with 100+ examples on standard benchmarks.

---

### 8. REPRODUCIBILITY CHECKLIST ASSESSMENT

- [x] Are the claims clearly stated? — Yes, generally clear.
- [ ] Are the main results supported by sufficient experiments? — Partially. The main study is underpowered (n=20). Only 10/42 curves are significant.
- [x] Is the experimental setup fully described? — Yes, with full prompt walkthroughs in appendices.
- [ ] Are error bars / confidence intervals reported? — Bootstrap CIs on T* are reported, but no error bars on the quality scores themselves. No repeated runs.
- [x] Is the code available (or planned for release)? — Yes, supplementary material includes prompts, evaluation code, and data.
- [ ] Are datasets described with enough detail to reproduce? — The 20 curated examples lack detailed provenance.
- [ ] Are compute requirements stated? — Not explicitly discussed. API costs are not mentioned.
- [x] Are all hyperparameters specified? — Temperature default, 512 max output tokens, bootstrap iterations (1,000), F-test alpha (0.05), threshold levels — yes.

---

### NUMERICAL SCORING

### A. Soundness: 2/4
The experimental design is clever (additive levels, ablation, padding control), but the execution is underpowered. With n=20 examples and no repeated runs, most curves fail significance, and the LLM-judge reliability for key tasks (product extraction) is questionable. The conclusions overreach relative to the statistical evidence.

### B. Presentation: 2/4
Generally well-written prose, excellent appendices, but Figure 2 is a placeholder. This alone would be grounds for desk rejection at most venues — it signals an unfinished manuscript. The inconsistent model counts and some unclear notation detract further.

### C. Contribution: 2/4
The additive prompt-level methodology is a genuine contribution, and the practical guidelines are useful. However, the prompt-sensitivity gradient (the paper's main conceptual contribution) is a post-hoc taxonomy of 6 tasks with no predictive validation. The core insight (information content matters, not token count) is partially intuitive and partially established by the compression literature.

### D. Overall Rating: 4/10
The paper asks a good question and proposes a sensible methodology. The controls (ablation, padding) are well-designed. But the execution has critical gaps: a main study with only 20 examples per task, a missing figure, unreliable inter-judge agreement on a key task, and a post-hoc taxonomy that cannot be validated from the presented data. At ACML's acceptance bar, I expect papers to have their quantitative claims supported by adequately powered experiments. This paper is not ready in its current form but could become a solid contribution with a properly powered main study and the missing figure.

### E. Confidence: 3/5
I am familiar with prompt engineering, LLM evaluation, and experimental methodology in NLP. I have not verified the curve-fitting details or bootstrap implementation. There is a chance I underestimate the difficulty of scaling the study to more examples due to API costs.

### F. Excitement: 3/5
The question is timely and practically relevant. If the study were properly powered and the gradient validated, I would be more enthusiastic. The methodology is reusable and the practical guidelines are valuable.

---

┌──────────────────────────────────┐
│         SCORE SUMMARY            │
├──────────────────────────────────┤
│ Soundness:       2/4             │
│ Presentation:    2/4             │
│ Contribution:    2/4             │
│ Overall Rating:  4/10            │
│ Confidence:      3/5             │
│ Excitement:      3/5             │
│                                  │
│ Recommendation:  Borderline      │
│                  Reject          │
└──────────────────────────────────┘

**Summary justification:** The paper tackles a relevant and timely question with a well-designed additive methodology and thoughtful controls. However, the main study is critically underpowered (20 examples/task, no repeated runs), the primary evaluation figure is missing, inter-judge reliability is poor for a core task, and the proposed taxonomy lacks predictive validation. The gap between the ambition of the claims and the statistical evidence supporting them is too large for acceptance at ACML. A revision with a properly powered study (100+ examples on standard benchmarks), the complete figure set, and heuristic-primary evaluation would substantially improve the paper.
