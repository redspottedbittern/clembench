import random
import pprint
import re


def get_current_hand(round, player, start_hand, played_cards):
    """Extract a certain players current hand."""
    old_cards = [trick_round[player] for trick_round in
                 played_cards[round].values()]

    current_hand = [card for card in start_hand if card not in old_cards]

    return current_hand


def get_current_trick(round, trick_round, played_cards, playing_order):
    """Extract the current trick in the correct order of played cards."""
    current_trick = []
    for player in playing_order:
        current_trick.append(played_cards[round][trick_round][player])

    return current_trick



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


def print_table(tab):
    return pprint.pp(tab)


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
