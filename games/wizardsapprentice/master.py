"""Main game class for the game The Wizard's Apprentice."""
from typing import List, Dict
from string import Template
import collections
import copy
import numpy as np

from backends import Model
from clemgame.clemgame import GameMaster, GameBenchmark, Player
import clemgame.metrics as ms
# from clemgame import get_logger
from games.wizardsapprentice.instancegenerator import GAME_NAME
from games.wizardsapprentice.utils.parser_utils import (
    Parser,
    InvalidAnswerError
)
from games.wizardsapprentice.utils.instantiation_utils import (
    convert_keys_to_int
)
from games.wizardsapprentice.utils.trick_utils import (
    evaluate_trick,
    shift_to_winner,
    evaluate_round
)

from games.wizardsapprentice.apprentice import Apprentice

# logger = get_logger(__name__)


class WizardsApprenticeGameMaster(GameMaster):
    # def __init__(self, experiment: Dict, player_backends: List[Model]):
    def __init__(self, game_name: str, experiment: Dict, player_backends: List[Model]):
        """
        Initialize a WizardsApprenticeGameMaster object.

        :param experiment: Dictionary containing the experiment configuration.
        :param player_backends: List of player backend models.

        - leaderboard: dict of dicts to save points during the game.
        """
        super().__init__(GAME_NAME, experiment, player_backends)

        if len(player_backends) == 3:
            self.model_a = player_backends[0]
            self.model_b = player_backends[1]
            self.model_c = player_backends[2]
        elif len(player_backends) == 2:
            self.model_a = player_backends[0]
            # focus_player = 2 

        # Saves experiment and player attributes
        self.config = experiment
        self.current_turn: int = 0
        self.players_by_number: Dict[str, Player] = collections.OrderedDict()
        self.messages_by_names: Dict[str, List] = dict()
        self.backends = player_backends
        self.num_players = len(player_backends)

        # Initialise attributes that will be used for the evaluation scores
        self.aborted: bool = 0
        self.lose: bool = 0
        self.request_counts = 0
        self.parsed_request_counts = 0
        self.violated_request_counts = 0

        # Import information about reprompting
        self.liberal_mode = self.config['liberal_mode']
        self.attempts = self.config['attempts']

        # Import prompts
        self.rules_prompt = self.config["rules_prompt"]
        self.round_start_prompt = self.config["round_start_prompt"]
        self.trick_start_prompt = self.config["trick_start_prompt"]
        self.trick_end_prompt = self.config["trick_end_prompt"]
        self.round_end_prompt = self.config["round_end_prompt"]
        self.game_end_prompt = self.config["game_end_prompt"]
        self.correction_suit_prompt = self.config["correction_suit_prompt"]
        self.correction_hand_prompt = self.config["correction_hand_prompt"]
        self.correction_prediction_prompt = self.config["correction_prediction_prompt"]
        self.correction_card_structure_prompt = self.config["correction_card_structure_prompt"]
        self.correction_prediction_structure_prompt = self.config[
            "correction_prediction_structure_prompt"]
        self.regex = self.config['regex']

        # Define parser
        self.parser = Parser(self.regex)

    def get_current_hand(self, round, player):
        """Extract a certain players current hand."""
        start_hand = self.dealt_cards[round][player]
        old_cards = [trick_round[player] for trick_round in
                     self.played_cards[round].values()]

        current_hand = [card for card in start_hand if card not in old_cards]

        return current_hand

    def get_current_trick(self, round, trick_round):
        """Extract the current trick in the correct order of played cards."""
        current_trick = []
        for player in self.playing_order[round][trick_round]:
            current_trick.append(self.played_cards[round][trick_round][player])

        return current_trick

    def determine_trick_winner(self, round, trick_round):
        """Determine best card and its player for a certain trick."""
        # Evaluate trick
        trick = self.get_current_trick(round, trick_round)
        trump = self.trump_cards[round][0]
        best_card = evaluate_trick(trick, trump)

        # Check which player played the best_card
        winner = [
            int(player) for player, card
            in self.played_cards[round][trick_round].items()
            if card == best_card
        ]

        return winner[0]

    def calculate_points(self, round, player):
        """Calculate points for a player in relation to last round."""
        if (round-1) in self.dealt_cards.keys():
            points = (
                self.points[round-1][player] +
                evaluate_round(self.predictions[round][player],
                               self.tricks_per_player[round][player])
            )
        else:
            points = evaluate_round(self.predictions[round][player],
                                    self.tricks_per_player[round][player])

        return points

    def add_player(self, model, number, name):
        """
        Add a player to the game.

        :param player: Player object to be added.
        """
        if model == 'programmatic':
            apprentice = Apprentice("programmatic", name)
        else:
            apprentice = Apprentice(model, name)
        # print(apprentice.player) -> Gets name of the player
        apprentice.descriptor = apprentice.player
        self.players_by_number[number] = apprentice
        self.messages_by_names[apprentice.descriptor] = []

    def add_message(self, player: Player, utterance: str, role="user") -> None:
        """
        Add a message to a player's history and log the event.

        :param player: Player object.
        :param utterance: Message content.
        :param role: Role of the message sender (default is "user").
        """
        message = {"role": role, "content": utterance}
        history = self.messages_by_names[player.descriptor]
        history.append(message)

        action = {'type': 'send message', 'content': utterance}
        self.log_event(from_='GM',
                       to=str(player.player),
                       # to=str(self.players_by_names[str(player)]),
                       action=action
                       )

    def get_answer(self, player: Player) -> str:
        """
        Get an answer from the player model based on current history and turn.

        :param player: Player object.
        :return: Answer string.
        """

        history = self.messages_by_names[player.descriptor]
        prompt, raw_answer, answer = player(history, self.current_turn)
        player.history = [] # Reset history after message has been sent
        self.messages_by_names[player.descriptor] = []
        action = {'type': 'get message', 'content': answer}
        self.log_event(
            # from_=str(self.players_by_names[str(player)]),
            from_=str(player.player),
            to='GM',
            action=action,
            call=(copy.deepcopy(prompt), raw_answer)
        )
        return answer

    def parse_prediction(self, answer, round):
        """
        Parse the answer from an LLM when a prediction is expected.

        This function takes the answer from the LLM, checks if it is a viable
        answer, that follows the move rules:
            - prediction is in range of total cards this round

        Returns prediction as an int or the prompt for the specific error.
        """
        if self.parser.is_comprehensible_prediction(answer):
            prediction = self.parser.extract_prediction(answer)
        else:
            return self.correction_prediction_structure_prompt

        if not self.parser.is_possible_prediction(prediction, round):
            return self.correction_prediction_prompt

        return int(prediction)

    def parse_card(self, answer, hand, trick):
        """
        Parse the answer from an LLM when a card is expected.

        This function takes the answer from the LLM, checks if it is a viable
        answer, that follows the move rules:
            - is in players hand
            - follows suit correctly

        Returns the card or the prompt for the specific error
        """
        if self.parser.is_comprehensible_card(answer):
            card = self.parser.extract_card(answer)
        else:
            return self.correction_card_structure_prompt

        if not self.parser.is_in_hand(card, hand):
            return self.correction_hand_prompt

        if not self.parser.follows_suit(card, hand, trick):
            return self.correction_suit_prompt

        return card

    def prompt_model(self, prompt, receiver, expect, round, hand, trick,
                     rec_anchor=0):
        """
        Wrap around prompting, parsing and reprompting.

        This produces a prompt, when it is called, and sends it to the model.
        The answer is then parsed. Depending on the liberal mode, the model is
        either reprompted with a correction or the game is aborted.
        """
        # Produce the prompt
        prompt = Template(prompt)
        prompt = prompt.substitute(self.info)
        # Send it to the LLM and parse the answer
        self.add_message(receiver, prompt)
        answer = self.get_answer(receiver)
        self.request_counts += 1

        print(prompt)
        print(answer)

        # Get an answer depending on the exectation and return if valid
        if expect == "prediction":
            parse = self.parse_prediction(answer, round)
            if self.parser.validate_prediction(answer, round):
                self.parsed_request_counts += 1
                return parse
        elif expect == "card":
            parse = self.parse_card(answer, hand, trick)
            if self.parser.validate_card(answer, hand, trick):
                self.parsed_request_counts += 1
                return parse

        # reprompt if the answer was not correctly parsed
        if self.liberal_mode and (rec_anchor < self.attempts):
            return self.prompt_model(parse, receiver, expect, round, hand,
                                     trick, rec_anchor+1)
        else:
            self.aborted = True
            # log the abortion event
            action = {'type': 'invalid format', 'content': 'abort'}
            self.log_event(from_='GM', to='GM', action=action)

            raise InvalidAnswerError

    def setup(self, **game_instance) -> None:
        """
        Set up the game with the provided game instance configuration.

        :param game_instance: Configuration dictionary for the game instance.
        """
        # logger.info("SETUP!")

        # Import game instances
        self.game_instance = game_instance
        self.game_id = self.game_instance["game_id"]
        self.seating_order = self.game_instance["seating_order"]
        self.dealt_cards = self.game_instance["dealt_cards"]
        self.trump_cards = self.game_instance["trump_cards"]
        self.dealt_cards = convert_keys_to_int(self.dealt_cards)
        self.trump_cards = convert_keys_to_int(self.trump_cards)

        # create dictionarys for the leaderboard
        # dict[round][player] = int
        self.points = {
            d: dict.fromkeys(self.seating_order)
            for d in self.dealt_cards.keys()
        }
        self.predictions = self.points.copy()
        self.tricks_per_player = {
            d: dict.fromkeys(self.seating_order, 0)
            for d in self.dealt_cards.keys()
        }

        # create a dictionary to save played card
        # played_cards[round][trick_round][player] = card
        self.played_cards = {
            d: {dd: dict.fromkeys(self.seating_order)
                for dd in range(1, int(d)+1)}
            for d in self.dealt_cards.keys()
        }

        # create a dictionarry to save the seating order at a certain point
        # playing_order[round][trick_round] = list
        self.playing_order = {
            d: {dd: {}
                for dd in range(1, int(d)+1)}
            for d in self.dealt_cards.keys()
        }
        # Set the first seating order
        self.playing_order[list(self.dealt_cards.keys())[
            0]][1] = self.seating_order

        # Create the info dictionary to feed the prompt templates
        self.info = {}

        # Create the players
        # TODO if we want to have a focused player or something, we have to
        # change the creation at this point and in self.add_player
        # focus_player = 2  # nur ein Platzhalter
        # for number in self.seating_order:
        #     if number % 2 == 0:
        #         self.add_player(self.model_b, number)
        #     else:
        #         self.add_player(self.model_a, number)

        if self.num_players == 3:
            list_models = [self.model_a, self.model_b, self.model_c]
            list_names = ['Gandalf', 'Merlin', 'Oz']
            if len(self.seating_order) == 3:
                for idx, value in enumerate(self.seating_order):
                    self.add_player(list_models[idx], value, list_names[idx])
        elif self.num_players == 2:
            self.add_player(self.model_a, self.seating_order[0], 'Gandalf')
            self.add_player('programmatic', self.seating_order[1], 'Merlin')
            self.add_player('programmatic', self.seating_order[2], 'Oz')

        # Log all the players
        self.log_players({
            apprentice.player: f'{apprentice.player}: {apprentice.model}'
            for apprentice in self.players_by_number.values()
        })

    def update_info(self, round, player, trick_round, players_name, winner=None):
        """
        Gather information that will be used to fill prompts.

        The 'info' dictionary contains information of the game in a string
        format. It will be later be used to substitute the Template objects
        of the prompts. This method gathers and formats these information.
        """
        # General true for the whole game
        first_round = list(self.dealt_cards.keys())[0]
        self.info['NUM_OTHER_PLAYERS'] = len(self.dealt_cards[first_round])-1

        # Fixes issue with number of cards in the trick round:
        if round is not None:
            self.info['NUM_CARDS'] = int(round)

        if round and player:
            self.info['PLAYER_NAME'] = str(players_name.player)
            # Declare trump color
            self.info['TRUMP_CARD'] = str(self.trump_cards[round])
            self.info['TRUMP_COLOR'] = (self.info['TRUMP_CARD'][0]
                                        if self.info['TRUMP_CARD'] != "None"
                                        else str(None)
                                        )
            self.info['HAND_SIZE'] = round
            # Declare current and full player hand
            self.info['PLAYER_HAND'] = self.dealt_cards[round][player]
            self.info['CURRENT_PLAYER_HAND'] = (
                self.get_current_hand(round, player)
            )
            # Declare player position
            self.info['PLAYER_POSITION'] = (
                self.playing_order[round][1].index(player) + 1
            )
            # Declare the predictions so far and for last round
            self.info['PLAYER_PREDICTIONS'] = [
                (player, prediction) for player, prediction
                in self.predictions[round].items()
            ]
            # Check if there were last predictions and retrieve them
            if (round-1) in self.predictions.keys():
                self.info['PLAYER_PREDICTIONS_LAST_ROUND'] = [
                    (player, prediction) for player, prediction
                    in self.predictions[round-1].items()
                ]
            else:
                self.info['PLAYER_PREDICTIONS_LAST_ROUND'] = ""

            # Declare leaderboard self.info
            self.info['LEADERBOARD_TRICKS'] = [
                (player, value) for player, value
                in self.tricks_per_player[round].items()
            ]
            self.info['LEADERBOARD_POINTS'] = [
                (player, points) for player, points
                in self.points[round].items()
            ]

        if round and player and trick_round:
            self.info['PLAYER_NAME'] = str(players_name.player)
            # Declare which cards were played already and last trick
            self.info['CARDS_PLAYED'] = (
                self.get_current_trick(round, trick_round)
            )

            # Check if there is a last trick that was played and retrieve it
            # Bit complicated, I know
            if (trick_round-1) in self.played_cards[round].keys():
                self.info['CARDS_PLAYED_LAST_TRICK'] = (
                    self.get_current_trick(round, trick_round-1))
            else:
                if (round-1) in self.played_cards.keys():
                    self.info['CARDS_PLAYED_LAST_TRICK'] = (
                        self.get_current_trick(round-1, round-1))
                else:
                    self.info['CARDS_PLAYED_LAST_TRICK'] = ''

        if winner:
            # Declare winner if there was one
            self.info['WINNER_LAST_TRICK'] = winner

    def play(self) -> None:
        """
        Play the game according to the predefined rules and prompts.

        The play method orchestrates the flow of the game by managing the
        turns, handling player interactions, and evaluating the game state.
        Key elements include:

        - info: dict that contains information for the string substitution.
        - dealt_cards: cards, every player gets (predetermined)
        - played_cards: record of the cards every player plays
        - predictions: record of the predictions every player made
        - points: total game points at a certain round
        - tricks_per_player: tricks a player won in a certain round
        """
        # Set a local variable to track the order of play
        current_order = self.seating_order

        # START round
        next_prompt = self.rules_prompt
        for round in self.dealt_cards:
            print("Round " + str(round))
            # logger.info("Round " + str(round))
            # Logs new round
            self.log_next_turn()

            # GET PREDICTIONS
            next_prompt += self.round_start_prompt
            for player in current_order:
                # Gather and update information for the prompting
                self.update_info(round, player, None,
                                 self.players_by_number[player])
                receiver = self.players_by_number[player]
                # Prompt the model
                try:
                    prediction = self.prompt_model(
                        next_prompt, receiver, "prediction", round, None, None
                    )
                except InvalidAnswerError:
                    return
                except AttributeError:
                        return
                # save players prediction
                self.predictions[round][player] = prediction

            # START trick round
            next_prompt = self.rules_prompt
            next_prompt += self.trick_start_prompt
            for trick_round in range(1, round+1):
                print("- Trick: " + str(trick_round))
                # GET CARDS
                for player in current_order:
                    # Gather and update information for the prompting
                    self.update_info(round, player, trick_round,
                                     self.players_by_number[player])
                    receiver = self.players_by_number[player]
                    trick = self.get_current_trick(round, trick_round)
                    hand = self.get_current_hand(round, player)
                    # Prompt the model
                    try:
                        card = self.prompt_model(
                            next_prompt, receiver, "card", round, hand, trick
                        )
                    except InvalidAnswerError:
                        return
                    except AttributeError:
                        return

                    # save the played card
                    self.played_cards[round][trick_round][player] = card

                # END OF TRICK
                # Determine the winner of the trick
                winner = self.determine_trick_winner(round, trick_round)
                # Update info and leaderboard
                self.update_info(None, None, None,
                                 self.players_by_number[player], winner=winner)
                self.tricks_per_player[round][winner] += 1
                # Shift seating order to winner and save the new order
                current_order = shift_to_winner(current_order, winner)
                self.playing_order[round][trick_round + 1] = current_order
                # Set new next prompt template
                next_prompt = self.rules_prompt
                next_prompt += self.trick_end_prompt + self.trick_start_prompt

            # END OF ROUND
            # calculate points for all player
            for player in self.seating_order:
                self.points[round][player] = self.calculate_points(round,
                                                                   player)
            # Shift original seating_order by one and save it
            current_order = (self.playing_order[round][1][1:] +
                             self.playing_order[round][1][:1])
            # a bit of a unclean hack. In the last round, there are no keys
            # left
            try:
                self.playing_order[round+1][1] = current_order
            except KeyError:
                pass
            # Add round end to next prompt
            next_prompt = self.rules_prompt
            next_prompt += self.trick_end_prompt + self.round_end_prompt

            # Log a message informing that the trick round was successfuly played
            action = {'type': 'info', 'content': 'Round successful'}
            self.log_event(from_='GM', to='GM', action=action)

        # logger.info("Game is finished!")  # TODO What is this logger for?
        # Log a final message saying that the game did come to an end
        action = {'type': 'info', 'content': 'end game'}
        self.log_event(from_='GM', to='GM', action=action)
        self.log_eval_assets()
        return

    def log_eval_assets(self) -> None:
        """Aux to log variables needed for scoring (firstlast specific)"""
        self.log_key('Played rounds', len(self.played_cards))
        self.log_key('predictions', self.predictions)
        self.log_key('tricks_per_player', self.tricks_per_player)
        self.log_key('points', self.points)
        self.log_key(ms.METRIC_LOSE, self.lose)
        self.log_key(ms.METRIC_ABORTED, self.aborted)
        self.log_key(ms.METRIC_REQUEST_COUNT, self.request_counts)
        self.log_key(ms.METRIC_REQUEST_COUNT_PARSED,
                     self.parsed_request_counts)
        self.log_key(ms.METRIC_REQUEST_COUNT_VIOLATED,
                     self.violated_request_counts)

    def compute_scores(self, episode_interactions: Dict) -> None:
        """Compute episode-level and turn-level scores (mandatory)."""
        aborted = int(episode_interactions[ms.METRIC_ABORTED])
        requests = episode_interactions[ms.METRIC_REQUEST_COUNT]
        p_requests = episode_interactions[ms.METRIC_REQUEST_COUNT_PARSED]
        v_requests = requests - p_requests
        request_success_rate = p_requests / requests
        lose = int(episode_interactions[ms.METRIC_LOSE]) if not aborted else 0
        success = 1 - lose if not aborted else 0

        # self.log_turn_score(round, 'points', self.points)

        bench_score = 50 if not aborted else np.nan

        self.log_episode_score(ms.METRIC_ABORTED, aborted)
        self.log_episode_score(ms.METRIC_REQUEST_COUNT, requests)
        self.log_episode_score(ms.METRIC_REQUEST_COUNT_PARSED, p_requests)
        self.log_episode_score(ms.METRIC_REQUEST_COUNT_VIOLATED, v_requests)
        self.log_episode_score(ms.METRIC_REQUEST_SUCCESS, request_success_rate)
        self.log_episode_score(ms.METRIC_LOSE, lose)
        self.log_episode_score(ms.METRIC_SUCCESS, success)

        self.log_episode_score(ms.BENCH_SCORE, bench_score)


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
        return WizardsApprenticeGameMaster(self.name, experiment, player_backends)

    def is_single_player(self) -> bool:
        return False
