"""Util functions for evaluating the winner of a trick."""
import re


def is_wizard(card):
    """Check if a card is a wizard."""
    return re.fullmatch(r'Z', card[0])


def is_jester(card):
    """Check if a card is a jester."""
    return re.fullmatch(r'J', card[0])


def is_special(card):
    """Check if a card is a special card."""
    return is_wizard(card) or is_jester(card)


def is_trump(card, trump_color):
    """Check if a card is of the trump color."""
    return re.fullmatch(card[0], trump_color)


def same_color(card, suit):
    """Check if a card has a certain suit."""
    return re.fullmatch(card[0], suit)


def is_higher_number(current_winner, challenger):
    """Check if a card has a higher number than another."""
    return int(current_winner[1:]) < int(challenger[1:])


def is_trump_after_normal(current_winner, challenger, trump_color):
    """If a trump card comes after a normal card, it wins."""
    # a trump card beats a non-trump card
    if not is_trump(current_winner, trump_color) and is_trump(challenger,
                                                              trump_color):
        return True

    return False


def is_wizard_after_normal(current_winner, challenger):
    """Wizards win, if played after non-wizards."""
    if not is_wizard(current_winner) and is_wizard(challenger):
        return True

    return False


def is_normal_after_jester(current_winner, challenger):
    """Non-jesters win, if played after jesters."""
    if is_jester(current_winner) and not is_jester(challenger):
        return True

    return False


def is_special_involved(current_winner, challenger):
    """Check if a special card wins the trick."""
    if is_wizard_after_normal(current_winner, challenger):
        return True

    if is_normal_after_jester(current_winner, challenger):
        return True

    return False


def challenger_is_higher(current_winner, challenger, trump_color):
    """
    Check if a card is better then a card played before.

    Returns False if none of four conditions are met:
        - a wizard beats non-wizards
        - a non-jester beats jesters
        - a trump card beats non-trump, non-special cards
        - a non-special card beats cards of the same color
    """
    # have specific rules, if a special card is involved
    if is_special(current_winner) or is_special(challenger):
        return is_special_involved(current_winner, challenger)

    # trump cards beat non-trump, non-special cards
    if is_trump_after_normal(current_winner, challenger, trump_color):
        return True

    # if both cards are the same color, check which one is higher
    if same_color(current_winner, challenger[0]):
        return is_higher_number(current_winner, challenger)

    return False


def evaluate_trick(trick, trump_color):
    """
    Determine who wins a trick.

    Returns:
        current_winner: card, that wins the trick
    """
    current_winner = trick[0]

    # loop through played cards and determine current_winner
    # if card beats the card before
    for card in trick:
        if card == current_winner:
            continue
        if challenger_is_higher(current_winner, card, trump_color):
            current_winner = card

    return current_winner


def shift_to_winner(liste, target):
    """Shift the seating order to the winner for next trick round."""
    idx = liste.index(target)
    shifted_list = liste[idx:] + liste[:idx]
    return shifted_list


def evaluate_round(prediction, tricks):
    """Calculate how many points a player earns."""
    if prediction == tricks:
        return (10*tricks)+20
    else:
        return -(abs(int(prediction[-1])-tricks)*10)
