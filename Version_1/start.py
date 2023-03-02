# Programme qui permet de démarrer le bot discord sous forme d'un processus
# Utile sur le serveur vps
from subprocess import Popen
import os

# On met à jour les fichiers
os.system("git pull")

Popen("nohup python3.10 bot_discord.py >/dev/null 2>&1", shell=True)
