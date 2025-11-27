#!/usr/bin/env python3

import socket
import sys
import os

# Configuration
DEFAULT_HOST = '127.0.0.1'
PORT = 5000

# Couleurs pour le terminal
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
      
       # Initialisation des grilles (10x10)
       self.my_board = [['~' for _ in range(10)] for _ in range(10)]
       self.tracking_board = [['?' for _ in range(10)] for _ in range(10)]
      
       self.my_ships_points = set()
      
       # Liste des bateaux à placer (Nom, Taille)
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

       header = "   1 2 3 4 5 6 7 8 9 10"                          #Gère l'interface graphique (les numeros)
       print(f"    MA FLOTTE (Défense)      RADAR (Attaque)")   #gère l'interface graphique
       print(f"{header}    {header}")

       rows_label = "ABCDEFGHIJ"
       for i in range(10):
           # Construction ligne gauche (Ma flotte)
           row_left = f"{rows_label[i]} "
           for cell in self.my_board[i]:
               if cell == 'B': char = f"{GREEN}#{RESET}"
               elif cell == 'X': char = f"{RED}X{RESET}"
               elif cell == 'O': char = f"{BLUE}O{RESET}"
               else: char = f"{BLUE}~{RESET}"
               row_left += f" {char}"

           # Construction ligne droite (Radar)
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

   def place_ship(self, start_coord, length, orientation):

#reste a faire : position des bateaux

