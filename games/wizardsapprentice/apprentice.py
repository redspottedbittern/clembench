import random
from typing import List
from clemgame.clemgame import Player
from games.wizardsapprentice.utils.trick_utils import (
    is_wizard,
    is_higher_number
)


def extract_card_list(prompt_snippet, prompt):
    # extract line that has the current hand
    hand = [line for line in prompt.splitlines() if prompt_snippet in line][0]

    # remove the leading dot if there is one
    if hand[-1] == '.':
        hand = hand[:-1]

    # split the text until only cards are left
    cards = hand.split(':')[1]
    cards = cards.split(',')
    return clean_input(cards)


def clean_input(input_list):
    # Joining the list into a single string
    joined_string = ''.join(input_list)

    # Removing unwanted characters and extra spaces
    cleaned_string = joined_string.replace("'", "").replace("[", "").replace("]", "").strip()

    # Splitting the cleaned string by spaces
    result = cleaned_string.split()

    return result


class Apprentice(Player):
    def __init__(self, model_name: str, player: str):
        """
        Initialize an Apprentice object.

        :param model_name: The name of the model.
        :param player: The name of the player.
        """
        super().__init__(model_name)
        self.model_name = model_name
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
        promptstring = prompt['content']
        if "PREDICTION: number" in promptstring:
            # search the word that is in front of "num_cards"
            word = "gets "
            idx = promptstring.index(word) + len(word)

            # loop through two positions and look for digits
            num_cards = ''
            for i in [idx, idx+1]:
                if promptstring[i].isnumeric():
                    num_cards += promptstring[i]

            # change a random number from that digits
            num_cards = int(num_cards)

            if str(self.model_name)  == "custom":
                guess = random.choice(range(1, num_cards+1))
            elif str(self.model_name)  == "programmatic":
                # TODO: Better guess -> but how?
                guess = random.choice(range(1, num_cards+1))

            return "PREDICTION: " + str(guess)
                
        elif "I PLAY: card" in promptstring:
            # extract line that has the current hand
            word = "Your current hand is: "
            #breakpoint()
            player_cards = extract_card_list(word, promptstring)
            
            cards_played_in_prompt = "These cards have been played in this trick already in this order: "

            cards_already_played = extract_card_list(cards_played_in_prompt, promptstring)
            suit = cards_already_played[0][0]

            if suit == "J":
                suit = cards_already_played[1][0]
            
            played_card = player_cards[0]

            # suits_found = [card for card in player_cards if card[0] == suit]
            highest_card_index = 0

            if str(self.model_name)  == "custom":
                suits = []
                [suits.append(x) for x in player_cards if x[0] == suit]
                if len(suits) > 0:
                    guessed_idx = random.choice(range(0, len(suits)))
                    return "I PLAY: " + suits[guessed_idx]
                else:
                    guessed_idx = random.choice(range(0, len(player_cards)))
                    return "I PLAY: " + player_cards[guessed_idx]
            elif str(self.model_name)  == "programmatic":
                for index, card in enumerate(player_cards):
                    new_suit_found = card[0] == suit or is_higher_number(played_card, card)
                    if is_wizard(card) or new_suit_found:
                        return "I PLAY: " + card
                    if max(card[0], player_cards[highest_card_index]) == card[0]:
                        highest_card_index = index

            return "I PLAY: " + player_cards[highest_card_index]
