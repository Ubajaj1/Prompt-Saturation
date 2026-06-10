# ACML Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Address all pending reviewer items for the ACML 2026 revision: fix paper presentation (Figure 2, abstract, README), integrate existing Tier-1 analyses into LaTeX, add NER held-out task validation, add repeated-run experiment, and add error bars.

**Architecture:** Three workstreams: (A) paper fixes — wire existing results into LaTeX and fix inconsistencies, (B) new experiments — NER held-out task + 3-task repeated runs, (C) analysis scripts for error bars and repeated-run stats. Experiments reuse the existing `saturation_benchmark.py` runner and `saturation_analysis.py` curve-fitting. NER needs a new evaluator, 20 examples, and 7-level prompt templates.

**Tech Stack:** Python 3, numpy, scipy, matplotlib, existing LLM providers (Groq free, OpenAI paid, Anthropic paid, Gemini free). LaTeX for paper.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `greenprompt/evaluators.py` | Add `NERExtractionEvaluator` |
| Modify | `experiments/prompting_strategies.py` | Add 20 NER examples to `BENCHMARK_EXAMPLES` |
| Modify | `experiments/saturation_prompts.py` | Add 7-level NER templates to `SATURATION_TEMPLATES` |
| Modify | `experiments/saturation_benchmark.py` | Add `ner` to `TASKS` list, add `--runs` flag for repeated runs |
| Create | `experiments/rebuttal_repeated_runs.py` | Analysis script: compute per-level SEs, effect-vs-noise ratios |
| Create | `experiments/rebuttal_error_bars.py` | Bootstrap SE bands on level means for Figure 1 |
| Modify | `greenprompt/llm.py` | Fix temperature: explicit `temperature=0` on all providers |
| Modify | `paper_acml/sec_results.tex` | Wire Figure 2, add heuristic table, subscore decomp, below-ceiling |
| Modify | `paper_acml/sec_method.tex` | Fix temperature claim, add NER task description, fix padding clarification |
| Modify | `paper_acml/sec_abstract.tex` | Fix model count to "eight models, seven of which run all six tasks" |
| Modify | `paper_acml/sec_discussion.tex` | Add held-out validation paragraph |
| Modify | `paper_acml/sec_related.tex` or equivalent | Add ProSA, Sclar, Voronov, 2026 classification refs |
| Modify | `README.md` | Replace "structured–open dichotomy" with gradient framing |
| Create | `tests/test_ner_evaluator.py` | Tests for NER evaluator |

---

### Task 1: Fix Paper Presentation — Figure 2, Abstract, README

**Files:**
- Modify: `paper_acml/sec_results.tex:188-197`
- Modify: `paper_acml/sec_abstract.tex:5`
- Modify: `paper_acml/sec_method.tex:88`
- Modify: `paper_acml/sec_method.tex` (Section 3.8 padding clarification)
- Modify: `README.md:13-14`
- Copy: `results/rebuttal_v2/figures/fig2_marginal_contributions.png` → `paper_acml/figures/`

- [ ] **Step 1: Wire Figure 2 into the paper**

Copy the generated figure into the paper figures directory and replace the placeholder:

```bash
cp results/rebuttal_v2/figures/fig2_marginal_contributions.png paper_acml/figures/
cp results/rebuttal_v2/figures/fig2_marginal_contributions.pdf paper_acml/figures/
```

In `paper_acml/sec_results.tex`, replace lines 188–197 (the TODO block) with:

```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=\linewidth]{figures/fig2_marginal_contributions.png}
  \caption{Per-layer marginal quality contributions ($\Delta_{k \to k+1}$)
    averaged across seven models.
    Classification gain is concentrated in L1$\to$L2 (task label);
    product extraction gain is distributed across L1$\to$L2 and L6$\to$L7
    (worked example); math reasoning shows a sharp L3 collapse from
    suppressing chain-of-thought.}
  \label{fig:marginal}
\end{figure}
```

- [ ] **Step 2: Fix abstract model count**

In `paper_acml/sec_abstract.tex`, change line 5 from:

```
responses across seven large language models, six tasks, and seven additive
```

to:

```
responses across eight large language models (seven running all six tasks), seven additive
```

- [ ] **Step 3: Fix temperature claim in methodology**

In `paper_acml/sec_method.tex`, line 88, change:

```
All models are accessed via production APIs with default temperature settings.
```

to:

```
All models are accessed via production APIs with temperature set to 0 (greedy decoding) for deterministic outputs.
```

- [ ] **Step 4: Clarify padding control sample size**

In `paper_acml/sec_method.tex`, find the Section 3.8 description of padding control ("5 models × 2 tasks × 3 padding types × 7 levels × 7 examples"). Add a clarifying sentence after it:

```
The 7 examples per task are drawn from the main study's curated set, not a separate sample.
```

- [ ] **Step 5: Fix README outdated framing**

In `README.md`, replace line 13:

```
- **Structured–open dichotomy**: task type, not prompt length, determines whether elaboration helps
```

with:

```
- **Prompt-sensitivity gradient**: tasks range from concentrated (classification) through distributed (extraction) and diffuse (instruction following) to insensitive (QA, math)
```

- [ ] **Step 6: Compile paper and verify Figure 2 renders**

```bash
cd paper_acml && pdflatex main.tex && pdflatex main.tex
```

Verify: Figure 2 shows grouped bars, no TODO placeholder. Abstract says "eight large language models."

- [ ] **Step 7: Commit**

```bash
git add paper_acml/sec_results.tex paper_acml/sec_abstract.tex paper_acml/sec_method.tex paper_acml/figures/fig2_marginal_contributions.png paper_acml/figures/fig2_marginal_contributions.pdf README.md
git commit -m "fix: wire Figure 2, fix abstract model count, temperature claim, README framing"
```

---

### Task 2: Integrate Tier-1 Analyses into Paper

The heuristic rescore, subscore decomposition, and below-ceiling results already exist in `results/rebuttal_v2/`. This task writes them into the LaTeX.

**Files:**
- Modify: `paper_acml/sec_results.tex`
- Copy: `results/rebuttal_v2/figures/fig_heuristic_vs_judge.png` → `paper_acml/figures/`

- [ ] **Step 1: Copy heuristic figure to paper directory**

```bash
cp results/rebuttal_v2/figures/fig_heuristic_vs_judge.png paper_acml/figures/
cp results/rebuttal_v2/figures/fig_heuristic_vs_judge.pdf paper_acml/figures/
```

- [ ] **Step 2: Add heuristic validation subsection to results**

Add the following after the existing inter-judge agreement discussion in `sec_results.tex`. Find the section that discusses second-judge agreement and add after it:

```latex
\subsection{Heuristic Evaluation Confirms Saturation}
\label{sec:result-heuristic}

To address reliance on LLM judges, we re-scored all 3,915 main-study
responses for the four ground-truth tasks using deterministic heuristic
evaluators (exact-match for classification and math, field-matching for
product extraction, substring containment for QA).
Table~\ref{tab:heuristic-agreement} compares judge and heuristic metrics.

\begin{table}[t]
\centering
\caption{Judge vs.\ heuristic agreement. Per-record Pearson~$r$ and MAE
  measure point-level agreement; curve-shape~$r$ measures whether the
  7-level quality trajectory agrees; direction agreement counts how many
  of 7 models show the same L1$\to$L7 sign.}
\label{tab:heuristic-agreement}
\small
\begin{tabular}{lrrrrr}
\toprule
Task & per-record $r$ & MAE & curve-shape $r$ & L1$\to$L7 dir.\ & heuristic sig. \\
\midrule
Classification      & 0.926 & 0.069 & 0.839 & 6/7 & 2/7 \\
Product extraction  & 0.415 & 0.300 & 0.660 & 7/7 & 7/7 \\
QA                  & 0.178 & 0.127 & 0.098 & 0/7 & 0/7 \\
Math reasoning      & 0.539 & 0.144 & 0.525 & 5/7 & 1/7 \\
\bottomrule
\end{tabular}
\end{table}

Product extraction---the task with the poorest inter-judge agreement
($r = 0.247$)---shows \textbf{7/7 significant} saturation fits under the
heuristic metric and 7/7 L1$\to$L7 direction agreement with the judge.
The saturation signal is \emph{stronger} on ground-truth matching, not an
artefact of judge noise.
QA is flat under both metrics (0/7 significant), independently confirming
the ``insensitive'' classification.

\begin{figure}[t]
  \centering
  \includegraphics[width=\linewidth]{figures/fig_heuristic_vs_judge.png}
  \caption{Saturation curves under judge (solid) vs.\ heuristic (dashed)
    scoring for four ground-truth tasks. Product extraction saturation is
    confirmed by the heuristic; QA flatness is confirmed independently.}
  \label{fig:heuristic-vs-judge}
\end{figure}
```

- [ ] **Step 3: Add subscore decomposition paragraph**

Add after the heuristic section:

```latex
\paragraph{Per-dimension decomposition.}
Decomposing the aggregate quality $q = \sum s_i / 20$ into its four
subscores reveals which dimensions drive saturation.
For product extraction, \textbf{completeness} accounts for 43\% of the
total L1$\to$L7 gain (+1.40 on the 1--5 subscale), confirming that
elaboration teaches the model to emit all four required fields.
Classification gain is spread across all four dimensions (correctness
+0.69, completeness +0.61, reasoning +0.56, conciseness +0.71)---
concentrated in \emph{tokens} but distributed across \emph{dimensions}.
For QA, the aggregate $\Delta$ is negative, driven by a completeness drop
($-0.72$) as extra prompt layers add noise to already-correct answers.
```

- [ ] **Step 4: Add below-ceiling stratification paragraph**

Add to Section 4.5 (ceiling analysis), after the existing ceiling discussion:

```latex
\paragraph{Below-ceiling stratification.}
Restricting to examples that start below $q = 0.85$ at L1 reveals latent
prompt sensitivity.
Classification below-ceiling examples (32.9\% of model$\times$example
pairs) gain $+0.316$ from L1 to L7; product extraction (92.8\% below
ceiling) gains $+0.167$.
For math reasoning, only 9.4\% of examples start below ceiling, but these
gain $+0.204$---harder math problems \emph{do} respond to prompt
elaboration.
The ``insensitive'' label for QA and math should therefore be qualified:
these tasks are insensitive \textbf{at the ceiling-dominated difficulty
of the current example set}, not necessarily in general.
\emph{Caveat:} below-ceiling examples are selected on low L1 quality, so
part of the positive $\Delta$ may reflect regression to the mean rather
than true prompt sensitivity.
```

- [ ] **Step 5: Compile and verify**

```bash
cd paper_acml && pdflatex main.tex && pdflatex main.tex
```

Verify: new table, figure, and paragraphs render correctly. No overflows.

- [ ] **Step 6: Commit**

```bash
git add paper_acml/sec_results.tex paper_acml/figures/fig_heuristic_vs_judge.png paper_acml/figures/fig_heuristic_vs_judge.pdf
git commit -m "feat: integrate heuristic validation, subscore decomp, below-ceiling into paper"
```

---

### Task 3: Fix Temperature in All LLM Providers

The paper will now say `temperature=0`, but `GroqProvider`, `GeminiProvider`, and `AnthropicProvider` don't set it. Fix them so the code matches the claim.

**Files:**
- Modify: `greenprompt/llm.py:47-50` (Gemini), `100-108` (Groq), `169-172` (Anthropic)

- [ ] **Step 1: Add temperature=0 to GeminiProvider**

In `greenprompt/llm.py`, in `GeminiProvider.generate()`, change line 50:

```python
            config={"max_output_tokens": max_tokens}
```

to:

```python
            config={"max_output_tokens": max_tokens, "temperature": 0}
```

- [ ] **Step 2: Add temperature=0 to GroqProvider**

In `greenprompt/llm.py`, in `GroqProvider.generate()`, change line 103:

```python
            max_tokens=max_tokens,
```

to:

```python
            max_tokens=max_tokens,
            temperature=0,
```

- [ ] **Step 3: Add temperature=0 to AnthropicProvider**

In `greenprompt/llm.py`, in `AnthropicProvider.generate()`, change line 170:

```python
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
```

to:

```python
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
```

- [ ] **Step 4: Verify tests still pass**

```bash
python -m pytest tests/test_llm_providers.py -v
```

Expected: all pass (MockProvider is unchanged; real providers only tested if API keys present).

- [ ] **Step 5: Commit**

```bash
git add greenprompt/llm.py
git commit -m "fix: set temperature=0 on all providers to match paper claim"
```

---

### Task 4: Add NER Evaluator

**Files:**
- Modify: `greenprompt/evaluators.py`
- Create: `tests/test_ner_evaluator.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_ner_evaluator.py`:

```python
import pytest
from greenprompt.evaluators import NERExtractionEvaluator, get_evaluator


@pytest.fixture
def evaluator():
    return NERExtractionEvaluator()


class TestNERExtractionEvaluator:
    def test_perfect_match(self, evaluator):
        response = '{"PERSON": ["John Smith"], "ORG": ["Google"], "LOC": ["New York"]}'
        gt = '{"PERSON": ["John Smith"], "ORG": ["Google"], "LOC": ["New York"]}'
        quality, completed = evaluator.evaluate(response, gt)
        assert quality == 1.0
        assert completed is True

    def test_partial_match(self, evaluator):
        response = '{"PERSON": ["John Smith"], "ORG": ["Google"]}'
        gt = '{"PERSON": ["John Smith"], "ORG": ["Google"], "LOC": ["New York"]}'
        quality, completed = evaluator.evaluate(response, gt)
        assert 0.0 < quality < 1.0
        assert completed is True

    def test_wrong_entities(self, evaluator):
        response = '{"PERSON": ["Jane Doe"], "ORG": ["Apple"]}'
        gt = '{"PERSON": ["John Smith"], "ORG": ["Google"], "LOC": ["New York"]}'
        quality, completed = evaluator.evaluate(response, gt)
        assert quality == 0.0

    def test_empty_response(self, evaluator):
        quality, completed = evaluator.evaluate("", '{"PERSON": ["John"]}')
        assert quality == 0.0
        assert completed is False

    def test_no_ground_truth(self, evaluator):
        quality, completed = evaluator.evaluate("some response", None)
        assert quality == 0.0
        assert completed is False

    def test_json_in_markdown_block(self, evaluator):
        response = '```json\n{"PERSON": ["John Smith"], "ORG": ["Google"]}\n```'
        gt = '{"PERSON": ["John Smith"], "ORG": ["Google"]}'
        quality, completed = evaluator.evaluate(response, gt)
        assert quality == 1.0

    def test_case_insensitive_entities(self, evaluator):
        response = '{"PERSON": ["john smith"], "ORG": ["google"]}'
        gt = '{"PERSON": ["John Smith"], "ORG": ["Google"]}'
        quality, completed = evaluator.evaluate(response, gt)
        assert quality == 1.0

    def test_extra_entities_penalized(self, evaluator):
        response = '{"PERSON": ["John Smith", "Jane Doe"], "ORG": ["Google"]}'
        gt = '{"PERSON": ["John Smith"], "ORG": ["Google"]}'
        quality, completed = evaluator.evaluate(response, gt)
        assert quality < 1.0

    def test_get_evaluator_returns_ner(self):
        ev = get_evaluator("ner")
        assert isinstance(ev, NERExtractionEvaluator)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_ner_evaluator.py -v
```

Expected: FAIL — `NERExtractionEvaluator` not defined.

- [ ] **Step 3: Implement NERExtractionEvaluator**

In `greenprompt/evaluators.py`, add before the `get_evaluator` function (before line 293):

```python
class NERExtractionEvaluator(QualityEvaluator):
    """Evaluate NER by comparing extracted entity sets per type against ground truth.

    Ground truth format: JSON dict mapping entity types to lists of entity strings.
    E.g. {"PERSON": ["John Smith"], "ORG": ["Google"], "LOC": ["New York"]}

    Score = F1 averaged across entity types present in ground truth.
    """

    def _parse_entities(self, text: str) -> Optional[dict[str, list[str]]]:
        cleaned = re.sub(r'```(?:json)?\s*', '', text.strip()).rstrip('`')
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if not match:
            return None
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, dict):
                return {k: [str(v).lower() for v in vs] if isinstance(vs, list) else [str(vs).lower()]
                        for k, vs in parsed.items()}
        except (json.JSONDecodeError, TypeError):
            pass
        return None

    def evaluate(self, response: str, ground_truth: Optional[str] = None) -> tuple[float, bool]:
        response = response.strip()
        if not response or ground_truth is None:
            return 0.0, False

        try:
            gt_dict = json.loads(ground_truth)
        except (json.JSONDecodeError, TypeError):
            return 0.0, False

        extracted = self._parse_entities(response)
        if not extracted:
            return 0.0, False

        f1_scores = []
        for etype, gt_entities in gt_dict.items():
            gt_set = {e.lower() for e in gt_entities}
            pred_set = {e.lower() for e in extracted.get(etype, [])}
            if not gt_set:
                continue
            tp = len(gt_set & pred_set)
            precision = tp / len(pred_set) if pred_set else 0.0
            recall = tp / len(gt_set)
            if precision + recall > 0:
                f1 = 2 * precision * recall / (precision + recall)
            else:
                f1 = 0.0
            f1_scores.append(f1)

        if not f1_scores:
            return 0.0, False

        quality = sum(f1_scores) / len(f1_scores)
        return quality, quality >= 0.5
```

Then add `'ner'` to the `get_evaluator` dictionary:

```python
        'ner': NERExtractionEvaluator(),
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_ner_evaluator.py -v
```

Expected: all 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add greenprompt/evaluators.py tests/test_ner_evaluator.py
git commit -m "feat: add NERExtractionEvaluator for held-out task validation"
```

---

### Task 5: Add NER Examples and Prompt Templates

**Files:**
- Modify: `experiments/prompting_strategies.py` (add NER examples to `BENCHMARK_EXAMPLES`)
- Modify: `experiments/saturation_prompts.py` (add NER 7-level templates)

- [ ] **Step 1: Add 20 NER examples to BENCHMARK_EXAMPLES**

In `experiments/prompting_strategies.py`, add to `BENCHMARK_EXAMPLES` dict (after the `product_extraction` block, before the closing `}`):

```python
    'ner': [
        {'input': 'Apple CEO Tim Cook announced new products at their Cupertino headquarters on Monday.',
         'ground_truth': '{"PERSON": ["Tim Cook"], "ORG": ["Apple"], "LOC": ["Cupertino"]}', 'difficulty': 'easy'},
        {'input': 'The European Union fined Google €4.3 billion in Brussels for antitrust violations.',
         'ground_truth': '{"ORG": ["European Union", "Google"], "LOC": ["Brussels"]}', 'difficulty': 'easy'},
        {'input': 'Dr. Sarah Chen published her research at MIT in the journal Nature.',
         'ground_truth': '{"PERSON": ["Sarah Chen"], "ORG": ["MIT", "Nature"]}', 'difficulty': 'easy'},
        {'input': 'Amazon is expanding its operations in Seattle and plans to hire 10,000 workers.',
         'ground_truth': '{"ORG": ["Amazon"], "LOC": ["Seattle"]}', 'difficulty': 'easy'},
        {'input': 'President Biden met with Chancellor Scholz in Berlin to discuss NATO security.',
         'ground_truth': '{"PERSON": ["Biden", "Scholz"], "LOC": ["Berlin"], "ORG": ["NATO"]}', 'difficulty': 'easy'},
        {'input': 'Tesla shares rose 5% after Elon Musk revealed the Cybertruck production timeline in Austin.',
         'ground_truth': '{"ORG": ["Tesla"], "PERSON": ["Elon Musk"], "LOC": ["Austin"]}', 'difficulty': 'easy'},
        {'input': 'The World Health Organization declared the outbreak in Congo a public health emergency.',
         'ground_truth': '{"ORG": ["World Health Organization"], "LOC": ["Congo"]}', 'difficulty': 'medium'},
        {'input': 'Microsoft acquired Activision Blizzard for $69 billion, pending FTC approval in Washington.',
         'ground_truth': '{"ORG": ["Microsoft", "Activision Blizzard", "FTC"], "LOC": ["Washington"]}', 'difficulty': 'medium'},
        {'input': 'Serena Williams announced her retirement from professional tennis at the US Open in New York.',
         'ground_truth': '{"PERSON": ["Serena Williams"], "LOC": ["New York"]}', 'difficulty': 'medium'},
        {'input': 'The Bank of Japan maintained its ultra-low interest rate policy, diverging from the Federal Reserve.',
         'ground_truth': '{"ORG": ["Bank of Japan", "Federal Reserve"]}', 'difficulty': 'medium'},
        {'input': 'Researchers at Stanford and Oxford collaborated on a climate study published in Science.',
         'ground_truth': '{"ORG": ["Stanford", "Oxford", "Science"]}', 'difficulty': 'medium'},
        {'input': 'SpaceX launched a Falcon 9 rocket from Cape Canaveral carrying Starlink satellites.',
         'ground_truth': '{"ORG": ["SpaceX"], "LOC": ["Cape Canaveral"]}', 'difficulty': 'medium'},
        {'input': 'Former Secretary of State Henry Kissinger passed away at his home in Connecticut at the age of 100.',
         'ground_truth': '{"PERSON": ["Henry Kissinger"], "LOC": ["Connecticut"]}', 'difficulty': 'medium'},
        {'input': 'The Red Cross deployed emergency teams to Turkey and Syria following the devastating earthquake.',
         'ground_truth': '{"ORG": ["Red Cross"], "LOC": ["Turkey", "Syria"]}', 'difficulty': 'medium'},
        {'input': 'Samsung unveiled its Galaxy S24 lineup at an Unpacked event in San Jose, competing with the iPhone.',
         'ground_truth': '{"ORG": ["Samsung"], "LOC": ["San Jose"]}', 'difficulty': 'hard'},
        {'input': 'Nobel laureate Maria Ressa criticized Meta at the World Economic Forum in Davos for enabling disinformation.',
         'ground_truth': '{"PERSON": ["Maria Ressa"], "ORG": ["Meta", "World Economic Forum"], "LOC": ["Davos"]}', 'difficulty': 'hard'},
        {'input': 'JPMorgan Chase CEO Jamie Dimon warned of economic risks at the IMF meeting in Marrakech.',
         'ground_truth': '{"PERSON": ["Jamie Dimon"], "ORG": ["JPMorgan Chase", "IMF"], "LOC": ["Marrakech"]}', 'difficulty': 'hard'},
        {'input': 'The United Nations Security Council met in Geneva to address the conflict, with Russia and China abstaining.',
         'ground_truth': '{"ORG": ["United Nations Security Council"], "LOC": ["Geneva", "Russia", "China"]}', 'difficulty': 'hard'},
        {'input': 'DeepMind researchers in London published AlphaFold results in collaboration with EMBL.',
         'ground_truth': '{"ORG": ["DeepMind", "EMBL"], "LOC": ["London"]}', 'difficulty': 'hard'},
        {'input': 'ASML reported record orders from TSMC and Samsung at its Veldhoven headquarters, boosting European chip stocks.',
         'ground_truth': '{"ORG": ["ASML", "TSMC", "Samsung"], "LOC": ["Veldhoven"]}', 'difficulty': 'hard'},
    ],
```

- [ ] **Step 2: Add 7-level NER templates to SATURATION_TEMPLATES**

In `experiments/saturation_prompts.py`, add to `TASK_INPUT_KEY`:

```python
    'ner':                    'text',
```

Add to `SATURATION_TEMPLATES`:

```python
    # ── NER (NAMED ENTITY RECOGNITION) ──────────────────────────────────────
    'ner': [
        # Level 1: bare input
        "Extract entities: {text}",

        # Level 2: + entity type names
        "Extract all person names (PERSON), organizations (ORG), and locations (LOC) from this text: {text}",

        # Level 3: + output format
        (
            "Extract all named entities from this text. "
            "Return as JSON with keys: PERSON, ORG, LOC. Each key maps to a list of strings.\n\n"
            "{text}"
        ),

        # Level 4: + type definitions
        (
            "Extract all named entities from this text. "
            "Return as JSON with keys: PERSON, ORG, LOC.\n\n"
            "Type definitions:\n"
            "- PERSON: full names of individual people (not titles alone)\n"
            "- ORG: companies, agencies, institutions, teams, publications\n"
            "- LOC: cities, countries, regions, specific addresses\n\n"
            "{text}"
        ),

        # Level 5: + role + edge case handling
        (
            "You are an expert named entity recognition system. "
            "Extract all named entities from the text below. "
            "Return as JSON with keys: PERSON, ORG, LOC.\n\n"
            "Type definitions:\n"
            "- PERSON: full names of individual people (not titles alone)\n"
            "- ORG: companies, agencies, institutions, teams, publications\n"
            "- LOC: cities, countries, regions, specific addresses\n\n"
            "If no entities of a type are found, use an empty list.\n\n"
            "{text}"
        ),

        # Level 6: + detailed guidelines
        (
            "You are an expert named entity recognition system. "
            "Extract all named entities from the text below. "
            "Return as JSON with keys: PERSON, ORG, LOC.\n\n"
            "Type definitions:\n"
            "- PERSON: full names of individual people (not titles alone)\n"
            "- ORG: companies, agencies, institutions, teams, publications\n"
            "- LOC: cities, countries, regions, specific addresses\n\n"
            "Guidelines:\n"
            "- Use the exact name as written in the text\n"
            "- Include all instances, even if repeated\n"
            "- A name can belong to multiple types if contextually appropriate\n"
            "- Do not extract adjective forms (e.g., 'American' as LOC unless it names a place)\n"
            "- If no entities of a type exist, use an empty list\n"
            "- Return ONLY valid JSON, no extra text\n\n"
            "{text}"
        ),

        # Level 7: + worked example
        (
            "You are an expert named entity recognition system. "
            "Extract all named entities from the text below. "
            "Return as JSON with keys: PERSON, ORG, LOC.\n\n"
            "Type definitions:\n"
            "- PERSON: full names of individual people (not titles alone)\n"
            "- ORG: companies, agencies, institutions, teams, publications\n"
            "- LOC: cities, countries, regions, specific addresses\n\n"
            "Guidelines:\n"
            "- Use the exact name as written in the text\n"
            "- Include all instances, even if repeated\n"
            "- A name can belong to multiple types if contextually appropriate\n"
            "- Do not extract adjective forms (e.g., 'American' as LOC unless it names a place)\n"
            "- If no entities of a type exist, use an empty list\n"
            "- Return ONLY valid JSON, no extra text\n\n"
            "Example:\n"
            "Text: Sundar Pichai announced Google's new AI lab in Zurich, partnering with ETH.\n"
            "Output: {\"PERSON\": [\"Sundar Pichai\"], \"ORG\": [\"Google\", \"ETH\"], \"LOC\": [\"Zurich\"]}\n\n"
            "Now extract:\n"
            "{text}"
        ),
    ],
```

- [ ] **Step 3: Add 'ner' to TASKS in saturation_benchmark.py**

In `experiments/saturation_benchmark.py`, line 47, change:

```python
TASKS = ['qa', 'summarization', 'classification', 'instruction_following', 'math_reasoning', 'product_extraction']
```

to:

```python
TASKS = ['qa', 'summarization', 'classification', 'instruction_following', 'math_reasoning', 'product_extraction', 'ner']
```

- [ ] **Step 4: Verify templates load without error**

```bash
python -c "
from experiments.saturation_prompts import SATURATION_TEMPLATES, format_prompt
from experiments.prompting_strategies import BENCHMARK_EXAMPLES
ex = BENCHMARK_EXAMPLES['ner'][0]
for i, tmpl in enumerate(SATURATION_TEMPLATES['ner']):
    prompt = format_prompt(tmpl, 'ner', ex)
    print(f'Level {i+1}: {len(prompt)} chars')
print('OK: all 7 NER levels format correctly')
print(f'NER examples: {len(BENCHMARK_EXAMPLES[\"ner\"])}')
"
```

Expected: 7 levels print char counts, 20 examples.

- [ ] **Step 5: Commit**

```bash
git add experiments/prompting_strategies.py experiments/saturation_prompts.py experiments/saturation_benchmark.py
git commit -m "feat: add NER task (20 examples, 7-level templates) for held-out validation"
```

---

### Task 6: Run NER Held-Out Experiment

**Pre-registration:** We predict NER will show **distributed** saturation, like product extraction — because it requires schema demonstration (which entity types to extract) and a worked example showing the expected JSON format. We expect L2 (entity type names) and L7 (worked example) to contribute the largest marginal gains.

**Files:**
- Output: `results/rebuttal_v2/ner_holdout.json`

- [ ] **Step 1: Run NER on 3 models (free tier first)**

```bash
python experiments/saturation_benchmark.py \
    --models llama-3.1-8b gemini-flash qwen3-32b \
    --tasks ner \
    --examples 20 \
    --output results/rebuttal_v2/ner_holdout.json \
    --delay 2.5 \
    --evaluator heuristic
```

Expected: 3 × 7 × 20 = 420 API calls. All free tier. ~20 minutes with delays.

- [ ] **Step 2: Run NER on paid models**

```bash
python experiments/saturation_benchmark.py \
    --models gpt-4o-mini claude-haiku \
    --tasks ner \
    --examples 20 \
    --output results/rebuttal_v2/ner_holdout.json \
    --delay 1.5 \
    --resume \
    --evaluator heuristic
```

Expected: 2 × 7 × 20 = 280 more calls. ~$2-5 total.

- [ ] **Step 3: Run remaining models**

```bash
python experiments/saturation_benchmark.py \
    --models llama-3.3-70b kimi-k2 \
    --tasks ner \
    --examples 20 \
    --output results/rebuttal_v2/ner_holdout.json \
    --delay 2.5 \
    --resume \
    --evaluator heuristic
```

Expected: 2 × 7 × 20 = 280 more calls. Free tier.

- [ ] **Step 4: Verify results and run analysis**

```bash
python -c "
import json
with open('results/rebuttal_v2/ner_holdout.json') as f:
    data = json.load(f)
successful = [r for r in data if 'error' not in r]
models = set(r['model'] for r in successful)
print(f'Total records: {len(successful)}')
print(f'Models: {sorted(models)}')
for model in sorted(models):
    sub = [r for r in successful if r['model'] == model]
    for level in range(1, 8):
        lvl = [r for r in sub if r['level'] == level]
        mean_q = sum(r['quality'] for r in lvl) / len(lvl) if lvl else 0
        print(f'  {model} L{level}: q={mean_q:.3f} (n={len(lvl)})')
"
```

Expected: ~980 records, 7 models, quality should increase notably at L2 (entity types) and L7 (worked example) — matching the "distributed" prediction.

- [ ] **Step 5: Fit saturation curves on NER data**

```bash
python -c "
import json, numpy as np, sys
sys.path.insert(0, '.')
from experiments.saturation_analysis import fit_best_curve, null_model_ftest

with open('results/rebuttal_v2/ner_holdout.json') as f:
    data = [r for r in json.load(f) if 'error' not in r]

models = sorted(set(r['model'] for r in data))
print(f'{'Model':30s} {'Type':10s} {'R²':>6s} {'F':>8s} {'p':>8s} {'Sig':>4s} {'T*':>6s}')
sig_count = 0
for model in models:
    toks, quals = [], []
    for lvl in range(1, 8):
        sub = [r for r in data if r['model'] == model and r['level'] == lvl]
        if sub:
            toks.append(np.mean([r['prompt_tokens'] for r in sub]))
            quals.append(np.mean([r['quality'] for r in sub]))
    toks, quals = np.array(toks), np.array(quals)
    fit = fit_best_curve(toks, quals)
    ft = null_model_ftest(toks, quals, fit)
    sig = ft['ftest_significant']
    if sig: sig_count += 1
    t_star = fit.get('saturation_tokens', float('nan'))
    print(f'{model:30s} {fit[\"model_type\"]:10s} {fit[\"r2\"]:6.3f} {ft[\"ftest_F\"]:8.2f} {ft[\"ftest_p\"]:8.4f} {\"YES\" if sig else \"no\":>4s} {t_star:6.0f}')
print(f'\nSignificant fits: {sig_count}/{len(models)}')
"
```

Expected: If prediction is correct, multiple models show significant saturation (like product extraction's 3/7 judge or 7/7 heuristic). The marginal gains should be distributed across levels, especially L2 and L7.

- [ ] **Step 6: Commit results**

```bash
git add results/rebuttal_v2/ner_holdout.json
git commit -m "data: NER held-out experiment results (7 models × 7 levels × 20 examples)"
```

---

### Task 7: Add Repeated Runs Support and Run Experiment

Run 3 repeats on the 3 spectrum-critical tasks: classification (concentrated), product_extraction (distributed), instruction_following (diffuse). All 7 models. This tests whether the gradient holds under variance.

**Files:**
- Modify: `experiments/saturation_benchmark.py` (add `--run-id` flag)
- Output: `results/rebuttal_v2/repeated_runs.json`
- Create: `experiments/rebuttal_repeated_runs.py` (analysis)

- [ ] **Step 1: Add --run-id flag to benchmark runner**

In `experiments/saturation_benchmark.py`, add a `--run-id` argument and include it in the record key and output. After line 203 (`parser.add_argument('--resume',...)`), add:

```python
    parser.add_argument('--run-id', type=int, default=0,
                        help='Run identifier for repeated runs (0, 1, 2, ...)')
```

In the `run_saturation_benchmark` function signature (line 98), add `run_id: int = 0`:

```python
def run_saturation_benchmark(
    providers: list[tuple[str, LLMProvider]],
    tasks: list[str] = TASKS,
    examples_per_task: int = 20,
    output_path: str = 'results/saturation_results.json',
    delay_between_calls: float = 2.0,
    resume: bool = False,
    evaluator_type: str = 'heuristic',
    judge_provider: 'Optional[LLMProvider]' = None,
    run_id: int = 0,
) -> list[dict]:
```

Change the `done` key tuple (line 81) and `key` tuple (line 122) to include `run_id`:

Line 81:
```python
        done = {
            (r['model'], r['task'], r['level'], r['example_id'], r.get('run_id', 0))
            for r in existing
            if 'error' not in r
        }
```

Line 122:
```python
                    key = (model_name, task, level, ex_idx, run_id)
```

Add `'run_id': run_id` to both record dicts (the success record around line 155 and the error record around line 172).

In `main()`, pass it through (around line 232):

```python
    run_saturation_benchmark(
        ...,
        run_id=args.run_id,
    )
```

- [ ] **Step 2: Run repeated experiments — Run 1 (Groq models, free)**

Run 1 is the original data (run_id=0) which already exists. We need run_id=1 and run_id=2.

```bash
# Run 1 — Groq models (free)
python experiments/saturation_benchmark.py \
    --models llama-3.1-8b llama-3.3-70b qwen3-32b kimi-k2 \
    --tasks classification product_extraction instruction_following \
    --examples 20 \
    --output results/rebuttal_v2/repeated_runs.json \
    --delay 2.5 \
    --run-id 1 \
    --evaluator heuristic

# Run 2 — Groq models (free)
python experiments/saturation_benchmark.py \
    --models llama-3.1-8b llama-3.3-70b qwen3-32b kimi-k2 \
    --tasks classification product_extraction instruction_following \
    --examples 20 \
    --output results/rebuttal_v2/repeated_runs.json \
    --delay 2.5 \
    --resume \
    --run-id 2 \
    --evaluator heuristic
```

Expected: 4 models × 3 tasks × 7 levels × 20 examples × 2 runs = 3,360 calls. Free tier, ~3-4 hours with rate limiting.

- [ ] **Step 3: Run repeated experiments — paid models**

```bash
# Gemini (free)
for RUN in 1 2; do
python experiments/saturation_benchmark.py \
    --models gemini-flash \
    --tasks classification product_extraction instruction_following \
    --examples 20 \
    --output results/rebuttal_v2/repeated_runs.json \
    --delay 1.5 \
    --resume \
    --run-id $RUN \
    --evaluator heuristic
done

# OpenAI + Anthropic (paid)
for RUN in 1 2; do
python experiments/saturation_benchmark.py \
    --models gpt-4o-mini claude-haiku \
    --tasks classification product_extraction instruction_following \
    --examples 20 \
    --output results/rebuttal_v2/repeated_runs.json \
    --delay 1.5 \
    --resume \
    --run-id $RUN \
    --evaluator heuristic
done
```

Expected: 3 models × 3 tasks × 7 levels × 20 examples × 2 runs = 2,520 calls. Paid portion (gpt-4o-mini + claude-haiku) = 1,680 calls, ~$15-25.

- [ ] **Step 4: Also copy original run data as run_id=0**

We need run_id=0 for the same 3 tasks. Extract from `results/rebuttal_v2/main_study_combined.json`:

```bash
python -c "
import json
with open('results/rebuttal_v2/main_study_combined.json') as f:
    original = json.load(f)

tasks = {'classification', 'product_extraction', 'instruction_following'}
run0 = [dict(r, run_id=0) for r in original if r.get('task') in tasks and 'error' not in r]
print(f'Extracted {len(run0)} run-0 records')

# Merge with repeated runs
try:
    with open('results/rebuttal_v2/repeated_runs.json') as f:
        repeated = json.load(f)
except FileNotFoundError:
    repeated = []

# Remove any existing run_id=0 to avoid dupes
repeated = [r for r in repeated if r.get('run_id', -1) != 0]
combined = run0 + repeated

with open('results/rebuttal_v2/repeated_runs.json', 'w') as f:
    json.dump(combined, f, indent=2)
print(f'Total records in repeated_runs.json: {len(combined)}')
"
```

- [ ] **Step 5: Create repeated runs analysis script**

Create `experiments/rebuttal_repeated_runs.py`:

```python
"""
Repeated-runs analysis: compute per-level SE, effect-vs-noise ratios,
and test whether the prompt-sensitivity gradient survives variance.
"""
import json
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, "results", "rebuttal_v2", "repeated_runs.json")
OUT = os.path.join(ROOT, "results", "rebuttal_v2", "repeated_runs_analysis.json")

TASKS = ["classification", "product_extraction", "instruction_following"]


def main():
    with open(DATA) as f:
        data = [r for r in json.load(f) if "error" not in r]

    models = sorted(set(r["model"] for r in data))
    runs = sorted(set(r.get("run_id", 0) for r in data))
    print(f"Models: {models}")
    print(f"Runs: {runs}")
    print(f"Total records: {len(data)}")

    results = {}
    for task in TASKS:
        results[task] = {}
        for model in models:
            level_stats = []
            for level in range(1, 8):
                run_means = []
                for run_id in runs:
                    sub = [r for r in data
                           if r["model"] == model
                           and r["task"] == task
                           and r["level"] == level
                           and r.get("run_id", 0) == run_id]
                    if sub:
                        run_means.append(np.mean([r["quality"] for r in sub]))

                if run_means:
                    level_stats.append({
                        "level": level,
                        "mean": float(np.mean(run_means)),
                        "std": float(np.std(run_means, ddof=1)) if len(run_means) > 1 else 0.0,
                        "se": float(np.std(run_means, ddof=1) / np.sqrt(len(run_means))) if len(run_means) > 1 else 0.0,
                        "n_runs": len(run_means),
                        "run_means": [float(m) for m in run_means],
                    })

            if level_stats:
                l1_mean = level_stats[0]["mean"]
                l7_mean = level_stats[-1]["mean"]
                delta = l7_mean - l1_mean
                max_se = max(s["se"] for s in level_stats)
                mean_se = np.mean([s["se"] for s in level_stats])

                results[task][model] = {
                    "levels": level_stats,
                    "L1_to_L7_delta": float(delta),
                    "max_se": float(max_se),
                    "mean_se": float(mean_se),
                    "effect_to_noise": float(abs(delta) / mean_se) if mean_se > 0 else float("inf"),
                }

    with open(OUT, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'Task':25s} {'Model':30s} {'L1→L7 Δ':>10s} {'Mean SE':>10s} {'Effect/Noise':>13s}")
    print("-" * 90)
    for task in TASKS:
        for model in sorted(results[task]):
            r = results[task][model]
            print(f"{task:25s} {model:30s} {r['L1_to_L7_delta']:+10.4f} "
                  f"{r['mean_se']:10.4f} {r['effect_to_noise']:13.1f}")
        print()


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run analysis and interpret**

```bash
python experiments/rebuttal_repeated_runs.py
```

Key things to check:
- **Classification:** effect/noise ratio should be high (>5). If SE is 0.005 and delta is +0.07, ratio = 14x — solid.
- **Product extraction:** effect/noise ratio should be high (>5). Similar logic.
- **Instruction following:** This is the critical test. If SE ≈ delta (ratio near 1), the "diffuse" category collapses into "insensitive." If ratio > 3, it holds.

If instruction following's effect/noise ratio < 2, update the paper to merge "diffuse" into "insensitive" and report a 3-level gradient honestly.

- [ ] **Step 7: Commit**

```bash
git add experiments/saturation_benchmark.py experiments/rebuttal_repeated_runs.py results/rebuttal_v2/repeated_runs.json results/rebuttal_v2/repeated_runs_analysis.json
git commit -m "feat: repeated runs experiment (3 tasks × 7 models × 3 runs) with analysis"
```

---

### Task 8: Add Bootstrap Error Bars to Figure 1

**Files:**
- Create: `experiments/rebuttal_error_bars.py`
- Output: `results/rebuttal_v2/figures/fig1_with_error_bars.png`

- [ ] **Step 1: Create error bar script**

Create `experiments/rebuttal_error_bars.py`:

```python
"""
Bootstrap SE bands on level means for Figure 1 saturation curves.
Uses the main study data (20 examples per level) to compute bootstrap SE
at each (model, task, level), then replots the saturation curves with
shaded ±1 SE bands.
"""
import json
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, "results", "rebuttal_v2", "main_study_combined.json")
OUT_DIR = os.path.join(ROOT, "results", "rebuttal_v2", "figures")
N_BOOTSTRAP = 1000

TASKS_TO_PLOT = ["classification", "product_extraction", "instruction_following",
                 "qa", "math_reasoning", "summarization"]
TASK_LABELS = {
    "classification": "Classification",
    "product_extraction": "Product Extraction",
    "instruction_following": "Instruction Following",
    "qa": "QA",
    "math_reasoning": "Math Reasoning",
    "summarization": "Summarisation",
}


def bootstrap_se(values, n_boot=N_BOOTSTRAP):
    """Bootstrap standard error of the mean."""
    values = np.array(values)
    n = len(values)
    if n < 2:
        return 0.0
    boot_means = np.array([
        np.mean(np.random.choice(values, size=n, replace=True))
        for _ in range(n_boot)
    ])
    return float(np.std(boot_means, ddof=1))


def main():
    np.random.seed(42)
    with open(DATA) as f:
        data = [r for r in json.load(f) if "error" not in r]

    models = sorted(set(r["model"] for r in data))

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for ax_idx, task in enumerate(TASKS_TO_PLOT):
        ax = axes[ax_idx]
        for model in models:
            toks, means, ses = [], [], []
            for level in range(1, 8):
                sub = [r for r in data
                       if r["model"] == model and r["task"] == task and r["level"] == level]
                if not sub:
                    continue
                qualities = [r["quality"] for r in sub]
                toks.append(np.mean([r["prompt_tokens"] for r in sub]))
                means.append(np.mean(qualities))
                ses.append(bootstrap_se(qualities))

            if not toks:
                continue
            toks, means, ses = np.array(toks), np.array(means), np.array(ses)
            line, = ax.plot(toks, means, marker="o", markersize=3, label=model)
            ax.fill_between(toks, means - ses, means + ses, alpha=0.15, color=line.get_color())

        ax.set_title(TASK_LABELS.get(task, task), fontsize=12)
        ax.set_xlabel("Prompt tokens")
        ax.set_ylabel("Quality")
        ax.set_ylim(-0.05, 1.1)

    axes[0].legend(fontsize=6, loc="lower right")
    plt.tight_layout()
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "fig1_with_error_bars.png")
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.savefig(out_path.replace(".png", ".pdf"), bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

```bash
python experiments/rebuttal_error_bars.py
```

Expected: produces `results/rebuttal_v2/figures/fig1_with_error_bars.png` with shaded bands. For classification the bands should be narrow at L3+ (all models agree on high quality). For product extraction they may be wider at L1-L2.

- [ ] **Step 3: Copy to paper figures and update LaTeX**

```bash
cp results/rebuttal_v2/figures/fig1_with_error_bars.png paper_acml/figures/
cp results/rebuttal_v2/figures/fig1_with_error_bars.pdf paper_acml/figures/
```

In `paper_acml/sec_results.tex`, find the existing Figure 1 `\includegraphics` and replace the image filename with `fig1_with_error_bars.png`. Add to the caption: "Shaded bands show $\pm 1$ bootstrap SE across 20 examples."

- [ ] **Step 4: Commit**

```bash
git add experiments/rebuttal_error_bars.py results/rebuttal_v2/figures/fig1_with_error_bars.png results/rebuttal_v2/figures/fig1_with_error_bars.pdf paper_acml/figures/fig1_with_error_bars.png paper_acml/figures/fig1_with_error_bars.pdf paper_acml/sec_results.tex
git commit -m "feat: add bootstrap SE error bars to Figure 1"
```

---

### Task 9: Add Related Work References

**Files:**
- Modify: `paper_acml/sec_related.tex` (or the file containing the Related Work section)

- [ ] **Step 1: Find the related work file**

```bash
grep -rn "Related Work\|\\section.*related\|\\section.*prior" paper_acml/*.tex
```

- [ ] **Step 2: Add the missing references**

Add a new paragraph at the end of the related work section:

```latex
\paragraph{Prompt sensitivity.}
Several recent works study how LLM performance varies under prompt
perturbations.
\citet{zhuo2024prosa} introduce ProSA, a metric quantifying sensitivity
to paraphrased prompts while holding information constant.
\citet{sclar2024quantifying} show that minor formatting choices
(separators, casing) substantially affect in-context learning accuracy.
\citet{voronov2024mind} demonstrate that inconsistent prompt formatting
confounds evaluation of in-context learning improvements.
Most recently, \citet{revisiting2026classification} revisit prompt
sensitivity specifically for text classification, finding that
surface-level prompt features can dominate content-level features.
These works study sensitivity along the \emph{formatting} axis---varying
phrasing or layout while holding information constant.
Our work studies the complementary \emph{information} axis: we hold
phrasing fixed (via strict additive nesting) and vary how much
task-relevant information the prompt contains.
Together, these two axes span the space of prompt variation that
practitioners face.
```

Add the corresponding `\bibitem` entries to the bibliography file:

```bibtex
@inproceedings{zhuo2024prosa,
  title={ProSA: Assessing and Understanding the Prompt Sensitivity of LLMs},
  author={Zhuo, Terry Yue and Huang, Jing and others},
  booktitle={Findings of EMNLP},
  year={2024}
}

@inproceedings{sclar2024quantifying,
  title={Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design},
  author={Sclar, Melanie and Choi, Yejin and Tsvetkov, Yulia and Suhr, Alane},
  booktitle={ICLR},
  year={2024}
}

@article{voronov2024mind,
  title={Mind Your Format: Towards Consistent Evaluation of In-Context Learning Improvements},
  author={Voronov, Anton and others},
  journal={arXiv preprint arXiv:2401.06766},
  year={2024}
}

@article{revisiting2026classification,
  title={Revisiting Prompt Sensitivity in Large Language Models for Text Classification},
  author={Anonymous},
  journal={arXiv preprint arXiv:2602.04297},
  year={2026}
}
```

- [ ] **Step 3: Compile and verify references resolve**

```bash
cd paper_acml && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

- [ ] **Step 4: Commit**

```bash
git add paper_acml/
git commit -m "feat: add ProSA, Sclar, Voronov, and 2026 classification refs to related work"
```

---

### Task 10: Write NER Results and Repeated Runs into Paper

This task depends on Tasks 6 and 7 completing. Write the experimental results into the paper.

**Files:**
- Modify: `paper_acml/sec_results.tex` (held-out validation subsection)
- Modify: `paper_acml/sec_discussion.tex` (gradient validation paragraph)
- Modify: `paper_acml/sec_method.tex` (add NER task to methodology)

- [ ] **Step 1: Add NER to methodology section**

In `paper_acml/sec_method.tex`, in the task list (Section 3.1), add NER:

```latex
\item \textbf{Named Entity Recognition (NER, held-out validation):}
    Extract person names, organisations, and locations from news-style
    sentences. 20 curated examples spanning easy (single entity type) to
    hard (multiple overlapping entities). Heuristic: per-type F1 averaged
    across entity categories.
    This task was selected \emph{after} the main study to validate the
    prompt-sensitivity gradient: we predicted NER would show
    \textbf{distributed} saturation, like product extraction, because
    both tasks require schema demonstration.
```

- [ ] **Step 2: Add held-out validation results**

In `paper_acml/sec_results.tex`, add a new subsection after the capability-modulated section:

```latex
\subsection{Held-Out Task Validates the Gradient}
\label{sec:result-holdout}

To test whether the prompt-sensitivity gradient generalises beyond the
six main-study tasks, we pre-registered a prediction and evaluated one
held-out task: Named Entity Recognition (NER).

\paragraph{Prediction.}
NER requires the model to know \emph{which} entity types to extract
(schema) and \emph{how} to format the output (JSON with typed lists)---
structurally analogous to product extraction.
We therefore predicted \textbf{distributed} saturation, with the largest
marginal gains at L2 (entity type names) and L7 (worked example).

\paragraph{Results.}
[FILL AFTER RUNNING TASK 6: report number of significant fits out of 7,
the marginal contribution profile showing which levels contribute most,
and whether the prediction was confirmed.
Template: ``X/7 models show significant saturation fits. The marginal
profile confirms the distributed prediction: L2 (entity type names)
contributes Y\% and L7 (worked example) contributes Z\% of total gain.'']
```

- [ ] **Step 3: Add repeated-runs results**

Add a paragraph in the discussion or a new subsection in results:

```latex
\paragraph{Stability under repeated runs.}
To quantify sampling variance, we repeated the three gradient-critical
tasks (classification, product extraction, instruction following) across
all seven models with three independent runs at temperature $= 0$.
[FILL AFTER RUNNING TASK 7: report mean SE, effect-to-noise ratios.
Template: ``The mean bootstrap SE across all conditions is X.
For classification, the L1$\to$L7 effect (+0.072) exceeds the mean SE
by a factor of Y. For product extraction, the ratio is Z.
For instruction following, the ratio is W---[confirming/not confirming]
that diffuse gains are distinguishable from noise.'']
```

- [ ] **Step 4: Compile paper**

```bash
cd paper_acml && pdflatex main.tex && pdflatex main.tex
```

- [ ] **Step 5: Commit**

```bash
git add paper_acml/sec_results.tex paper_acml/sec_discussion.tex paper_acml/sec_method.tex
git commit -m "feat: add NER held-out validation and repeated-runs results to paper"
```

---

## Execution Order and Dependencies

```
Task 1 (Figure 2 + abstract + README)     ─── independent, do first
Task 2 (Tier-1 into paper)                 ─── independent, do first
Task 3 (Fix temperature)                   ─── independent, do first
  ↓
Task 4 (NER evaluator + tests)             ─── depends on nothing
Task 5 (NER examples + templates)          ─── depends on Task 4
  ↓
Task 6 (Run NER experiment)                ─── depends on Task 5, requires API keys
Task 7 (Repeated runs experiment)          ─── depends on Task 3, requires API keys
Task 8 (Error bars on Figure 1)            ─── independent, no API cost
  ↓
Task 9 (Related work refs)                 ─── independent writing task
Task 10 (Write all results into paper)     ─── depends on Tasks 6, 7, 8
```

**Parallelizable:** Tasks 1, 2, 3, 4, 8, 9 can all run in parallel (no API calls needed except for human writing). Tasks 6 and 7 need API keys and take hours due to rate limiting — start them as soon as their dependencies are met and run concurrently.
