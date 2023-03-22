"""
from donnees_serveur import Binance
from datetime import datetime
import locale

symbol_run = "XRP"

dico = {}

with open(f"Autre_fichiers/message_bot/message_bot_{symbol_run}.txt", "r") as f:
    content_file = f.read().split(
        f"Bot {symbol_run} toujours en cour d'exécution le : ")[1:]
    cpt = 0
    ls = []

    for element in content_file:
        elt = element.split("\n")
        date = elt[0]

        for prix_ls in elt[1:]:

            prix = prix_ls.split(", ")

            for pr in prix:
                price = pr.split(" : ")

                ls.append(float(price[1]))
        ls.append(date)

        dico[cpt] = ls
        cpt += 1
        ls = []


locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

bb = Binance()

toto_up = 0
pas_toto_up = 0

toto_down = 0
pas_toto_down = 0

liste_ = []
liste_up = []
liste_down = []

for i in range(len(dico)):
    liste = dico[i]

    if liste[0] <= liste[1] and liste[2] <= liste[3] and liste[4] >= liste[5]:

        ancienne_date = datetime.strptime(
            str(liste[6]), "%A %d %B %Y %H:%M:%S")

        ancienne_date = int(ancienne_date.strftime("%s"))

        date = datetime.now()

        date = int(date.strftime("%s"))

        heure = int(((date - ancienne_date) / 60) / 60)

        donnee_serveur = bb.donnée(
            f"{symbol_run}USDT", f"{heure + 1} hour ago utc", f"{heure} hour ago utc")["high"]

        if (liste[0] * (1 + (0.015 / 3))) >= float(donnee_serveur):
            a = ""
            toto_up += 1
            print("toto ", liste[1] - liste[0], liste[3] - liste[2], liste[4] - liste[5])
            liste_.append(liste[1] - liste[0])
            liste_up.append(liste[3] - liste[2])
            liste_down.append(liste[4] - liste[5])

        else:
            a = ""
            pas_toto_up += 1

    elif liste[0] >= liste[1] and liste[2] >= liste[3] and liste[4] <= liste[5]:
        ancienne_date = datetime.strptime(
            str(liste[6]), "%A %d %B %Y %H:%M:%S")

        ancienne_date = int(ancienne_date.strftime("%s"))

        date = datetime.now()

        date = int(date.strftime("%s"))

        heure = int(((date - ancienne_date) / 60) / 60)

        donnee_serveur = bb.donnée(
            f"{symbol_run}USDT", f"{heure + 1} hour ago utc", f"{heure} hour ago utc")["low"]

        if (liste[0] * (1 - (0.015 / 3))) <= float(donnee_serveur):
            a = ""
            toto_down += 1
            #print("toto ", liste[0] - liste[1], liste[2] - liste[3], liste[5] - liste[4])
            #liste_.append(liste[0] - liste[1])
            #liste_up.append(liste[2] - liste[3])
            #liste_down.append(liste[5] - liste[4])

        else:
            a = ""
            pas_toto_down += 1


print("toto_up = ", toto_up)
print("pas toto up = ", pas_toto_up)

print("toto_down = ", toto_down)
print("pas toto down = ", pas_toto_down)

if liste_ != []:
    print("liste_ ", max(liste_))
    print("liste_up ", max(liste_up))
    print("liste_down ", max(liste_down))
"""