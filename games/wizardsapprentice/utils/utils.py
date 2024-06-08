import random
import pprint
import re


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


def create_table(num_players):
    """
    Initialize dictionary of all players with default values.

    A player is represented by their prediction, by their hand, by the cards
    played, the position they sit in, and by the points they accumulated.
    """
    # get a random order of players
    order_list = [*range(1, num_players+1)]
    random.shuffle(order_list)

    # Create dictionary of players and populate
    table = {
        i: {
            # Each player's position to play
            "Order": order_list[i-1],
            # Each player's prediction for the number of tricks they will take
            "Prediction": None,
            # List to store the cards dealt to each player
            "Cards_dealt": [],
            # List to store the cards each player has played
            "Cards_played": [],
            # Each player's points
            "Points": 0,
            # Tricks won
            "Tricks_won": 0
        }
        for i in range(1, num_players + 1)
    }

    return table


def get_seating_order(table):
    """Return an ordered list of the players positions at the table."""
    order_dict = {}
    for key, nested_dict in table.items():
        order = nested_dict.get('Order')
        if order is not None:
            if order not in order_dict:
                order_dict[order] = []
            order_dict[order].append(key)

    sorted_orders = sorted(order_dict.keys())
    sorted_keys = []

    for order in sorted_orders:
        sorted_keys.extend(order_dict[order])

    return sorted_keys


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
        raise ValueError(f"Not enough unplayed cards to select from. Undealt Cards: {undealt_cards_count}, Round: {n}")

    # Randomly select n undealt cards
    selected_keys = random.sample(undealt_keys, n)

    for key in selected_keys:  # Mark the selected cards as dealt
        deck[key]["dealt"] = True

    return selected_keys


def print_table(tab):
    return pprint.pp(tab)


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

    # select one random card out of the undealt cards
    selected_keys = random.sample(undealt_keys, 1)

    # Mark the selected card as dealt
    deck[selected_keys[0]]["dealt"] = True

    return selected_keys[0]


def summarize_predictions(player, table):
    """
    Summarize the last players' predictions.

    Parameters:
    player (int): The current player.
    table (dict): A dictionary containing player information.

    Returns:
    - larger_text (str): The summary of players' predictions.
    """
    prediction_sentence = ""
    # Warning: Have to use "player_id" as it will overwrite the correct order (in the loop)
    for player_id, player_info in table.items():
        if player_info.get("Prediction") is not None:
            prediction = player_info.get("Prediction")
            prediction_sentence += f"Player number {player_id} predicted {prediction} tricks"
    prediction_sentence = prediction_sentence.strip()
    # Construct the larger text with the summary sentence
    larger_text = f"\n\nAfter careful consideration, here are the players' predictions: {prediction_sentence}\n"

    return larger_text
    # TODO: make it more customizable (e.g. "You selected ... Player 2 selected... Etc.")


def summarize_trick_round(table):
    pred_list = []
    for key, nested_dict in table.items():
        predictions = nested_dict.get('Prediction')
        if predictions is not None:
            pred_list.append(f"Player number {key} predicted {predictions} tricks")

    predictions_text = " ".join(pred_list)
    return predictions_text


def remove_card(table, player, value):
    cards_dealt = list(table[player]["Cards_dealt"])
    cards_dealt.remove(value)
    table[player]["Cards_dealt"] = cards_dealt

    cards_played = list(table[player]["Cards_played"])
    cards_played.append(str(value))
    table[player]["Cards_played"] = cards_played
    return None


def same_color(card, suit):
    return card['color'] == suit


def is_wizard(card):
    return re.fullmatch(r'Z\s*\d+', card[0])


def is_jester(card):
    return re.fullmatch(r'Z\s*\d+', card[0])


def card_allowed(first_card_played, card_played, player_hand):
    """
    Check game rules.

    This function controls, if a played card follows the rules and is
    admissible.

    Returns:
        True: if card follows suit, is special or doesn't has to follow suit.
        False: if card is not same color, but player has same color cards in
        hand.
    """
    # The card follows suit
    if same_color(first_card_played, card_played):
        return True

    # special cards don't need to follow suit
    if is_wizard(card_played) or is_jester(card_played):
        return True

    # if players hasn't played the same color, but still has it, return false
    for card in player_hand:
        if same_color(first_card_played, card):
            return False


def get_ordered_played_cards(table):
    sorted_players = sorted(table.items(), key=lambda item: item[1]["Order"])

    ordered_played_cards = []

    max_len = max(len(player["Cards_played"]) for player in table.values())

    for idx in range(max_len):
        for key, data in sorted_players:
            cards_played = data.get("Cards_played", [])
            if idx < len(cards_played):
                ordered_played_cards.append(cards_played[idx])

    return str(ordered_played_cards)
