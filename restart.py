from subprocess import Popen, PIPE
import os

commande_bot_terminale = """ps -aux | grep "bot_discord.py"| awk -F " " '{ print $2 }' """

# D'abord on arrête tous les processus du bot
proc = Popen(commande_bot_terminale, shell=True, stdout=PIPE, stderr=PIPE)

sortie, autre = proc.communicate()

processus = sortie.decode('utf-8').split("\n")[:-1]

for elt in processus:
    os.system(f"kill -9 {elt}")

# On met à jour les fichiers
os.system("git pull")

# Et enfin, on redémarre le bot
Popen("nohup python3.10 bot_discord.py >/dev/null 2>&1", shell=True)
