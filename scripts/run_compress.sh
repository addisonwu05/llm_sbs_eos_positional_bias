#!/bin/bash
# ======================================================
# Run the SbS-Compressed ablation in both evidence orders (DP, PD)
# for every model on one case.
# Parallel across models; within a model, DP and PD run in parallel.
# API keys are read from .env (see .env.example).
# Usage: bash scripts/run_compress.sh [case_dir]
#   case_dir defaults to cases/murder
# ======================================================

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CASE_DIR="${1:-$REPO_DIR/cases/murder}"

SBS_SCRIPT="$REPO_DIR/sbs.py"
NUM_RUNS=30
LOG_DIR="$CASE_DIR/logs_compress"
mkdir -p "$LOG_DIR"

# Edit this list to run a subset. Some older models may since have been retired by their providers.
MODELS=(
  "gpt-3.5-turbo" "gpt-4o" "gpt-5.4"
  "claude-sonnet-4-20250514" "claude-sonnet-4-6"
  "gemini-2.0-flash" "gemini-2.5-flash" "gemini-3-flash-preview"
  "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
  "Qwen/Qwen2.5-72B-Instruct-Turbo"
)

# Runs SbS-Compressed in both orders: DP and PD in parallel
run_model() {
  local model=$1

  echo "======================================"
  echo "Running SbS (compress) for $model"
  echo "======================================"

  python3 "$SBS_SCRIPT" --model "$model" --num_runs "$NUM_RUNS" --defend_then_prosecute --case_dir "$CASE_DIR" --compress &
  python3 "$SBS_SCRIPT" --model "$model" --num_runs "$NUM_RUNS" --case_dir "$CASE_DIR" --compress &
  wait
}

for model in "${MODELS[@]}"; do
  log_file="$LOG_DIR/${model//\//_}.log"
  echo "  -> $model -> $log_file"
  run_model "$model" &> "$log_file" &
done

wait

echo "All compress experiments completed."
echo "Logs saved in: $LOG_DIR"
