Interesting Empirical Study on Prompt Construction
Official Reviewby Reviewer R19f11 May 2026, 15:34 (modified: 22 May 2026, 09:51)Program Chairs, Area Chairs, Reviewers Submitted, Authors, Reviewer R19fRevisions
Summary:
This paper investigates whether increasingly verbose prompts continue improving LLM performance or whether quality eventually saturates. The authors construct a controlled “additive prompt” framework with seven prompt elaboration levels per task, where each level strictly appends new instruction content without modifying earlier text. Across six tasks and seven LLMs, they fit quality-token curves and define a saturation point as the token count where quality reaches 95% of the maximum.

Reasons To Accept:
The statistical methodology is reasonable given the small setup, and the paired bootstrap procedure is appropriate.

The paper is clearly written overall. The additive prompt construction is easy to understand, and the figures communicate the main trends reasonably well. The structured/open dichotomy is articulated clearly and motivates the discussion effectively.

The core idea—measuring prompt-quality saturation curves—is sufficiently novel and relevant for acceptance at COLM. It is also operationally useful for practitioners across academia and industry. There's relatively little work characterizing marginal returns of additional prompt elaboration in a controlled manner.

Reasons To Reject:
The biggest issue is that the paper frames itself as studying “prompt length” or “token saturation,” but the additive prompt levels simultaneously introduce qualitatively different prompting mechanisms.

The experimental scope is currently too narrow to support broad recommendations about prompt engineering in general. The tasks are simplistic, the evaluation datasets are small, and modern agentic or retrieval-heavy prompting workflows are largely absent.

For a paper with its main contribution more on the empirical side than theoretical, this is a strong reason to reject because it makes it hard to trust any of the conclusions.

Questions To Authors:
Have you looked into varying the order of the additive layers. If you were able to control for this, it'd help to strengthen conclusions (or not)

Few-shot examples are known to produce large gains in many settings. Why do these not help the QA or math tasks here? Any insights would be helpful.

Have you tested whether saturation thresholds correlate with model capability across a broader range of models, including weaker open-source models? That would be another interesting take to add to this paper.

Rating: 4: Ok but not good enough - rejection
Confidence: 4: The reviewer is confident but not absolutely certain that the evaluation is correct
Ethics Flag: No
Add:
Review
Official Reviewby Reviewer 4x2b09 May 2026, 02:31 (modified: 22 May 2026, 09:51)Program Chairs, Area Chairs, Reviewers Submitted, Authors, Reviewer 4x2bRevisions
Summary:
This paper presents a controlled study of prompt saturation across six tasks (classification, product extraction, question answering, mathematical reasoning, summarization, and instruction following) using seven large language models. Each task includes 20 examples, with an additional replication experiment on 200 examples for classification and QA. The authors define seven additive prompt levels, where each level incrementally appends further elaboration to the previous one. Response quality at each level is evaluated using an LLM-as-a-judge, whose reliability is supported through task-specific heuristic validation. By analyzing response quality as a function of prompt length, the study finds clear saturation effects for the classification task and for three of the seven models in the product extraction task, while no significant saturation is observed for the remaining tasks. Based on these findings, the paper offers practical recommendations on where prompts may be trimmed for different task types to improve prompt efficiency.

Reasons To Accept:
While there has been much work looking into performance against output token length, studying response quality against prompt length is a novel contribution and offers a refreshing angle.
The resulting insights – particularly around trimming structured prompts after a saturation point – are actionable and potentially useful for practitioners.
The effort to validate the LLM-as-a-judge using task-specific heuristics is valuable and helps increase confidence in the evaluation methodology.
The inclusion of multiple models from different providers and of varying sizes strengthens the empirical scope of the study.
Reasons To Reject:
The title “Quality Plateaus at Task-Specific Token Thresholds in Large Language Models” appears somewhat overstated - saturation is clearly demonstrated for the sentiment classification task and for three out of seven models for the product extraction task but not significant for the other four tasks. A more qualified framing would better reflect the findings.
The claim that prompt saturation is a stable property of structured tasks would benefit from broader empirical support. For example, the classification results are based solely on sentiment classification; extending this to additional classification domains would strengthen the argument.
Different prompt layers likely contain information of varying importance, making it unclear whether the observed effects are driven primarily by prompt length or by the specific content introduced at each level. A more informative analysis would disentangle these factors – for example, by measuring the marginal contribution of each elaboration layer and exploring how different combinations of layers affect performance. Additionally, the ordering of these layers may influence results, but this is not examined. As a result, it remains uncertain whether prompt length itself is the determining factor in response quality, or whether the content and structure of the prompt play a more significant role.
Questions To Authors:
“Practitioners routinely craft increasingly verbose prompts under the assumption that more context yields better responses.” Could the authors provide more concrete examples or references (e.g., benchmark prompts used in model releases or dataset papers) to better ground this claim?
Were steps taken to control for output length across prompt levels? Differences in response length could potentially confound the relationship between prompt length and quality.
The sample size (n=20 per task) appears quite limited, and even the replication with 200 examples remains relatively small by current standards in the field. Could the authors comment on this choice? In particular, would it be possible to leverage existing benchmark datasets with larger and more diverse samples to strengthen the robustness and generalizability of the findings?
Rating: 4: Ok but not good enough - rejection
Confidence: 4: The reviewer is confident but not absolutely certain that the evaluation is correct
Ethics Flag: No
Add:
Useful empirics but limited statistics and a rather narrow scope
Official Reviewby Reviewer CnfP08 May 2026, 03:00 (modified: 22 May 2026, 09:51)Program Chairs, Area Chairs, Reviewers Submitted, Authors, Reviewer CnfPRevisions
Summary:
The paper studies prompt saturation which can be described as the token count beyond which additional prompt elaboration stops improving response quality. The core methodological contribution is an additive prompt design; seven nested templates 
 where each level adds exactly one elaboration layer and isolates amount of instruction from its content. On 
 models, 
 tasks, and 
 LLM-judge-evaluated responses, the authors report a structured–open dichotomy: classification and product extraction show significant saturation, while QA, math, summarization, and instruction following largely do not.

The question is practically relevant and the additive design is quite clean. But the empirical foundation is perhaps too thin to support the strong framing.

Reasons To Accept:
The strictly additive prompt construction is a good methodological contribution because most prompt-engineering studies confound length with content, and this design cleanly separates them. The token-budget guidance is immediately actionable for practitioners, and Figure 2 is a useful and compact summary across 
 model–task pairs. The authors are honest about negative results, validate the LLM judge against task-specific heuristics (
), and attempt a replication on standard benchmarks instead of hiding robustness concerns.

Reasons To Reject:
The F-test is severely limited with only 
 level means and 
 parameters. Borderline cases such as llama-3.1-8b classification at 
 and kimi-k2 product extraction at 
 are plausibly true positives, which would imply that dichotomy partly reflects statistical power rather. The structured-vs-open grouping is also done in a post hoc fashion and after observing which tasks saturate, converting a potential hypothesis test into a description of the data.

Negative result on QA and math is rather confounded with ceiling effects in the sense that capable models already score above 
 at level 1, leaving little room for improvement. The paper offers two interpretations (near-ceiling vs. knowledge-bottlenecked) without separating them empirically, even though, in my opinion, stratifying by level-1 quality would directly test this. A single-judge design and the absence of any layer-ordering ablation leave two large sources of variance untested, though given COLM guidelines pertaining to 'large-scale compute', I find it acceptable.

Also, schema-compliance hypothesis is presented as a contribution but is never actually tested. Finally, the gap from existing prompt-compression work (LLMLingua, LLMLingua-2) is narrower than the introduction suggests; the contribution is really the task-typed characterization, not the observation that prompts contain redundant tokens.

Questions To Authors:
How sensitive are the results to the 
-of-asymptote definition of 
 versus a second-derivative knee estimate?
If you stratify QA/math examples by level-1 quality and remove near-ceiling cases, does saturation appear in the remainder?
Can you report results for at least one permuted layer ordering (e.g., worked example at level 2 instead of 7) to test whether 
 is intrinsic to the task?
How do results change with a second judge model (to save costs, a local LLM judge is acceptable as well)? And why group summarization and instruction following with QA/math when both arguably involve schema compliance?
Rating: 5: Marginally below acceptance threshold
Confidence: 3: The reviewer is fairly confident that the evaluation is correct
Ethics Flag: No
Add:
Interesting and practically relevant paper, however, its claims would be more convincing with clearer task specification, more detailed per-level results, stronger qualitative analysis, and larger evaluation coverage.
Official Reviewby Reviewer C2JD05 May 2026, 23:02 (modified: 22 May 2026, 09:51)Program Chairs, Area Chairs, Reviewers Submitted, Authors, Reviewer C2JDRevisions
Summary:
This paper investigates prompt saturation in large language models. The main research question is whether adding more prompt tokens continues to improve response quality. The authors specifically designed seven additive prompt levels across six tasks and evaluate seven LLMs. Their main finding is that structured tasks, such as sentiment classification and product extraction, show clearer saturation patterns, while open-ended or reasoning-heavy tasks do not show significant improvement from longer prompts.

Reasons To Accept:
The paper addresses an important and practical problem. Prompt verbosity is common in real-world LLM applications, but it is still unclear when additional prompt detail actually helps. The paper’s focus on prompt saturation is therefore useful for both researchers and practitioners.
The experimental design covers multiple task types and seven different LLMs. This makes the analysis more informative than a single task or single model study. The comparison between structured tasks and open-ended tasks is also interesting.
The paper is generally well written. The motivation is clear, the methodology is easy to follow, and the main findings are presented in a structured way. The figures and tables also help readers understand the saturation patterns.
Reasons To Reject:
The paper lacks detailed case studies or qualitative analysis. The main results rely heavily on curve fitting and aggregate statistics. It would be helpful to include concrete examples showing how model outputs change across prompt levels. This would make the saturation claim more convincing and would help explain why some tasks benefit from additional prompt layers while others do not.
The definition of Level 1 may introduce ambiguity. For example, Appendix C shows Level 1 as: "Classify: The product works great and I’m very happy with my purchase." However, this prompt only tells the model to classify the text. It does not specify the classification criterion. The model may infer that the task is sentiment classification because the sentence contains an obvious positive opinion, but this inference is not guaranteed. In other cases, the same instruction could refer to topic classification, product category classification, intent classification, or another label space. Therefore, the performance at Level 1 may depend heavily on whether the model can infer the hidden task from the input itself. This makes it difficult to separate the effect of prompt length from the effect of task specification. A clearer experimental design would distinguish between a truly bare input, an under-specified task prompt, and a minimally specified task prompt. This would make the saturation analysis more convincing.
The paper does not provide enough direct performance results per prompt level. For example, it would be useful to report the mean accuracy or mean quality score at each level for each task and model. Without these detailed results, readers mainly see fitted curves and saturation estimates. This makes it harder to judge whether the actual performance differences across levels are meaningful.
The evaluation set is limited. The main experiment uses only 20 examples per task, and the examples are not described in enough detail. Although the paper includes a larger replication experiment, the replication only covers selected tasks. The paper would be stronger if the authors provided more information about the data construction process and extended the larger-scale replication to more tasks, especially product extraction and instruction following.
The use of an LLM judge is reasonable, but the evaluation design may be too general. The same four dimensions, including correctness, completeness, reasoning, and conciseness, are used across very different tasks. However, each task may require a different evaluation focus. For example, QA should emphasize answer correctness and factual matching, product extraction should emphasize field-level accuracy, and instruction following should emphasize constraint satisfaction. A more task-specific evaluation prompt or metric would make the results more reliable.
Additionally, there appear to be incorrect references in the bibliography:

"A Survey of Automatic Prompt Engineering: An Optimization Perspective" is cited as Amatriain et al., but the author information appears to be incorrect.
The correct author listing seems to be Li et al. "CompactPrompt: A Unified Pipeline for Prompt Data Compression in LLM Workflows" is cited as Wang et al., but the author information also appears to be incorrect.
Questions To Authors:
Please refer to the "Reasons To Reject" discussed above.

Rating: 3: Clear rejection
Confidence: 4: The reviewer is confident but not absolutely certain that the evaluation is correct
Ethics Flag: No
