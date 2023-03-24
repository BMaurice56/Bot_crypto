# Programme qui permet d'arrêter le bot discord
# Utile sur le serveur vps
from subprocess import Popen, PIPE
import os

commande_bot_terminale = """ps -aux | grep "bot_discord.py"| awk -F " " '{ print $2 }' """

proc = Popen(commande_bot_terminale, shell=True, stdout=PIPE, stderr=PIPE)

sortie, autre = proc.communicate()

processus = sortie.decode('utf-8').split("\n")[:-1]

for elt in processus:
    os.system(f"kill -9 {elt}")
