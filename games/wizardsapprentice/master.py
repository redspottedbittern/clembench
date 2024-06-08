"""
Main Game class for the Wizard's Apprentice.
"""

from backends import Model, CustomResponseModel
from clemgame.clemgame import GameMaster, GameBenchmark, Player, DialogueGameMaster
from clemgame import get_logger
from games.wizardsapprentice.utils.utils import *
from games.wizardsapprentice.instancegenerator import GAME_NAME

logger = get_logger(__name__)


class Apprentice(Player):
    def __init__(self, name):
        super().__init__(CustomResponseModel())
        self.name = name

class WizardsApprenticeGameMaster(DialogueGameMaster):
    def __init__(self, experiment: dict, player_backends: list[str]):
        super().__init__(GAME_NAME, experiment, player_backends)

        # Defines models TODO: How do we add a third model?
        self.model_a = player_backends[0]
        self.model_b = player_backends[1]

        # Import prompts from instance
        self.rules_prompt = self.experiment["rules_prompt"]
        self.round_start_prompt = self.experiment["round_start_prompt"]
        self.round_start_prompt = self.round_start_prompt.replace("$NUM_OTHER_PLAYERS$", str(self.experiment["NUM_OTHER_PLAYERS"]-1)) # TODO: When 3 players, erase -1
        self.trick_start_prompt = self.experiment["trick_start_prompt"]
        self.trick_start_prompt = self.trick_start_prompt.replace("$NUM_OTHER_PLAYERS$", str(self.experiment["NUM_OTHER_PLAYERS"]-1)) # TODO: When 3 players, erase -1
        self.trick_end_prompt = self.experiment["trick_end_prompt"]
        self.round_end_prompt = self.experiment["round_end_prompt"]
        # Create table for the round
        self.table = create_table(self.experiment["NUM_PLAYERS"]-1) # TODO: When 3 players, erase -1

        # Create deck for the round (with randomized order for players)
        self.deck = create_deck(self.experiment["colors"], self.experiment["cards_per_color"], self.experiment["special_cards"], self.experiment["special_cards_num"])

    def setup(self, **game_parameters):
        """
        Mandatatory function.

        This takes all the keys and values from the instanciation.
        """
        logger.info("setup")

        # Imports instance parameters (in this case only number of cards necessary)
        self.game_parameters = game_parameters

        # Deal cards based on order in table for the round
        self.players_position = get_players_by_order(self.table)
        for player in self.players_position:
            self.dealt_cards = get_random_undealt_cards(self.deck, self.game_parameters["NUM_CARDS"])
            self.table[player]['Cards_dealt'] = self.dealt_cards

        # Get random trump card and color for the round
        self.trump_card = get_random_trump_card(self.deck)
        # Finds keys with same trump color for the round
        keys_with_trump_color = [key for key, value in self.deck.items() if value.get("color") == self.deck[str(self.trump_card)]["color"]]
        # Sets the trump attribute to True for cards with the same color as the trump card for the round
        for key in keys_with_trump_color:
            self.deck[key]["trump"] = True
            
        # Create the players TODO: How do we add a third model?
        self.apprentince1 = Apprentice(self.model_a)
        self.apprentince2 = Apprentice(self.model_b)

        # Add the players: these will be logged to the records interactions.json
        # Note: During game play the players will be called in the order added here
        # TODO: How do we make the game comply to order of table? 
        # Correction: Really doesnt matter as play() already deals succesfully. 
        # LLMs are being tested to understand which num of player they are, even if in a different order, e.g. Order:3 PlayerN:2.
        self.add_player(self.apprentince1)
        self.add_player(self.apprentince2)


    def play(self):
        """
        Mandatory function.

        Main function for the game.
        """

        # TODO: Include prompt to explain rules

        # Prompt round start template
        for idx, val in enumerate(self.players_position):
            start_prompt = self.round_start_prompt.replace("$PLAYER_POSITION$", str(val)) #Notice we do not want to update the original round_start_prompt from the setup
            start_prompt = start_prompt.replace("$NUM_CARDS$", str(self.game_parameters["NUM_CARDS"])) 
            start_prompt = start_prompt.replace("$TRUMP_CARD$", str(self.trump_card)) 
            start_prompt = start_prompt.replace("$TRUMP_COLOR$", str(self.deck[str(self.trump_card)]["color"])) 
            start_prompt = start_prompt.replace("$PLAYER_HAND$", str(self.table[int(val)]["Cards_dealt"]))

            if idx == 0:
                start_prompt = start_prompt.replace("$PLAYER_PREDICTIONS$"," You are the first one to play, so there are no predictions so far.")
                self.table[val]['Prediction'] = "TEST" # TODO: Remove when players are ready. Only for testing.
            else:
                start_prompt = start_prompt.replace("$PLAYER_PREDICTIONS$", str(summarize_trick_round(self.table)))

        # Loop through trick rounds
        for trick_round in range(1, int(self.game_parameters["NUM_CARDS"]+1)):
            idx = 0
            # Loop through players in the correct order to let them play
            for val in self.players_position:
                # Start trick prompt:
                trick_prompt = self.trick_start_prompt.replace("$PLAYER_POSITION$", str(val)) #Notice we do not want to update the original round_start_prompt from the setup
                trick_prompt = trick_prompt.replace("$NUM_CARDS$", str(self.game_parameters["NUM_CARDS"]))
                trick_prompt = trick_prompt.replace("$TRUMP_CARD$", str(self.trump_card)) 
                trick_prompt = trick_prompt.replace("$TRUMP_COLOR$", str(self.deck[str(self.trump_card)]["color"])) 
                trick_prompt = trick_prompt.replace("$PLAYER_HAND$", str(self.table[int(val)]["Cards_dealt"]))

                # In case its the first play in the first trick round
                if trick_round == 1 and idx == 0:
                    trick_prompt = trick_prompt.replace("$PLAYER_PREDICTIONS$","You are the first one to play, so there are no predictions so far")
                    trick_prompt = trick_prompt.replace("$CARDS_PLAYED$", "")                    
                    self.table[val]['Prediction'] = "TEST" # TODO: Remove when players are ready. Only for testing.
                else: # If not the first play, repeats predictions of other players and cards played so far
                    trick_prompt = trick_prompt.replace("$PLAYER_PREDICTIONS$", str("\nAfter careful consideration, the players' predictions are as follows: " + summarize_trick_round(self.table)))
                    trick_prompt = trick_prompt.replace("$CARDS_PLAYED$", str("\n\nThese cards have been played in this trick already in this order: " + get_ordered_played_cards(self.table)))

                print(trick_prompt)

                test = input() # TODO: Remove when players are ready. Only for testing.
                # TODO: Accepts or denies input of player
                remove_card(self.table, val, str(test)) # Removes played card and updates the table

                idx += 1

            # Prompts results for trick round
            # TODO: Decide winner (use utils.py), update table (see "Tricks_won"), generate text with won tricks by each player, similar to summarize_trick_round()
            tend_prompt = self.trick_end_prompt.replace("$CARDS_PLAYED_LAST_TRICK$", get_ordered_played_cards(self.table))
            print(tend_prompt)

        # TODO: Calculate score so far
        # TODO: Generate leaderboard for round 
        rend_prompt = self.round_end_prompt.replace("$PLAYER_PREDICTIONS$", str(summarize_trick_round(self.table)))
        print(rend_prompt)

    def parse_answer(self, answer):
        """
        Parse the answer from the LLM.

        This function takes the answer from the LLM, checks if it is a viable
        answer, that follows the move rules.

        Returns:
            - if predction: int
            - if card: str and int
        """
        r"^I PLAY:\s([GBRY]([1-9]|1[0123])|[ZJ])$"
        pass


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
