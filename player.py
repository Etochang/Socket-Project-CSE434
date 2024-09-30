import socket
import sys

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

        # otherwise, send whatever the player types to the tracker server
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