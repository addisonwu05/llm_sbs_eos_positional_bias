#!/bin/bash
# ======================================================
# Run every EoS + SbS experiment (standard and interleaved-verdict)
# in both evidence orders (DP, PD) for every model on one case.
# Parallel across models; within a model, DP and PD run in parallel.
# API keys are read from .env (see .env.example).
# Usage: bash scripts/run_all.sh [case_dir]
#   case_dir defaults to cases/murder
# ======================================================

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CASE_DIR="${1:-$REPO_DIR/cases/murder}"

EOS_SCRIPT="$REPO_DIR/eos.py"
SBS_SCRIPT="$REPO_DIR/sbs.py"
NUM_RUNS=30
LOG_DIR="$CASE_DIR/logs"
mkdir -p "$LOG_DIR"

# Edit this list to run a subset. Some older models may since have been retired by their providers.
MODELS=(
  "gpt-3.5-turbo" "gpt-4o" "gpt-5" "gpt-5.4"
  "claude-3-haiku-20240307" "claude-3-5-haiku-20241022" "claude-3-7-sonnet-20250219"
  "claude-sonnet-4-20250514" "claude-sonnet-4-6"
  "gemini-2.0-flash" "gemini-2.5-flash" "gemini-3-flash-preview"
  "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
  "Qwen/Qwen2.5-72B-Instruct-Turbo"
)

# Runs one experiment variant in both orders: DP and PD in parallel
run_model() {
  local model=$1
  local script=$2
  local exp_type=$3
  local extra_args="${4:-}"

  echo "======================================"
  echo "Running $exp_type for $model"
  echo "======================================"

  python3 "$script" --model "$model" --num_runs "$NUM_RUNS" --defend_then_prosecute --case_dir "$CASE_DIR" $extra_args &
  python3 "$script" --model "$model" --num_runs "$NUM_RUNS" --case_dir "$CASE_DIR" $extra_args &
  wait
}

# Runs all 4 experiment variants for a single model, sequentially
run_model_all() {
  local model=$1
  run_model "$model" "$EOS_SCRIPT" "EoS"               ""
  run_model "$model" "$SBS_SCRIPT" "SbS"               ""
  run_model "$model" "$EOS_SCRIPT" "EoS (interleaved)" "--interleave_verdict"
  run_model "$model" "$SBS_SCRIPT" "SbS (interleaved)" "--interleave_verdict"
}

for model in "${MODELS[@]}"; do
  log_file="$LOG_DIR/${model//\//_}.log"
  echo "  -> $model -> $log_file"
  run_model_all "$model" &> "$log_file" &
done

wait

echo "All experiments completed."
echo "Logs saved in: $LOG_DIR"
