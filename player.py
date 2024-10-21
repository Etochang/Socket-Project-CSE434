import socket
import sys
import threading

# global buffer size, same as tracker.py
BUFFER_SIZE = 1024

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
            print(f"Received message from player: {message}")
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
            s.send(f"Hello from player {player_details[my_index][0]} at {player_details[my_index][1]}:{player_details[my_index][2]}".encode())
            print(f"Connected to next player {next_player[0]} at {next_ip}:{next_p}")
    except Exception as e:
        print(f"Failed to connect to next player {next_player[0]} at {next_ip}:{next_p}: {e}")

# Function for each player to start their own listener and notify next player
def start_listener_and_notify(player_details, my_index):
    my_ip, my_port = player_details[my_index][1], player_details[my_index][2]
    print(f"Starting listener thread for player {player_details[my_index][0]} at {my_ip}:{my_port}")
    start_listener_thread(my_ip, my_port)
    notify_next_player(player_details, my_index)

def handle_user_input(client_socket):
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
                        # Each player starts their own listener and notifies the next player
                        start_listener_and_notify(response, i)
                else:
                    print(response)
            else:
                print("Invalid start game command. Usage: start game <dealer_name> <n> <#holes>")
        else:
            send_message(client_socket, command)


# function to act as a 'player CLI' that can interact with the tracker server continuously
def player_cli(tracker_ip, tracker_port, t):
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

    player_cli(tracker_ip, tracker_port, t_port)