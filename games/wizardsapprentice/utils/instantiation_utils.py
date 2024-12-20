"""Util functions for the instance generation."""
import random
from copy import deepcopy

WIZARDS = [
    'Gandalf',
    'Oz',
    'Merlin',
]

# HEY! Use this longer list if calculate_points_for... is not so specific
# anymore
# WIZARDS = [
#     'Gandalf',
#     'Oz',
#     'Merlin',
#     'Harry Potter',
#     'Houdini',
#     'Elminster Aumar'
# ]

def convert_keys_to_int(d):
    """
    Recursively convert the keys of the dictionary and any nested dictionaries from strings to integers.
    """
    if not isinstance(d, dict):
        return d
    
    new_dict = {}
    for k, v in d.items():
        new_key = int(k)
        if isinstance(v, dict):
            new_value = convert_keys_to_int(v)
        else:
            new_value = v
        new_dict[new_key] = new_value
    
    return new_dict


def deal_cards_for_round(round, deck, seating_order, mode="random"):
    """Deal cards for a specific round."""
    deck = deepcopy(deck)
    dealt_cards = {}

    # draw round many cards for every player and save them
    for player in seating_order:
        if player == "Gandalf":
            hand = get_cards(deck, round, mode)
        else:
            hand = get_cards(deck, round, "random")
        dealt_cards[player] = hand

    # determine a trump color
    trump_card = get_random_trump_card(deck)

    return dealt_cards, trump_card


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

def get_cards(deck, n=0, mode="random"):
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
    if mode == "random":
        selected_keys = get_random_cards(undealt_keys, n)
    elif mode == "bad_cards":
        selected_keys = get_bad_cards(undealt_keys, n)
    else:
        selected_keys = get_good_cards(undealt_keys, n)
        
    for key in selected_keys:  # Mark the selected cards as dealt
        deck[key]["dealt"] = True

    return selected_keys

def get_random_cards(undealt_keys, n):
    # Randomly select n undealt cards
    return random.sample(undealt_keys, n)

def get_bad_cards(undealt_keys, n):
    bad_cards = [s for s in undealt_keys if s[0] in 'RYGBJ' and s[1:].isdigit() and int(s[1:]) <= 5]
    return random.sample(bad_cards, n)

def get_good_cards(undealt_keys, n):
    good_cards = [s for s in undealt_keys if s[0] in 'RYGBZ' and s[1:].isdigit() and (int(s[1:]) >= 9 or s[0] == 'Z')]
    return random.sample(good_cards, n)


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


def create_seating_order(num_players, position):
    """Get a random order of players."""

    # Copy the list of wizards, save the first name for the model
    wizards = WIZARDS.copy()
    model = wizards.pop(0)

    # shuffle the non-model wizards and restrict to number of players
    random.shuffle(wizards)
    wizards = wizards[:num_players-1]

    # insert the model at the target position
    wizards.insert(position-1, model)

    return wizards


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
