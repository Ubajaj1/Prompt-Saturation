# Prompt Saturation

**Quality Plateaus at Task-Specific Token Thresholds in Large Language Models**

Research code and data for the paper studying prompt saturation — the point at which
LLM response quality stops improving as prompt length increases.

## Key Findings

- **Structured-output tasks saturate**: classification at ~42–64 tokens, product extraction at ~92–536 tokens
- **Open-ended tasks do not saturate**: QA and math reasoning show no significant quality improvement from longer prompts
- **Stronger models saturate earlier**: requiring fewer instruction tokens to reach peak quality
- **Structured–open dichotomy**: task type, not prompt length, determines whether elaboration helps

## Repository Structure

```
greenprompt/          Core library
  evaluators.py         Task-specific quality evaluators (6 tasks)
  llm.py                LLM provider abstraction (OpenAI, Gemini, Groq, Anthropic)

experiments/          Benchmark and analysis
  saturation_prompts.py    7-level additive prompt templates × 6 tasks
  saturation_benchmark.py  Benchmark runner with LLM judge evaluation
  saturation_analysis.py   Curve fitting, F-tests, bootstrap CIs
  prompting_strategies.py  Task configs and 20 examples per task

results/              Figures, summary CSVs (raw JSON excluded via .gitignore)
paper/                COLM 2026 submission (LaTeX source + supplementary zip)
archive/              Deprecated modules with rationale
```

## Reproducing Results

```bash
# Install dependencies
pip install openai google-generativeai groq anthropic tiktoken scipy numpy matplotlib

# Set API keys
export OPENAI_API_KEY=...
export GEMINI_API_KEY=...
export GROQ_API_KEY=...
export ANTHROPIC_API_KEY=...

# Run saturation benchmark (7 models × 6 tasks × 7 levels × 20 examples)
python experiments/saturation_benchmark.py --evaluator llm_judge

# Run analysis (curve fitting, F-tests, figures)
python experiments/saturation_analysis.py
```

## Models Evaluated

| Model | Provider | Parameters |
|-------|----------|------------|
| llama-3.1-8b-instant | Groq | 8B |
| qwen/qwen3-32b | Groq | 32B |
| llama-3.3-70b-versatile | Groq | 70B |
| gemini-2.0-flash | Gemini | undisclosed |
| moonshotai/kimi-k2 | Groq | undisclosed |
| gpt-4o-mini | OpenAI | undisclosed |
| claude-haiku-4-5 | Anthropic | undisclosed |

## Citation

Paper under review at COLM 2026.
