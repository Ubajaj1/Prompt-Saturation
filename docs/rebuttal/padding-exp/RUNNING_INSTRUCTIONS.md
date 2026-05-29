# Running the Padding Control Experiment

## Prerequisites

1. Python 3.11+
2. API keys for the LLM providers (see below)
3. The project repository

## Setup

```bash
# Clone/pull the repo
cd Prompt-Saturation-main

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies (use public PyPI if on a corporate machine)
pip install --index-url https://pypi.org/simple/ --trusted-host pypi.org \
    "numpy<2" "pandas<2.1" "scipy>=1.10,<1.12" \
    "python-dotenv>=1.0.0" "openai>=1.0.0" "anthropic>=0.18.0" \
    "groq>=0.4.0" "google-genai>=1.0.0" "matplotlib>=3.7.0" "seaborn>=0.12.0"
```

## Verify Setup (No API Keys Needed)

Before running with real keys, verify the code works end-to-end using the mock test:

```bash
source .venv/bin/activate
python tests/test_padding_control.py
```

This runs 5 tests using mock providers (no API calls). You should see:

```
  ALL TESTS PASSED ✓
```

If this passes, the code is working correctly and you're ready to run with real keys.

## API Keys

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your actual keys:

```
GROQ_API_KEY=your-groq-key       # Free tier, 30 RPM — for llama-3.1-8b, llama-3.3-70b, qwen3-32b
GEMINI_API_KEY=your-gemini-key   # Free tier, 60 RPM — for gemini-flash AND the LLM judge
ANTHROPIC_API_KEY=your-anthropic-key  # Paid — for claude-haiku
```

**Required keys:**
- `GROQ_API_KEY` — needed for llama-3.1-8b, llama-3.3-70b, qwen3-32b
- `GEMINI_API_KEY` — needed for gemini-flash model AND the judge (gemini-2.0-flash)
- `ANTHROPIC_API_KEY` — needed for claude-haiku

**Note:** The judge model is always gemini-2.0-flash (uses GEMINI_API_KEY). This is the same judge used in the other rebuttal experiments for consistency.

## Running the Experiment

### Full run (recommended)

```bash
source .venv/bin/activate

python experiments/rebuttal_padding_control.py \
    --models gemini-flash llama-3.3-70b llama-3.1-8b qwen3-32b claude-haiku \
    --tasks classification product_extraction \
    --delay 2.0 \
    --resume
```

**Estimated time:** ~2-3 hours at 2.0s delay (1,470 generation + 1,470 judge calls).

**Estimated cost:**
- Groq models: free (rate-limited)
- Gemini (model + judge): free tier
- Claude-haiku: ~$0.50-1.00 (small prompts, 7 examples × 7 levels × 3 padding types = 147 calls)

### If you hit rate limits

The script has built-in retry logic for 429 errors. If Groq's daily limit is hit:

```bash
# Run one model at a time, resume next day
python experiments/rebuttal_padding_control.py \
    --models llama-3.1-8b \
    --delay 3.0 --resume

# Next day
python experiments/rebuttal_padding_control.py \
    --models llama-3.3-70b \
    --delay 3.0 --resume

# etc.
```

The `--resume` flag skips already-completed experiments, so you can stop and restart freely.

### Partial run (if budget is tight)

If you can only run a subset, prioritize:

```bash
# Minimum viable: 2 models, 1 task, all 3 padding types
python experiments/rebuttal_padding_control.py \
    --models llama-3.3-70b qwen3-32b \
    --tasks product_extraction \
    --delay 2.0 --resume
```

Product extraction is the priority because it's the task with the clearest saturation signal in the real experiment. llama-3.3-70b and qwen3-32b are the models with the strongest ablation results (13/15 significant fits across orderings).

### Quick test (verify setup works)

```bash
# Run just 1 model, 1 task to verify everything connects
python experiments/rebuttal_padding_control.py \
    --models gemini-flash \
    --tasks classification \
    --padding-types irrelevant_facts \
    --delay 1.0
```

This runs 49 experiments (7 levels × 7 examples) and should complete in ~3 minutes.

## Output

Results are saved incrementally to:
```
results/rebuttal/padding_control_results.json
```

Each record looks like:
```json
{
    "model": "gemini-flash",
    "task": "classification",
    "padding_type": "irrelevant_facts",
    "level": 4,
    "example_id": 0,
    "prompt_tokens": 152,
    "output_tokens": 3,
    "response_text": "positive",
    "quality": 0.95,
    "completed": true,
    "timestamp": "2026-05-29T..."
}
```

## Analysis

After the experiment completes:

```bash
# Basic analysis
python experiments/rebuttal_padding_control.py --analyze-only

# With comparison to real saturation results
python experiments/rebuttal_padding_control.py --analyze-only --compare
```

This produces `results/rebuttal/padding_control_analysis.json` with:
- Mean quality at each level per (model, task, padding_type)
- Spearman correlation tests (is there a significant trend?)
- L1→L7 quality deltas
- Comparison with real experiment deltas (if `--compare`)

## What to Look For

**Expected result:** Quality should be approximately flat across levels for all padding conditions.

Key numbers to report:
1. **Mean L1→L7 delta** across all conditions — should be near 0 (vs. +0.10 to +0.16 in real experiment)
2. **Number of significant trends** — should be 0/30 or very few (vs. 7/14 significant in real experiment)
3. **Comparison table** — real delta vs. padding delta per model

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'dotenv'` | Run `pip install python-dotenv` in your venv |
| `Missing env var 'GROQ_API_KEY'` | Check your `.env` file exists and has the key |
| `429 rate limit` | Script auto-retries; increase `--delay` if persistent |
| `insufficient_quota` | You've hit a hard limit; wait 24h or use a different key |
| Script crashes mid-run | Just re-run with `--resume` — it picks up where it left off |

## Files to Share Back

After running, please share:
1. `results/rebuttal/padding_control_results.json` (raw data)
2. `results/rebuttal/padding_control_analysis.json` (analysis output)
3. Terminal output from the `--analyze-only --compare` run
