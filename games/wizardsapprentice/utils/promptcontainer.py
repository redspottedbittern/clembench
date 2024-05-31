"""Container class for all prompts."""

from clemgame.clemgame import GameResourceLocator
from string import Template


class PromptContainer(GameResourceLocator):
    """
    Container class for all prompts.

    The prompts are modular and need to be connected depending on the
    current situation of the game.

    Keywords:
        rules: contains information if the game is starting and no keywords
        round_start: num_cards, num_players, trump_card, trump_color,
            player_position, player_hand, player_predictions
        trick_start: num_cards, num_players, trump_card, trump_color,
            player_position, player_hand, player_hand_current,
            cards_played, player_predictions
        trick_end: cards_played_last_trick, winner_last_trick, player_tricks
        round_end: player_predictions_last_round, point_table, player_tricks
        game_end: winner
        correction_hand: none
        correction_regex: needs a regex for the correct format of the input
        correction_suit: none
    """

    def __init__(self):
        """
        Load the text files and turn them into Templates.

        This class loads all needed prompts and returns them with substituted
        keywords if needed.
        """
        # this are the filenames of the different prompts
        self.prompt_names = [
            "rules",
            "round_start",
            "trick_start",
            "trick_end",
            "round_end",
            "game_end",
            "correction_suit",
            "correction_hand",
            "correction_regex"
        ]

        # load the texts and save them in a dictionary
        self.prompts = self.load_prompts(self.prompt_names)

    def load_prompts(self, prompt_names):
        """
        Loader function for text prompts.

        The text for the different prompts is saved in seperate txt files. This
        function reads them in and

        Returns: A Template object for every prompt.
        """
        # set the path of the current file
        folder = 'ressources/'

        # create a dictionary to hold the different prompt templates
        prompts = {}

        for name in prompt_names:
            # Construct the full file path
            full_path = folder + name

            # use the parent classes loader function
            text = self.load_file(full_path, file_ending='.template')

            # save as a template in the dictionary
            prompts[name] = Template(text)

        return prompts

    def substitute(self, prompt, keywords):
        """
        Substitute the keywords in a Template from a dictionary.

        Parameters:
            prompt (str): name of the prompt template
            keywords (dict): key value pairs for the substitution in the
            Template
        """
        return self.prompts[prompt].substitute(keywords)
