"""Main game class for the game The Wizard's Apprentice."""
from typing import List, Dict
from string import Template
import copy
import re

from backends import Model
from clemgame.clemgame import GameMaster, GameBenchmark, Player, GameScorer
import clemgame.metrics as ms
from games.wizardsapprentice.instancegenerator import GAME_NAME
from games.wizardsapprentice.apprentice import Apprentice
from games.wizardsapprentice.utils.parser_utils import (
    Parser,
    InvalidAnswerError
)
from games.wizardsapprentice.utils.trick_utils import (
    evaluate_trick,
    evaluate_round
)


class WizardsApprenticeGameMaster(GameMaster):
    def __init__(self, game_name: str, experiment: Dict, player_backends: List[Model]):
        """
        Initialize a WizardsApprenticeGameMaster object.

        :param experiment: Dictionary containing the experiment configuration.
        :param player_backends: List of player backend models.

        - leaderboard: dict of dicts to save points during the game.
        """
        super().__init__(GAME_NAME, experiment, player_backends)

        # if len(player_backends) >= 2:
        #     for index, _ in enumerate(player_backends):
        #         setattr(self, f"model_{index}", player_backends[index])
        # else:
        #     message = f"Not enough players for game '{game_name}': '{len(player_backends)}'"
            # raise ValueError(message)

        # Saves experiment and player attributes
        self.config = experiment
        self.current_turn: int = 0
        self.player_by_name = dict()
        self.messages_by_names: Dict[str, List] = dict()
        # self.num_players = len(player_backends)
        self.player_backends = player_backends
        # Initialise attributes that will be used for the evaluation scores
        self.aborted: int = 0
        self.lose: int = 0
        self.request_counts = 0
        self.last_round_played = 0
        self.parsed_request_counts = 0
        self.error_card_not_in_hand = 0
        self.error_card_doesnt_follow_suit = 0
        self.error_card_not_comprehensible = 0
        self.error_prediction_int_not_possible = 0
        self.error_prediction_not_comprehensible = 0

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
        trump = (self.trump_cards[round][0]
                 if self.trump_cards[round] else "")
        best_card = evaluate_trick(trick, trump)

        # Check which player played the best_card
        winner = [
            str(player) for player, card
            in self.played_cards[round][trick_round].items()
            if card == best_card
        ]

        return str(winner[0])

    def calculate_points(self, round, player):
        """Calculate points for a player in relation to last round."""
        points = evaluate_round(
            self.predictions[round][player], self.tricks_per_player[round][player])
        return points

    def add_player(self, model: str, name):
        """
        Add a player to the game.

        :param player: Player object to be added.
        """
        # if model == 'programmatic':
        #     apprentice = Apprentice("programmatic", name) # TODO: Check this with Hakimov
        # else:
        #     apprentice = Apprentice(model, name)
        apprentice = Apprentice(model, name)
        apprentice.descriptor = apprentice.player
        self.player_by_name[name] = apprentice
        self.messages_by_names[name] = []

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
        player.history = []  # Reset history after message has been sent
        self.messages_by_names[player.descriptor] = [] # Reset history after message has been sent
        action = {'type': 'get message', 'content': answer}
        self.log_event(
            from_=str(player.player),
            to='GM',
            action=action,
            call=(copy.deepcopy(prompt), raw_answer)
        )
        return answer

    def parse_prediction(self, answer, round, prompt=None, receiver=None):
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
            self.error_card_not_comprehensible += 1
            prompt += self.correction_prediction_structure_prompt
            result = re.sub("§ANSWER", str(answer), prompt) # Must be handled like this because of Template() function
            return result

        if not self.parser.is_possible_prediction(prediction, round):
            self.error_prediction_int_not_possible += 1
            prompt += self.correction_prediction_structure_prompt
            result = re.sub("§ANSWER", str(answer), prompt)
            return result

        return int(prediction)

    def parse_card(self, answer, hand, trick, prompt=None, player=None, round=None):
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
            self.error_card_not_comprehensible += 1
            prompt += self.correction_card_structure_prompt
            result = re.sub("§ANSWER", str(answer), prompt)
            return result

        if not self.parser.is_in_hand(card, hand):
            self.error_card_not_in_hand += 1
            prompt += self.correction_hand_prompt
            result = re.sub("§ANSWER", str(answer), prompt)
            return result

        if not self.parser.follows_suit(card, hand, trick):
            self.error_card_doesnt_follow_suit += 1
            prompt += self.correction_suit_prompt
            result = re.sub("§ANSWER", str(answer), prompt)
            return result

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

        self.request_counts += 1 # TODO: Not being used

        # print(prompt)
        # print(answer)

        # Get an answer depending on the exectation and return if valid
        if expect == "prediction":
            parse = self.parse_prediction(answer, round, prompt, receiver)
            if self.parser.validate_prediction(answer, round):
                self.parsed_request_counts += 1
                return parse
        elif expect == "card":
            parse = self.parse_card(answer, hand, trick, prompt, receiver, round)
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
            self.last_round_played = round
            self.log_eval_assets()
            raise InvalidAnswerError

    def setup(self, **game_instance) -> None:
        """
        Set up the game with the provided game instance configuration.

        :param game_instance: Configuration dictionary for the game instance.
        """
        # Import game instances
        self.game_instance = game_instance
        self.game_id = self.game_instance["game_id"]
        self.seating_order = self.game_instance["seating_order"]
        self.dealt_cards = self.game_instance["dealt_cards"]
        self.trump_cards = self.game_instance["trump_cards"]

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

        # check if there are enough models and players
        assert len(self.player_backends) == len(self.playing_order)

        # create player: Gandalf is the model, the rest gets random names
        names = self.seating_order.copy()
        names.remove('Gandalf')

        for idx, model in enumerate(self.player_backends):
            if idx == 0:
                self.add_player(model, "Gandalf")
            else:
                self.add_player(model, names.pop(0))

        # num_players = len(self.playing_order["2"][1])

        # list_names = ['Gandalf', 'Merlin', 'Oz', 'Harry', 'Giogini', 'Houdini', 'Carlos']
        # list_names = list_names[:num_players]

        # for index, _ in enumerate(self.player_backends):
        #     name = self.seating_order[index]
        #     # if name is "Gandalf"
        #     self.add_player(getattr(self, f"model_{index}"), list_names[index])

        self.predictions = {
            d: dict.fromkeys(self.seating_order, None)
            for d in self.dealt_cards.keys()
        }

        self.points = {
            d: dict.fromkeys(self.seating_order, 0)
            for d in self.dealt_cards.keys()
        }

        self.tricks_per_player = {
            d: dict.fromkeys(self.seating_order, 0)
            for d in self.dealt_cards.keys()
        }

        self.played_cards = {
            d: {dd: dict.fromkeys(self.seating_order)
                for dd in range(1, int(d)+1)}
            for d in self.dealt_cards.keys()
        }

        self.log_players({
            apprentice: f'{apprentice}: {self.player_by_name[apprentice].model}'
            for apprentice in self.player_by_name
        })

        self.played_cards_in_game = []

    def get_last_complete_trick(self, played_cards):
        for trick_number in reversed(sorted(played_cards.keys())):
            trick_data = played_cards[trick_number]
            if all(card is not None for card in trick_data.values()):
                return trick_number, trick_data
        return None, None  # Return None if no complete trick is found

    def get_ordered_trick_cards(self, played_cards, playing_order):
        ordered_cards = {}
        for player in playing_order:
            ordered_cards[player] = played_cards[player]
        return ordered_cards

    def update_info(self, round, trick_round, players_name, previous_play = False, winner=None):
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

        if round and players_name:
            self.info['PLAYER_NAME'] = str(players_name)
            # Declare trump color
            self.info['TRUMP_CARD'] = str(self.trump_cards[round])
            self.info['TRUMP_COLOR'] = (self.info['TRUMP_CARD'][0]
                                        if self.info['TRUMP_CARD'] != "None"
                                        else str(None)
                                        )
            self.info['HAND_SIZE'] = round
            # Declare current and full player hand
            self.info['PLAYER_HAND'] = self.dealt_cards[round][str(
                players_name)]
            self.info['CURRENT_PLAYER_HAND'] = (
                self.get_current_hand(round, players_name)
            )

            # Declare player position
            self.info['PLAYER_POSITION'] = (
                self.playing_order[round][1].index(players_name) + 1
            )

            num_players = len(self.playing_order[round][1])

            if previous_play is True:
                self.info['PLAYER_PREDICTIONS'] = list(self.predictions[round].items())[:num_players]
                self.info['PLAYER_PREDICTIONS_LAST_ROUND'] = list(self.predictions[round].items())[num_players:]
            else:
                self.info['PLAYER_PREDICTIONS'] = [
                    (player, prediction) for player, prediction
                    in self.predictions[round].items()
                ][:num_players]
                self.info['PLAYER_PREDICTIONS_LAST_ROUND'] = ""

            # Declare leaderboard self.info
            self.info['LEADERBOARD_TRICKS'] = list(
                self.tricks_per_player[round].items())[:num_players]
            self.info['LEADERBOARD_POINTS'] = list(self.points[round].items())[:num_players]

            if int(round) > 2:
                trick_number, trick_data = self.get_last_complete_trick(
                    self.played_cards[str(int(round) - 1)])
            else:
                trick_number, trick_data = self.get_last_complete_trick(
                    self.played_cards[round])

            if trick_number is not None:
                playing_order = self.playing_order[round][trick_number]
                ordered_trick_data = self.get_ordered_trick_cards(
                    trick_data, playing_order)
                self.info['CARDS_PLAYED_LAST_TRICK'] = ordered_trick_data
            else:
                self.info['CARDS_PLAYED_LAST_TRICK'] = ''

            self.info['CARDS_PLAYED_IN_GAME'] = self.played_cards_in_game



        if round and players_name and trick_round:
            # Declare leaderboard self.info
            self.info['LEADERBOARD_TRICKS'] = list(
                self.tricks_per_player[round].items())[:num_players]
            self.info['LEADERBOARD_POINTS'] = list(self.points[round].items())[:num_players]

            self.info['PLAYER_NAME'] = str(players_name)
            # Declare which cards were played already and last trick
            self.info['CARDS_PLAYED'] = (
                self.get_current_trick(round, trick_round)
            )
            # Declare player position
            self.info['PLAYER_POSITION'] = (
                self.playing_order[round][trick_round].index(players_name) + 1
            )

            if trick_round == 1 and int(round) > 2:
                trick_number, trick_data = self.get_last_complete_trick(
                    self.played_cards[str(int(round)-1)])
            else:
                trick_number, trick_data = self.get_last_complete_trick(
                    self.played_cards[str(int(round))])


            if trick_number is not None:
                playing_order = self.playing_order[round][trick_number]
                ordered_trick_data = self.get_ordered_trick_cards(
                    trick_data, playing_order)
                self.info['CARDS_PLAYED_LAST_TRICK'] = ordered_trick_data

            self.info['CARDS_PLAYED_IN_GAME'] = self.played_cards_in_game

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

        # START round
        next_prompt = self.rules_prompt
        for round in self.dealt_cards:
            print("\nRound " + str(round) + "\n", end='')
            self.log_next_turn()

            # GET PREDICTIONS
            next_prompt += self.round_start_prompt
            for player in self.playing_order[round][1]:
                # Gather and update information for the prompting
                if int(round) > 2:
                    self.update_info(str(int(round)-1), None, player, previous_play=True)
                else:
                    self.update_info(round, None, player)
                receiver = self.player_by_name[player]
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
                self.predictions[round][str(receiver.player)] = prediction

            # START trick round
            next_prompt = self.rules_prompt
            next_prompt += self.trick_start_prompt
            for trick_round in range(1, int(round)+1):
                print("Trick round: " + str(trick_round) + "\n", end='')
                # GET CARDS
                for player in self.playing_order[round][trick_round]:
                    # Gather and update information for the prompting
                    self.update_info(round, trick_round, player)
                    receiver = self.player_by_name[player]
                    trick = self.get_current_trick(round, trick_round)
                    hand = self.get_current_hand(round, player)
                    # Prompt the model
                    try:
                        card = self.prompt_model(
                            next_prompt, receiver, "card", round, hand, trick
                        )
                    except InvalidAnswerError:
                        return None
                    except AttributeError:
                        return None

                    # save the played card
                    self.played_cards[round][trick_round][player] = card
                    self.played_cards_in_game.append(card)


                # END OF TRICK
                # Determine the winner of the trick
                winner = self.determine_trick_winner(round, trick_round)
                # Update info and leaderboard
                self.update_info(None, None, player, winner=winner)
                self.tricks_per_player[str(round)][str(winner)] += 1
                # Shift seating order to winner and save the new order

                winner_index = self.playing_order[round][trick_round].index(
                    winner)
                new_order = self.playing_order[round][trick_round][winner_index:] + \
                    self.playing_order[round][trick_round][:winner_index]

                if max(range(1, int(round)+1)) == trick_round and max(self.dealt_cards) != round:
                    try:
                        self.playing_order[str(int(round) + 1)][1] = new_order
                    except KeyError:
                        pass
                elif max(self.dealt_cards) == round and max(range(1, int(round)+1)) == trick_round:
                    pass
                else:
                    self.playing_order[round][trick_round + 1] = new_order

                # Set new next prompt template
                next_prompt = self.rules_prompt
                next_prompt += self.trick_end_prompt + self.trick_start_prompt

            # END OF ROUND
            # calculate points for all player
            for player in self.player_by_name.keys():
                self.points[round][player] = self.calculate_points(
                    round, player)
            # Shift original seating_order by one and save it
            current_order = (self.playing_order[round][1][1:] +
                             self.playing_order[round][1][:1])
            # a bit of a unclean hack. In the last round, there are no keys
            # left
            try:
                self.playing_order[str(int(round)+1)][1] = current_order
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
        self.last_round_played = round
        self.log_eval_assets()

        return

    def log_eval_assets(self) -> None:
        """Aux to log variables needed for scoring (firstlast specific)"""
        self.log_key('predictions', self.predictions)
        self.log_key('tricks_per_player', self.tricks_per_player)
        self.log_key('points', self.points)
        self.log_key('last_round', self.last_round_played)
        self.log_key('error_card_not_in_hand', self.error_card_not_in_hand)
        self.log_key('error_card_doesnt_follow_suit', self.error_card_doesnt_follow_suit)
        self.log_key('error_card_not_comprehensible', self.error_card_not_comprehensible)
        self.log_key('error_prediction_int_not_possible', self.error_prediction_int_not_possible)
        self.log_key('error_prediction_not_comprehensible', self.error_prediction_not_comprehensible)
        self.log_key(ms.METRIC_LOSE, self.lose)
        self.log_key(ms.METRIC_ABORTED, self.aborted)
        self.log_key(ms.METRIC_REQUEST_COUNT, self.request_counts)
        self.log_key(ms.METRIC_REQUEST_COUNT_PARSED,
                     self.parsed_request_counts)

def calculate_gandalf_points(data):
    total_points = 0
    for key in data:
        if 'Gandalf' in data[key]:
            total_points += data[key]['Gandalf']
    return total_points

def calculate_merlin_points(data):
    total_points = 0
    for key in data:
        if 'Merlin' in data[key]:
            total_points += data[key]['Merlin']
    return total_points

def calculate_oz_points(data):
    total_points = 0
    for key in data:
        if 'Oz' in data[key]:
            total_points += data[key]['Oz']
    return total_points

def transform_clemscore(points, rounds):
    """Transform the points to a value between 0 and 100 for the clemscore."""
    # This uses a sigmoid function which isn't usable.
    # return 100 / (1 + np.exp(-k * x))

    # Gauß'sche Summenformel
    base_value = ((rounds * (rounds+1)) // 2) * 10
    max_points = base_value + (20 * rounds)
    min_points = -base_value

    clemscore = ((points - min_points) * 100) / (max_points-min_points)

    return clemscore

class WizardsApprenticeScorer(GameScorer):
    def __init__(self, experiment: Dict, game_instance: Dict):
        super().__init__(GAME_NAME, experiment, game_instance)

    def compute_scores(self, episode_interactions: Dict) -> None:
        """Compute episode-level and turn-level scores (mandatory)."""
        aborted = int(episode_interactions[ms.METRIC_ABORTED])
        requests = episode_interactions[ms.METRIC_REQUEST_COUNT]
        p_requests = episode_interactions[ms.METRIC_REQUEST_COUNT_PARSED]
        v_requests = requests - p_requests
        if requests > 0:
            request_success_rate = p_requests / requests
        else:
            request_success_rate = 0

        points = calculate_gandalf_points(episode_interactions["points"])
        lose = 1 if ((points < calculate_merlin_points(episode_interactions["points"])) and (points < calculate_oz_points(episode_interactions["points"]))) else 0
        success = 1 - lose if not aborted else 0

        rounds = len(episode_interactions['points'])
        bench_score = transform_clemscore(points, int(rounds)) if not aborted else 0

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

    def create_game_scorer(self, experiment: Dict, game_instance: Dict) -> GameScorer:
        return WizardsApprenticeScorer(experiment, game_instance)

    def create_game_master(self, experiment: dict, player_backends: list[str]) -> GameMaster:
        return WizardsApprenticeGameMaster(self.name, experiment, player_backends)

    def is_single_player(self) -> bool:
        return False
