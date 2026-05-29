# Padding Control Experiment: Design Document

## Plain English Summary

### What question does this answer?

Our paper shows that when you add more instructions to a prompt, quality improves up to a point and then stops (saturation). But reviewers ask: **is it the *useful information* in those instructions that helps, or does simply making the prompt longer (more tokens) somehow help regardless of what those tokens say?**

### What does this experiment do?

We take the exact same task inputs (product reviews, product descriptions) and instead of adding real instructions (like "classify as positive/negative" or "return JSON format"), we pad the prompt with **completely irrelevant text** — geography facts, repeated filler phrases, or random words — matched to the same token counts as our real experiment.

### What do we expect?

- **If quality stays flat** (same at 50 tokens of padding as at 200 tokens of padding): This proves that the saturation we observe in the real experiment is driven by the *information content* of the instructions, not the raw number of tokens. This is the expected result and directly refutes the reviewer concern.

- **If quality rises with padding**: This would suggest there's a token-count effect independent of content (unlikely, but would be an interesting finding in itself).

### Why three types of padding?

To make the result robust. If we only used one type of filler, a reviewer could argue "maybe that specific filler accidentally helped." By testing three very different types (coherent facts, repeated phrases, random words), we show the result isn't an artifact of the filler choice.

---

## Technical Design

### Experimental Structure

```
Real experiment (already done):
  L1: "Classify: {text}"                              → ~48 tokens
  L2: "Classify sentiment as positive/negative: {text}" → ~84 tokens  
  L3: + format spec                                    → ~111 tokens
  L4: + definitions                                    → ~155 tokens
  ...
  L7: + worked example                                 → ~217 tokens
  
  Result: Quality rises from L1→L4, then plateaus (saturation)

Padding control (this experiment):
  L1: "Classify: {text}"                               → ~48 tokens (SAME)
  L2: "Classify: {text}" + irrelevant padding          → ~84 tokens (MATCHED)
  L3: "Classify: {text}" + more irrelevant padding     → ~111 tokens (MATCHED)
  L4: "Classify: {text}" + even more padding           → ~155 tokens (MATCHED)
  ...
  L7: "Classify: {text}" + lots of padding             → ~217 tokens (MATCHED)
  
  Expected result: Quality stays flat (no improvement from padding)
```

### Variables

| Variable | Values |
|----------|--------|
| Models | gemini-flash, llama-3.3-70b, llama-3.1-8b, qwen3-32b, claude-haiku |
| Tasks | classification, product_extraction |
| Padding types | irrelevant_facts, repeated_filler, random_words |
| Levels | 7 (token-matched to real experiment) |
| Examples | 7 curated per task (same as random ablation) |

### Padding Types

1. **irrelevant_facts**: Coherent English paragraphs about geography, history, science, cooking, architecture, music. Grammatically correct, semantically irrelevant to sentiment/extraction.

2. **repeated_filler**: The phrase "Note: additional context follows for reference purposes." repeated to fill the target token count. Tests whether even structured-looking but vacuous text helps.

3. **random_words**: Common English words in random order ("out your with now way long have are it and about day"). No coherent meaning at all.

### Token Count Targets (from real experiment data)

**Classification:**
| Level | Real experiment tokens | Padding target |
|-------|----------------------|----------------|
| L1 | 48 | 48 (bare, no padding) |
| L2 | 84 | 84 |
| L3 | 111 | 111 |
| L4 | 155 | 155 |
| L5 | 175 | 175 |
| L6 | 196 | 196 |
| L7 | 217 | 217 |

**Product Extraction:**
| Level | Real experiment tokens | Padding target |
|-------|----------------------|----------------|
| L1 | 66 | 66 (bare, no padding) |
| L2 | 102 | 102 |
| L3 | 135 | 135 |
| L4 | 194 | 194 |
| L5 | 212 | 212 |
| L6 | 261 | 261 |
| L7 | 300 | 300 |

### Evaluation

- Same LLM judge as the rest of the rebuttal experiments (gemini-2.0-flash)
- Same 4-dimension rubric (correctness, completeness, reasoning, conciseness)
- Same task-specific ground truth

### Scale

- 5 models × 2 tasks × 3 padding types × 7 levels × 7 examples = **1,470 generation calls**
- Each generation call also requires 1 judge call = **1,470 judge calls**
- **Total: 2,940 API calls**

### Statistical Analysis

For each (model, task, padding_type) combination:
1. Compute mean quality at each level
2. Spearman correlation between level and quality (tests for monotonic trend)
3. Linear regression of quality on token count (tests for linear relationship)
4. Compare L1→L7 quality delta with the real experiment's delta

**Key metric:** Number of conditions showing a significant positive trend. If 0/30 (or very few) show significance while the real experiment shows clear saturation, the confound is ruled out.

---

## How to Interpret Results

### Best case (expected):
- Padding conditions: flat quality, no significant trends
- Real experiment: clear saturation curves
- **Conclusion:** "Saturation is driven by information content, not token count"

### Alternative outcomes:
- If ONE padding type shows a trend but others don't → that specific filler type may accidentally contain useful signal; the other two conditions still support the conclusion
- If ALL padding types show improvement → there IS a token-count effect (would need to be reported honestly, but this is very unlikely given prior literature on prompt compression)

---

## Rebuttal Integration

Once results are in, add to the rebuttal response for R19f Q1 (Length vs. Content Confound):

> "To directly test whether saturation is driven by token count or information content, we conducted a padding control experiment. We matched the token counts of our 7 additive levels using three types of irrelevant filler (factual trivia unrelated to the task, repeated neutral phrases, and random word sequences). Across 1,470 experiments (5 models × 2 tasks × 3 padding types × 7 levels × 7 examples), quality remained flat: mean L1→L7 delta = [X] (vs. [Y] in the real experiment), with [0/30] conditions showing a significant positive trend (Spearman p < 0.05). This confirms that the saturation curves in our main experiment are driven by information content reaching a task-specific sufficiency threshold, not by raw token count."
