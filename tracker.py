import socket
import threading

# global dictionary to store registered players: {player_name: (ip_address, t_port, p_port, state)}
players = {}
# global dictionary to store games: {game_id: {"dealer": dealer_name, "players": [player1, player2, ...]}}
games = {}
game_tracker = 0

# random global buffer size
BUFFER_SIZE = 1024

# function to handle incoming messages from players
def handle_player(conn, addr):
    print(f"Connected to player: {addr}")

    while True:
        try:
            message = conn.recv(BUFFER_SIZE).decode()
            if not message:
                break
            print(f"Received message from player: {message}")
            response = process_message(message)
            conn.send(response.encode())
        except Exception as e:
            print(f"Error handling player: {e}")
            break

    print(f"Disconnected from player: {addr}")
    conn.close()


# function to process the incoming messages and execute corresponding commands
def process_message(message):
    parts = message.split()
    # the first word is the command, rest are arguments
    command = parts[0]

    if command == "register":
        if len(parts) == 5:
            return register_player(parts[1], parts[2], parts[3], parts[4])
        else:
            return "FAILURE: Invalid register command format. Usage: register <player_name> <ip_address> <t_port> <p_port>"

    elif command == "deregister":
        if len(parts) == 2:
            return deregister_player(parts[1])
        else:
            return "FAILURE: Invalid deregister command format. Usage: deregister <player_name>"

    elif command == "query" and parts[1] == "players":
        if len(parts) == 2:
            return query_players()
        else:
            return "FAILURE: Invalid query command format. Usage: query players"

    elif command == "query" and parts[1] == "games":
        if len(parts) == 2:
            return query_games()
        else:
            return "FAILURE: Invalid query command format. Usage: query games"


# function to register a new player
def register_player(player_name, ip_address, t_port, p_port):
    if player_name in players:
        return "FAILURE: Player already registered"
    else:
        players[player_name] = (ip_address, t_port, p_port, "free")
        return "SUCCESS: Player registered"


# function to deregister a player
def deregister_player(player_name):
    if player_name in players and players[player_name][3] == "free":
        del players[player_name]
        return "SUCCESS: Player deregistered"
    else:
        return "FAILURE: Player not registered or is currently in a game"


# function to query players
def query_players():
    num_players = len(players)

    # return 0 and an empty list if no players are registered
    if num_players == 0:
        return "0: []"

    # otherwise, make the list of tuples for each registered player
    player_list = []
    for player, details in players.items():
        player_tuple = f"({player}, {details[0]}, {details[1]}, {details[2]}, {details[3]})"
        player_list.append(player_tuple)

    # return the number of players and the list of tuples
    return f"{num_players}: [{', '.join(player_list)}]"


# placeholder start game function to help with prototyping query_games
"""
def start_game(dealer, n, #holes):
    if dealer not in players:
        return "FAILURE: Dealer not registered"
        
    if players[dealer][3] != "free":
        return "FAILURE: Dealer is already in a game"
    
    if n < 1 or n > 3:
        return "FAILURE: Invalid number of players"
        
    free_players = [p for p in players if players[p][3] == 'free' and p != dealer_name]
    if len(free_players) < n:
        return f"FAILURE: Not enough available players. Only {len(free_players)} free players."
    
    if #holes < 1 or #holes > 9:
        return "FAILURE: Invalid number of holes"
        
    # select n free players for the game
    selected_players = random.sample(free_players, n)
    
    # assign a unique game identifier
    game_id = game_tracker
    game_tracker += 1
    
    # Update the states of the dealer and selected players to "in-play"
    players[dealer_name] = (*players[dealer_name][:3], 'in-play')
    for player in selected_players:
        players[player] = (*players[player][:3], 'in-play')
    
    # Store the game information
    games[game_id] = {
        "dealer": dealer_name,
        "players": [(player, players[player][0], players[player][2]) for player in selected_players]
    }
    
    # Build the response with dealer and player details
    dealer_info = f"{dealer_name} (IP: {players[dealer_name][0]}, p-port: {players[dealer_name][2]})"
    player_info = ', '.join([f"{player} (IP: {players[player][0]}, p-port: {players[player][2]})" for player in selected_players])
    
    # return success message
    return f"SUCCESS: Game {game_id}: Dealer={dealer_info}, Players=[{player_info}]"
"""

# function to query games
def query_games():
    num_games = len(games)

    # return 0 and an empty list if no games are registered
    if num_games == 0:
        return "0: []"

    # otherwise, make the list of tuples for each registered game based off start_game function above
    game_list = []
    for game_id, game_details in games.items():
        game_tuple = f"({game_id}, {game_details['dealer']}, {game_details['players']})"
        game_list.append(game_tuple)

    # return the number of games and the list of tuples
    return f"{num_games}: [{' | '.join(game_list)}]"


# function to start the tracker server on a port
def start_tracker_server(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", port))
    server_socket.listen()

    print(f"Tracker server listening on port {port}")

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_player, args=(conn, addr)).start()


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python tracker.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    # within 11500-11999
    start_tracker_server(port)