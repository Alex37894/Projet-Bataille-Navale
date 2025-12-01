import socket
import sys
import threading
import time  

HOST = '' 
PORT = 5000

# Fonction pour gérer le spectateur et lui envoyer l'historique
def handle_new_spectator(conn, addr, spectators, history):
    """Thread pour gérer un nouvel observateur"""
    print(f"Connexion reçue de {addr} (Observateur)")
    spectators.append(conn)
    conn.send("Vous êtes un observateur. Vous pouvez suivre le jeu.\n".encode('utf-8'))
    
    # <--- AJOUT 2 : Petite pause pour éviter que tout arrive en un seul bloc
    time.sleep(0.5) 
    
    # Envoi de l'historique
    for log in history:
        try:
            conn.send(log.encode('utf-8'))
            # Une micro-pause ici aide aussi si l'historique est long
            time.sleep(0.05) 
        except:
            break

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((HOST, PORT))
    except socket.error as e:
        print(f"Erreur de liaison : {e}")
        sys.exit(1)

    server_socket.listen(3)
    print(f"Serveur en attente sur le port {PORT}...")

    clients = []
    spectators = []
    history = [] # La liste qui garde les coups en mémoire
    boards_ready = {}
  
    while len(clients) < 2:
        conn, addr = server_socket.accept()
        print(f"Connexion reçue de {addr}")
        clients.append(conn)
        boards_ready[conn] = False
        conn.send("Bienvenue sur le serveur de bataille navale !\n".encode('utf-8'))
        conn.send("Vous êtes connecté. Placez vos bateaux pour commencer.\n".encode('utf-8'))
        conn.send("En attente de l'adversaire...\n".encode('utf-8'))

    print("Deux joueurs connectés. Le jeu commence !")
  
    clients[0].send("START 0\n".encode('utf-8'))
    clients[1].send("START 1\n".encode('utf-8'))

    for conn in clients:
        conn.send("FIN_PLACEMENT?\n".encode('utf-8'))

    while not all(boards_ready.values()):
        for conn in clients:
            if not boards_ready[conn]:
                try:
                    data = conn.recv(1024).decode('utf-8').strip()
                    if data == "PLACEMENT_OK":
                        boards_ready[conn] = True
                except:
                    pass

    # Partie démarrée
    for i, c in enumerate(clients):
        c.send(f"START {i}\n".encode('utf-8'))

    # Thread pour accepter les observateurs (avec l'argument history)
    def accept_spectators():
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_new_spectator, args=(conn, addr, spectators, history), daemon=True).start()
            
    threading.Thread(target=accept_spectators, daemon=True).start()

    current_player = 0
    game_over = False

    while not game_over:
        opponent = (current_player + 1) % 2
      
        try:
            clients[current_player].send("YOUR_TURN\n".encode('utf-8'))
            clients[opponent].send("WAIT\n".encode('utf-8'))

            data = clients[current_player].recv(1024).decode('utf-8').strip()
            print(f"Joueur {current_player} joue : {data}")
          
            if not data: break

            clients[opponent].send(f"{data}\n".encode('utf-8'))

            result_data = clients[opponent].recv(1024).decode('utf-8').strip()
            print(f"Résultat du Joueur {opponent} : {result_data}")

            clients[current_player].send(f"{result_data}\n".encode('utf-8'))

            # On enregistre les coups dans l'historique
            history.append(f"Joueur {current_player} joue : {data}\n")
            history.append(f"Résultat : {result_data}\n")

            for spectator in spectators:
                try:
                    spectator.send(f"Joueur {current_player} joue : {data}\n".encode('utf-8'))
                    spectator.send(f"Résultat : {result_data}\n".encode('utf-8'))
                except socket.error:
                     spectators.remove(spectator)

            if "GAME_OVER" in result_data:
                game_over = True
                print(f"Le joueur {current_player} a gagné !")
            else:
                current_player = opponent

        except Exception as e:
            print(f"Erreur de connexion : {e}")
            break

    print("Fermeture du serveur.")
    for c in clients + spectators:
        c.close()
    server_socket.close()

if __name__ == "__main__":
    main()
