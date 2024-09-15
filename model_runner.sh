#!/bin/bash

MODELS=(
	#DONE "Meta-Llama-3.1-70B-Instruct-Turbo"
	"Qwen2-72B-Instruct"
	#DONE "gemma-2-27b-it"
	#DONE "Mixtral-8x22B-Instruct-v0.1"
	#DONE "gemini-1.0-pro-002"
	#OUT "claude-3-5-sonnet-20240620"
)

EXPERIMENTS=(
	# "full_game"
	# "full_no_special_cards"
	# "short_no_reprompting"
	# "short_pos1_easy"
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
	# echo "Make programmatic run with: $model"
    # # python3 scripts/cli.py run -g wizardsapprentice -e full_programmatic2 -m "$model" programmatic programmatic
  
    # next: start a loop over all experiments
    for experiment in "${EXPERIMENTS[@]}"; do
	  	# now make a run for each experiment with the custom player
		echo "Make custom run with: $model for $experiment."
      	python3 -u scripts/cli.py run -g wizardsapprentice -e $experiment -m $model custom custom
      
    done
  done
}

make_run_with_models "${MODELS[@]}"
