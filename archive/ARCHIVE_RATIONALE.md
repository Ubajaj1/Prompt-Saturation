# Archive Rationale

> **Date:** 2026-03-08
> **Decision:** Archive GreenPES metric and all findings that depend on it.

## Why GreenPES Was Rejected

The GreenPES metric `Quality / (Input_Tokens + α × Output_Tokens)` has fundamental design flaws:

1. **Circular reasoning** — Dividing quality by token count mechanically rewards shorter prompts. Findings like "concise beats CoT" are tautological: the metric *defines* brevity as efficient, then "discovers" brevity wins.
2. **Arbitrary α** — α=1.5 was chosen to match OpenAI's API pricing ratio, not from any theoretical or cognitive grounding. It's a billing artifact, not a property of language or information.
3. **α sensitivity is not validation** — Rankings being stable across α=1.0–4.0 just means the quality numerator dominates regardless of α weighting. It doesn't validate the metric design.

## What Was Archived

### RQ Audit

| RQ | Finding | Depends on GreenPES? | Verdict |
|----|---------|---------------------|---------|
| RQ1 | "concise/zero_shot beat CoT/few_shot" | **Yes** — GreenPES divides by tokens, shorter wins by definition | **REJECTED — circular** |
| RQ2 | Token efficiency by task | **Yes** — same metric | **REJECTED** |
| RQ3 | Model ranking by GreenPES | **Yes** — ranks by GreenPES | **REJECTED** |
| RQ4 | Quality-efficiency tradeoff (r=0.242) | **Yes** — and weak | **REJECTED** |
| RQ5 | Model×strategy interaction (F=1.89, p=0.005) | **No** — uses `quality ~ model × strategy` | **KEPT** |
| RQ6 | No universal best strategy (universality=0.000) | **No** — Kendall τ on quality rankings | **KEPT** |
| RQ7 | Scaling laws from main benchmark | Partially — **superseded** by controlled saturation | **ARCHIVED — replaced by Phase 7** |
| RQ8 | "Be concise" ≈ LLM optimization | **No** — compression ratio + quality retention | **KEPT (weak: n=36, 1 model)** |
| RQ9a | Heuristic ≈ LLM judge (r=0.986) | **No** — validates quality measurement | **KEPT** |
| RQ9b | α sensitivity | **Yes** — about GreenPES parameter | **REJECTED** |
| Phase 7 | Saturation curves | **No** — quality = f(tokens), pure curve fitting | **KEPT — main contribution** |

### Archived Code

| File | Original Location | Why Archived |
|------|------------------|-------------|
| `metrics.py` | `greenprompt/metrics.py` | GreenPES calculator — the rejected metric |
| `scorer.py` | `greenprompt/scorer.py` | GreenPES scoring orchestrator |
| `optimizer.py` | `greenprompt/optimizer.py` | Prompt optimizer (RQ8 underpowered, n=36) |
| `benchmark.py` | `experiments/benchmark.py` | Main benchmark runner (GreenPES-focused, data already collected) |
| `optimizer_benchmark.py` | `experiments/optimizer_benchmark.py` | Optimizer benchmark runner |
| `test_analysis.py` | `tests/test_analysis.py` | Tests for GreenPES analysis |
| `test_optimizer.py` | `tests/test_optimizer.py` | Tests for optimizer |

### Archived Results

| File | Why Archived |
|------|-------------|
| `benchmark_results.json` | Early test run |
| `optimizer_results.json` | v1 optimizer (superseded) |
| `optimizer_results_v2.json` | v2 optimizer (underpowered, n=36) |
| `quick_test.json` | Test data |
| `saturation_results.json` | Heuristic saturation (superseded by LLM judge version) |
| `saturation_summary.csv` | Heuristic saturation summary |
| `stats_summary.csv` | GreenPES-centric statistics |

### Archived Figures

| Figure | RQ | Why |
|--------|-----|-----|
| fig1_strategy_heatmap | RQ1 | GreenPES-dependent |
| fig2_model_comparison, fig2_token_efficiency | RQ2/3 | GreenPES-dependent |
| fig3_model_comparison, fig3_quality_efficiency_scatter | RQ3/4 | GreenPES-dependent |
| fig4_greenpes_distribution, fig4_quality_efficiency_scatter | RQ4 | GreenPES-dependent |
| fig7_scaling_curves | RQ7 | Superseded by saturation experiment |
| fig8_saturation_points | RQ7 | Superseded by saturation experiment |
| fig12_alpha_sensitivity | RQ9b | GreenPES α parameter |
| fig_sat1, fig_sat2 | Phase 7 heuristic | Superseded by LLM judge version |

## What Was Kept

### Active Code
- `greenprompt/evaluators.py` — quality evaluators (used by saturation experiment)
- `greenprompt/llm.py` — LLM provider abstraction
- `experiments/saturation_benchmark.py` — saturation experiment runner
- `experiments/saturation_analysis.py` — curve fitting + saturation point extraction
- `experiments/saturation_prompts.py` — 7-level additive prompt templates
- `experiments/prompting_strategies.py` — task configs + benchmark examples
- `experiments/analysis.py` — contains code for RQ5/RQ6 (model×strategy interaction)

### Active Results
- `results/benchmark_judge_full.json` — main benchmark data (needed for RQ5/RQ6 analysis)
- `results/saturation_results_judge.json` — saturation experiment with LLM judge (main finding)
- `results/saturation_judge/` — saturation analysis output + figures

### Kept Figures (in results/figures/)
- `fig5_transfer_heatmap.png` — RQ5: strategy transfer matrix
- `fig6_interaction_plot.png` — RQ6: model×strategy interaction
- `fig9_compression_scatter.png` — RQ8: optimizer compression vs quality
- `fig10_compression_bars.png` — RQ8: compression by strategy
- `fig11_quality_signal_comparison.png` — RQ9a: heuristic vs LLM judge

## Paper Structure (Post-Archive)

The paper is no longer about a metric. It's about a **phenomenon**:

> "LLM response quality saturates as a function of prompt length, following task-specific
> logarithmic and sigmoid curves. Beyond identifiable thresholds, additional prompt tokens
> yield no quality gain."

### Proposed Structure

1. **Introduction** — Prompts are getting longer. Is this helping?
2. **Methodology** — 7 models, 4 tasks, 7 controlled additive prompt levels, 20 examples each. Two independent quality evaluation methods that agree at r=0.986.
3. **Main Result: Saturation Curves** — Quality follows log/sigmoid. Saturation points: QA ~8–43 tokens, classification ~38–164, summarization ~69–104, instruction-following ~15–112.
4. **Finding: Stronger Models Saturate Earlier** — Gemini-flash QA at 8 tokens vs. Llama-8b at 43.
5. **Finding: Optimal Strategy Is Model-Specific** — Universality=0.000 across 7 models (RQ5/RQ6).
6. **Practical Implication** — "Be concise" suffix captures most optimization benefit (RQ8, caveat: weak evidence).
7. **Discussion** — Limitations, implications for prompt engineering, connection to scaling laws.

### Key Reviewer Risk

A reviewer may ask: "Are your 7 additive levels adding *relevant* information or just fluff?"
If the higher levels pad with irrelevant verbosity, saturation is obvious. The paper must show
each level adds genuinely useful instructions/context. Check `experiments/saturation_prompts.py`.
