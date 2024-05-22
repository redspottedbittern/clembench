import pprint
import random
import re

# Create a dictionary to represent a deck of cards
deck_dict = {}
for color in ['G', 'B', 'R', 'Y']:
    for number in range(1, 14):
        # Each card is represented by a combination of color and number
        card_key = f"{color}{number}"
        card_properties = {"color": color,
                           "dealt": False,  # Indicates whether the card has been dealt to a player
                           "trump": False}  # Indicates whether the card is a trump card
        deck_dict[card_key] = card_properties

# Extend the deck dictionary to include Wizards and Jesters
deck_dict.update({f"{color}{number}": {"dealt": False}  # They do not have a color or trump attribute
                  for color in ['Z', 'J']
                  for number in range(1, 5)})

# Create dictionary of players and populate
num_players = int(input("Enter the number of players: "))
players_dict = {
    i: {
        "Prediction": None,    # Each player's prediction for the number of tricks they will take
        "Cards_played": [],    # List to store the cards each player has played
        "Cards_dealt": [],     # List to store the cards dealt to each player
        "Points": 0            # Each player's points
    }
    for i in range(1, num_players + 1)
}

# Calculate the number of rounds based on the total number of cards (60) and the number of players
rounds = 1
while 60 >= (rounds + 1) * num_players:
    num_cards = rounds * num_players
    rounds += 1
# Create dictionary of cards to be dealt in each round
tricks_dict = {round_num: {"num_cards": int(round_num * num_players)}  # Number of cards to be dealt in this round
               for round_num in range(1, rounds + 1)}


def get_random_undealt_cards(deck_dict, n):
    """
    Get random undealt cards from the deck.

    Parameters:
    deck_dict (dict): The dictionary representing the deck of cards.
    n (int): The number of undealt cards to select.

    Returns:
    list: A list of keys representing the selected undealt cards.

    Raises:
    ValueError: If there are not enough undealt cards to select.
    """
    # Create a list of keys for cards that have not been dealt
    undealt_keys = [key for key, value in deck_dict.items()
                    if not value["dealt"]]
    if len(undealt_keys) < n:  # Check if there are enough undealt cards available
        raise ValueError("Not enough unplayed cards to select from.")
    # Randomly select n undealt cards
    selected_keys = random.sample(undealt_keys, n)
    for key in selected_keys:  # Mark the selected cards as dealt
        deck_dict[key]["dealt"] = True
    return selected_keys


def get_random_trump_card(deck_dict):
    """
    Get a random undealt card with a specified color (not a wizard or jester) and mark it as dealt.

    Parameters:
    deck_dict (dict): The dictionary representing the deck of cards.

    Returns:
    str: The key of the selected undealt card.
    """
    # Create a list of keys for undealt cards that have a specified color (excluding wizards and jesters)
    undealt_keys = [key for key, value in deck_dict.items(
    ) if not value.get("dealt", False) and value.get("color")]
    selected_keys = random.sample(undealt_keys, 1)
    # Mark the selected card as dealt
    deck_dict[selected_keys[0]]["dealt"] = True
    return selected_keys[0]


def summarize_last_predictions(player, players_dict):
    """
    Summarize the last players' predictions.

    Parameters:
    player (int): The current player.
    players_dict (dict): A dictionary containing player information.

    Returns:
    tuple: A tuple containing:
           - skip_predictions (bool): Indicates whether to skip summarizing predictions for the current player.
           - larger_text (str): The summary of players' predictions.
    """
    skip_predictions = False
    # Skip the first player as there are no predictions so far
    if player == 1 and players_dict[player]["Prediction"] == None:
        skip_predictions = True
        return skip_predictions, None
    else:
        prediction_sentence = ""
        # Warning: Have to use "player_id" as it will overwrite the correct order (in the loop)
        for player_id, player_info in players_dict.items():
            if player_info.get("Prediction") is not None:
                prediction = player_info.get("Prediction")
                prediction_sentence += f"Player number {player_id} predicted {prediction} tricks. "
        prediction_sentence = prediction_sentence.strip()
        # Construct the larger text with the summary sentence
        larger_text = f"After careful consideration, here are the players' predictions: {prediction_sentence}\n"
        return skip_predictions, larger_text
    # TODO: make it more customizable (e.g. "You selected ... Player 2 selected... Etc.")

def match_cards_to_players(players_dict):
    result = []
    for index, player in enumerate(players_dict):
        last_card_played = players_dict[player]['Cards_played'][-1]
        result.append((index, last_card_played))
    return result

def is_wizard(card):
    return re.fullmatch(r'Z\s*\d+', user_input)

def is_trump(card, trump_color):
    return re.fullmatch(card[0], trump_color)

def challenger_has_higher_number(current_winner, challenger):
    return int(current_winner[1:]) < int(challenger[1:])

def is_higher_trump(current_winner, challenger, trump_color):
    if not (is_trump(current_winner)) and  is_trump(challenger):
        return True
    if is_trump(current_winner) and is_trump(challenger):
        return challenger_has_higher_number(current_winner, challenger)
    return False

def follow_suit(card, suit):
    return re.fullmatch(card[0], suit)
    
def is_higher_suit(current_winner, challenger, trump_color):
    if follow_suit(current_winner) and follow_suit(challenger):
        return challenger_has_higher_number(current_winner, challenger)
    return False


def challenger_is_higher(current_winner, challenger, trump_color, suit):
    if is_wizard(challenger):
        return True
    if is_higher_trump(current_winner, challenger, trump_color):
        return True
    if is_higher_suit(current_winner, challenger, suit):
        return True
    return False
    
def evaluate_trick(cards_played, trump_color, suit):
    current_winner = cards_played[0]

    for card in cards_played:
        if card == current_winner:
            next
        if challenger_is_higher(current_winner[1], card[1], trump_color, suit):
            current_winner = card  
    return current_winner



# 1. Starts game...
for round in tricks_dict:
    # First, the instructions are given and the predictions are stored
    if round != len(tricks_dict):  # Except for last round, each trick round has a trump card
        # Select a random trump card for this round
        trump_card = get_random_trump_card(deck_dict)
        # Finds keys with same trump color
        keys_with_trump_color = [key for key, value in deck_dict.items(
        ) if value.get("color") == deck_dict[str(trump_card)]["color"]]
        # Sets the trump attribute to True for cards with the same color as the trump card
        for key in keys_with_trump_color:
            deck_dict[key]["trump"] = True

    for player in players_dict:
        # Deals cards to the player
        dealt_cards = get_random_undealt_cards(
            deck_dict, int(tricks_dict[int(round)]["num_cards"]/num_players))
        players_dict[player]['Cards_dealt'] = dealt_cards

        # Summarize the predictions made by players
        skip_predictions, larger_text = summarize_last_predictions(
            player, players_dict)

        # TODO: Wollen wir nochmal die genaue Ziele wiederholen, oder einfach direkt mit der Runde machen?
        """
        If round == 1; then initial prompt, otherwise:
        ############################################
        Next round:
        Each player gets 6 cards, and the rest stay in the deck. I've shuffled the cards. 
        The trump card is B11 with the color B.

        You've been dealt the following cards: ['R9', 'G5']. 
        
        What's your prediction?
        ############################################
        """


        initial_prompt = f"""
############################################

You are playing a competitive card game in which you have to correctly predict how many 
tricks you are going to take in each round. In each trick round you -and the other players- 
take turns playing one card each. These cards together make up a trick. For example, if 
each player has five cards, you will play five tricks in one round. At the end of each trick 
round, you will earn points for a correct prediction. Additionally, in each round, you will 
get more cards, so you will play more tricks. The player who has earned the most experience 
points at the end of the game wins. 

The trick round consists of 4 phases:
(a) Dealing Cards 
(b) Predicting Tricks 
(c) Playing Tricks 
(d) Earning Experience Points

Rules:
(a) After dealing the cards to each player, the first card of the remaining deck determines 
the trump color for this trick round. Every card in the trump color is a trump. A trump wins 
against any card of another color. At the start of each trick round, a new trump color is 
determined. The last round has no trump color.
(b) If you play the first card into a trick, you may play any card. However, all other 
players must follow suit. That means that they must play a card of the same color as the 
first card in the trick. Trumps or other colors can only be played if you do not have any 
cards of the required color in your hand. While a trick is being played, the color you must 
follow suit with never changes.
(c) There are 52 cards. Each card has a number from 1 to 13 and one of four colors: green, 
red, blue, and yellow. Cards are represented with a capital letter for the color and a number,
like B5 for blue 5 or R12 for red 12.
(d) There are also two kinds of special cards: four Wizard and four Jesters. They are represented 
with a Z and a J respectively.
(e) Wizards and Jesters can be played at any time, even if you could actually follow suit. 
They do not have any color. Wizards always win the trick round. Jesters always lose the trick round.
(f) At the start, each player predicts how many tricks they'll win. The goal is to match your 
prediction. 

Who wins the trick?
(a) The first Wizard (Z) played in the trick wins.
(b) If none Wizards (Z) were played, the highest card in the trump color wins.
(c) If there are neither Wizards nor trump cards in the trick, the highest card in the color 
that was first played into the trick round wins.

End conditions:
When there are no more cards in the deck, the game is finished.        

########################################################################################


Let us start:
You're playing with {len(players_dict)-1} other players, and you're player number {player}. 
Each player gets {tricks_dict[int(round)]["num_cards"]} cards, and the rest stay in the deck. I've shuffled the cards. 
The trump card is {str(trump_card)} with the color {deck_dict[str(trump_card)]["color"]}.

You've been dealt the following cards: {players_dict[player]['Cards_dealt']}. 
{larger_text if skip_predictions is False else ''} 
What's your prediction?

Important! Predictions are made in the format "PREDICTION: number".
############################################
"""
        user_input = input(initial_prompt)

        if re.fullmatch(r'PREDICTION:\s*\d+', user_input):
            user_input_without_prefix = user_input.replace("PREDICTION: ", "")
            players_dict[player]['Prediction'] = int(
                user_input_without_prefix)  # Stores predictions
        else:
            raise ValueError(
                "Invalid input. Please use the format 'PREDICTION: number'.")

    # ... Continuation of game flow ...
    for trick in range(1, int(tricks_dict[round]['num_cards']/num_players)+1):
        for player in players_dict:
            _, larger_text = summarize_last_predictions(player, players_dict)

            current_hand = [card for card in players_dict[player]['Cards_dealt'] if card not in players_dict[player]['Cards_played']]

            second_prompt = f"""
############################################
Time to play your cards!

You're playing with {len(players_dict)-1} other players, and you're player number {player}. 
The trump card is {str(trump_card)} with the color {deck_dict[str(trump_card)]["color"]}.

You've been dealt: {players_dict[player]['Cards_dealt']}. 

Your current hand is: {current_hand}

{larger_text if skip_predictions is False else ''} 
Which card from your hand do you play?

Important! Remember to use the format "PLAYED: color + number".
############################################
"""
            user_input = input(second_prompt)
            # Check if the input matches the expected format
            if re.fullmatch(r'PLAYED:\s*[GBRYZJ]\d+', user_input):
                user_input_without_prefix = user_input.replace("PLAYED: ", "")

                # Checks if it was a valid card
                if user_input_without_prefix not in players_dict[player]['Cards_dealt']:
                    raise ValueError(
                    "Invalid input. Please use one of the cards dealt to you.")

                players_dict[player]['Cards_played'].append(
                    str(user_input_without_prefix))  # Stores played cards
            else:
                raise ValueError(
                    "Invalid input. Please use the format 'PLAYED: color + number'.")
            #print(players_dict[player]['Cards_dealt'] - players_dict[player]['Cards_played'])
        

    # ... 3. Points are counted and updated ...
    # TODO: Compute using players_dict and update dictionary
    # TODO: Print who won trick round and points so far

    # ... 4. Resets the attributes of dictionaries to start next round ...
    for key in deck_dict.values():
        key["dealt"] = False
        key["trump"] = False
    for key in players_dict.values():
        key["Cards_dealt"] = []
        key["Cards_played"] = []
        key["Prediction"] = None
