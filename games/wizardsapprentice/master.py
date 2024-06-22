from typing import List, Tuple, Dict
from string import Template
import collections

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

logger = get_logger(__name__)


class Apprentice(Player):
    def __init__(self, model_name: str, player: str):
        super().__init__(model_name)
        self.player: str = player

        # a list to keep the dialogue history
        self.history: List = []


class WizardsApprenticeGameMaster(GameMaster):
    def __init__(self, experiment: Dict, player_backends: List[Model]):
        super().__init__(GAME_NAME, experiment, player_backends)
        self.config = experiment
        self.player_model_names = [
            player_model.get_name() for player_model in player_backends
        ]
        self.messages_by_names: Dict[str, List] = dict()
        self.players_by_names: Dict[str, Player] = collections.OrderedDict()


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
        self.regex = self.config['regex']
        # self.card_played = self.config["card_played"]
        # self.wizard = self.config["wizard"]
        # self.jester = self.config["jester"]
        # self.prediction = self.config["prediction"]

        # define parser
        self.parser = Parser(self.regex)

        # Defines models
        self.model_a = player_backends[0]
        self.model_b = player_backends[1]

    def setup(self, **game_instance):
        logger.info("SETUP")

        # Import game instances
        self.game_instance = game_instance
        self.game_id = self.game_instance["game_id"]
        self.seating_order = self.game_instance["seating_order"]
        self.dealt_cards = self.game_instance["dealt_cards"]

        # Create the players
        self.apprentice1 = Apprentice(self.model_a, 1)
        self.apprentice2 = Apprentice(self.model_b, 2)

        self.add_player(self.apprentice1)
        self.add_player(self.apprentice2)


    def add_message(self, player: Player, utterance: str, role: str):
        message = {"role": role, "content": utterance}
        history = self.messages_by_names[player.descriptor]
        history.append(message)

    def add_user_message(self, player: Player, utterance: str):
        self.add_message(player, utterance, role="user")

    def add_player(self, player: Player):
        """
        Add a player to the game.

        Note: The players will be called in the same order as added!

        :param player: to be added to the game
        """
        idx = len(self.players_by_names)
        player.descriptor = f"Player {idx + 1}"
        self.players_by_names[player.descriptor] = player
        self.messages_by_names[player.descriptor] = []

    def prompt(self, player: Player, is_reprompt=False):
        # GM -> Player
        history = self.messages_by_names[player.descriptor]
        assert history, f"messages history must not be empty for {player.descriptor}"

        last_entry = history[-1]
        assert last_entry["role"] != "assistant", "Last entry should not be assistant " \
                                                  "b.c. this would be the role of the current player"
        message = last_entry["content"]

        action_type = 'send message' if not is_reprompt else 'send message (reprompt)'
        action = {'type': action_type, 'content': message}
        #self.log_event(from_='GM', to=player.descriptor, action=action)

        _prompt, _response, response_message = player(history, 1)
        print(response_message)

        # Player -> GM
        action = {'type': 'get message', 'content': response_message}
        #self.log_event(from_=player.descriptor, to="GM", action=action, call=(_prompt, _response))

        # GM -> GM
        #self.__validate_parse_and_add_player_response(player, response_message)

    def play(self):
        """
        info: dict that contains information for the string substitution
        leaderboard: dict of dicts to save points during the game
        current_hands: dict to manipulate current hand during one round
        playing_order = list to manipulate the current order of play
        """

        print(self.apprentice1.get_description())

        self.add_user_message(self.apprentice1, "Tell me a joke!")
        print(self.apprentice1.history)
        print(self.messages_by_names)
        self.prompt(self.apprentice1)

        #prompt, raw_answer, answer = self.apprentince1.__call__(self.apprentince1.history, 1)

        # create a leaderboard to calculate the score
        leaderboard = {}

        # declare info dict to substitute the prompts later
        info = {}
        # extract how many players there are and the total number of cards
        info['NUM_OTHER_PLAYERS'] = len(self.dealt_cards["1"]) - 2
        info['NUM_CARDS'] = len(self.dealt_cards)

        # add rules to next prompt
        next_prompt = self.rules_prompt
        # declare seating_order
        playing_order = self.seating_order


        # loop over all rounds
        for round, round_cards in self.dealt_cards.items():

            # leaderboard
            leaderboard[round] = {}

            # current player hands
            current_hands = {}

            # declare trump card for round
            info['TRUMP_CARD'] = str(round_cards['trump'])
            # declare trump color
            info['TRUMP_COLOR'] = (info['TRUMP_CARD'][0] if info['TRUMP_CARD']
                                   != "None" else str(None))
            # declare player predictions
            info['PLAYER_PREDICTIONS'] = ''

            # add round_start to next prompt
            next_prompt += self.round_start_prompt


            # FIRST: get predictions
            for position, player in enumerate(playing_order):

                # declare player hand
                info['PLAYER_HAND'] = round_cards[str(player)]
                # declare current player hand
                info['CURRENT_PLAYER_HAND'] = info['PLAYER_HAND'].copy()
                # declare player position
                info['PLAYER_POSITION'] = position + 1


                # PROMPT player for prediction
                next_prompt = Template(next_prompt)
                next_prompt = next_prompt.substitute(info)

                # send that to the model and parse the answer
                # answer = self.send_to_model(?!?!)
                # prediction = self.parse_prediction(answer, round)
                # TODO: actually send that to a model and delete the next lines
                answer = ''
                prediction = int(round) // info['NUM_OTHER_PLAYERS']
                # append answer to player predictions
                info['PLAYER_PREDICTIONS'] += str(prediction)
                # update the leaderboard
                leaderboard[round][player] = {}
                leaderboard[round][player]['tricks'] = 0
                leaderboard[round][player]['points'] = 0
                leaderboard[round][player]['prediction'] = prediction
                # fill current_hands
                current_hands[player] = info['CURRENT_PLAYER_HAND'].copy()


            # TIDY UP after prediction phase

            # clear next prompt and add trick_start to next prompt
            next_prompt = self.trick_start_prompt


            # NEXT: play the tricks
            for trick_round in range(1, int(round)+1):

                # declare trick
                info['CARDS_PLAYED'] = []

                # let every player play a card
                for position, player in enumerate(playing_order):

                    # declare player hand
                    info['PLAYER_HAND'] = round_cards[str(player)]
                    # declare current player hand
                    info['CURRENT_PLAYER_HAND'] = current_hands[player]

                    # declare player position
                    info['PLAYER_POSITION'] = position + 1

                    # PROMPT player for card
                    next_prompt = Template(next_prompt)
                    next_prompt = next_prompt.substitute(info)

                    # send that to the model and parse the answer
                    # answer = self.send_to_model(?!?!)
                    # card = self.parse_prediction(answer, round)
                    # TODO: actually send that to a model and delete the next lines
                    answer = ''
                    card = current_hands[player][0]

                    # add card to trick
                    info['CARDS_PLAYED'].append(card)
                    # substract card from current player hand
                    current_hands[player].remove(card)

                # NOW AFTER TRICK IS FINISHED
                # EVALUATE trick
                best_card = evaluate_trick(info['CARDS_PLAYED'], info['TRUMP_COLOR'])
                # check which player played the best_card
                winner = [player for player in self.seating_order if best_card
                          in round_cards[str(player)]][0]
                winner = int(winner)
                # declare winner
                info['WINNER_LAST_TRICK'] = winner
                # update leaderboard_tricks
                leaderboard[round][winner]['tricks'] += 1
                info['LEADERBOARD_TRICKS'] = [(player, value['tricks']) for player,
                                           value in leaderboard[round].items()]

                # shift seating order to winner
                playing_order = shift_to_winner(self.seating_order, winner)

                # TIDY UP after the trick is finished
                # declare last_trick by copying trick
                info['CARDS_PLAYED_LAST_TRICK'] = info['CARDS_PLAYED'].copy()
                # clear trick
                info['CARDS_PLAYED'] = []
                # add trick_end prompt
                next_prompt = self.trick_end_prompt + self.trick_start_prompt


            # NOW AFTER ROUND IS FINISHED

            # calculate points for all player
            for player in self.seating_order:
                d = leaderboard[round][player]
                d['points'] = evaluate_round(d['prediction'], d['tricks'])

            # declare last_predictios by copying predictions
            info['PLAYER_PREDICTIONS_LAST_ROUND'] = info['PLAYER_PREDICTIONS']
            # clear predictions
            info['PLAYER_PREDICTIONS'] = ''
            # declare leaderboard points
            info['LEADERBOARD_POINTS'] = [(player, value['points']) for player,
                                           value in leaderboard[round].items()]
            # shift original seating_order by one
            self.seating_order = (self.seating_order[1:] +
                                  self.seating_order[:1])
            # add round end to next prompt
            next_prompt = self.trick_end_prompt + self.round_end_prompt

        # declare winner_game
        end_points = [(values['points'], player) for player, values in
                      leaderboard[str(len(self.dealt_cards))].items()]
        info['WINNER_GAME'] = max(end_points)[1]
        # PROMPT for end game
        next_prompt += self.game_end_prompt
        next_prompt = Template(next_prompt)
        next_prompt = next_prompt.substitute(info)


        return None


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
            return  # TODO correction template

        if not self.parser.is_possible_prediction(prediction, round):
            return  # TODO correction template

        return int(prediction)
    
    def compute_scores():
        return None


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
