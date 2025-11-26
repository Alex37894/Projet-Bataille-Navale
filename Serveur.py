
import socket
import sys

HOST = ''  # Écoute sur toutes les interfaces
PORT = 5000

def main():
   server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  
   server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

   try:
       server_socket.bind((HOST, PORT))
   except socket.error as e:
       print(f"Erreur de liaison : {e}")
       sys.exit(1)

   server_socket.listen(2)
   print(f"Serveur en attente sur le port {PORT}...")

   clients = []
  
   while len(clients) < 2:
       conn, addr = server_socket.accept()
       print(f"Connexion reçue de {addr}")
       clients.append(conn)
       conn.send("Bienvenue! En attente de l'adversaire...\n".encode('utf-8'))

   print("Deux joueurs connectés. Le jeu commence !")
  
   clients[0].send("START 0\n".encode('utf-8'))
   clients[1].send("START 1\n".encode('utf-8'))

   current_player = 0
   game_over = False

# finir qui joue, Synchroniser les joueurs et Vérifier de la victoire