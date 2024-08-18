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

GAME_NAME = "wizardsapprentice"
SEED = 123
EXPERIMENTS = [
    "test_game"
    # "full_game"
    # "full_no_special_cards",
    # "full_programmatic2",
    # "short_no_reprompting",
    # "short_pos1_easy",
    # "short_pos1_hard",
    # "short_pos2_easy",
    # "short_pos2_hard",
    # "short_pos3_easy",
    # "short_pos3_hard"
]

class WizardsApprenticeInstanceGenerator(GameInstanceGenerator):
    """Create an experiment.

    It contains cards dealt for the whole game, prompts and regexe.
    """

    def load_experiments(self):
        """Use base method to load settings for the different experiments."""
        # set the path
        folder = 'ressources/experiment_settings/'

        # create a dictionary of the options for every experiment
        experiment_settings = {}
        for name in EXPERIMENTS:
            # use the load_function of the base class
            experiment_settings[name] = self.load_json(folder + name + '.json')

        return experiment_settings

    def load_prompts(self, settings):
        """Use base method to load prompt texts."""
        # set the path for the prompts
        folder = 'ressources/'

        # create a dictionary of the prompts for this experimen
        prompts = {}
        for name in settings['PROMPT_NAMES']:
            # use the parent classes loader function
            prompts[name + '_prompt'] = self.load_template(folder + name)

        # prepare rules prompt with information
        # i don't know a better place to do this
        prompts['rules_prompt'] = self.prepare_rules(prompts['rules_prompt'],
                                                     settings)

        return prompts

    def prepare_rules(self, prompt, settings):
        """Fill rules prompt with information avaible only in instantiation."""
        rules_template = Template(prompt)

        # get the total number of cards in the game
        num_cards = (len(settings['COLORS']) * settings['CARDS_PER_COLOR'] +
                     len(settings['SPECIAL_CARDS']) * settings['SPECIAL_CARDS_NUM'])
        # get the full name strings for colors and special cards
        used_colors = str([settings['COLORS_MEANING'][key]
                           for key
                           in settings['COLORS']])[1:-1]
        used_special = str([settings['SPECIAL_CARDS_MEANING'][key]
                            for key
                            in settings['SPECIAL_CARDS']])[1:-1]

        subs = {
            'CARDS_PER_COLOR': settings['CARDS_PER_COLOR'],
            'NUM_CARDS': num_cards,
            'SPECIAL_CARDS': used_special,
            'SPECIAL_CARDS_NUM': settings['SPECIAL_CARDS_NUM'],
            'LEN_COLORS': len(settings['COLORS']),
            'COLORS': used_colors
        }

        return rules_template.substitute(subs)

    def prepare_regex(self, settings):
        """
        Prepare language sensitive Regular Expressions.

        In dependence of the set global variables regex are created:
            - 'card_played': to check the answer when a card should be played
            - 'prediction': to check the answer when a prediction was made
            - 'wizard' and 'jester'
        """
        # create a dictionary for the regex
        regex = {}

        # get regex strings for the colors
        colors = "".join(settings['COLORS'])

        # get regex strings for the numbers for the colors
        if settings['CARDS_PER_COLOR'] < 10:
            part_1 = list(map(str, range(1, settings['CARDS_PER_COLOR']+1)))
            cards_per_color = "[" + "".join(part_1) + "]"
        elif settings['CARDS_PER_COLOR'] < 20:
            part_1 = list(map(str, range(1, 10)))
            part_2 = list(map(str, range(settings['CARDS_PER_COLOR']-9)))
            cards_per_color = "[" + "".join(part_1) + "]|1[" +\
                "".join(part_2) + "]"

        # only get regex for special cards if there are more than 0 in the deck
        if settings['SPECIAL_CARDS_NUM'] > 0:
            # get regex strings for the special cards
            s_cards = "ZJ"
            s_cards = "|[" + s_cards + "]"

            # get regex string for the number of special cards
            num_s_cards = list(map(str, range(settings['SPECIAL_CARDS_NUM']+1)))
            num_s_cards = "[" + "".join(num_s_cards) + "]"
        else:
            s_cards = ""
            num_s_cards = ""

        # finally fill all string together in the full regex
        regex['card_played'] = f"^I PLAY: ([{colors}]({cards_per_color}){s_cards}{num_s_cards})$"

        # determine the right letters for the special cards
        regex['wizard'] = ""
        regex['jester'] = ""
        for letter in settings['SPECIAL_CARDS']:
            if letter == "Z":
                regex['wizard'] = "Z"
            elif letter == "W":
                regex['wizard'] = "W"
            elif letter == "J":
                regex['jester'] = "J"

        # prepare the regex for the prediction prompt
        regex['prediction'] = "PREDICTION: ([0-9]{1,2})$"

        return regex

    def on_generate(self):
        """We have to build this method ourselves."""
        # load all experiment settings and create the experiment for each
        for name, settings in self.load_experiments().items():

            experiment = self.add_experiment(name)
            # load prompts and regex
            experiment.update(self.load_prompts(settings))
            experiment['regex'] = self.prepare_regex(settings)
            # fill general info about remprompting
            experiment['liberal_mode'] = settings['LIBERAL_MODE']
            experiment['attempts'] = settings['ATTEMPTS']

            # create deck and check number of rounds
            deck = create_deck(settings['COLORS'],
                               settings['CARDS_PER_COLOR'],
                               settings['SPECIAL_CARDS'],
                               settings['SPECIAL_CARDS_NUM'])
            end_round = self.rounds_to_be_played(len(deck),
                                                 settings['PLAYERS'],
                                                 settings['END_ROUND'])

            # create the target number of instances
            for n in range(settings['N_INSTANCES']):
                # create instance with id
                game_id = str(name) + '_i' + str(n)
                game_instance = self.add_game_instance(experiment, game_id)

                # create a seating order for this instance
                n_players = settings['PLAYERS']
                position = settings['PLAYER_POSITION']
                seating_order = create_seating_order(n_players, position)

                # for every round deal cards to each player
                dealt_cards = {}
                trump_cards = {}
                card_difficulty = ""
                if settings['DIFFICULTY'] == "easy":
                    card_difficulty = "good_cards"
                elif settings["DIFFICULTY"] == "hard":
                    card_difficulty = "bad_cards"
                else:
                    card_difficulty = "random"
                for round in range(settings['START_ROUND'], end_round + 1):
                    dealt_cards[round], trump_cards[round] = (
                        deal_cards_for_round(round, deck, seating_order, card_difficulty)
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
