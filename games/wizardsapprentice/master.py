from typing import List, Tuple, Dict
from string import Template
import collections
import copy

from backends import Model
from clemgame.clemgame import GameMaster, GameBenchmark, Player
from clemgame import get_logger
from games.wizardsapprentice.utils.utils import *
from games.wizardsapprentice.instancegenerator import GAME_NAME
from games.wizardsapprentice.utils.parser_utils import Parser
from games.wizardsapprentice.utils.trick_utils import (
    evaluate_trick,
    shift_to_winner,
    evaluate_round
)
from games.wizardsapprentice.player import Apprentice

logger = get_logger(__name__)


class WizardsApprenticeGameMaster(GameMaster):
    def __init__(self, experiment: Dict, player_backends: List[Model]):
        """
        Initialize a WizardsApprenticeGameMaster object.

        :param experiment: Dictionary containing the experiment configuration.
        :param player_backends: List of player backend models.

        - leaderboard: dict of dicts to save points during the game.
        """
        super().__init__(GAME_NAME, experiment, player_backends)

        # Saves experiment and player attributes
        self.config = experiment
        self.name = self.config["name"]
        self.current_turn: int = 0
        self.model_a = player_backends[0]
        self.model_b = player_backends[1]
        self.players_by_names: Dict[str, Player] = collections.OrderedDict()

        # Initialise attributes that will be used for the evaluation scores
        # TODO: What other attributes should be used?
        self.aborted: bool = False # Boolean to stop game if parsing is incorrect
        self.leaderboard = {}

        # Import prompts
        self.rules_prompt = self.config["rules_prompt"]
        self.round_start_prompt = self.config["round_start_prompt"]
        self.trick_start_prompt = self.config["trick_start_prompt"]
        self.trick_end_prompt = self.config["trick_end_prompt"]
        self.round_end_prompt = self.config["round_end_prompt"]
        self.game_end_prompt = self.config["game_end_prompt"]
        self.correction_suit_prompt = self.config["correction_suit_prompt"]
        self.correction_hand_prompt = self.config["correction_hand_prompt"]
        self.correction_regex_prompt = self.config["correction_regex_prompt"]
        self.regex = self.config['regex']

        # Define parser
        self.parser = Parser(self.regex)

    def add_player(self, player: Player):
        """
        Add a player to the game.

        :param player: Player object to be added.
        """
        idx = len(self.players_by_names)
        player.descriptor = f"Player {idx + 1}"
        self.players_by_names[str(player)] = player.descriptor

    def add_message(self, player: Player, utterance: str, role="user") -> None:
        """
        Add a message to a player's history and log the event.

        :param player: Player object.
        :param utterance: Message content.
        :param role: Role of the message sender (default is "user").
        """
        player.history.append({'role': role, 'content': utterance})
        action = {'type': 'send message', 'content': utterance}
        self.log_event(from_='GM', to=str(
            self.players_by_names[str(player)]), action=action)

    def get_answer(self, player: Player) -> str:
        """
        Get an answer from the player model based on the current history and turn.

        :param player: Player object.
        :return: Answer string.
        """
        prompt, raw_answer, answer = player(player.history, self.current_turn)
        action = {'type': 'get message', 'content': answer}
        self.log_event(from_=str(self.players_by_names[str(
            player)]), to='GM', action=action, call=(copy.deepcopy(prompt), raw_answer))
        # TODO: Figure out how to deal with this. Let's ask Hakimov.
        player.history = []
        return answer
    
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
            return  # TODO correction template

        if not self.parser.is_possible_prediction(prediction, round):
            return  # TODO correction template

        return int(prediction)

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

    def setup(self, **game_instance) -> None:
        """
        Set up the game with the provided game instance configuration.

        :param game_instance: Configuration dictionary for the game instance.
        """
        logger.info("SETUP!")

        # Import game instances
        self.game_instance = game_instance
        self.game_id = self.game_instance["game_id"]
        self.seating_order = self.game_instance["seating_order"]
        self.dealt_cards = self.game_instance["dealt_cards"]

        # Create the players
        self.apprentice1 = Apprentice(self.model_a, "Gandalf")
        #self.apprentice2 = Apprentice(self.model_b, "Merlin")
        self.add_player(self.apprentice1)
        #self.add_player(self.apprentice2)

    def play(self) -> None:
        """
        Play the game according to the predefined rules and prompts.

        The play method orchestrates the flow of the game by managing the turns,
        handling player interactions, and evaluating the game state. Key elements include:

        - info: dict that contains information for the string substitution.
        - current_hands: dict to manipulate current hand during one round.
        - playing_order: list to manipulate the current order of play.
        """

        # Declare info dict to substitute the prompts later
        info = {}
        # Extract how many players there are and the total number of cards
        info['NUM_OTHER_PLAYERS'] = len(self.dealt_cards["1"]) - 2
        info['NUM_CARDS'] = len(self.dealt_cards)

        # Add rules to next prompt
        next_prompt = self.rules_prompt
        # Declare seating_order
        playing_order = self.seating_order

        while self.aborted == False:
            for round, round_cards in self.dealt_cards.items():
                logger.info("Trick round " + str(round))
                print("Trick round " + str(round))
                # Logs new trick round
                self.current_turn += 1
                self.log_next_turn()

                # Initialize leaderboard for the round
                self.leaderboard[round] = {}

                # Initialize current player hands
                current_hands = {}

                # Declare trump card for the round
                info['TRUMP_CARD'] = str(round_cards['trump'])
                # Declare trump color for the round
                info['TRUMP_COLOR'] = (
                    info['TRUMP_CARD'][0] if info['TRUMP_CARD'] != "None" else str(None))
                # Initialize player predictions
                info['PLAYER_PREDICTIONS'] = ''

                # Add round_start to next prompt
                next_prompt += self.round_start_prompt

                # FIRST: Get predictions of players in playing order
                for position, player in enumerate(playing_order):
                    # Declare player hand
                    info['PLAYER_HAND'] = round_cards[str(player)]
                    # Declare current player hand
                    info['CURRENT_PLAYER_HAND'] = info['PLAYER_HAND'].copy()
                    # Declare player position
                    info['PLAYER_POSITION'] = position + 1

                    # Prompt player for prediction
                    next_prompt = Template(next_prompt)
                    next_prompt = next_prompt.substitute(info)
                    self.add_message(self.apprentice1, next_prompt)
                    prediction = self.get_answer(self.apprentice1)

                    #TODO: Parse answer

                    # Append answer to player predictions
                    info['PLAYER_PREDICTIONS'] += str(prediction)
                    # Update the leaderboard
                    self.leaderboard[round][player] = {}
                    self.leaderboard[round][player]['tricks'] = 0
                    self.leaderboard[round][player]['points'] = 0
                    self.leaderboard[round][player]['prediction'] = prediction
                    # Fill current_hands
                    current_hands[player] = info['CURRENT_PLAYER_HAND'].copy()

                # clear next prompt and add trick_start to next prompt
                next_prompt = self.trick_start_prompt

                # NEXT: play the tricks
                for trick_round in range(1, int(round)+1):
                    # Declare trick
                    info['CARDS_PLAYED'] = []

                    # Let every player play a card
                    for position, player in enumerate(playing_order):
                        # Declare player hand
                        info['PLAYER_HAND'] = round_cards[str(player)]
                        # Declare current player hand
                        info['CURRENT_PLAYER_HAND'] = current_hands[player]
                        # Declare player position
                        info['PLAYER_POSITION'] = position + 1

                        # PROMPT player for card
                        next_prompt = Template(next_prompt)
                        next_prompt = next_prompt.substitute(info)
                        self.add_message(self.apprentice1, next_prompt)
                        answer = self.get_answer(self.apprentice1)

                        #TODO: Parse answer

                        answer = '' # card = self.parse_prediction(answer, round)
                        card = current_hands[player][0]

                        # Add card to trick
                        info['CARDS_PLAYED'].append(card)
                        # Substract card from current player hand
                        current_hands[player].remove(card)

                # FINALLY evaluate trick
                best_card = evaluate_trick(
                    info['CARDS_PLAYED'], info['TRUMP_COLOR'])
                # Check which player played the best_card
                winner = [player for player in self.seating_order if best_card
                          in round_cards[str(player)]][0]
                winner = int(winner)
                # Declare winner
                info['WINNER_LAST_TRICK'] = winner
                # Update leaderboard_tricks
                self.leaderboard[round][winner]['tricks'] += 1
                info['LEADERBOARD_TRICKS'] = [
                    (player, value['tricks']) for player, value in self.leaderboard[round].items()]

                # Shift seating order to winner
                playing_order = shift_to_winner(self.seating_order, winner)

                # TIDY UP after the trick is finished 
                # TODO: This part is not working as the loop is out of control
                # Declare last_trick by copying trick
                info['CARDS_PLAYED_LAST_TRICK'] = info['CARDS_PLAYED'].copy()
                # Clear trick
                info['CARDS_PLAYED'] = []
                # Add trick_end prompt
                next_prompt = self.trick_end_prompt + self.trick_start_prompt

                # Log a message informing that the trick round was successfuly played
                action = {'type': 'info', 'content': 'Trick round successful'}
                self.log_event(from_='GM', to='GM', action=action)
                
                self.aborted = True # Forcing the end. TODO: Remove when loop is working

        logger.info("Game is finished!")
        # Log a final message saying that the game did come to an end
        action = {'type': 'info', 'content': 'end game'}
        self.log_event(from_='GM', to='GM', action=action)

        # NEXT calculate points for all player
        for player in self.seating_order:
            d = self.leaderboard[round][player]
            d['points'] = evaluate_round(d['prediction'], d['tricks'])

        # Declare last_predictios by copying predictions
        info['PLAYER_PREDICTIONS_LAST_ROUND'] = info['PLAYER_PREDICTIONS']
        # Clear predictions
        info['PLAYER_PREDICTIONS'] = ''
        # Declare leaderboard points
        info['LEADERBOARD_POINTS'] = [
            (player, value['points']) for player, value in self.leaderboard[round].items()]
        # Shift original seating_order by one
        self.seating_order = (self.seating_order[1:] + self.seating_order[:1])
        # Add round end to next prompt
        next_prompt = self.trick_end_prompt + self.round_end_prompt

        # Declare winner_game
        end_points = [(values['points'], player) for player, values in
                      self.leaderboard[str(len(self.dealt_cards))].items()]
        info['WINNER_GAME'] = max(end_points)[1]

        # PROMPT for end game TODO: Do we need this?
        next_prompt += self.game_end_prompt
        next_prompt = Template(next_prompt)
        next_prompt = next_prompt.substitute(info)
        self.add_message(self.apprentice1, next_prompt)
        answer = self.get_answer(self.apprentice1)
        print(answer)


class WizardsApprenticeGameBenchmark(GameBenchmark):
    """
    Our own class that inherits from GameBenchmark.

    This class is called first and creates the game master. The instance is
    already loaded.
    """

    def __init__(self):
        super().__init__(GAME_NAME)

    def get_description(self):
        return "Trick tacking card game between 3-6 players."

    def create_game_master(self, experiment: dict, player_backends: list[str]) -> GameMaster:
        return WizardsApprenticeGameMaster(experiment, player_backends)

    def is_single_player(self) -> bool:
        return False
