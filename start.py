# Programme qui permet de démarrer le bot discord sous forme d'un processus
# Utile sur le serveur vps
from subprocess import Popen
from time import sleep
import os

# On met à jour les fichiers
os.system("git pull")

sleep(3)

Popen("python3 bot_discord.py >/dev/null 2>&1", shell=True)
