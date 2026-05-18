#!/bin/bash
# ======================================================
# Run all EoS + SbS experiments for all model families
# Parallel across AND within families (one key per model)
# Usage: bash scripts/modelruns.sh [case_dir]
#   case_dir defaults to cases/murder
# ======================================================

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CASE_DIR="${1:-$REPO_DIR/cases/murder}"

EOS_SCRIPT="$REPO_DIR/eos.py"
SBS_SCRIPT="$REPO_DIR/sbs.py"
NUM_RUNS=30
LOG_DIR="$CASE_DIR/logs"
mkdir -p "$LOG_DIR"

# ---- Load .env (handles "KEY = VALUE" with spaces around =) ----
while IFS='=' read -r key value; do
    [[ -z "$key" || "$key" == \#* ]] && continue
    key="${key// /}"        # strip spaces from key
    value="${value# }"      # strip one leading space from value
    [[ -z "$key" || -z "$value" ]] && continue
    export "$key=$value"
done < "$REPO_DIR/.env"

# ---- Define model families + one key per model ----
# Add more keys to unlock parallelism within a family.
# If fewer keys than models, extras fall back to the first key.

gpt_models=(   "gpt-3.5-turbo"  "gpt-4o"           "gpt-5"              "gpt-5.4"            )
gpt_keys=(     "$OpenAI_API_KEY" "$OpenAI_API_KEY_2" "$OpenAI_API_KEY_3"  "$OpenAI_API_KEY_4"  )

claude_models=( "claude-sonnet-4-6"    "claude-sonnet-4-20250514" ) #"claude-3-7-sonnet-20250219" "claude-3-5-haiku-20241022" "claude-3-haiku-20240307" )
claude_keys=(   "$Anthropic_API_KEY"   "$Anthropic_API_KEY_2" )    #"$Anthropic_API_KEY_3"       "$Anthropic_API_KEY_4"                                )

gemini_models=( "gemini-3-flash-preview" "gemini-2.5-flash"  "gemini-2.0-flash"  )
gemini_keys=(   "$Gemini_API_KEY"        "$Gemini_API_KEY_2" "$Gemini_API_KEY_3" )

llama_models=("cocoscilab/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8-808e2c49")
llama_keys=("$Together_API_KEY_Llama")

qwen_models=("cocoscilab/Qwen/Qwen2.5-72B-Instruct-Turbo-73999f7a")
qwen_keys=("$Together_API_KEY_Qwen")

# ---- Core runner ----
run_model() {
  local model=$1
  local script=$2
  local exp_type=$3
  local extra_args="${4:-}"
  local api_key="${5:-}"
  local key_arg=""
  [ -n "$api_key" ] && key_arg="--api_key $api_key"

  echo "======================================"
  echo "Running $exp_type for $model"
  echo "======================================"

  echo "Running DP..."
  python3 "$script" --model "$model" --num_runs "$NUM_RUNS" --defend_then_prosecute --case_dir "$CASE_DIR" $extra_args $key_arg

  echo "Running PD..."
  python3 "$script" --model "$model" --num_runs "$NUM_RUNS" --case_dir "$CASE_DIR" $extra_args $key_arg
}

# Runs all 4 experiment variants for a single model, sequentially
run_model_all() {
  local model=$1
  local api_key=$2
  run_model "$model" "$EOS_SCRIPT" "EoS"               ""                    "$api_key"
  run_model "$model" "$SBS_SCRIPT" "SbS"               ""                    "$api_key"
  run_model "$model" "$EOS_SCRIPT" "EoS (interleaved)" "--interleave_verdict" "$api_key"
  run_model "$model" "$SBS_SCRIPT" "SbS (interleaved)" "--interleave_verdict" "$api_key"
}

# Runs a family: each model in parallel, each with its own key
# Uses eval instead of local -n for bash 3.x compatibility (macOS default)
run_family() {
  local family_name=$1
  local models_ref=$2
  local keys_ref=$3

  eval "models_arr=(\"\${${models_ref}[@]}\")"
  eval "keys_arr=(\"\${${keys_ref}[@]}\")"

  local count=${#models_arr[@]}
  echo "Starting $family_name family ($count models in parallel)"

  for i in "${!models_arr[@]}"; do
    local model="${models_arr[$i]}"
    local key="${keys_arr[$i]:-${keys_arr[0]}}"    # fall back to first key if not enough
    local safe="${model//\//_}"
    local log_file="$LOG_DIR/${family_name}_${safe}.log"

    echo "  -> $model -> $log_file"
    run_model_all "$model" "$key" &> "$log_file" &
  done

  wait
  echo "Finished $family_name family."
}

# ---- Run families in parallel ----
run_family "gpt"    gpt_models    gpt_keys    &
run_family "claude" claude_models claude_keys &
run_family "gemini" gemini_models gemini_keys &
run_family "llama"  llama_models  llama_keys  &
run_family "qwen"   qwen_models   qwen_keys   &

wait

echo "All experiments completed successfully."
echo "Logs saved in: $LOG_DIR"
