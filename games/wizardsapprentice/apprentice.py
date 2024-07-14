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
            
            played_card = player_cards[0]

            for card in player_cards:
                if is_wizard(card):
                    return "I PLAY: " + card
                if card[0] == suit:
                    if is_higher_number(played_card, card):
                        played_card = card
                    else: # Still has to follow suit
                        played_card = card
            return "I PLAY: " + played_card
        
        elif "I PLAY: card" in promptstring:
            # extract line that has the current hand
            word = "Your current hand is: "
            #breakpoint()
            player_cards = extract_card_list(word, promptstring)
            
            cards_played_in_prompt = "These cards have been played in this trick already in this order: "

            cards_already_played = extract_card_list(cards_played_in_prompt, promptstring)
            suit = cards_already_played[0][0]
            
            played_card = player_cards[0]

            for card in player_cards:
                if is_wizard(card):
                    return "I PLAY: " + card
                if card[0] == suit:
                    if is_higher_number(played_card, card):
                        played_card = card
                    else: # Still has to follow suit 
                        # TODO: Make it more dynamically: go through all cards and use the best card. If not, must follow suit anyway.
                        played_card = card
            return "I PLAY: " + played_card