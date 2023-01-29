
"""
fichier = open("message_discord.txt", "r")

texte = fichier.read()

texte = texte.split("\\n")

for elt in texte:
    if "programme toujours en cour d'exécution le :" in elt:
        indice = texte.index(elt)

        ch = elt

        ch = ch.split('"')

        texte[indice] = ch[0]

texte.pop(0)

liste_final = []

for i in range(0, len(texte), 3):

    ch = texte[i]
    ch2 = texte[i+1]
    ch3 = texte[i+2]

    ch = ch.split(",")
    ch2 = ch2.split(",")
    ch3 = ch3.split(",")

    for elt in ch:
        chiffre = elt.split(" ")[-1]

        ch[ch.index(elt)] = chiffre

    for elt in ch2:
        chiffre = elt.split(" ")[-1]

        ch2[ch2.index(elt)] = chiffre

    for elt in ch3:
        chiffre = elt.split(" ")[-1]

        ch3[ch3.index(elt)] = chiffre

    liste_final.append(ch)
    liste_final.append(ch2)
    liste_final.append(ch3)


succes = 0
fail = 0

for ls in liste_final:
    indice = liste_final.index(ls)

    for elt in ls:
        indice2 = ls.index(elt)

        liste_final[indice][indice2] = float(elt.split('"')[0])

ls_moyenne = []

marge = 25
autre = 0

for i in range(0, len(liste_final)-9, 3):
    if liste_final[i][0] < liste_final[i][1] and liste_final[i+1][0] < liste_final[i+1][1] and liste_final[i+2][0] > liste_final[i+2][1] and liste_final[i+1][1] - liste_final[i+1][0] >= 0.045:
        if liste_final[i+3][0] > liste_final[i][0] and (liste_final[i+3][0] - liste_final[i][0]) > marge:
            succes += 1

        elif liste_final[i+6][0] > liste_final[i][0] and (liste_final[i+6][0] - liste_final[i][0]) > marge:
            succes += 1

        elif liste_final[i+9][0] > liste_final[i][0] and (liste_final[i+9][0] - liste_final[i][0]) > marge:
            succes += 1

        else:
            fail += 1

    else:
        autre += 1


my = 0

print("autre :", autre)
print("succes :", succes)
print("fail :", fail)
print(succes / fail)
"""

from zoneinfo import ZoneInfo
from datetime import datetime
from main import *
import locale

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

date = datetime.now(tz=ZoneInfo("Europe/Paris")
                    ).strftime("%A %d %B %Y %H:%M:%S")

print(date)

date = datetime.strptime(date, "%A %d %B %Y %H:%M:%S")

print(date)

date = int(date.strftime("%s"))

print(date)
