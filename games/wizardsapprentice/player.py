import random
from typing import List
from clemgame.clemgame import Player

class Apprentice(Player):
    def __init__(self, model_name: str, player: str):
        """
        Initialize an Apprentice object.

        :param model_name: The name of the model.
        :param player: The name of the player.
        """
        super().__init__(model_name)
        self.player: str = player

        # A list to keep the dialogue history
        self.history: List = []

    def _custom_response(self, messages, turn_idx) -> str:
        """
        Give a programmatic response without an API call to a model.

        This function searches for keywords in the given message:
        - If asked for predictions, determines the hand size and returns a random number.
        - If asked for a card, determines the current hand and returns a random card.

        :param messages: List of messages in the dialogue.
        :param turn_idx: Index of the current turn.
        :return: A programmatic response based on the prompt.
        """
        prompt = messages[-1]

        if "PREDICTION: number" in prompt:
            # search the word that is in front of "num_cards"
            word = "gets "
            idx = prompt.index(word) + len(word)

            # loop through two positions and look for digits
            num_cards = ''
            for i in [idx, idx+1]:
                if prompt[i].isnumeric():
                    num_cards += prompt[i]

            # change a random number from that digits
            num_cards = int(num_cards)
            guess = random.choice(range(1, num_cards+1))

            return "PREDICTION: " + str(guess)

        elif "PLAYED: color + number" in prompt:
            # extract line that has the current hand
            word = "Your current hand is: "
            hand = [line for line in prompt.splitlines() if word in line][0]

            # remove the leading dot if there is one
            if hand[-1] == '.':
                hand = hand[:-1]

            # split the text until only cards are left
            cards = hand.split(':')[1]
            cards = cards.split(',')
            cards = [c.strip() for c in cards]

            card = random.choice(cards)

            return "I PLAY: " + card
