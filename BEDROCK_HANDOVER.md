# Bedrock Handover: Finish llama-3.3-70b Repeated Runs

## What needs to happen

Run the remaining **543 repeated-run experiments** for `llama-3.3-70b` using AWS Bedrock instead of Groq (Groq's 100k tokens/day limit is exhausted).

These are stability/reproducibility runs: same model, same prompts, same examples — just re-run to show results are consistent across runs.

## Current state

- File: `results/rebuttal_v2/repeated_runs.json`
- llama-3.3-70b has **297/840** good records (run_id=1: 297/420, run_id=2: 0/420)
- Other models (llama-3.1-8b, gemini-flash) are **complete** — don't touch them
- Error records have been cleaned; `--resume` will skip existing good records

## What to implement

### 1. Add a BedrockProvider to `greenprompt/llm.py`

It must implement the same `LLMProvider` interface as the other providers. Key method:

```python
def generate(self, prompt: str, max_tokens: int = 512) -> LLMResponse
```

`LLMResponse` has three fields: `text`, `input_tokens`, `output_tokens`.

Use `boto3` with `bedrock-runtime` client and the `converse` API. Bedrock model ID for llama-3.3-70b: `meta.llama3-3-70b-instruct-v1:0`.

Look at existing providers in `greenprompt/llm.py` for the pattern — they're simple wrappers.

### 2. Add a Bedrock model config to `experiments/saturation_benchmark.py`

Add to `MODEL_CONFIGS`:

```python
'llama-3.3-70b-bedrock': {
    'provider_cls': BedrockProvider,
    'model': 'meta.llama3-3-70b-instruct-v1:0',
    'env_key': None,  # uses boto3 default credentials
}
```

Also add `'llama-3.3-70b-bedrock'` to the argparse model choices.

### 3. Run the experiments

**Important:** The output records must have `"model": "llama-3.3-70b"` (not `"llama-3.3-70b-bedrock"`) so they merge correctly with the existing 297 records. Either:
- (a) Name the config `llama-3.3-70b` and point it at Bedrock, or
- (b) Post-process the JSON to rename the model field

Option (a) is simpler — just temporarily change the existing `llama-3.3-70b` config to use `BedrockProvider`.

Commands to run:

```bash
# Run 1 (will resume from 297/420, so ~123 remaining)
python3 experiments/saturation_benchmark.py \
    --models llama-3.3-70b \
    --tasks classification product_extraction instruction_following \
    --evaluator llm_judge \
    --output results/rebuttal_v2/repeated_runs.json \
    --delay 2.0 --run-id 1 --resume

# Run 2 (full 420 runs)
python3 experiments/saturation_benchmark.py \
    --models llama-3.3-70b \
    --tasks classification product_extraction instruction_following \
    --evaluator llm_judge \
    --output results/rebuttal_v2/repeated_runs.json \
    --delay 2.0 --run-id 2 --resume
```

### 4. Judge calls

The judge (`gpt-4o-mini` via OpenAI) is separate from the model provider. It needs `OPENAI_API_KEY` set in `.env`. The user has loaded credits into their OpenAI account.

## Key files

| File | Role |
|------|------|
| `greenprompt/llm.py` | LLM provider classes — add `BedrockProvider` here |
| `experiments/saturation_benchmark.py` | Benchmark runner — add Bedrock model config here |
| `experiments/saturation_prompts.py` | Prompt templates (read-only, don't modify) |
| `greenprompt/evaluators.py` | Evaluators including LLM judge (read-only) |
| `results/rebuttal_v2/repeated_runs.json` | Output file (append to existing) |
| `.env` | API keys (needs OPENAI_API_KEY for judge) |

## Verification

After both runs complete, verify:

```python
import json
with open('results/rebuttal_v2/repeated_runs.json') as f:
    data = json.load(f)
good = [r for r in data if 'error' not in r]
l70 = [r for r in good if r['model'] == 'llama-3.3-70b']
by_run = {}
for r in l70:
    by_run[r.get('run_id',0)] = by_run.get(r.get('run_id',0), 0) + 1
# Should show: run_id=1: 420/420, run_id=2: 420/420
for rid in [1, 2]:
    print(f'run_id={rid}: {by_run.get(rid, 0)}/420')
```

## Don't touch

- Any other result files
- Paper files in `paper_acml/` or root (`sec_*.tex`)
- The llama-3.1-8b or gemini-flash records in `repeated_runs.json`
