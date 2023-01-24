# Programme qui permet d'arreter le bot discord
# Utile sur le serveur vps
from bot_discord import commande_bot_terminale
from subprocess import Popen, PIPE
import os

proc = Popen(commande_bot_terminale, shell=True, stdout=PIPE, stderr=PIPE)

sortie, autre = proc.communicate()

processus = sortie.decode('utf-8').split("\n")[:-1]

for elt in processus:
    os.system(f"kill -9 {elt}")
