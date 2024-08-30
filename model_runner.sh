#!/bin/bash

MODELS_TOGETHER_AI=(
	"Meta-Llama-3.1-70B-Instruct-Turbo"
	"Qwen2-72B-Instruct"
	"gemma-2-27b-it"
	"Mixtral-8x22B-Instruct-v0.1"
)

MODELS_GOOGLE=(
	"gemini-1.0-pro-002"
)

MODELS_CLAUDE=(
	"claude-3-5-sonnet-20240620"
)

EXPERIMENTS=(
	"full_game"
	"full_no_special_cards"
	"short_no_reprompting"
	"short_pos1_easy"
	"short_pos1_hard"
	"short_pos2_easy"
	"short_pos2_hard"
	"short_pos3_easy"
	"short_pos3_hard"
)

function make_run_with_models() {
  # Convert argument list into a local array
  local MODELS=("$@")
  
  for model in "${MODELS[@]}"; do
    # first make the single run with the programmatic player
    # python3 scripts/cli.py run -g wizardsapprentice -e full_programmatic2 -m "$model" programmatic programmatic
    echo "Make programmatic run with: $model"
  
    # next: start a loop over all experiments
    for experiment in "${EXPERIMENTS[@]}"; do
      # now make a run for each experiment with the custom player
      # python3 scripts/cli.py run -g wizardsapprentice -e $experiment -m $model custom custom
      echo "Make custom run with: $model for $experiment."

    done
  done
}


# Make the runs with together ai models
echo "cp key_togetherai.json key.json"
make_run_with_models "${MODELS_TOGETHER_AI[@]}"

# Make the runs with google models
echo "cp key_google.json key.json"
make_run_with_models "${MODELS_GOOGLE[@]}"

# Make the runs with claude models
echo "cp key_claude.json key.json"
make_run_with_models "${MODELS_CLAUDE[@]}"


