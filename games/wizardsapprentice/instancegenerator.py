"""
This is the class that produces our game instances.
"""

import random, sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from clemgame.clemgame import GameInstanceGenerator
from games.wizardsapprentice.utils.utils import *

GAME_NAME = "Wizard's Apprentice"
SEED = 123
NUM_ROUNDS = 9
START_ROUND = 1
PLAYERS = 2
COLORS =  ["G", "B", "R", "Y"],
CARDS_PER_COLOR =  13,
SPECIAL_CARDS = ["Z", "J"],
SPECIAL_CARDS_NUM = 4
RULES_PROMPT = "Let's play a game. You are playing a competitive card game in which you have to correctly predict how many tricks you are going to win in each round. In each trick round you and the other players take turns playing one card each. These cards together make up a trick. For example, if each player has five cards, you will play five tricks in one round. At the end of each trick round, you will earn points for a correct prediction and the number of tricks you've won. Additionally, in each round, you will get more cards, so you will play more tricks. The player who has earned the most points at the end of the game wins.\n\nA round consists of 4 phases:\n(a) Dealing Cards\n(b) Predicting Tricks\n(c) Playing Tricks\n(d) Earning Points\n\nRules:\n(a) After dealing the cards to each player, the first card of the remaining deck determines the trump color for this trick round. Every card in the trump color is a trump. A trump wins against any card of another color. At the start of each round, a new trump color is determined. The last round has no trump color.\n(b) If you play the first card in a trick, you may play any card. However, all other players must follow suit. This means they must play a card of the same color as the first card in the trick round. Trumps or other colors can only be played if you do not have any cards of the required color in your hand. While a trick is being played, the color you must follow suit with never changes.\n(c) There are 52 cards. Each card has a number from 1 to 13 and one of four colors: green, red, blue, and yellow. Cards are represented with a capital letter for the color and a number, like B5 for blue 5 or R12 for red 12.\n(d) There are also two kinds of special cards: four Wizards and four Jesters. They are represented by a capital letter Z for wizards and J for jester and a number. But here the number means no difference in power. Examples are Z1 or J3. A wizard also wins the trick, they are played in. A Jester never wins a trick.\n(e) Wizards and Jesters can be played at any time, even if you have to follow suit. They do not have any color. Wizards always win the trick round. Jesters always lose the trick round.\n(f) At the start, each player predicts how many tricks they'll win. The goal is to match your prediction. \n(g) When there are no more cards in the deck, the game is finished.",
ROUND_START_PROMPT =  "\nLet us start:\n\nYou're playing with $NUM_OTHER_PLAYERS$ other player(s), and you're player number $PLAYER_POSITION$. \nEach player gets $NUM_CARDS$ card(s), and the rest stay in the deck. I've shuffled the cards. \nThe trump card is $TRUMP_CARD$, thereby the trump color is $TRUMP_COLOR$.\n\nYou've been dealt the following cards: $PLAYER_HAND$.$PLAYER_PREDICTIONS$\n\nNow you have to predict how many tricks you will get. What's your prediction?\n\nImportant! Anwer only in this format: 'PREDICTION: number'. Omit any other text.",
TRICK_START_PROMPT = "\nIt's your turn to play a card in the current trick!\n\nYou're playing with $NUM_OTHER_PLAYERS$ other player(s), and you're player number $PLAYER_POSITION$.\n\nEach player has $NUM_CARDS$ card(s). The trump card is $TRUMP_CARD$, thereby the trump color is $TRUMP_COLOR$.\n$PLAYER_PREDICTIONS$.\n\nYour current hand is: $PLAYER_HAND$.$CARDS_PLAYED$\n\nNow you have to play a card from your current hand. Which card do you play? \n\nImportant: Answer in this format: 'PLAYED: color + number'. Omit any other text.",
TRICK_END_PROMPT = "\nIn the last trick, these cards were played: $CARDS_PLAYED_LAST_TRICK$. Thereby player number $WINNER$ has won the trick. This is, how many tricks every player has won so far: $LEADERBOARD_TRICK_ROUND$.",
ROUND_END_PROMPT = "\nThis round is over. All cards were played.\n\nThese were the players predictions: $PLAYER_PREDICTIONS$. \nThis is how many tricks every player won: $LEADERBOARD_TRICK_ROUND$. \n\nBecause of the difference of predictions and tricks, every player receives points. The point table looks as follows: $LEADERBOARD_GAME$",


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
        experiment = self.add_experiment(SEED)
        experiment["rules_prompt"] = RULES_PROMPT
        experiment["round_start_prompt"] = ROUND_START_PROMPT
        experiment["trick_start_prompt"] = TRICK_START_PROMPT
        experiment["trick_end_prompt"] = TRICK_END_PROMPT
        experiment["round_end_prompt"] = ROUND_END_PROMPT
        experiment["table"] = create_table(PLAYERS-1)
        experiment["deck"] = create_deck(COLORS, CARDS_PER_COLOR, SPECIAL_CARDS, SPECIAL_CARDS_NUM)
        experiment["player_positions"] = get_players_by_order(experiment["table"])
        for round in range(START_ROUND, self.rounds_to_be_played(len(experiment["deck"]), PLAYERS, NUM_ROUNDS)):
            game_instance = self.add_game_instance(experiment, round)
            game_instance["game_deck"] = experiment["deck"].copy()
            game_instance["players_position"] = get_players_by_order(experiment["table"])
            game_instance["player_cards"] = {}
            for player in game_instance["players_position"]:
                dealt_cards = get_random_undealt_cards(game_instance["game_deck"], round)
                game_instance["player_cards"][player] = dealt_cards

            # Get random trump card and color for the round
            game_instance["trump_card"] = get_random_trump_card(game_instance["game_deck"])
            # Finds keys with same trump color for the round
            keys_with_trump_color = [key for key, value in game_instance["game_deck"].items() if value.get("color") == game_instance["game_deck"][str(game_instance["trump_card"])]["color"]]
            # Sets the trump attribute to True for cards with the same color as the trump card for the round
            for key in keys_with_trump_color:
                game_instance["game_deck"]["trump"] = True
                        
    def rounds_to_be_played(self, number_of_cards, number_of_players, rounds_suggested):
        if rounds_suggested == -1:
            if not number_of_cards % number_of_players == 0:
                raise Exception('Deck needs to be divisible by players')
            return number_of_cards // number_of_players
        else:
            return rounds_suggested
        
if __name__ == '__main__':
    #random.seed(SEED)
    WizardsApprenticeInstanceGenerator().generate()
