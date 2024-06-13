"""Util functions for the GameMaster."""
import re


class Parser():
    """This class parses and checks answers from the LLM."""

    def __init__(self, regex):
        """Initialize the needed regex."""
        self.re_card = regex['card_played']
        self.re_prediction = regex['prediction']
        self.re_wizard = regex['wizard']
        self.re_jester = regex['jester']

    def is_comprehensible_prediction(self, answer):
        """Check regex and return number or None."""
        if re.fullmatch(self.re_prediction, answer):
            return True
        else:
            return False

    def is_comprehensible_card(self, answer):
        """Check regex and return number or None."""
        if re.fullmatch(self.re_card, answer):
            return True
        else:
            return False

    def extract_card(self, answer):
        """Find the card and return it."""
        card = re.findall(self.re_card, answer)[0][0]
        return card

    def extract_prediction(self, answer):
        """Find the number in the answer and return it as int."""
        prediction = re.findall(self.re_prediction, answer)[0]
        return int(prediction)

    def is_wizard(self, card):
        """Apply the wizard regex."""
        return re.fullmatch(self.re_wizard, card[0])

    def is_jester(self, card):
        """Apply the jester regex."""
        return re.fullmatch(self.re_jester, card[0])

    def same_color(self, card, suit):
        """Check for same color."""
        return card[0] == suit

    def is_in_hand(self, card, hand):
        """Check if card is in players hand."""
        return card in hand

    def which_suit_to_follow(self, trick):
        """Return the color that reigns a trick at a certain point."""
        # if no cards were played so far, no suit must be followed
        if not trick:
            return None

        # if the first card is a wizard, no suit must be followed
        first_card = trick[0]
        if self.is_wizard(first_card):
            return None

        # if first card is a jester, the next card determines the suit
        if self.is_jester(first_card):
            return self.which_suit_to_follow(trick[1:])

        # after all checks, get the suit of the first card
        color = first_card[0]

        return color

    def follows_suit(self, card, hand, trick):
        """Check if card follows suit correctly."""
        # first determine which suit to follow
        suit = self.which_suit_to_follow(trick)

        # if there is None, the played card doesn't matter
        if not suit:
            return True

        # wizards and jesters don't need to follow suit
        if self.is_wizard(card) or self.is_jester(card):
            return True

        # if the color is the same, everything is alright
        if self.same_color(card, suit):
            return True

        # false if players hasn't played the same color, but still has it
        for hand_card in hand:
            if self.same_color(hand_card, suit):
                return False

        return True

    def is_possible_prediction(self, prediction, round):
        """Check if the prediction if possible."""
        return prediction in range(1, round+1)
