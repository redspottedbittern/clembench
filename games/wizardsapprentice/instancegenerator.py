"""
This is the class that produces our game instances.

For new experiments change the game parameters below and also change the seed.
"""

import random
from string import Template
from clemgame.clemgame import GameInstanceGenerator
from games.wizardsapprentice.utils.instantiation_utils import (
    deal_cards_for_round,
    create_deck,
    create_seating_order
)

# define constants
GAME_NAME = "wizardsapprentice"
EXPERIMENT_NAME = "full_game_4p"
SEED = 123
N_INSTANCES = 1

# parameters for the game
START_ROUND = 2
END_ROUND = 4
PLAYERS = 3

# parameters for the cards
COLORS = ["G", "B", "R", "Y"]
CARDS_PER_COLOR = 13
SPECIAL_CARDS = ["Z", "J"]
SPECIAL_CARDS_NUM = 4

# prompts
LIBERAL_MODE = True
ATTEMPTS = 5
PROMPT_NAMES = [
    "rules",
    "round_start",
    "trick_start",
    "trick_end",
    "round_end",
    "game_end",
    "correction_suit",
    "correction_hand",
    "correction_prediction",
    "correction_card_structure",
    "correction_prediction_structure"
]


class WizardsApprenticeInstanceGenerator(GameInstanceGenerator):
    """Create an experiment.

    It contains cards dealt for the whole game, prompts and regexe.
    """

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

    def prepare_rules_prompt(self):
        """Fill rules prompt with information avaible only in instantiation."""
        rules_template = Template(self.prompts['rules_prompt'])
        num_cards = (len(COLORS) * CARDS_PER_COLOR +
                     len(SPECIAL_CARDS) * SPECIAL_CARDS_NUM)
        # get strings for colors
        all_colors = {'G': 'green', 'B': 'blue', 'R': 'red', 'Y': 'yellow'}
        used_colors = str([all_colors[key] for key in COLORS])[1:-1]

        # get strings for special cards
        all_special = {'Z': 'Wizard', 'J': 'Jester'}
        used_special = str([all_special[key] for key in SPECIAL_CARDS])[1:-1]

        subs = {
            'CARDS_PER_COLOR': CARDS_PER_COLOR,
            'NUM_CARDS': num_cards,
            'SPECIAL_CARDS': used_special,
            'SPECIAL_CARDS_NUM': SPECIAL_CARDS_NUM,
            'LEN_COLORS': len(COLORS),
            'COLORS': used_colors
        }

        self.prompts['rules_prompt'] = rules_template.substitute(subs)

    def prepare_regex(self):
        """
        Prepare language sensitive Regular Expressions.

        In dependence of the set global variables regex are created:
            - 'card_played': to check the answer when a card should be played
            - 'prediction': to check the answer when a prediction was made
            - 'wizard' and 'jester'
        """
        # create a dictionary for the regex
        self.regex = {}

        # get regex strings for the colors
        colors = "".join(COLORS)

        # get regex strings for the numbers for the colors
        if CARDS_PER_COLOR < 10:
            part_1 = list(map(str, range(1, CARDS_PER_COLOR+1)))
            cards_per_color = "[" + "".join(part_1) + "]"
        elif CARDS_PER_COLOR < 20:
            part_1 = list(map(str, range(1, 10)))
            part_2 = list(map(str, range(CARDS_PER_COLOR-9)))
            cards_per_color = "[" + "".join(part_1) + "]|1[" +\
                "".join(part_2) + "]"

        # only get regex for special cards if there are more than 0 in the deck
        if SPECIAL_CARDS_NUM > 0:
            # get regex strings for the special cards
            s_cards = "ZJ"
            s_cards = "|[" + s_cards + "]"

            # get regex string for the number of special cards
            num_s_cards = list(map(str, range(SPECIAL_CARDS_NUM+1)))
            num_s_cards = "[" + "".join(num_s_cards) + "]"
        else:
            s_cards = ""
            num_s_cards = ""

        # finally fill all string together in the full regex
        self.regex['card_played'] = f"^I PLAY: ([{colors}]({cards_per_color}){s_cards}{num_s_cards})$"

        # determine the right letters for the special cards
        self.regex['wizard'] = ""
        self.regex['jester'] = ""
        for letter in SPECIAL_CARDS:
            if letter == "Z":
                self.regex['wizard'] = "Z"
            elif letter == "W":
                self.regex['wizard'] = "W"
            elif letter == "J":
                self.regex['jester'] = "J"

        # prepare the regex for the prediction prompt
        self.regex['prediction'] = "PREDICTION: ([0-9]{1,2})$"

    def on_generate(self):
        """We have to build this method ourselves."""
        # load prompts and fill in rules
        self.load_prompts()
        self.prepare_rules_prompt()

        # prepare regex patterns
        self.prepare_regex()

        # create experiment
        experiment = self.add_experiment(EXPERIMENT_NAME)
        experiment.update(self.prompts)
        experiment['regex'] = self.regex

        # fill general info about remprompting
        experiment['liberal_mode'] = LIBERAL_MODE
        experiment['attempts'] = ATTEMPTS

        # create deck and check number of rounds
        deck = create_deck(COLORS, CARDS_PER_COLOR, SPECIAL_CARDS,
                           SPECIAL_CARDS_NUM)
        end_round = self.rounds_to_be_played(len(deck), PLAYERS, END_ROUND)

        # create the target number of instances
        for n in range(N_INSTANCES):
            # create instance with id
            game_id = str(EXPERIMENT_NAME) + '_i' + str(n)
            game_instance = self.add_game_instance(experiment, game_id)

            # create a seating order for this instance
            seating_order = create_seating_order(PLAYERS)

            # for every round deal cards to each player
            dealt_cards = {}
            trump_cards = {}
            for round in range(START_ROUND, end_round + 1):
                dealt_cards[round], trump_cards[round] = (
                    deal_cards_for_round(round, deck, seating_order)
                )

            game_instance['seating_order'] = seating_order
            game_instance['dealt_cards'] = dealt_cards
            game_instance['trump_cards'] = trump_cards

    def rounds_to_be_played(self, num_cards, num_players, rounds_suggested):
        """Check what the maximum number of rounds can be."""
        if rounds_suggested == -1:
            return num_cards // num_players
        elif rounds_suggested > num_cards // num_players:
            raise Exception("End round is too high for number of players.")
        else:
            return rounds_suggested


if __name__ == '__main__':
    random.seed(SEED)
    WizardsApprenticeInstanceGenerator(GAME_NAME).generate()
