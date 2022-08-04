from subprocess import Popen, PIPE
from time import sleep
import os

proc = Popen("""ps -aux | grep "bot_discord.py"| awk -F " " '{ print $2 }' """,
             shell=True, stdout=PIPE, stderr=PIPE)

sortie, autre = proc.communicate()

processus = sortie.decode('utf-8').split("\n")[:-1]

for elt in processus:
    os.system(f"kill -9 {elt}")

sleep(3)

Popen("python3.10 bot_discord.py", shell=True)
print("bot redémarré")
