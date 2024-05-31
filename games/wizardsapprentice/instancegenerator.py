"""
This is the class that produces our game instances.
"""

import random
from clemgame.clemgame import GameInstanceGenerator

GAME_NAME = "Wizard's Apprentice"
SEED = 123


class WizardsApprenticeInstanceGenerator(GameInstanceGenerator):

    def __init__(self):
        super().__init__(GAME_NAME)

    def on_generate(self):
        """
        We have to build this method ourselves.

        - write a class that inherits from GameInstanceGenerator.
        - you must implement the on_generate method, which should call
        self.add_experiment() to add experiments and self.add_game_instance()
        to add instances. Populate the game instance with keys and values.
        - GameInstanceGenerator has methods to load various files inside the
        game directory, for example self.load_template() and self.load_file().
        - in '__main__', call FirstLastGameInstanceGenerator().generate().
        - set a random seed if your generation relies on randomness; when you
        need new instances, change the random seed.
        """
        pass


if __name__ == '__main__':
    random.seed(SEED)
    WizardsApprenticeInstanceGenerator().generate()
