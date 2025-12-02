#!/usr/bin/env python3

import socket
import sys
import os
import random
import time

DEFAULT_HOST = '127.0.0.1' 
PORT = 5000

# Couleurs
RESET = "\033[0m"
RED = "\033[31m"    # Touché
BLUE = "\033[34m"   # Eau / Raté
GREEN = "\033[32m"  # Bateau intact
YELLOW = "\033[33m" # Texte informatif
CYAN = "\033[36m"   # Interface
MAGENTA = "\033[35m" # Robot

class BattleshipClient:
   def __init__(self, host=None): 
       self.host = host
       self.is_network_game = (host is not None)
       
       if self.is_network_game:
           self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
       else:
           self.sock = None

       self.is_spectator = False
       
       # Initialisation des variables
       self.reset_game_data()

       # bot (Données du robot)
       self.bot_board = [['~' for _ in range(10)] for _ in range(10)]
       self.bot_ships_points = set()
       self.bot_shots_fired = set()

       # Liste des bateaux
       self.ships_to_place = [
           ("Porte-avions", 5),
           ("Croiseur", 4),
           ("Contre-torpilleur", 3),
           ("Sous-marin", 3),
           ("Torpilleur", 2)
       ]

   def reset_game_data(self):
       """Remet à zéro toutes les grilles pour une nouvelle manche."""
       self.my_board = [['~' for _ in range(10)] for _ in range(10)] 
       self.tracking_board = [['?' for _ in range(10)] for _ in range(10)] 
       self.my_ships_points = set()
       # Pour le mode bot
       self.bot_shots_fired = set()
       self.bot_board = [['~' for _ in range(10)] for _ in range(10)]
       self.bot_ships_points = set()

   def clear_screen(self):
       os.system('clear')

   def display_boards(self, status_msg=""):
       """Affiche les deux grilles côte à côte."""
       self.clear_screen()
       mode_titre = "RÉSEAU" if self.is_network_game else "SOLO VS ROBOT"
       print(f"\n--- {CYAN}BATAILLE NAVALE ({mode_titre}){RESET} ---")
       if self.is_network_game:
           print(f"Serveur : {self.host}")
       print(f"{YELLOW}Statut : {status_msg}{RESET}\n")
      
       header = "   1 2 3 4 5 6 7 8 9 10"
       print(f"   MA FLOTTE (Défense)           RADAR (Attaque)")
       print(f"{header}      {header}")
      
       rows_label = "ABCDEFGHIJ"
      
       for i in range(10): 
           row_left = f"{rows_label[i]} " # --- Ma flotte ---
           for cell in self.my_board[i]:
               if cell == 'B': char = f"{GREEN}#{RESET}"
               elif cell == 'X': char = f"{RED}X{RESET}"
               elif cell == 'O': char = f"{BLUE}O{RESET}"
               else: char = f"{BLUE}~{RESET}"
               row_left += f" {char}"
          
           # --- Radar ---
           row_right = f"{rows_label[i]} "
           for cell in self.tracking_board[i]:
               if cell == 'X': char = f"{RED}X{RESET}"
               elif cell == 'O': char = f"{BLUE}O{RESET}"
               elif cell == '?': char = "."
               else: char = " "
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

   # --- PLACEMENT DES BATEAUX DU JOUEUR ---
   def place_ship(self, start_coord, length, orientation):
       r, c = self.parse_coord(start_coord)
       if r is None: return False

       coords_to_occupy = []
       for i in range(length):
           if orientation == "H":
               curr_r, curr_c = r, c + i
           else: # Vertical
               curr_r, curr_c = r + i, c

           if not (0 <= curr_r < 10 and 0 <= curr_c < 10):
               return False
          
           if self.my_board[curr_r][curr_c] == 'B':
               return False
          
           coords_to_occupy.append((curr_r, curr_c))

       for (pr, pc) in coords_to_occupy:
           self.my_board[pr][pc] = 'B'
           self.my_ships_points.add((pr, pc))
      
       return True

   def setup_phase(self):
       """Boucle interactive pour placer tous les bateaux."""
       # On ne fait plus de reset conditionnel ici, c'est géré avant l'appel
           
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
      
       # Si c'est un jeu réseau avec un autre joueur on prévient le serveur
       if self.is_network_game:
           self.display_boards("Flotte prête ! Tentative de connexion...")
           try:
              self.sock.send("PLACEMENT_OK\n".encode('utf-8'))
           except:
               print(f"{RED}Impossible d’envoyer le statut de placement au serveur.{RESET}")

   # bot
   def bot_setup_ships(self):
       """placement des bateau"""
       print(f"{MAGENTA}Le Robot place ses navires...{RESET}")
       time.sleep(1) 
       
       for name, size in self.ships_to_place:
           placed = False
           while not placed:  # Choix aléatoire pour tirer 
               r = random.randint(0, 9)
               c = random.randint(0, 9)
               ori = random.choice(['H', 'V'])
               
               # Verifie si l'endroit ou il veut tirer et valide (pas deja tirer) 
               coords_to_occupy = []
               possible = True
               for i in range(size):
                   if ori == "H": curr_r, curr_c = r, c + i
                   else:          curr_r, curr_c = r + i, c
                   
                   # Verifie si on ne joue pas hors limites ou si il y a pas une collision
                   if not (0 <= curr_r < 10 and 0 <= curr_c < 10) or \
                      self.bot_board[curr_r][curr_c] == 'B':
                       possible = False
                       break
                   coords_to_occupy.append((curr_r, curr_c))
               
               if possible:
                   for (pr, pc) in coords_to_occupy:
                       self.bot_board[pr][pc] = 'B'
                       self.bot_ships_points.add((pr, pc))
                   placed = True

   def bot_play_turn(self):
       """Le robot tire une case au hasard."""
       while True:
           r = random.randint(0, 9)
           c = random.randint(0, 9)
           if (r, c) not in self.bot_shots_fired:
               self.bot_shots_fired.add((r, c))
               coord_str = f"{chr(r+65)}{c+1}"
               return r, c, coord_str

   def run_solo(self):
       self.reset_game_data() # Reset au début du solo
       self.setup_phase() 
       self.bot_setup_ships() 
       
       game_running = True
       player_turn = True 
       last_msg = "La partie commence contre le Robot !"

       while game_running:
           self.display_boards(last_msg)

           if player_turn:
               print(f"{GREEN}C'est à VOTRE TOUR !{RESET}")
               shot = input("Coordonnées de tir (ex: B5) : ").strip().upper()
               r, c = self.parse_coord(shot)

               if r is None:
                   last_msg = f"{RED}Coordonnée invalide.{RESET}"
                   continue
               
               if self.tracking_board[r][c] != '?':
                   last_msg = f"{YELLOW}Déjà visé ici !{RESET}"
                   continue
               
               if (r, c) in self.bot_ships_points:
                   self.tracking_board[r][c] = 'X' 
                   self.bot_ships_points.remove((r, c)) 
                   last_msg = f"Tir en {shot} : {GREEN}TOUCHÉ !{RESET}"
                   
                   if not self.bot_ships_points:
                       self.display_boards(f"{GREEN}VICTOIRE ! Vous avez coulée toute la flotte du Robot !{RESET}")
                       print("\nBravo capitaine.")
                       break
               else:
                   self.tracking_board[r][c] = 'O' 
                   last_msg = f"Tir en {shot} : {BLUE}Dans l'eau...{RESET}"
                   player_turn = False 
                   
           else:
               self.display_boards(f"{MAGENTA}Le Robot vise...{RESET}")
               time.sleep(1.5) 
               
               r, c, coord_str = self.bot_play_turn()
               
               if (r, c) in self.my_ships_points:
                   self.my_board[r][c] = 'X'
                   self.my_ships_points.remove((r, c))
                   last_msg = f"{RED}Le Robot a TOUCHÉ en {coord_str} !{RESET}"
                   if not self.my_ships_points:
                       self.display_boards(f"{RED}DÉFAITE... Le Robot a détruit votre flotte.{RESET}")
                       break
               else:
                   self.my_board[r][c] = 'O'
                   last_msg = f"{BLUE}Le Robot a raté en {coord_str}.{RESET}"
               
               player_turn = True # au tour du joueur

   def run_network(self):
       """Logique du jeu en mode RÉSEAU (Code original)."""
       try: 
           self.sock.connect((self.host, PORT))
           last_status = "Connexion réussie au serveur !"
           self.display_boards(last_status)
       except socket.error as e:
           print(f"\n{RED}ERREUR CRITIQUE : Impossible de joindre {self.host}:{PORT}{RESET}")
           print(f"Détail : {e}")
           sys.exit(1)

       # FIX: Réception et vérification si PLACE_BATEAUX est collé au message de bienvenue
       welcome = self.sock.recv(1024).decode("utf-8").strip()

       if "observateur" in welcome.lower():
           self.is_spectator = True
           print("Connecté en tant qu'observateur.")
       else:
           self.is_spectator = False
           
           if "PLACE_BATEAUX" in welcome:
               self.reset_game_data() # Reset forcé
               self.setup_phase()
               self.display_boards("Flotte prête ! Attente de l'adversaire")
           else:
               self.display_boards("Connecté. En attente du serveur...")


       # --- EXTENSION : BOUCLE INFINIE ---
       while True:
           try:
               msg = self.sock.recv(1024).decode('utf-8').strip()
               if not msg: break

               if self.is_spectator:
                   # (Logique spectateur inchangée)
                   pass 

               commands = msg.split('\n')
               for command in commands:
                   command = command.strip()
                   if not command: continue

                   # --- C'EST ICI LA CORRECTION IMPORTANTE ---
                   if "PLACE_BATEAUX" in command:
                       self.reset_game_data() # On remet TOUT à zéro
                       self.setup_phase() # Lance le placement
                       self.display_boards("Flotte prête ! Attente de l'adversaire")

                   elif "START" in command:
                       # Sécurité si on a raté l'ordre de placement (compatibilité)
                       if not self.my_ships_points:
                           self.reset_game_data() # Reset aussi ici par sécurité
                           self.setup_phase()
                           
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
                               if self.tracking_board[r][c] == '?': valid = True
                               else: print(f"{YELLOW}Déjà visé !{RESET}")
                           else: print(f"{RED}Invalide.{RESET}")

                       self.sock.send(f"{shot}\n".encode('utf-8'))
                       res = self.sock.recv(1024).decode('utf-8').strip()
                      
                       if "TOUCHE" in res or "GAME_OVER" in res:
                           self.tracking_board[r][c] = 'X'
                           last_status = f"Tir en {shot} : {GREEN}TOUCHÉ !{RESET}"
                       else:
                           self.tracking_board[r][c] = 'O'
                           last_status = f"Tir en {shot} : {BLUE}Raté...{RESET}"

                       if "GAME_OVER" in res:
                           last_status = f"{GREEN}VICTOIRE ! Vous avez gagné la manche !{RESET}"
                           
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
                               if not self.my_ships_points: response = "GAME_OVER"
                               else: response = "TOUCHE"
                           else: self.my_board[r][c] = 'O'
                      
                       self.sock.send(f"{response}\n".encode('utf-8'))
                       if response == "GAME_OVER":
                           last_status = f"{RED}DÉFAITE... Flotte détruite.{RESET}"
                       elif response == "TOUCHE": last_status = f"Touché reçu en {opp_shot} !"
                       else: last_status = f"L'ennemi a raté en {opp_shot}."
                       self.display_boards(last_status)

           except KeyboardInterrupt:
               break
           except Exception as e:
               print(f"Erreur : {e}")
               break
       self.sock.close()
       print("\nFin de partie Réseau.")

if __name__ == "__main__":
    print(f"--- BATAILLE NAVALE ---")
    print("1. Joueur vs Joueur (Réseau)")
    print("2. Joueur vs Robot (Solo)")
    
    choice = input("Votre choix (1 ou 2) : ").strip()
    
    if choice == "1":
       print(f"--- CONFIGURATION CLIENT ---")
       target_host = DEFAULT_HOST
       # Si argument en ligne de commande, prioritaire
       if len(sys.argv) > 1:
           target_host = sys.argv[1]
       else:
           user_input = input(f"Entrez l'IP du serveur (Entrée pour {DEFAULT_HOST}) : ").strip()
           if user_input:
               target_host = user_input
               
       client = BattleshipClient(host=target_host)
       client.run_network()
       
    else:
       # Mode solo : pas besoin d'IP
       client = BattleshipClient(host=None)
       client.run_solo()