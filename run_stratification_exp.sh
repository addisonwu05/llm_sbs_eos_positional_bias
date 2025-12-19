#!/bin/bash

# ===== MODEL FAMILIES =====
gpt_models=("gpt-4o")
gpt_models=("gpt-5")

claude_models=("claude-sonnet-4-20250514",claude-3-7-sonnet-20250219,claude-3-5-haiku-20241022,claude-3-haiku-20240307)
gemini_models=("gemini-2.5-flash","gemini-2.0-flash")
size_ablation_models=("gpt-3.5-turbo" "claude-3-haiku-20240307" "gemini-2.0-flash")

# ===== PROMPT VARIANTS =====
flag_combinations=(
    "--direct"      # direct
    ""              # CoT (default)
)

refugee_flag_combinations=(
    ""
    "--set_age"
    "--set_education"
    "--set_age --set_education"
)

refugee_flag_combinations_clean=( # we already have the default results from the protected features experiment
    "--set_hair"
    "--set_tattoo"
    "--set_hair --set_tattoo"
)

# ===== PROBABILITIES TO TEST =====
probabilities=("0.1" "0.9" "1.0")

# ===== TASK FUNCTIONS (per single model) =====
run_model_fake() {
    local model="$1"
    for p in "${probabilities[@]}"; do
        for flags in "${flag_combinations[@]}"; do
            echo "Running: $model $flags p=$p fake"
            python stratification_exp.py --model "$model" --num_runs 30 --num_hiring_rounds 40 \
                --probability_success "$p" $flags
        done
    done
}

run_model_realistic_probs() {
    local model="$1"
    for flags in "${flag_combinations[@]}"; do
        echo "Running: $model $flags realistic_probs"
        python stratification_exp.py --model "$model" --num_runs 30 --num_hiring_rounds 40 \
            --realistic_probs $flags
    done
}

run_model_diversity() {
    local model="$1"
    for flags in "${flag_combinations[@]}"; do
        echo "Running: $model $flags diversity"
        python stratification_exp.py --model "$model" --num_runs 30 --num_hiring_rounds 40 \
            --diversity_reward $flags
    done
}

run_model_diversity_no_reward_signal() {
    local model="$1"
    for flags in "${flag_combinations[@]}"; do
        echo "Running: $model $flags diversity_no_reward_signal"
        python stratification_exp.py --model "$model" --num_runs 30 --num_hiring_rounds 40\
            --diversity_reward --no_reward_signal $flags
    done
}

run_model_diversity_system_prompt() {
    local model="$1"
    for flags in "${flag_combinations[@]}"; do
        echo "Running: $model $flags diversity_system_prompt"
        python stratification_exp.py --model "$model" --num_runs 30 --num_hiring_rounds 40\
            --diversity_system_prompt $flags
    done
}

run_model_implicit_fairness_steer() {
    local model="$1"
    for flags in "${flag_combinations[@]}"; do
        echo "Running: $model $flags implicit_fairness_steer"
        python stratification_exp.py --model "$model" --num_runs 30 --num_hiring_rounds 40\
            --implicit_fairness_steer $flags
    done
}

run_model_diverse_city() {
    local model="$1"
    for flags in "${flag_combinations[@]}"; do
        echo "Running: $model $flags implicit_fairness_steer"
        python stratification_exp.py --model "$model" --num_runs 30 --num_hiring_rounds 40\
            --diverse_city $flags
    done
}

run_model_robustness_variants() {
    local model="$1"
    for flags in "${flag_combinations[@]}"; do
        echo "Running: $model $flags robustness only"
        python stratification_exp.py --model "$model" --num_runs 30 --num_hiring_rounds 40 \
            --robustness_check --probability_success 0.9 $flags

        echo "Running: $model $flags robustness + diversity"
        python stratification_exp.py --model "$model" --num_runs 30 --num_hiring_rounds 40 \
            --robustness_check --diversity_reward --probability_success 0.9 $flags
    done
}

run_model_resettlement_exps() {
    local model="$1"
    for prompt_flags in "${flag_combinations[@]}"; do
      for profile_flags in "${refugee_flag_combinations[@]}"; do
        echo "Running: $model $prompt_flags $profile_flags resettlement experiment"
        python stratification_exp.py --model "$model" --num_runs 30 --num_hiring_rounds 40 \
          --real_demographics --resettlement $profile_flags $prompt_flags
      done
    done
}

run_model_resettlement_exps_neutral() {
    local model="$1"
    for prompt_flags in "${flag_combinations[@]}"; do
      for profile_flags in "${refugee_flag_combinations_clean[@]}"; do
        echo "Running: $model $prompt_flags $profile_flags resettlement experiment"
        python stratification_exp.py --model "$model" --num_runs 30 --num_hiring_rounds 40 \
          --use_neutral_features --real_demographics --resettlement $profile_flags $prompt_flags
      done
    done
}

run_all_tasks_for_model() {
  local model="$1"
  run_model_fake "$model"
  run_model_realistic_probs "$model"
  run_model_diversity "$model"
  run_model_diversity_no_reward_signal "$model"
  #run_model_diversity_system_prompt "$model"
  run_model_implicit_fairness_steer "$model"
  run_model_robustness_variants "$model"
  run_model_resettlement_exps "$model"
  run_model_diverse_city "$model"
  run_model_resettlement_exps_neutral "$model"
}

run_family_serially() {
  local models=("$@")
  for model in "${models[@]}"; do
    run_all_tasks_for_model "$model"
  done
}

run_ablation_fake_only() {
  local models=("$@")
  for model in "${models[@]}"; do
    echo "Running: $model (size ablation) p=0.9 fake (default prompt only)"
    python stratification_exp.py --model "$model" --num_runs 30 --num_hiring_rounds 40 
    python stratification_exp.py --model "$model" --num_runs 30 --num_hiring_rounds 40 --direct
  done
}

# === PARALLEL EXECUTION: One process per family ===
(run_family_serially "${gpt_models[@]}") &
(run_family_serially "${gemini_models[@]}") &
(run_family_serially "${claude_models[@]}") &
(run_family_serially "${together_models[@]}") &

wait 

(run_ablation_fake_only "${size_ablation_models[@]}")

wait

# Ablations
#python stratification_exp.py --model gpt-4o --direct --alter_temperature --temperature 1.5; python stratification_exp.py --model gpt-4o --alter_temperature --temperature 1.5

echo "✅ All experiments complete."