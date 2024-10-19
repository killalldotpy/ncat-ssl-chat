import socket
import threading
import ssl

clients = []
clients_lock = threading.Lock()
PASSWORD = "hej123"  # Byt detta till det lösenord du vill använda

def broadcast(message, client_socket=None):
    with clients_lock:
        for client, addr in clients:
            if client != client_socket:
                try:
                    client.send(message)
                except:
                    client.close()
                    clients.remove((client, addr))

def handle_client(client_socket, addr):
    name = None
    try:
        # Be om klientens lösenord
        client_socket.send(b'Enter the password: ')
        password = client_socket.recv(1024).decode().strip()
        if password != PASSWORD:
            client_socket.send(b'Incorrect password. Connection will be closed.\n')
            client_socket.close()
            return

        # Skicka välkomstmeddelande
        client_socket.send(b'This is NRG cryptchat - type /help for available commands\n')

        # Be om klientens namn
        client_socket.send(b'Enter your name: ')
        name = client_socket.recv(1024).decode().strip()
        welcome_message = f'{name} has joined the chat!\n'.encode()
        broadcast(welcome_message, client_socket)

        with clients_lock:
            clients.append((client_socket, name))

        while True:
            message = client_socket.recv(1024)
            if not message:
                break
            decoded_message = message.decode().strip()
            if decoded_message.startswith("/"):
                handle_command(decoded_message, client_socket, name)
            else:
                formatted_message = f'{name}: {decoded_message}\n'.encode()
                broadcast(formatted_message, client_socket)
    except:
        pass
    finally:
        with clients_lock:
            clients.remove((client_socket, name))
        client_socket.close()
        if name:
            leave_message = f'{name} has left the chat!\n'.encode()
            broadcast(leave_message)

def handle_command(command, client_socket, name):
    if command == "/help":
        client_socket.send(b'Available commands: /help, /list, /quit\n')
    elif command == "/list":
        with clients_lock:
            client_names = [name for client, name in clients]
        client_socket.send(f'Connected clients: {", ".join(client_names)}\n'.encode())
    elif command == "/quit":
        client_socket.close()
        leave_message = f'{name} has left the chat!\n'.encode()
        broadcast(leave_message)
    else:
        client_socket.send(b'Unknown command. Type /help for a list of commands.\n')

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 6666))
    server.listen(5)
    print("Server is listening on port 6666")

    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr}")

        try:
            client_socket = context.wrap_socket(client_socket, server_side=True)
            threading.Thread(target=handle_client, args=(client_socket, addr)).start()
        except ssl.SSLError as e:
            print(f"SSL error: {e}")
            client_socket.close()

if __name__ == "__main__":
    main()
