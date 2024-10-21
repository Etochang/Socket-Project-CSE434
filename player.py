import json
import random
import socket
import sys
import threading

# global buffer size, same as tracker.py
BUFFER_SIZE = 1024

# Store player relationships (dealer, left, right) for each player
player_neighbors = {
    "dealer": None,
    "left": None,
    "right": None,
    "self": None
}

# Global game state variables
player_hands = {}
stock = []
discard = []
scores = {}
current_turn = None
round_number = 1
round_end = False

# Game logic functions

# initialize a deck of cards
def create_deck():
    suits = ["H", "D", "S", "C"]
    ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    deck = [f"{rank}{suit}" for suit in suits for rank in ranks]
    return deck

# shuffle the deck
def shuffle_deck(deck):
    random.shuffle(deck)

# deal 6 cards to each player, cycling through players
def deal_cards(deck, players):
    hands = {player: [] for player in players}
    for i in range(6):
        for player in players:
            hands[player].append(deck.pop(0))
    return hands

# Randomly turn two cards face up and leave the rest as ***
def initialize_player_hand(hand):
    # Make all cards face-down initially
    hand_status = [('***', card) for card in hand]
    # Randomly turn two cards face up
    face_up = random.sample(range(6), 2)
    for i in face_up:
        hand_status[i] = (hand[i], hand[i])
    return hand_status

# set up stock and discard piles
def create_stock_and_discard_piles(deck):
    stock = deck[:-1]
    discard = [deck[-1]]
    return stock, discard

# set up the game, called by dealer only
def setup_game(players):
    deck = create_deck()
    shuffle_deck(deck)

    # deal 6 cards to each player
    hands = deal_cards(deck, players)

    # initialize player hands
    for player in hands:
        hands[player] = initialize_player_hand(hands[player])

    # create stock and discard piles
    stock, discard = create_stock_and_discard_piles(deck)
    return hands, stock, discard

# function to display player hands
def display_player_hand(player_name, player_hand):
    row_width = 3*3 + 2
    print("\n" + player_name.center(row_width))

    # Split hand into two rows of three
    top_row = ' '.join([card[0].center(3) for card in player_hand[:3]])
    bottom_row = ' '.join([card[0].center(3) for card in player_hand[3:]])

    # Print rows
    print(top_row)
    print(bottom_row + '\n')

def display_player_hands(player_hands):
    for player, hand in player_hands.items():
        display_player_hand(player, hand)

# function to draw a card
def draw_card(stock, discard):
    choice = input("Draw from stock (s) or discard pile (d)? ")
    if choice == 's' and stock:
        return stock.pop(0), 'stock'
    elif choice == 'd' and discard:
        return discard.pop(), 'discard'
    else:
        print("Invalid choice or empty pile.")
        return None, None

# function to swap a card
def swap_card(player_hand, card, pile):
    global stock, discard
    print("Your current hand:")
    display_player_hand(player_hand)
    choice = input("Enter position of card to swap (1-6 from top left to bottom right), or d for discard pile: ").strip().lower()
    if choice.isdigit() and 1 <= int(choice) <= 6:
        position = int(choice) - 1
        olc_card = player_hand[position][1]
        player_hand[position] = (card, card)
        if pile == 'stock':
            stock.insert(0, olc_card)
        else:
            discard.append(olc_card)
        print(f"Swapped {olc_card} with {card} to {pile}.")
        return True
    elif choice == 'd':
        discard.append(card)
        print(f"Added {card} to discard pile.")
        return True
    else:
        print("Invalid choice.")
        return False

# check for round end
def check_round_end(player_hand):
    return all(card[0] != '***' for card in player_hand)

def end_round_and_start_new(players):
    global player_hands, stock, discard, scores, current_turn, round_number, round_end

    # Display scores for the current round
    print("\nRound", round_number, "scores:")
    for player, score in scores.items():
        print(f"{player}: {score}")

    # Increment round number and reset round_end flag
    round_number += 1
    round_end = False

    # Set up a new deck, shuffle, deal new hands
    deck = create_deck()
    shuffle_deck(deck)
    player_hands = deal_cards(deck, players)

    # Initialize player hands for the new round
    for player in player_hands:
        player_hands[player] = initialize_player_hand(player_hands[player])

    # Create new stock and discard piles
    stock, discard = create_stock_and_discard_piles(deck)

    # Reset the current turn to the player after the dealer
    current_turn = players[1]

    # Reset scores for the new round
    scores = {player: 0 for player in players}

    # Serialize and push the new game state to all players
    game_state = serialize_game_state(player_hands, stock, discard, scores, current_turn, round_number, round_end)
    push_updates_to_players(players, game_state)

    print("\nStarting new round", round_number)


# calculating score
def calculate_score(player_hand):
    score = 0
    score_map = {
        'A': 1,
        '2': -2,
        '3': 3,
        '4': 4,
        '5': 5,
        '6': 6,
        '7': 7,
        '8': 8,
        '9': 9,
        '10': 10,
        'J': 10,
        'Q': 10,
        'K': 0
    }

    for i in range(3):  # columns are indexed as 0, 1, 2
        if player_hand[i][1][0] == player_hand[i + 3][1][0]:  # pair in the column
            continue  #  0
        else:
            score += score_map[player_hand[i][1][0]]
            score += score_map[player_hand[i + 3][1][0]]

    return score

# main gameplay loop for player turns, drawing cards, swapping/discarding, and checking for end of round
def play_turn(players):
    global player_hands, stock, discard, scores, current_turn, round_number, round_end

    current_player = current_turn
    print(f"{current_player}'s turn:")

    # Display player hands
    display_player_hands(player_hands)

    # Draw a card
    card, pile = draw_card(stock, discard)
    if card is None:
        return True  # Continue the round if no valid card was drawn

    # Attempt to swap the card
    swapped = swap_card(player_hands[current_player], card, pile)
    if not swapped:
        return True  # Continue the round if the swap was unsuccessful

    # Check if the current player has ended the round
    if check_round_end(player_hands[current_player]):
        print(f"{current_player} has ended the round.")
        round_end = True
        return False  # End the round

    # Calculate scores for the current state
    scores = {player: calculate_score(hand) for player, hand in player_hands.items()}

    # Move to the next player
    current_index = players.index(current_turn)
    current_turn = players[(current_index + 1) % len(players)]

    # Serialize the updated game state
    game_state = serialize_game_state(player_hands, stock, discard, scores, current_turn, round_number, round_end)

    # Push the updated game state to all players
    push_updates_to_players(players, game_state)

    return True  # Continue the round

# serialization function for game state
def serialize_game_state(player_hands, stock, discard, scores, current_turn, round_number, round_end):
    state = {
        "player_hands": player_hands,
        "stock": stock,
        "discard": discard,
        "scores": scores,
        "current_turn": current_turn,
        "round_number": round_number,
        "round_end": round_end
    }
    return json.dumps(state)
def push_updates_to_players(player_details, game_state):
    game_state_message = f"GameStateUpdate:{game_state}"
    for i, player in enumerate(player_details):
        ip, p = player[1], player[2]
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, p))
                s.sendall(game_state_message.encode())
                print(f"Sent game state to {player[0]} at {ip}:{p}.")
        except Exception as e:
            print(f"Error sending game state to {player[0]} at {ip}:{p}: {e}")


def update_local_game_state(game_state):
    global player_hands, stock, discard, scores, current_turn
    player_hands = game_state["player_hands"]
    stock = game_state["stock"]
    discard = game_state["discard"]
    scores = game_state["scores"]
    current_turn = game_state["current_turn"]
    print("Updated local game state")
    print("Current scores:", scores)
    print("Next turn:", current_turn)

# function to send a message to the tracker server
def send_message(client_socket, message):
    try:
        # send the message
        client_socket.send(message.encode())
        # receive the response
        response = client_socket.recv(BUFFER_SIZE).decode()
        print(f"Tracker server response: {response}")
        # parse the response if it's a start game response
        if "SUCCESS: Game" in response:
            game_info = response.split(":")[2].strip()
            parts = game_info.split(" | ")
            dealer_info = parts[0][8:-1].strip()
            players_info = parts[1].strip()[9:-1].split(") (")

            player_details = []
            # dealer details
            dealer, ip, p = dealer_info.split(", ")
            player_details.append((dealer, ip, int(p)))

            # player details
            for player in players_info:
                player_name, ip, p = player.split(", ")
                player_details.append((player_name, ip, int(p)))

            return player_details
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


# function to listen for messages from other players via their p_port
def listen_for_messages(ip_address, p_port):
    global player_neighbors, round_end
    try:
        # create a TCP socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind the socket to the IP address and port
        server_socket.bind((ip_address, p_port))
        # listen for incoming connections
        server_socket.listen()
        print(f"Listening for messages from players on port {p_port}...")

        while True:
            # accept an incoming connection
            conn, addr = server_socket.accept()
            # receive the message
            message = conn.recv(BUFFER_SIZE).decode()
            print(f"Received message from player: {message}\n")

            # parse the message
            if message.startswith("Hello from player"):
                try:
                    parts = message.split(";", 2)
                    if len(parts) == 3:
                        greeting, player_details_str, my_index_str = parts
                        # parse the player details and index
                        player_details = eval(player_details_str)
                        my_index = int(my_index_str)

                        left_player_index = (my_index - 1) % len(player_details)

                        # identify dealer, left, and right players
                        player_neighbors["dealer"] = player_details[0]
                        player_neighbors["left"] = player_details[left_player_index]
                        player_neighbors["self"] = player_details[my_index]

                        # send the message to the next player in the ring
                        if player_neighbors["right"] is None:
                            notify_next_player(player_details, my_index)
                    else:
                        print("Invalid message format")
                except Exception as e:
                    print(f"Failed to parse player details: {e}")
            elif message.startswith("GameStateUpdate:"):
                game_state_str = message.split(":", 1)[1]
                game_state = json.loads(game_state_str)
                update_local_game_state(game_state)

                # check if it is this process's turn
                if current_turn == player_neighbors["self"][0]:
                    if not round_end:
                        players = list(player_hands.keys())
                        play_turn(players)
                    else:
                        players = list(player_hands.keys())
                        end_round_and_start_new(players)
            conn.close()
    except Exception as e:
        print(f"Error: {e}")


# function to start a listener thread for a specific p_port
def start_listener_thread(ip_address, p):
    listener_thread = threading.Thread(target=listen_for_messages, args=(ip_address, p))
    listener_thread.daemon = True # terminate the thread when the main thread terminates
    listener_thread.start()

# function to set up ring topology
def notify_next_player(player_details, my_index):
    next_index = (my_index + 1) % len(player_details)
    next_player = player_details[next_index]
    next_ip, next_p = next_player[1], next_player[2]

    try:
        # create socket to connect to next player in the ring
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((next_ip, next_p))
            s.send(f"Hello from player {player_details[my_index][0]} at {player_details[my_index][1]}:{player_details[my_index][2]};{player_details};{next_index}".encode())

            # set right player in dictionary
            player_neighbors["right"] = next_player

            print(f"Connected to next player {next_player[0]} at {next_ip}:{next_p}\n")
    except Exception as e:
        print(f"Failed to connect to next player {next_player[0]} at {next_ip}:{next_p}: {e}")


def handle_user_input(client_socket):
    global player_hands, stock, discard, scores, current_turn, round_number, round_end
    while True:
        command = input("> ")
        if command == 'exit':
            print("Goodbye!")
            break
        # otherwise, send whatever the player types to the tracker server, special case for start game since
        # threads need to be initialized
        if command.startswith("start game"):
            parts = command.split()
            if len(parts) == 5 or len(parts) == 4:
                # send the command to the tracker server
                response = send_message(client_socket, command)
                if isinstance(response, list):
                    print("Starting game...")
                    for i, player in enumerate(response):
                        print(f" {player[0]}:{player[1]}:{player[2]}")

                    #get next player to notify others
                    notify_next_player(response, 0)

                    # set up game variables
                    players = [player[0] for player in response]
                    player_hands, stock, discard = setup_game(players)
                    scores = {player: 0 for player in players}
                    current_turn = players[1]
                    round_number = 1
                    round_end = False

                    # send game state
                    game_state = serialize_game_state(player_hands, stock, discard, scores, current_turn, round_number,
                                                      round_end)
                    push_updates_to_players(response, game_state)
                else:
                    print(response)
            else:
                print("Invalid start game command. Usage: start game <dealer_name> <n> <#holes>")
        else:
            send_message(client_socket, command)


# function to act as a 'player CLI' that can interact with the tracker server continuously
def player_cli(tracker_ip, tracker_port, t, p):
    # start listener thread immediately for player to player communication
    start_listener_thread("0.0.0.0", p)

    # Create a TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # allow sockets to be reused
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind the socket to the IP address and port
    client_socket.bind(("", t))
    # Connect to the tracker server
    client_socket.connect((tracker_ip, tracker_port))

    print("Welcome to the player CLI!")
    print("Available commands:")
    print("  register <player_name> <ip_address> <t_port> <p_port>")
    print("  deregister <player_name>")
    print("  query players")
    print("  query games")
    print("  start game <dealer_name> <n> <#holes>")
    print("Enter 'exit' to quit.")

    # create separate thread for handling user input so listener can function at the same time
    input_thread = threading.Thread(target=handle_user_input, args=(client_socket,))
    input_thread.daemon = True
    input_thread.start()

    try:
        input_thread.join()
    finally:
        client_socket.close()

if __name__ == "__main__":
    # check if the correct number of arguments is passed
    if len(sys.argv) != 5:
        print("Usage: python player.py <tracker_ip> <tracker_port> <t_port> <p_port>")
        sys.exit(1)

    tracker_ip = sys.argv[1]
    tracker_port = int(sys.argv[2])
    t_port = int(sys.argv[3])
    p_port = int(sys.argv[4])

    player_cli(tracker_ip, tracker_port, t_port, p_port)