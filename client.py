#!/usr/bin/env python3

import socket
import sys
import os

DEFAULT_HOST = '127.0.0.1' #Adresse par default si on met rien ca la prend 
PORT = 5000

# Couleurs des différente actions du jeu dans le terminal 
RESET = "\033[0m"
RED = "\033[31m"    # Touché
BLUE = "\033[34m"   # Eau / Raté
GREEN = "\033[32m"  # Bateau intact
YELLOW = "\033[33m" # Texte informatif
CYAN = "\033[36m"   # Interface

class BattleshipClient:
   def __init__(self, host):
       self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
       self.host = host
      
       
       self.my_board = [['~' for _ in range(10)] for _ in range(10)] # Initialisation des grilles (10x10)
       self.tracking_board = [['?' for _ in range(10)] for _ in range(10)] # Initialisation des grilles (10x10)
      
       self.my_ships_points = set()
      
       # Liste des bateaux à placer (Nom et Taille) si on veut on rajouter il suffit de rajouter une ligne 
       self.ships_to_place = [
           ("Porte-avions", 5),
           ("Croiseur", 4),
           ("Contre-torpilleur", 3),
           ("Sous-marin", 3),
           ("Torpilleur", 2)
       ]

   def clear_screen(self):
       """Efface le terminal."""
       os.system('cls' if os.name == 'nt' else 'clear')

   def display_boards(self, status_msg=""):
       """Affiche les deux grilles côte à côte."""
       self.clear_screen()
       print(f"\n--- {CYAN}BATAILLE NAVALE RÉSEAU{RESET} ---")
       print(f"Serveur : {self.host}")
       print(f"{YELLOW}Statut : {status_msg}{RESET}\n")
      
       header = "   1   2   3 4  5 6  7 8 9 10"                          #Gère l'interface graphique (les numeros)
       print(f"    MA FLOTTE (Défense)             RADAR (Attaque)")   #gère l'interface graphique
       print(f"{header}    {header}")
      
       rows_label = "ABCDEFGHIJ"
      
       for i in range(10): # Construction ligne Ma flotte
           row_left = f"{rows_label[i]} "
           for cell in self.my_board[i]:
               if cell == 'B': 
                  char = f"{GREEN}#{RESET}"
               elif cell == 'X': 
                  char = f"{RED}X{RESET}"
               elif cell == 'O': 
                  char = f"{BLUE}O{RESET}"
               else: 
                  char = f"{BLUE}~{RESET}"
               row_left += f" {char}"
          
           row_right = f"{rows_label[i]} "   # Construction ligne Radar
           for cell in self.tracking_board[i]:
               if cell == 'X': 
                  char = f"{RED}X{RESET}"
               elif cell == 'O': 
                  char = f"{BLUE}O{RESET}"
               elif cell == '?': 
                  char = "."
               else: 
                  char = " "
               row_right += f" {char}"
          
           print(f"{row_left}       {row_right}")
       print("\n" + "-"*60)

   def parse_coord(self, coord):
       """Convertit 'A1' en indices (0, 0)."""
       try:
           coord = coord.upper().strip()
           if len(coord) < 2: return None, None
           row = ord(coord[0]) - ord('A')
           col = int(coord[1:]) - 1
           if 0 <= row < 10 and 0 <= col < 10:
               return row, col
       except:
           pass
       return None, None

   def place_ship(self, start_coord, length, orientation):
       """
       Tente de placer un bateau.
       Retourne True si réussi, False si impossible.
       """
       r, c = self.parse_coord(start_coord)
       if r is None: return False

       coords_to_occupy = []
       for i in range(length):
           if orientation == "H":
               curr_r, curr_c = r, c + i
           else: # Vertical
               curr_r, curr_c = r + i, c

           # test si un coup n'es pas jouer en dohors de la grille ?
           if not (0 <= curr_r < 10 and 0 <= curr_c < 10):
               return False
          
           # test si il n'y a pas eu de colision 
           if self.my_board[curr_r][curr_c] == 'B':
               return False
          
           coords_to_occupy.append((curr_r, curr_c))

       for (pr, pc) in coords_to_occupy:
           self.my_board[pr][pc] = 'B'
           self.my_ships_points.add((pr, pc))
      
       return True

   def setup_phase(self):
       """Boucle interactive pour placer tous les bateaux."""
       for name, size in self.ships_to_place:
           placed = False
           while not placed:
               self.display_boards(f"Placement : {name} ({size} cases)")
               print(f"Format : 'A1' pour la position, puis 'H' (Horizontal) ou 'V' (Vertical)")
              
               coord = input(f"Position début {name} (ex: A1) : ")
               if not coord: continue
              
               ori = input(f"Orientation (H/V) : ").upper()
               if ori not in ['H', 'V']:
                   input(f"{RED}Orientation invalide ! Tapez Entrée...{RESET}")
                   continue

               if self.place_ship(coord, size, ori):
                   placed = True
               else:
                   input(f"{RED}Placement impossible ! Tapez Entrée...{RESET}")
      
       self.display_boards("Flotte prête ! Tentative de connexion...")

   def run(self):       # debut de parti placement des bateaux
       self.setup_phase()

       try: # gére la connexion au serveur avec l'adresse IP (variable : {self.host}) et le port (Variable :  {PORT})
           self.sock.connect((self.host, PORT))
       except socket.error as e:
           print(f"\n{RED}ERREUR CRITIQUE : Impossible de joindre {self.host}:{PORT}{RESET}")
           print(f"Détail : {e}")
           sys.exit(1)

       game_running = True
       last_status = "Connecté. Attente d'un adversaire..."
       self.display_boards(last_status)


       # Boucle du jeu principale
       while game_running:
           try:
               msg = self.sock.recv(1024).decode('utf-8').strip()
               if not msg: break

               commands = msg.split('\n')
               for command in commands:
                   command = command.strip()
                   if not command: continue

                   if "Bienvenue" in command:
                       pass
                  
                   elif "START" in command:
                       last_status = "La partie commence !"
                       self.display_boards(last_status)

                   elif command == "YOUR_TURN":
                       last_status = "C'est à VOTRE TOUR !"
                       self.display_boards(last_status)
                      
                       valid = False
                       while not valid:
                           shot = input("Coordonnées de tir (ex: B5) : ").strip().upper()
                           r, c = self.parse_coord(shot)
                           if r is not None:
                               if self.tracking_board[r][c] == '?':
                                   valid = True
                               else:
                                   print(f"{YELLOW}Déjà visé !{RESET}")
                           else:
                               print(f"{RED}Invalide.{RESET}")

                       self.sock.send(f"{shot}\n".encode('utf-8'))
                      
                       res = self.sock.recv(1024).decode('utf-8').strip()
                      
                       if "TOUCHE" in res or "GAME_OVER" in res:
                           self.tracking_board[r][c] = 'X'
                           last_status = f"Tir en {shot} : {GREEN}TOUCHÉ !{RESET}"
                       else:
                           self.tracking_board[r][c] = 'O'
                           last_status = f"Tir en {shot} : {BLUE}Raté...{RESET}"

                       if "GAME_OVER" in res:
                           last_status = f"{GREEN}VICTOIRE ! Vous avez gagné !{RESET}"
                           game_running = False
                      
                       self.display_boards(last_status)

                   elif command == "WAIT":
                       last_status = "L'adversaire vise..."
                       self.display_boards(last_status)
                      
                       opp_shot = self.sock.recv(1024).decode('utf-8').strip()
                       r, c = self.parse_coord(opp_shot)
                      
                       response = "RATE"
                       if r is not None:
                           if (r, c) in self.my_ships_points:
                               self.my_board[r][c] = 'X'
                               self.my_ships_points.remove((r, c))
                               if not self.my_ships_points:
                                   response = "GAME_OVER"
                               else:
                                   response = "TOUCHE"
                           else:
                               self.my_board[r][c] = 'O'
                      
                       self.sock.send(f"{response}\n".encode('utf-8'))
                      
                       if response == "GAME_OVER":
                           last_status = f"{RED}DÉFAITE... Flotte détruite.{RESET}"
                           game_running = False
                       elif response == "TOUCHE":
                           last_status = f"Touché reçu en {opp_shot} !"
                       else:
                           last_status = f"L'ennemi a raté en {opp_shot}."
                      
                       self.display_boards(last_status)

           except KeyboardInterrupt:
               break
           except Exception as e:
               print(f"Erreur : {e}")
               break
      
       self.sock.close()
       print("\nFin de partie.")

if __name__ == "__main__":
   target_host = DEFAULT_HOST     # si rien d'entrée ca prend la DEFAULT_HOST defini au debut
   
   if len(sys.argv) > 1: # verifie si une ip a était donnée en argument a l'exécution du script
       target_host = sys.argv[1]
   else:     # sinon demande une ip
       print(f"--- CONFIGURATION CLIENT ---")
       user_input = input(f"Entrez l'IP du serveur (Entrée pour {DEFAULT_HOST}) : ").strip()
       if user_input:
           target_host = user_input
          
   client = BattleshipClient(target_host)
   client.run()




