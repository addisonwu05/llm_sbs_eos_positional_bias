#!/bin/bash
# ======================================================
# Run all EoS + SbS experiments for all model families
# Parallel across GPT / Claude / Gemini
# Sequential within each family
# ======================================================

# ---- Define model families ----
#gpt_models=("gpt-3.5-turbo" "gpt-4o" "gpt-5")
#claude_models=("claude-sonnet-4-20250514" "claude-3-7-sonnet-20250219" "claude-3-5-haiku-20241022" "claude-3-haiku-20240307")
#gemini_models=("gemini-2.5-flash" "gemini-2.0-flash")
together_models=("Qwen/Qwen2.5-72B-Instruct-Turbo" "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8")

# ---- Paths to experiment scripts ----
EOS_SCRIPT="/Users/jasincekinmez/llm_sbs_eos_positional_bias/eos.py"
SBS_SCRIPT="/Users/jasincekinmez/llm_sbs_eos_positional_bias/sbs.py"

# ---- Config ----
NUM_RUNS=30
LOG_DIR="/Users/jasincekinmez/llm_sbs_eos_positional_bias/logs"
mkdir -p "$LOG_DIR"

# ---- Helper function ----
run_model() {
  local model=$1
  local script=$2
  local exp_type=$3

  echo "======================================"
  echo "▶️ Running $exp_type for $model"
  echo "======================================"

  echo "Running DP..."
  python3 "$script" --model "$model" --num_runs "$NUM_RUNS" --defend_then_prosecute

  echo "Running PD..."
  python3 "$script" --model "$model" --num_runs "$NUM_RUNS"
}

run_family() {
  local family_name=$1
  shift
  local models=("$@")
  local log_file="$LOG_DIR/${family_name}.log"

  echo "🚀 Starting $family_name family (logging to $log_file)"
  {
    for model in "${models[@]}"; do
      run_model "$model" "$EOS_SCRIPT" "EoS"
      run_model "$model" "$SBS_SCRIPT" "SbS"
    done
    echo "✅ Finished $family_name family."
  } &> "$log_file"
}

# ---- Run families in parallel ----
#run_family "gpt" "${gpt_models[@]}" &
#run_family "claude" "${claude_models[@]}" &
#run_family "gemini" "${gemini_models[@]}" &
run_family "together" "${together_models[@]}" &

# Wait for all background processes (families) to finish
wait

echo "🎉 All experiments completed successfully."
echo "📂 Logs saved in: $LOG_DIR"
