from discord_webhook import DiscordWebhook, DiscordEmbed
from time import sleep, perf_counter
from multiprocessing import Process
from subprocess import Popen, PIPE
from binance.client import Client
from indices_techniques import *
from sklearn import linear_model
from dotenv import load_dotenv
from functools import wraps
from database import *
import locale
import copy
import ast
import sys
import os

#from keras.models import Sequential
#from keras.layers import Dense

# Définition de la zone pour l'horodatage car la date était en anglais avec le module datetime
locale.setlocale(locale.LC_TIME, '')


# Chargement des clés

load_dotenv(dotenv_path="config_bot")

# Décorateurs


def connexion(f):
    """
    Décorateur permettant de vérifier si on est bien connecté à internet
    """
    @wraps(f)
    def auto_con(*args, **kwargs):
        """
        Fonction qui reconnecte automatiquement le pc à internet
        commande à implenter :
        """
        # On regarde si on est connecté à internet via wifi ou ethernet
        proc = Popen("nmcli con show --active",
                     shell=True, stdout=PIPE, stderr=PIPE)

        sortie, autre = proc.communicate()

        type_connexion = sortie.decode('utf-8')
        ###############################################################

        connex = False

        if "ethernet" not in type_connexion and "wifi" not in type_connexion:
            # Tant qu'on est pas connecté, on continue
            while connex == False:
                # On regarde les réseaux disponibles autour de l'appareil et on supprime les doublons de noms de réseaux
                proc = Popen(
                    """nmcli device wifi | awk -F " " '{ print $2 }'""", shell=True, stdout=PIPE, stderr=PIPE)
                sortie, autre = proc.communicate()
                result = sortie.decode('utf-8')[6:-1].split(chr(10))
                reseau_dispo = list(set(result))
                ###############################################################
                if len(reseau_dispo) == 0:
                    return "Pas de connexion disponible"
                # On regarde les réseaux connus de l'appareil
                proc2 = Popen("nmcli con --show | grep wifi",
                              shell=True, stdout=PIPE, stderr=PIPE)
                sortie2, autre = proc2.communicate()
                resultat = sortie2.decode('utf-8').split(chr(10))
                reseaux_connu = []
                for i in range(len(resultat)):
                    temp = ""
                    # Dès qu'on arrive aux ssid, le nom étant forcément avant, on garde tout ce qui y'a devant
                    for j in range(len(resultat[i])):
                        if resultat[i][j].isnumeric() and resultat[i][j+8] == "-" and resultat[i][j+13] == "-" and resultat[i][j+18] == "-" and resultat[i][j+23] == "-":
                            temp = resultat[i][:j]
                            break
                    # Etant donnée qu'il reste des espaces à la fin (car taille des noms de réseaux différents)
                    # Tant qu'il y a un espace à la fin, on garde tout sauf l'espace
                    for k in range(len(temp)-1, 0, -1):
                        if ord(temp[k]) == 32:
                            temp = temp[:-1]
                        else:
                            break
                    reseaux_connu.append(temp)
                # Et à la fin, on enlève le dernier élément de la liste qui est ''
                reseaux_connu.pop()
                ###############################################################

                # On regarde si le réseau est connu et si oui, on essaye de se connecter à celui-ci
                # On re-regarde si on est bien connecté à internet
                # Et si ce n'est pas le cas alors on passe au réseau suivant
                # Si on est bien connecté, on peut arrêter la boucle while qui permet de reéssayer en boucle
                # Et on ne teste pas les autres réseaux
                for reseau in reseau_dispo:
                    if reseau in reseaux_connu:
                        Popen(f"nmcli con up {reseau}", shell=True)
                        sleep(4)

                        proc = Popen("nmcli con show --active",
                                     shell=True, stdout=PIPE, stderr=PIPE)

                        sortie, autre = proc.communicate()

                        type_connexion = sortie.decode('utf-8')
                        if "wifi" not in type_connexion:
                            continue
                        else:
                            connex = True
                            break

                ###############################################################

        return f(*args, **kwargs)

    return auto_con


# Fonctions qui récupère les données du serveur

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")

client = Client(api_key, api_secret)
client2 = Client(api_key, api_secret)
client3 = Client(api_key, api_secret)


@connexion
def donnée(symbol: str, début: str, fin: str, longueur: int) -> pandas.DataFrame:
    """
    Fonction qui prend en argument un symbol de type "BTCEUR" ou encore "ETHEUR" etc...
    Et qui renvoie les données sous forme d'une dataframe pandas
    Ex param :
    symbol : 'BTCEUR'
    interval : client.KLINE_INTERVAL_5MINUTE ou client.KLINE_INTERVAL_1HOUR ...
    début : "200 min ago UTC" ou "40 hour ago UTC" ...
    fin : "0 min ago UTC" ...
    interval : 40 données ...
    """
    donnée_historique = []
    while len(donnée_historique) != longueur:
        # Récupération des données de la crypto
        if fin[0] == "0":
            donnée_historique = client.get_historical_klines(
                symbol, client.KLINE_INTERVAL_15MINUTE, début)

        else:
            donnée_historique = client.get_historical_klines(
                symbol, client.KLINE_INTERVAL_15MINUTE, début, fin)

        # On enlève les données pas nécessaire
        for i in range(len(donnée_historique)):
            donnée_historique[i] = donnée_historique[i][:7]

    # Création de la df et nommage des colonnes
    data = pandas.DataFrame(donnée_historique)

    data.columns = ['timestart', 'open', 'high', 'low',
                    'close', 'volume', 'timeend']

    return data


@connexion
def donnée_bis(symbol: str, début: str, fin: str, longueur: int, client_n) -> pandas.DataFrame:
    """
    Fonction qui prend en argument un symbol de type "BTCEUR" ou encore "ETHEUR" etc...
    Et qui renvoie les données sous forme d'une dataframe pandas
    Ex param :
    symbol : 'BTCEUR'
    interval : client.KLINE_INTERVAL_5MINUTE ou client.KLINE_INTERVAL_1HOUR ...
    début : "200 min ago UTC" ou "40 hour ago UTC" ...
    fin : "0 min ago UTC" ...
    interval : 40 données ...
    """
    donnée_historique = []
    while len(donnée_historique) != longueur:
        # Récupération des données de la crypto
        if fin[0] == "0":
            donnée_historique = client_n.get_historical_klines(
                symbol, client_n.KLINE_INTERVAL_15MINUTE, début)

        else:
            donnée_historique = client_n.get_historical_klines(
                symbol, client_n.KLINE_INTERVAL_15MINUTE, début, fin)

        # On enlève les données pas nécessaire
        for i in range(len(donnée_historique)):
            donnée_historique[i] = donnée_historique[i][:7]

    # Création de la df et nommage des colonnes
    data = pandas.DataFrame(donnée_historique)

    data.columns = ['timestart', 'open', 'high', 'low',
                    'close', 'volume', 'timeend']

    return data


@connexion
def prix_temps_reel(symbol: str) -> float:
    """
    Fonction qui récupère le prix en temps réel d'un symbol voulu
    Ex param :
    symbol : BTCEUR
    """

    return float(client.get_ticker(symbol=symbol)['lastPrice'])


# Fonctions de prédiction

def prédiction(donnée_serveur_data: pandas.DataFrame, donnée_serveur_rsi: pandas.DataFrame) -> float:
    """
    Fonction qui prédit le future prix de la crypto
    """
    X, y = select_donnée_bdd()[0]

    regr = linear_model.LinearRegression()
    regr.fit(X, y)

    sma = SMA(donnée_serveur_data)
    ema = EMA(donnée_serveur_data)
    macd = MACD(donnée_serveur_data)
    stochrsi = stochRSI(donnée_serveur_data)
    bb = bandes_bollinger(donnée_serveur_data)

    rsi = RSI(donnée_serveur_rsi)
    vwap = VWAP(donnée_serveur_rsi)
    cmf = chaikin_money_flow(donnée_serveur_rsi)

    ls = []

    for elt in sma:
        ls.append(elt)

    for elt in ema:
        ls.append(elt)

    for element in macd:
        for elt in element:
            ls.append(elt)

    for element in stochrsi:
        for elt in element:
            ls.append(elt)

    for element in bb:
        for elt in element:
            ls.append(elt)

    ls.append(rsi)
    ls.append(vwap)
    ls.append(cmf)

    df_liste = pandas.DataFrame([ls])

    prediction = regr.predict(df_liste)

    return prediction[0][0]


def prédiction_keras(donnée_serveur_data: pandas.DataFrame, donnée_serveur_rsi: pandas.DataFrame) -> float:
    """"""
    X, y = select_donnée_bdd()[1]

    modele = Sequential()

    modele.fit(X, y)

    sma = SMA(donnée_serveur_data)
    ema = EMA(donnée_serveur_data)
    macd = MACD(donnée_serveur_data)
    stochrsi = stochRSI(donnée_serveur_data)
    bb = bandes_bollinger(donnée_serveur_data)

    rsi = RSI(donnée_serveur_rsi)
    vwap = VWAP(donnée_serveur_rsi)
    cmf = chaikin_money_flow(donnée_serveur_rsi)

    ls = []

    for elt in sma:
        ls.append(elt)

    for elt in ema:
        ls.append(elt)

    for element in macd:
        for elt in element:
            ls.append(elt)

    for element in stochrsi:
        for elt in element:
            ls.append(elt)

    for element in bb:
        for elt in element:
            ls.append(elt)

    ls.append(rsi)
    ls.append(vwap)
    ls.append(cmf)

    df_liste = numpy.array(ls)

    predic = modele.predict(df_liste)

    return predic


# Fonctions de surveillance de position


def surveillance(symbol: str, argent: int, position: dict, temps_execution: int, effet_levier: int) -> None or float:
    """
    Fonction qui prend en argument un symbol, l'argent du compte, la prise de position ou non et le temps d'execution de la fonction
    Et renvoie soit None soit l'argent sous forme d'un float si la position a été vendue
    Ex param :
    symbol : 'BTCEUR'
    argent : 150 euros
    position : {75 : 37000}
    temps_execution : 15*60 secondes
    effet_levier : 5
    """
    t1 = perf_counter()
    for elt in position.items():
        argent_pos, prix_pos = elt

    sleep(50)

    historique_prix = [prix_temps_reel(symbol)]
    while True:
        t2 = perf_counter()
        if t2 - t1 >= temps_execution:
            break
        elif t2 - t1 + 2*60 >= temps_execution:
            sleep(temps_execution - (t2 - t1))
            break

        prix = prix_temps_reel(symbol)

        if prix_pos <= prix and historique_prix[-1] <= prix:
            historique_prix.append(prix)
            sleep(2*60)
        if len(historique_prix) >= 2:
            if historique_prix[-2] > historique_prix[-1] > prix:
                gain = ((prix * argent_pos) / prix_pos) - argent_pos
                argent += argent_pos / effet_levier + gain
                msg = f"Vente de position au prix de {prix}€, prix avant : {prix_pos}€, gain de {gain}, il reste {argent}€"
                message_prise_position(msg, False)
                sleep(temps_execution - (t2 - t1))
                return argent

    return None


# Autres fonctions

def moyenne(liste: list or dict) -> float:
    """
    Fonction qui calcule la moyenne des éléments d'une liste d'entier ou de décimaux
    Obliger de faire la deuxième liste en deux étape car parfois, les nombres décimaux
    sont sous forme d'une chaine de caractère, et donc faut d'abord les re-transformer en décimaux
    """
    liste2 = [float(x) for x in liste]
    liste2 = [float(x) for x in liste2 if math.isnan(x) == False]

    return sum(liste2) / len(liste2)


# Adresse du webhook discord
adr_webhook_prise_position = os.getenv("ADR_WEBHOOK_PRISE_POSITION")
adr_webhook_état_bot = os.getenv("ADR_WEBHOOK_ETAT_BOT")
adr_webhook_général = os.getenv("ADR_WEBHOOK_GENERAL")


def message_prise_position(message: str, prise_position: bool) -> None:
    """
    Fonction qui envoie un message au serveur discord au travers d'un webhook sur le canal de prise de position
    Envoie la prise ou vente de position, les gains, etc...
    Ex param :
    message : "vente d'une position etc...
    prise_position : True pour un achat et False pour une vente
    """
    webhook = DiscordWebhook(
        url=adr_webhook_prise_position, username="Bot crypto")

    if prise_position == True:
        embed = DiscordEmbed(title='Prise de position', color="03b2f8")
    else:
        embed = DiscordEmbed(title='Vente de position', color="03b2f8")

    embed.add_embed_field(name="Message :", value=message)
    webhook.add_embed(embed)
    webhook.execute()


def message_webhook_état_bot(message: str) -> None:
    """
    Fonction qui envoie un message au serveur discord au travers d'un webhook sur le canal éta bot
    Envoie l'état en cours du bot
    Ex param :
    message : "Bot toujours en cours d'execution ..."
    """
    webhook = DiscordWebhook(
        url=adr_webhook_état_bot, username="Bot crypto")

    embed = DiscordEmbed(title='Etat du bot !', color="03b2f8")
    embed.add_embed_field(name="Message :", value=message)
    webhook.add_embed(embed)
    webhook.execute()


def message_status_général(message: str) -> None:
    """
    Fonction qui envoie un message au serveur discord au travers d'un webhook sur le canal général
    Ex param :
    message : "Bot crypto est lancé"
    """
    webhook = DiscordWebhook(
        url=adr_webhook_général, username="Bot crypto", content=message)

    webhook.execute()
