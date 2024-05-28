import pprint
import random
import re
import os
import json
from utils.promptcontainer import PromptContainer


def load_game_parameters(json_file):
    """
    Load function for the game parameters.

    The parameters of the game (e.g. cards and colors) are specified in a
    seperate json file.

    Returns:
        dict: containing the parameters of the game
    """
    # get the path of the current file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, json_file)

    with open(full_path, 'r') as f:
        parameters = json.load(f)

    return parameters


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
        for number in range(1, cards_per_color+1):
            # Fill the deck with cards and their properties
            card_key = f"{color}{number}"
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


def create_table(num_players, **kwargs):
    """
    Initialize all players with default values.

    A player is represented by their prediction, by their hand, by the cards
    played, and by the points they accumulated.

    Parameters:
        num_players (int): number of players in the game
        **kwargs: other arguments from the parameters

    Returns:
    dict: Dictionary for all players in the game.
    """
    # Create dictionary of players and populate
    table = {
        i: {
            # Each player's prediction for the number of tricks they will take
            "Prediction": None,
            # List to store the cards each player has played
            "Cards_played": [],
            # List to store the cards dealt to each player
            "Cards_dealt": [],
            # Each player's points
            "Points": 0
        }
        for i in range(1, num_players + 1)
    }

    return table


def create_cards_per_round(colors, cards_per_color, special_cards,
                           special_cards_num, num_players, num_rounds,
                           start_round, **kwargs):
    """
    Calculate the tricks for every round.

    Depending on the game parameters, this function calculates how much cards
    must be dealt each round.

    Parameters:
        num_rounds: represents the number of rounds that should be played. If
        it is -1, all possible rounds should be played.

    Returns:
        dict: dictionary containing the number of cards for every round
    """
    # Calculate the total number of cards
    num_cards = (len(colors) * cards_per_color +
                 len(special_cards) * special_cards_num)

    # If num_rounds is -1 calculate the max possible number of rounds
    # Based on the total number of cards and player number
    if num_rounds == -1:
        num_rounds = num_cards // num_players

    # Number of cards to be dealt in this round
    cards_per_round = {i: {"num_cards": i * num_players}
                       for i in range(start_round, num_rounds + 1)}

    return cards_per_round


def get_random_undealt_cards(deck, n):
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

    # Check if there are enough undealt cards available
    if len(undealt_keys) < n:
        raise ValueError("Not enough unplayed cards to select from.")

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

    # select one random card out of the undealt cards
    selected_keys = random.sample(undealt_keys, 1)

    # Mark the selected card as dealt
    deck[selected_keys[0]]["dealt"] = True

    return selected_keys[0]


def summarize_last_predictions(player, table):
    """
    Summarize the last players' predictions.

    Parameters:
    player (int): The current player.
    table (dict): A dictionary containing player information.

    Returns:
    tuple: A tuple containing:
           - skip_predictions (bool): Indicates whether to skip summarizing
                predictions for the current player.
           - larger_text (str): The summary of players' predictions.
    """
    skip_predictions = False
    # Skip the first player as there are no predictions so far
    if player == 1 and table[player]["Prediction"] is None:
        skip_predictions = True
        return skip_predictions, None
    else:
        prediction_sentence = ""
        # Warning: Have to use "player_id" as it will overwrite the correct order (in the loop)
        for player_id, player_info in table.items():
            if player_info.get("Prediction") is not None:
                prediction = player_info.get("Prediction")
                prediction_sentence += f"Player number {player_id} predicted {prediction} tricks. "
        prediction_sentence = prediction_sentence.strip()
        # Construct the larger text with the summary sentence
        larger_text = f"After careful consideration, here are the players' predictions: {prediction_sentence}\n"
        return skip_predictions, larger_text
    # TODO: make it more customizable (e.g. "You selected ... Player 2 selected... Etc.")


def match_cards_to_players(table):
    """
    Create a list of player numbers and last played cards.

    Returns:
        result: list of tuples of player number and the last card they played.
    """
    # loop through table and extract the last played card of every player
    result = []
    for index, player in enumerate(table):
        last_card_played = table[player]['Cards_played'][-1]
        result.append((index, last_card_played))

    return result


def is_wizard(card):
    """Check if a card is a wizard."""
    return re.fullmatch(r'Z\s*\d+', card[0])


def is_jester(card):
    """Check if a card is a jester."""
    return re.fullmatch(r'J\s*\d+', card[0])


def is_trump(card, trump_color):
    """Check if a card is of the trump color."""
    return re.fullmatch(card[0], trump_color)


def challenger_has_higher_number(current_winner, challenger):
    """Check if a card has a higher number than another."""
    return int(current_winner[1:]) < int(challenger[1:])


def is_higher_trump(current_winner, challenger, trump_color):
    """
    Check if a card beats the one before with trumps.

    Returns:
        True: if a trump card is beats the card played before
        False: if it isn't a trump card or doesn't beat the card before
    """
    # a trump card beats a non-trump card
    if not is_trump(current_winner) and is_trump(challenger):
        return True

    # if both are trump cards, check which one is higher
    if is_trump(current_winner) and is_trump(challenger):
        return challenger_has_higher_number(current_winner, challenger)

    return False


def same_color(card, suit):
    """Check if a card has a certain suit."""
    return re.fullmatch(card[0], suit)


def is_higher_suit(current_winner, challenger, trump_color):
    """Check if a card beats another card of the same color."""
    if (same_color(current_winner, trump_color) and
            same_color(challenger, trump_color)):
        return challenger_has_higher_number(current_winner, challenger)

    return False


def challenger_is_higher(current_winner, challenger, trump_color, suit):
    """
    Check if a card is better then a card played before.

    Returns False if none of three conditions are met:
        - a second wizard beats the first
        - a higher trump card beats the first
        - a higher same-suit-card beats the first
    """
    if is_wizard(challenger):
        return True

    if is_higher_trump(current_winner, challenger, trump_color):
        return True

    if is_higher_suit(current_winner, challenger, suit):
        return True

    return False


def evaluate_trick(cards_played, trump_color, suit):
    """
    Determine who wins a trick.

    Returns:
        current_winner: card, that wins the trick
    """
    current_winner = cards_played[0]

    # loop through played cards and determine current_winner
    # if card beats the card before
    for card in cards_played:
        if card == current_winner:
            continue
        if challenger_is_higher(current_winner[1], card[1], trump_color, suit):
            current_winner = card

    return current_winner


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

    return True


def game_loop(deck, table, cards_per_round, num_players, prompts):
    # 1. Starts game...
    for round in cards_per_round:
        # First, the instructions are given and the predictions are stored
        if round != len(cards_per_round):  # Except for last round, each trick round has a trump card
            # Select a random trump card for this round
            trump_card = get_random_trump_card(deck)
            # Finds keys with same trump color
            keys_with_trump_color = [key for key, value in deck.items(
            ) if value.get("color") == deck[str(trump_card)]["color"]]
            # Sets the trump attribute to True for cards with the same color as the trump card
            for key in keys_with_trump_color:
                deck[key]["trump"] = True

        for player in table:
            # Deals cards to the player
            dealt_cards = get_random_undealt_cards(
                deck, int(cards_per_round[int(round)]["num_cards"]/num_players))
            table[player]['Cards_dealt'] = dealt_cards

            # Summarize the predictions made by players
            skip_predictions, larger_text = summarize_last_predictions(
                player, table)

            # TODO: Wollen wir nochmal die genaue Ziele wiederholen, oder einfach direkt mit der Runde machen?

            initial_subs = {
                'num_players': num_players,
                'player_position': player,
                'num_cards': cards_per_round[int(round)]["num_cards"],
                'trump_card': trump_card,
                'trump_color': deck[str(trump_card)]["color"],
                'player_hand': table[player]['Cards_dealt'],
                'player_predictions': ''
            }

            rules_prompt = prompts.substitute('rules', None)
            first_round_prompt = prompts.substitute('round_start', initial_subs)
            initial_prompt = rules_prompt + first_round_prompt
            user_input = input(initial_prompt)

            if re.fullmatch(r'PREDICTION:\s*\d+', user_input):
                user_input_without_prefix = user_input.replace("PREDICTION: ", "")
                table[player]['Prediction'] = int(
                    user_input_without_prefix)  # Stores predictions
            else:
                raise ValueError(
                    "Invalid input. Please use the format 'PREDICTION: number'.")

        # ... Continuation of game flow ...
        for trick in range(1, int(cards_per_round[round]['num_cards']/num_players)+1):
            for player in table:
                _, larger_text = summarize_last_predictions(player, table)

                current_hand = [card for card in table[player]['Cards_dealt']
                                if card not in table[player]['Cards_played']]


                trick_subs = {
                    'num_players': num_players,
                    'player_position': player,
                    'num_cards': cards_per_round[int(round)]["num_cards"],
                    'trump_card': trump_card,
                    'trump_color': deck[str(trump_card)]["color"],
                    'player_hand': table[player]['Cards_dealt'],
                    'current_hand': current_hand,
                    'cards_played': '',
                    'player_hand_current': '',
                    'player_predictions': ''
                }
                second_prompt = prompts.substitute('trick_start', trick_subs)
                user_input = input(second_prompt)

                # Check if the input matches the expected format
                if re.fullmatch(r'PLAYED:\s*[GBRYZJ]\d+', user_input):
                    user_input_without_prefix = user_input.replace("PLAYED: ", "")

                    # Checks if it was a valid card
                    if user_input_without_prefix not in table[player]['Cards_dealt']:
                        raise ValueError(
                        "Invalid input. Please use one of the cards dealt to you.")

                    table[player]['Cards_played'].append(
                        str(user_input_without_prefix))  # Stores played cards
                else:
                    raise ValueError(
                        "Invalid input. Please use the format 'PLAYED: color + number'.")
                #print(table[player]['Cards_dealt'] - table[player]['Cards_played'])
            

        # ... 3. Points are counted and updated ...
        # TODO: Compute using table and update dictionary
        # TODO: Print who won trick round and points so far

        # ... 4. Resets the attributes of dictionaries to start next round ...
        for key in deck.values():
            key["dealt"] = False
            key["trump"] = False
        for key in table.values():
            key["Cards_dealt"] = []
            key["Cards_played"] = []
            key["Prediction"] = None


if __name__ == '__main__':

    # load game_parameters
    parameters_file = 'game_parameters.json'
    parameters = load_game_parameters(parameters_file)

    prompts = PromptContainer()

    # initialize important game objects
    deck = create_deck(**parameters)
    table = create_table(**parameters)
    cards_per_round = create_cards_per_round(**parameters)

    num_players = parameters['num_players']
    game_loop(deck, table, cards_per_round, num_players, prompts)
