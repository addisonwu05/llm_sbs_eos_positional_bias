#!/bin/bash
# ======================================================
# Run SbS compress experiments for all model families
# Parallel: across families, within families (one key per model),
#           and within each model (DP vs PD use separate keys)
# Usage: bash scripts/modelruns_compress.sh [case_dir]
#   case_dir defaults to cases/murder
# ======================================================

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CASE_DIR="${1:-$REPO_DIR/cases/murder}"

SBS_SCRIPT="$REPO_DIR/sbs.py"
NUM_RUNS=30
LOG_DIR="$CASE_DIR/logs_compress"
mkdir -p "$LOG_DIR"

# ---- Load .env (handles "KEY = VALUE" with spaces around =) ----
while IFS='=' read -r key value; do
    [[ -z "$key" || "$key" == \#* ]] && continue
    key="${key// /}"        # strip spaces from key
    value="${value# }"      # strip one leading space from value
    [[ -z "$key" || -z "$value" ]] && continue
    export "$key=$value"
done < "$REPO_DIR/.env"

# ---- Define model families ----
gpt_models=(    "gpt-3.5-turbo"       "gpt-4o"               "gpt-5.4"              )
gpt_keys_dp=(   "$OpenAI_API_KEY"     "$OpenAI_API_KEY_2"    "$OpenAI_API_KEY_3"    )
gpt_keys_pd=(   "$OpenAI_API_KEY_4"   "$OpenAI_API_KEY_5"    "$OpenAI_API_KEY_6"    )

claude_models=(  "claude-sonnet-4-6"   "claude-sonnet-4-20250514" )
claude_keys_dp=( "$Anthropic_API_KEY"  "$Anthropic_API_KEY_2"     )
claude_keys_pd=( "$Anthropic_API_KEY_3" "$Anthropic_API_KEY_4"    )

gemini_models=(  "gemini-3-flash-preview" "gemini-2.5-flash"   "gemini-2.0-flash"   )
gemini_keys_dp=( "$Gemini_API_KEY"        "$Gemini_API_KEY_2"  "$Gemini_API_KEY_3"  )
gemini_keys_pd=( "$Gemini_API_KEY_4"      "$Gemini_API_KEY_5"  "$Gemini_API_KEY_6"  )

llama_models=(  "cocoscilab/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8-808e2c49" )
llama_keys_dp=( "$Together_API_KEY_Llama"   )
llama_keys_pd=( "$Together_API_KEY_Llama_2" )

qwen_models=(  "cocoscilab/Qwen/Qwen2.5-72B-Instruct-Turbo-73999f7a" )
qwen_keys_dp=( "$Together_API_KEY_Qwen"   )
qwen_keys_pd=( "$Together_API_KEY_Qwen_2" )

# ---- Core runner ----
run_model() {
  local model=$1
  local exp_type=$2
  local extra_args="${3:-}"
  local key_dp="${4:-}"
  local key_pd="${5:-$key_dp}"

  local arg_dp="" arg_pd=""
  [ -n "$key_dp" ] && arg_dp="--api_key $key_dp"
  [ -n "$key_pd" ] && arg_pd="--api_key $key_pd"

  echo "======================================"
  echo "Running $exp_type for $model"
  echo "======================================"

  python3 "$SBS_SCRIPT" --model "$model" --num_runs "$NUM_RUNS" --defend_then_prosecute --case_dir "$CASE_DIR" --compress $extra_args $arg_dp &
  python3 "$SBS_SCRIPT" --model "$model" --num_runs "$NUM_RUNS" --case_dir "$CASE_DIR" --compress $extra_args $arg_pd &
  wait
}

# Runs SbS non-interleaved and interleaved compress variants for a single model
run_model_all() {
  local model=$1
  local key_dp=$2
  local key_pd=$3
  run_model "$model" "SbS (compress)" "" "$key_dp" "$key_pd"
}

# Runs a family: each model in parallel with its own dp/pd key pair
run_family() {
  local family_name=$1
  local models_ref=$2
  local dp_ref=$3
  local pd_ref=$4

  eval "models_arr=(\"\${${models_ref}[@]}\")"
  eval "dp_arr=(\"\${${dp_ref}[@]}\")"
  eval "pd_arr=(\"\${${pd_ref}[@]}\")"

  local count=${#models_arr[@]}
  echo "Starting $family_name family ($count models in parallel)"

  for i in "${!models_arr[@]}"; do
    local model="${models_arr[$i]}"
    local key_dp="${dp_arr[$i]:-${dp_arr[0]}}"
    local key_pd="${pd_arr[$i]:-}"
    local safe="${model//\//_}"
    local log_file="$LOG_DIR/${family_name}_${safe}.log"

    echo "  -> $model -> $log_file"
    run_model_all "$model" "$key_dp" "$key_pd" &> "$log_file" &
  done

  wait
  echo "Finished $family_name family."
}

# ---- Run families in parallel ----
run_family "gpt"    gpt_models    gpt_keys_dp    gpt_keys_pd    &
run_family "claude" claude_models claude_keys_dp claude_keys_pd &
run_family "gemini" gemini_models gemini_keys_dp gemini_keys_pd &
run_family "llama"  llama_models  llama_keys_dp  llama_keys_pd  &
run_family "qwen"   qwen_models   qwen_keys_dp   qwen_keys_pd   &

wait

echo "All compress experiments completed successfully."
echo "Logs saved in: $LOG_DIR"
