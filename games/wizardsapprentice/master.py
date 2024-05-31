"""
Main Game class for the Wizard's Apprentice.
"""

from clemgame.clemgame import DialogueGameMaster
from clemgame.clemgame import GameBenchmark
from games.wizardsapprentice.instancegenerator import GAME_NAME


class WizardsApprenticeGameMaster(DialogueGameMaster):
    def __init__(self, experiment: dict, player_backends: list[str]):
        super().__init__(GAME_NAME, experiment, player_backends)

        self.model_a = player_backends[0]
        self.model_b = player_backends[1]
        pass

    def setup(self, **game_parameters):
        """
        Mandatatory function.

        This takes all the keys and values from the instanciation.
        """
        pass

    def play(self):
        """
        Mandatory function.

        Main function for the game.
        """
        pass

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
        pass

    def is_single_player(self) -> bool:
        return False
