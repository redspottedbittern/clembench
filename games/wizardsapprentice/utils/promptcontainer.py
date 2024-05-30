"""Container class for all prompts."""

import os
from string import Template


class PromptContainer():
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
        self.prompt_texts = [
            "rules.template",
            "round_start.template",
            "trick_start.template",
            "trick_end.template",
            "round_end.template",
            "game_end.template",
            "correction_suit.template",
            "correction_hand.template",
            "correction_regex.template"
        ]

        # load the texts and save them in a dictionary
        self.prompts = self.load_prompts(self.prompt_texts)

    def load_prompts(self, text_files):
        """
        Loader function for text prompts.

        The text for the different prompts is saved in seperate txt files. This
        function reads them in and

        Returns: A Template object for every prompt.
        """
        # get the path of the current file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_dir = script_dir.rsplit('/', 1)[0]
        prompt_dir = os.path.join(script_dir, 'ressources')

        # create a dictionary to hold the different prompt templates
        prompts = {}

        for filename in text_files:
            # Construct the full file path
            full_path = os.path.join(prompt_dir, filename)

            # load the text and save it as a Template
            with open(full_path, 'r') as f:
                text = f.read()
                prompts[filename.split('.')[0]] = Template(text)

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
