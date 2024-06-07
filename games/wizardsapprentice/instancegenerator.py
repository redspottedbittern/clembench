"""
This is the class that produces our game instances.

For new experiments change the game parameters below and also change the seed.
"""

import random
from clemgame.clemgame import GameInstanceGenerator
from games.wizardsapprentice.utils.utils import (
    create_deck,
    create_table,
    get_seating_order,
    get_random_undealt_cards,
    get_random_trump_card
)

# define constants
GAME_NAME = "wizardsapprentice"
SEED = 123

# parameters for the game
NUM_ROUNDS = 9
START_ROUND = 1
PLAYERS = 2

# parameters for the cards
COLORS = ["G", "B", "R", "Y"]
CARDS_PER_COLOR = 13
SPECIAL_CARDS = ["Z", "J"]
SPECIAL_CARDS_NUM = 4

# prompts
PROMPT_NAMES = [
    "rules",
    "round_start",
    "trick_start",
    "trick_end",
    "round_end",
    "game_end",
    "correction_suit",
    "correction_hand",
    "correction_regex"
]


class WizardsApprenticeInstanceGenerator(GameInstanceGenerator):

    def load_prompts(self):
        """Use base method to load prompt texts."""
        # set the path for the prompts
        folder = 'ressources/'

        self.prompts = {}
        # use the load_function of the base class
        for name in PROMPT_NAMES:
            # use the parent classes loader function
            text = self.load_template(folder + name)

            # save in the dictionary
            self.prompts[name + '_prompt'] = text

    def on_generate(self):
        """
        We have to build this method ourselves.

        - you must implement the on_generate method, which should call
        self.add_experiment() to add experiments and self.add_game_instance()
        to add instances. Populate the game instance with keys and values.
        """
        experiment = self.add_experiment(SEED)

        # put all prompts in the experiment
        self.load_prompts()
        experiment.update(self.prompts)

        # create the deck, table, and positions for the game
        experiment["deck"] = create_deck(COLORS, CARDS_PER_COLOR,
                                         SPECIAL_CARDS, SPECIAL_CARDS_NUM)
        experiment["table"] = create_table(PLAYERS-1)
        experiment["player_positions"] = get_seating_order(experiment["table"])

        # eine instance entspricht gerade einer Runde, soll es aber nicht
        for round in range(START_ROUND, self.rounds_to_be_played(len(experiment["deck"]), PLAYERS, NUM_ROUNDS)):
            game_instance = self.add_game_instance(experiment, round)
            game_instance["game_deck"] = experiment["deck"].copy()
            game_instance["player_positions"] = experiment['player_positions']
            game_instance["player_cards"] = {}
            for player in game_instance["player_positions"]:
                dealt_cards = get_random_undealt_cards(game_instance["game_deck"], round)
                game_instance["player_cards"][player] = dealt_cards

            # Get random trump card and color for the round
            game_instance["trump_card"] = get_random_trump_card(game_instance["game_deck"])
            # Finds keys with same trump color for the round
            keys_with_trump_color = [key for key, value in game_instance["game_deck"].items() if value.get("color") == game_instance["game_deck"][str(game_instance["trump_card"])]["color"]]
            # Sets the trump attribute to True for cards with the same color as the trump card for the round
            for key in keys_with_trump_color:
                game_instance["game_deck"]["trump"] = True

    def rounds_to_be_played(self, number_of_cards, number_of_players, rounds_suggested):
        if rounds_suggested == -1:
            if not number_of_cards % number_of_players == 0:
                raise Exception('Deck needs to be divisible by players')
            return number_of_cards // number_of_players
        else:
            return rounds_suggested


if __name__ == '__main__':
    random.seed(SEED)
    WizardsApprenticeInstanceGenerator(GAME_NAME).generate()
