"""Util functions for the instance generation."""
import random
from copy import deepcopy


def deal_cards_for_round(round, deck, seating_order):
    """Deal cards for a specific round."""
    deck = deepcopy(deck)
    dealt_cards = {}

    # draw round many cards for every player and save them
    for player in seating_order:
        hand = get_random_undealt_cards(deck, round)
        dealt_cards[player] = hand

    # determine a trump color
    dealt_cards['trump'] = get_random_trump_card(deck)

    return dealt_cards


def get_random_undealt_cards(deck, n=0):
    """
    Get random undealt cards from the deck.

    Parameters:
    deck (dict): The dictionary representing the deck of cards.
    n (int): The number of undealt cards to select.

    Returns:
    list: A list of keys representing the selected undealt cards.

    Raises:
    ValueError: If there are not enough undealt cards to select.
    """
    # Create a list of keys for cards that have not been dealt
    undealt_keys = [key for key, value in deck.items()
                    if not value["dealt"]]

    undealt_cards_count = len(undealt_keys)
    # Check if there are enough undealt cards available
    if undealt_cards_count < n:
        raise ValueError(f"Not enough unplayed cards to select from.\
                         Undealt Cards: {undealt_cards_count}, Round: {n}")

    # Randomly select n undealt cards
    selected_keys = random.sample(undealt_keys, n)

    for key in selected_keys:  # Mark the selected cards as dealt
        deck[key]["dealt"] = True

    return selected_keys


def get_random_trump_card(deck):
    """
    Determine trump card at the beginning of round.

    Get a random undealt card with a specified color (not a wizard or jester)
    and mark it as dealt.

    Parameters:
    deck (dict): The dictionary representing the deck of cards.

    Returns:
    str: The key of the selected undealt card.
    """
    # Create a list of keys for undealt cards that have a specified color
    # (excluding wizards and jesters)
    undealt_keys = [key for key, value in deck.items()
                    if not value.get("dealt", False)
                    and value.get("color")]

    # check if enough undealt_keys are left
    if len(undealt_keys) < 1:
        return None

    # select one random card out of the undealt cards
    selected_keys = random.sample(undealt_keys, 1)

    # Mark the selected card as dealt
    deck[selected_keys[0]]["dealt"] = True

    return selected_keys[0]


def create_seating_order(num_players):
    """Get a random order of players."""
    order_list = [*range(1, num_players+1)]
    random.shuffle(order_list)

    return order_list


def create_deck(colors, cards_per_color, special_cards, special_cards_num,
                **kwargs):
    """
    Deck builder.

    Each normal card is represented by a color, a number, wether the card was
    already dealt to a player, and whether the card is a trump card.
    Special cards ave their own colors and can't be trump cards.

    Returns: a dictionary of cards and dictionaries according to the input
    """
    # Create a dictionary to represent a deck of cards
    deck = {}
    for color in colors:
        for number in range(1, cards_per_color + 1):
            # Fill the deck with cards and their properties
            card_key = color + str(number)
            card_properties = {"color": color, "dealt": False, "trump": False}
            deck[card_key] = card_properties

    # Extend the deck dictionary to include Wizards and Jesters
    # Only if they are wanted
    if special_cards_num > 0:
        # They do not have a color or trump attribute
        deck.update({f"{kind}{number}": {"dealt": False}
                    for kind in special_cards
                    for number in range(1, special_cards_num+1)})

    return deck
