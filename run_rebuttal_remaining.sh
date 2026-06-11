#!/bin/bash
# Run remaining experiments skipping llama-3.3-70b (daily Groq quota hit)
cd "$(dirname "$0")"

MODELS="llama-3.1-8b gemini-flash"

echo "=========================================="
echo "REMAINING EXPERIMENTS (skip llama-3.3-70b) — $(date)"
echo "=========================================="

# --- Repeated runs — run 1 ---
echo ""
echo "[1/2] Repeated runs — run_id=1 (2 models × 3 tasks)"
echo "Started: $(date)"
python3 experiments/saturation_benchmark.py \
    --models $MODELS \
    --tasks classification product_extraction instruction_following \
    --evaluator llm_judge \
    --output results/rebuttal_v2/repeated_runs.json \
    --delay 2.5 \
    --run-id 1 \
    --resume || echo "[1/2] finished with errors at $(date)"
echo "[1/2] Run 1 done: $(date)"

# --- Repeated runs — run 2 ---
echo ""
echo "[2/2] Repeated runs — run_id=2 (2 models × 3 tasks)"
echo "Started: $(date)"
python3 experiments/saturation_benchmark.py \
    --models $MODELS \
    --tasks classification product_extraction instruction_following \
    --evaluator llm_judge \
    --output results/rebuttal_v2/repeated_runs.json \
    --delay 2.5 \
    --run-id 2 \
    --resume || echo "[2/2] finished with errors at $(date)"
echo "[2/2] Run 2 done: $(date)"

echo ""
echo "=========================================="
echo "DONE — $(date)"
echo "=========================================="
