import socket
import sys

HOST = '' 
PORT = 5000

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
  
   while len(clients) < 2:
       conn, addr = server_socket.accept()
       print(f"Connexion reçue de {addr}")
       clients.append(conn)
       conn.send("Bienvenue sur le serveur de bataille navale !\n".encode('utf-8'))
       conn.send("Vous êtes connecté. Placez vos bateaux pour commencer.\n".encode('utf-8'))
       conn.send("En attente de l'adversaire...\n".encode('utf-8'))

   print("Deux joueurs connectés. Le jeu commence !")
  
   clients[0].send("START 0\n".encode('utf-8'))
   clients[1].send("START 1\n".encode('utf-8'))

   while len(clients) + len(spectators) < 3:
        conn, addr = server_socket.accept()
        print(f"Connexion reçue de {addr} (Observateur)")
        spectators.append(conn)
        conn.send("Vous êtes un observateur. Vous pouvez suivre le jeu.\n".encode('utf-8'))

   print("Troisième personne connectée en tant qu'observateur.")

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

           for spectator in spectators:
               spectator.send(f"Joueur {current_player} joue : {data}\n".encode('utf-8'))
               spectator.send(f"Résultat : {result_data}\n".encode('utf-8'))

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
