import socket
import sys
import threading

# global buffer size, same as tracker.py
BUFFER_SIZE = 1024

# function to send a message to the tracker server
def send_message(tracker_ip, tracker_port, message):
    try:
        # create a TCP socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # connect to the tracker server
        client_socket.connect((tracker_ip, tracker_port))

        # send the message
        client_socket.send(message.encode())

        # receive the response
        response = client_socket.recv(BUFFER_SIZE).decode()
        print(f"Tracker server response: {response}")

        # close the socket
        client_socket.close()

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
def start_listener_thread(ip_address, p_port):
    listener_thread = threading.Thread(target=listen_for_messages, args=(ip_address, p_port))
    listener_thread.daemon = True # terminate the thread when the main thread terminates
    listener_thread.start()


# function to act as a 'player CLI' that can interact with the tracker server continuously
def player_cli(tracker_ip, tracker_port):
    print("Welcome to the player CLI!")
    print("Available commands:")
    print("  register <player_name> <ip_address> <t_port> <p_port>")
    print("  deregister <player_name>")
    print("  query players")
    print("  query games")

    print("Enter 'exit' to quit.")

    while True:
        command = input("> ")

        # exit the player CLI if the user enters 'exit'
        if command == 'exit':
            print("Goodbye!")
            break

        # otherwise, send whatever the player types to the tracker server, special case for start game since
        # threads need to be initialized
        if command.startswith("start game"):
            parts = command.split()
            if len(parts) != 5:
                print("Invalid start game command. Usage: start game <dealer_name> <n> <#holes>")
            else:
                n = int(parts[3])
                response = send_message(tracker_ip, tracker_port, command)
                if "SUCCESS" in response:
                    break
                    # create a thread for each user
                    # 1. extract player IPs and ports for the n players in the response
                    # 2. create a thread for each player
                    # i.e., player_details = [(ip1, port1), (ip2, port2), ...]
                    # for ip, port in player_details:
                    #     start_listener_thread(ip, port)
        else:
            send_message(tracker_ip, tracker_port, command)


if __name__ == "__main__":
    # check if the correct number of arguments are passed
    if len(sys.argv) != 5:
        print("Usage: python player.py <tracker_ip> <tracker_port> <t_port> <p_port>")
        sys.exit(1)

    tracker_ip = sys.argv[1]
    tracker_port = int(sys.argv[2])
    t_port = int(sys.argv[3])
    p_port = int(sys.argv[4])

    player_cli(tracker_ip, tracker_port)