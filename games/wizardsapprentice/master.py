from typing import List, Tuple, Dict

from backends import Model
from clemgame.clemgame import GameMaster, GameBenchmark, Player
from clemgame import get_logger
from games.wizardsapprentice.utils.utils import *
from games.wizardsapprentice.instancegenerator import GAME_NAME
from games.wizardsapprentice.utils.parser_utils import Parser
from games.wizardsapprentice.utils.trick_utils import evaluate_trick

logger = get_logger(__name__)


class Apprentice(Player):
    def __init__(self, model: Model):
        super().__init__(model)


class WizardsApprenticeGameMaster(GameMaster):
    def __init__(self, experiment: Dict, player_backends: List[Model]):
        super().__init__(GAME_NAME, experiment, player_backends)
        self.config = experiment
        self.player_model_names = [
            player_model.get_name() for player_model in player_backends
        ]

        # Import prompts
        self.name = self.config["name"]
        self.rules_prompt = self.config["rules_prompt"]
        self.round_start_prompt = self.config["round_start_prompt"]
        self.trick_start_prompt = self.config["trick_start_prompt"]
        self.trick_end_prompt = self.config["trick_end_prompt"]
        self.round_end_prompt = self.config["round_end_prompt"]
        self.game_end_prompt = self.config["game_end_prompt"]
        self.correction_suit_prompt = self.config["correction_suit_prompt"]
        self.correction_hand_prompt = self.config["correction_hand_prompt"]
        self.correction_regex_prompt = self.config["correction_regex_prompt"]
        self.card_played = self.config["card_played"]
        self.wizard = self.config["wizard"]
        self.jester = self.config["jester"]
        self.is_wizard = self.config["is_wizard"]
        self.is_jester = self.config["is_jester"]
        self.prediction = self.config["prediction"]

        # Defines models 
        self.model_a = player_backends[0]
        self.model_b = player_backends[1]

    def setup(self, **game_instance):
        logger.info("SETUP")

        # Import game instances
        self.game_instance = game_instance
        self.game_id = self.game_instance["game_id"]
        self.seating_order = self.game_instance["seating_order"]
        self.dealt_cards = dict(self.game_instance["dealt_cards"])

        # Create the players
        self.apprentince1 = Apprentice(self.model_a)
        self.apprentince2 = Apprentice(self.model_b)

    def play(self):

        # Loops through trick rounds
        for trick_round_number in self.dealt_cards.keys():
            trick_round_cards = dict(self.dealt_cards[str(trick_round_number)])
            trick_round_trump = trick_round_cards["trump"]

            # Loops through the players considering their seating order
            for seating in range(1, len(self.seating_order)+1):
                player_cards = list(trick_round_cards[str(seating)])
                print(player_cards)

        return None

        '''
        # TODO: Include prompt to explain rules
        # Prompt round start template

        for idx, val in enumerate(self.players_position):
            # Notice we do not want to update the original round_start_prompt from the setup
            start_prompt = self.round_start_prompt.replace(
                "$PLAYER_POSITION$", str(val))
            start_prompt = start_prompt.replace(
                "$NUM_CARDS$", str(self.game_parameters["NUM_CARDS"]))
            start_prompt = start_prompt.replace(
                "$TRUMP_CARD$", str(self.trump_card))
            start_prompt = start_prompt.replace(
                "$TRUMP_COLOR$", str(self.deck[str(self.trump_card)]["color"]))
            start_prompt = start_prompt.replace(
                "$PLAYER_HAND$", str(self.table[int(val)]["Cards_dealt"]))

            if idx == 0:
                start_prompt = start_prompt.replace(
                    "$PLAYER_PREDICTIONS$", " You are the first one to play, so there are no predictions so far.")
                # TODO: Remove when players are ready. Only for testing.
                self.table[val]['Prediction'] = "TEST"
            else:
                start_prompt = start_prompt.replace(
                    "$PLAYER_PREDICTIONS$", str(summarize_trick_round(self.table)))

        # Loop through trick rounds
        for trick_round in range(1, int(self.game_parameters["NUM_CARDS"]+1)):
            idx = 0
            # Loop through players in the correct order to let them play
            for val in self.players_position:
                # Start trick prompt:
                # Notice we do not want to update the original round_start_prompt from the setup
                trick_prompt = self.trick_start_prompt.replace(
                    "$PLAYER_POSITION$", str(val))
                trick_prompt = trick_prompt.replace(
                    "$NUM_CARDS$", str(self.game_parameters["NUM_CARDS"]))
                trick_prompt = trick_prompt.replace(
                    "$TRUMP_CARD$", str(self.trump_card))
                trick_prompt = trick_prompt.replace(
                    "$TRUMP_COLOR$", str(self.deck[str(self.trump_card)]["color"]))
                trick_prompt = trick_prompt.replace(
                    "$PLAYER_HAND$", str(self.table[int(val)]["Cards_dealt"]))

                # In case its the first play in the first trick round
                if trick_round == 1 and idx == 0:
                    trick_prompt = trick_prompt.replace(
                        "$PLAYER_PREDICTIONS$", "You are the first one to play, so there are no predictions so far")
                    trick_prompt = trick_prompt.replace("$CARDS_PLAYED$", "")
                    # TODO: Remove when players are ready. Only for testing.
                    self.table[val]['Prediction'] = "TEST"
                else:  # If not the first play, repeats predictions of other players and cards played so far
                    trick_prompt = trick_prompt.replace("$PLAYER_PREDICTIONS$", str(
                        "\nAfter careful consideration, the players' predictions are as follows: " + summarize_trick_round(self.table)))
                    trick_prompt = trick_prompt.replace("$CARDS_PLAYED$", str(
                        "\n\nThese cards have been played in this trick already in this order: " + get_ordered_played_cards(self.table)))

                print(trick_prompt)

                # TODO: Remove when players are ready. Only for testing.
                test = input()
                # TODO: Accepts or denies input of player
                # Removes played card and updates the table
                remove_card(self.table, val, str(test))

                idx += 1

            # Prompts results for trick round
            # TODO: Decide winner (use utils.py), update table (see "Tricks_won"), generate text with won tricks by each player, similar to summarize_trick_round()
            tend_prompt = self.trick_end_prompt.replace(
                "$CARDS_PLAYED_LAST_TRICK$", get_ordered_played_cards(self.table))
            print(tend_prompt)

        # TODO: Calculate score so far
        # TODO: Generate leaderboard for round
        rend_prompt = self.round_end_prompt.replace(
            "$PLAYER_PREDICTIONS$", str(summarize_trick_round(self.table)))
        print(rend_prompt)
        '''

    def parse_card(self, answer, hand, trick):
        """
        Parse the answer from an LLM when a card is expected.

        This function takes the answer from the LLM, checks if it is a viable
        answer, that follows the move rules:
            - is in players hand
            - follows suit correctly

        Returns the card
        """
        if self.parser.is_comprehensible_card(answer):
            card = self.parser.extract_card(answer)
        else:
            # TODO The correction template must be included here
            pass

        if not self.parser.is_in_hand(card, hand):
            pass  # TODO The correction template must be included here

        if not self.parser.follows_suit(card, hand, trick):
            pass  # TODO The correction template must be included here

        return card

    def parse_prediction(self, answer, round):
        """
        Parse the answer from an LLM when a prediction is expected.

        This function takes the answer from the LLM, checks if it is a viable
        answer, that follows the move rules:
            - prediction is in range of total cards this round

        Returns prediction as an int.
        """
        if self.parser.is_comprehensible_prediction(answer):
            prediction = self.parser.extract_prediction(answer)
        else:
            pass  # TODO correction template

        if not self.parser.is_possible_prediction(prediction, round):
            pass  # TODO correction template

        return int(prediction)


class WizardsApprenticeGameBenchmark(GameBenchmark):
    """
    Our own class that inherits from GameBenchmark.

    This class is called first and creates the game master. The instance is
    already loaded.
    """

    def __init__(self):
        # here the games name is declared
        super().__init__(GAME_NAME)

    def get_description(self):
        return "Trick tacking card game between 3-6 players."

    def create_game_master(self, experiment: dict, player_backends: list[str]) -> GameMaster:
        # this has to return our own gamemaster class
        # return Taboo(experiment, player_backends)
        return WizardsApprenticeGameMaster(experiment, player_backends)

    def is_single_player(self) -> bool:
        return False
