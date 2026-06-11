#!/bin/bash
# Run all rebuttal experiments sequentially in background-safe mode.
# Usage: tmux new -s rebuttal 'caffeinate -s bash run_rebuttal_experiments.sh'
#
# Experiments:
#   1. NER held-out task: 6 models × 7 levels × 20 examples = 840 calls
#   2. Hard examples: 3 models × 3 tasks × 7 levels × 20 examples = 1,260 calls
#   3. Repeated run 1: 3 models × 3 tasks × 7 levels × 20 examples = 1,260 calls
#   4. Repeated run 2: 3 models × 3 tasks × 7 levels × 20 examples = 1,260 calls
# Total: ~4,620 calls (+judge calls)
# Estimated time: ~4-5 hours (Groq 30 RPM is the bottleneck)
#
# Note: kimi-k2 dropped (deprecated on Groq), gpt-4o-mini skipped for now (quota)

cd "$(dirname "$0")"

NER_MODELS="llama-3.1-8b llama-3.3-70b qwen3-32b claude-haiku gemini-flash"
REP_MODELS="llama-3.1-8b llama-3.3-70b gemini-flash"

echo "=========================================="
echo "REBUTTAL EXPERIMENTS — $(date)"
echo "=========================================="

# --- Experiment 1: NER held-out task (6 models, no kimi-k2/gpt-4o-mini) ---
echo ""
echo "[1/4] NER held-out task (6 models × 7 levels × 20 examples)"
echo "Started: $(date)"
python3 experiments/saturation_benchmark.py \
    --models $NER_MODELS \
    --tasks ner \
    --evaluator llm_judge \
    --output results/rebuttal_v2/ner_held_out.json \
    --delay 2.5 \
    --resume || echo "[1/4] NER finished with errors at $(date)"
echo "[1/4] NER done: $(date)"

# --- Experiment 2: Hard examples (3 models, free-tier only) ---
echo ""
echo "[2/4] Hard examples (3 models × 3 hard tasks × 7 levels × 20 examples = 1,260)"
echo "Started: $(date)"
python3 experiments/saturation_benchmark.py \
    --models $REP_MODELS \
    --tasks math_reasoning_hard qa_hard instruction_following_hard \
    --evaluator llm_judge \
    --output results/rebuttal_v2/hard_examples_results.json \
    --delay 2.5 \
    --resume || echo "[2/4] Hard examples finished with errors at $(date)"
echo "[2/4] Hard examples done: $(date)"

# --- Experiment 3: Repeated runs — run 1 (3 models) ---
echo ""
echo "[3/4] Repeated runs — run_id=1 (3 models × 3 tasks × 7 levels × 20 examples = 1,260)"
echo "Started: $(date)"
python3 experiments/saturation_benchmark.py \
    --models $REP_MODELS \
    --tasks classification product_extraction instruction_following \
    --evaluator llm_judge \
    --output results/rebuttal_v2/repeated_runs.json \
    --delay 2.5 \
    --run-id 1 \
    --resume || echo "[3/4] Run 1 finished with errors at $(date)"
echo "[3/4] Run 1 done: $(date)"

# --- Experiment 4: Repeated runs — run 2 (3 models) ---
echo ""
echo "[4/4] Repeated runs — run_id=2 (3 models × 3 tasks × 7 levels × 20 examples = 1,260)"
echo "Started: $(date)"
python3 experiments/saturation_benchmark.py \
    --models $REP_MODELS \
    --tasks classification product_extraction instruction_following \
    --evaluator llm_judge \
    --output results/rebuttal_v2/repeated_runs.json \
    --delay 2.5 \
    --run-id 2 \
    --resume || echo "[4/4] Run 2 finished with errors at $(date)"
echo "[4/4] Run 2 done: $(date)"

echo ""
echo "=========================================="
echo "ALL EXPERIMENTS COMPLETE — $(date)"
echo "=========================================="
echo "Output files:"
echo "  results/rebuttal_v2/ner_held_out.json"
echo "  results/rebuttal_v2/hard_examples_results.json"
echo "  results/rebuttal_v2/repeated_runs.json"
