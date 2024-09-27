# Wizard's Apprentice

Wizard's Apprentice is a multi-player, trick-taking card game. Each trick a card must be played in order to collect the trick and thus points. At the beginning of the round every player makes a prediction how many cards they think they will win. The goal is to meet this prediction.

# How to sample new instances

Change the seed that is set in instancegenerator.py and run the script afterwards. New randomly set cards and seating orders will be generated.

# How to create a new experiment

The instancegenerator.py accepts different settings in order to make a specific set of rules. The settings are determined as a json file in [ressources/experiment-settings](./ressources/experiment-settings/). The name of the json-file must be declared in instancegenerator.py.

# Resources
* [experiment_settings](./ressources/experiment_settings): contains the settings for all experiments as described above
* [prompts](./ressources/prompts/): contains the prompt-templates used during the game
