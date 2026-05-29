# COLM 2026 Rebuttal: Acceptance Assessment & Strategy

## Current Standing

| Reviewer | Rating | Confidence | Likely Movable? |
|----------|--------|------------|-----------------|
| CnfP | 5 (marginally below) | 3 | Yes → 6 |
| R19f | 4 (rejection) | 4 | Possible → 5 |
| 4x2b | 4 (rejection) | 4 | Possible → 5 |
| C2JD | 3 (clear rejection) | 4 | Unlikely |

**Average: 4.0** — solidly in rejection territory. Need at least 2 reviewers to move up.

---

## What Reviewers Agree On (Strengths)

- The core idea (measuring prompt-quality saturation curves) is novel and practically useful
- The additive prompt design is a clean methodological contribution
- The paper is clearly written with good figures
- Honest about negative results

## The #1 Concern Across All Reviews

**Length vs. content confound.** Every reviewer raises this in some form:

- **R19f** (central question): "The biggest issue is that the paper frames itself as studying 'prompt length' but the additive levels simultaneously introduce qualitatively different prompting mechanisms."
- **CnfP**: "Can you report results for at least one permuted layer ordering to test whether saturation is intrinsic to the task?"
- **4x2b**: "It remains uncertain whether prompt length itself is the determining factor, or whether the content and structure of the prompt play a more significant role."

## What the Rebuttal Already Has

The rebuttal draft includes strong new evidence:

1. **Randomized layer-ordering ablation** (2,986 experiments) — shows saturation persists across orderings for mid-range models on product extraction (13/15 significant fits)
2. **Second independent judge** (3,915 re-evaluations) — strong agreement on classification/math
3. **Ceiling stratification** — confirms QA/math "non-saturation" is ceiling-at-L1
4. **Marginal contribution analysis** — schema-defining layers drive most quality gains
5. **Math L3 non-monotonicity** — harmful instruction finding
6. **Output length control** — partial correlations confirm prompt→quality after controlling output

## The Gap the Padding Control Fills

The ablation shows saturation is robust to *information ordering* — but the rebuttal currently acknowledges this limitation:

> "We acknowledge that a stronger test would include a control with irrelevant padding tokens (to test whether raw token count alone shifts the curve). Absent that, the ablation shows the saturation curve is robust to information ordering but **cannot fully rule out a token-count component**."

This is an open invitation for reviewers to say "interesting but not conclusive." The padding control closes this gap entirely.

### How the Padding Control Moves the Needle

**Before padding control:**
- Ablation shows: ordering doesn't matter → saturation is robust
- But: maybe ANY tokens help, regardless of content?
- Reviewer can still argue: "you haven't separated length from content"

**After padding control:**
- Padding shows: irrelevant tokens DON'T help → quality stays flat
- Real experiment shows: relevant tokens DO help → quality rises then saturates
- Combined conclusion: **saturation is driven by information content reaching a sufficiency threshold, not by raw token count**

This transforms the acknowledged limitation into a positive finding. Instead of writing "we cannot fully rule out a token-count component," you write:

> "We conducted a padding control experiment (n=1,470) matching token counts at each level with three types of irrelevant filler (factual trivia, repeated phrases, random words). Quality remained flat across all conditions (mean L1→L7 delta = X, 0/N significant trends), while the real experiment shows significant quality gains over the same token range. This confirms that saturation is driven by information content reaching a task-specific sufficiency threshold, not by raw token count."

### Impact on Each Reviewer

| Reviewer | Current concern | How padding helps |
|----------|----------------|-------------------|
| CnfP (5) | Layer ordering, threshold sensitivity | Padding + ablation together = complete answer. Should move to 6. |
| R19f (4) | "Length vs content is the central methodological question" | Padding directly answers this. Combined with ablation = strong evidence. Could move to 5. |
| 4x2b (4) | "Unclear whether prompt length itself is the determining factor" | Padding is exactly the experiment they're asking for. Could move to 5. |
| C2JD (3) | Multiple concerns (examples, evaluation, scope) | Padding helps but won't address all concerns. Unlikely to move enough. |

### Revised Acceptance Probability

- Without padding control: ~25-35%
- With padding control (assuming flat result): ~40-50%

The padding control is the single highest-ROI experiment available because it directly addresses the #1 shared concern and converts a stated limitation into a strength.

---

## What Else Would Help (Lower Priority)

1. **Additional classification domain** (topic classification) — addresses 4x2b's "only sentiment" concern
2. **Product extraction replication at 200 examples** — addresses C2JD's coverage concern
3. **Small human evaluation** (50 responses) — addresses single-judge concern beyond second automated judge

These are all good but lower ROI than the padding control. The padding control should be run first.
