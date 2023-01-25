
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

"""
from main import *

entete = headers("GET", "/api/v1/symbols")

toto = requests.get(api + "/api/v1/symbols", headers=entete)

toto2 = json.loads(toto.content)

toto = toto2["data"]

for elt in toto:
    if elt["symbol"] == "BTC3L-USDT" or elt["symbol"] == "BTC3S-USDT":
        print(elt)
"""
"""
from multiprocessing import Pool
import asyncio
from main import *
tt = sys.argv[1]


def suppresion_message_sup_10(toto):
    """
# Fonction qui supprime les messages sur le canal discord
# s'il y a plus de 10 messages
"""

    # Id des channels
    id_etat_bot = "972545416786751488"
    id_prise_position = "973269585547653120"

    channel_etat_bot = toto.get_channel(int(id_etat_bot))
    channel_prise_position = toto.get_channel(int(id_prise_position))

    # jeton pour acceder au serveur
    entete = {
        'authorization': 'NTMxNTg2MTg4OTE0NTg5NzA4.GdHYmv.OlmPtm1FyssGqEJLSymyJAN-I_0noR6Y2kGBkM'}

    # Récupération des messages
    r_etat_bot = requests.get(
        'https://discord.com/api/v9/channels/972545416786751488/messages', headers=entete)
    r_prise_position = requests.get(
        'https://discord.com/api/v9/channels/973269585547653120/messages', headers=entete)

    # Conversion en liste
    text_etat_bot = json.loads(r_etat_bot.text)
    text_prise_position = json.loads(r_prise_position.text)

    return [text_etat_bot, channel_etat_bot]


async def jsp(text_etat_bot, channel_etat_bot):
    if len(text_etat_bot) > 10:
        for message in text_etat_bot[10:]:
            msg = await channel_etat_bot.fetch_message(message['id'])
            await msg.delete()

tototo = suppresion_message_sup_10(tt)[0]
totototototo = suppresion_message_sup_10(tt)[1]

loop = asyncio.get_event_loop()
loop.run_until_complete(jsp(tototo, totototototo))
loop.close()

"""

from datetime import datetime
import locale

from zoneinfo import ZoneInfo

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

print(datetime.now(tz=ZoneInfo("Europe/Paris")).strftime("%A %d %B %Y %H:%M:%S"))

"""
toto = tzinfo("Europe/Paris")
print(toto)
"""