
import random
from clemgame.clemgame import Player


class CardPlayer(Player):

    def __init__(self, model_name: str, player: str):
        # always initialise the Player class with the model_name argument
        # if the player is a program and you don't want to make API calls to
        # LLMS, use model_name="programmatic"
        super().__init__(model_name)
        self.player: str = player

        # a list to keep the dialogue history
        self.history: list = []

    def _custom_response(self, messages, turn_idx) -> str:
        """
        Give a programmatic response without a API call to a model.

        This function searches for keywords in the given message:
            - if it is aksed for predictions, the hand size must be determined
            and a random number returned
            - if it is asked for a card, the current hand must be determined
            and a random card returned

        Returns:
            - int: a random number in range of num_cards (for PREDICTION)
            - str: a card from the current hand (for CARD)
        """
        # is this correct=
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
