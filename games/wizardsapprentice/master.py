"""
Main Game class for the Wizard's Apprentice.
"""

from backends import Model, CustomResponseModel
from clemgame.clemgame import GameMaster, GameBenchmark, Player, DialogueGameMaster
from clemgame import get_logger
from games.wizardsapprentice.utils import *

logger = get_logger(__name__)

GAME_NAME = "wizardsapprentice"

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

        # Import prompts
        self.rules_prompt = self.experiment["rules_prompt"]
        self.round_start_prompt = self.experiment["round_start_prompt"]
        self.round_start_prompt = self.round_start_prompt.replace("$NUM_OTHER_PLAYERS$", str(self.experiment["NUM_OTHER_PLAYERS"]-1)) # TODO: When 3 players, erase -1
        self.trick_start_prompt = self.experiment["trick_start_prompt"]

        # Create table for the round
        self.table = create_table(self.experiment["NUM_PLAYERS"]-1) # TODO: When 3 players, erase -1

        # Create deck for the round (with randomized order)
        self.deck = create_deck(self.experiment["colors"], self.experiment["cards_per_color"], self.experiment["special_cards"], self.experiment["special_cards_num"])

    def setup(self, **game_parameters):
        """
        Mandatatory function.

        This takes all the keys and values from the instanciation.
        """
        logger.info("setup")

        # Imports instance parameters (in this case only number of cards)
        self.game_parameters = game_parameters

        # Deal cards based on order in table for the round
        self.players_position = get_players_by_order(self.table)
        for player in self.players_position:
            self.dealt_cards = get_random_undealt_cards(self.deck, self.game_parameters["NUM_CARDS"])
            self.table[player]['Cards_dealt'] = self.dealt_cards

        # Get random trump card and color for the round
        self.trump_card = get_random_trump_card(self.deck)
        # Finds keys with same trump color
        keys_with_trump_color = [key for key, value in self.deck.items() if value.get("color") == self.deck[str(self.trump_card)]["color"]]
        # Sets the trump attribute to True for cards with the same color as the trump card
        for key in keys_with_trump_color:
            self.deck[key]["trump"] = True
            
        # Create the players TODO: How do we add a third model?
        self.apprentince1 = Apprentice(self.model_a)
        self.apprentince2 = Apprentice(self.model_b)

        # Add the players: these will be logged to the records interactions.json
        # Note: During game play the players will be called in the order added here
        # TODO: How do we make the game comply to order of table?
        self.add_player(self.apprentince1)
        self.add_player(self.apprentince2)


    def play(self):
        """
        Mandatory function.

        Main function for the game.
        """

        # TODO: Explain rules

        # Prompt Round start template
        for idx, val in enumerate(self.players_position): # TODO: Get right order of players, for now focused on prompting
            start_prompt = self.round_start_prompt.replace("$PLAYER_POSITION$", str(val)) #Notice we do not want to update the original round_start_prompt from the setup
            start_prompt = start_prompt.replace("$NUM_CARDS$", str(self.game_parameters["NUM_CARDS"])) 
            start_prompt = start_prompt.replace("$TRUMP_CARD$", str(self.trump_card)) 
            start_prompt = start_prompt.replace("$TRUMP_COLOR$", str(self.deck[str(self.trump_card)]["color"])) 
            start_prompt = start_prompt.replace("$PLAYER_HAND$", str(self.table[int(val)]["Cards_dealt"])) 

            if val == 1:
                start_prompt = start_prompt.replace("$PLAYER_PREDICTIONS$","")
            else:
                # TODO: Text for players predictions so far
                start_prompt = start_prompt.replace("$PLAYER_PREDICTIONS$", "\n\n$PLAYER_PREDICTIONS$")
            print(start_prompt)


        # Loop through trick rounds
        for trick_round in range(1, int(self.game_parameters["game_id"]+1)):
            print("Trick round: ", trick_round)
            # 4. Based on players order, generate trick start template 

            # 5. Accepts or denies input of player
            # 5. When trick round is over, prompt end of trick round
        
        # 6. When round is over, prompt end of round with leaderboard
        # 7. TODO: Calculate score so far

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
