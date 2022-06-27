from multiprocessing import Process, Manager
from subprocess import Popen, PIPE
from binance.client import Client
from dotenv import load_dotenv
from functools import wraps
import requests
import hashlib
import base64
import pandas
import time
import hmac
import json
import ast
import os

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

# BINANCE
# Fonctions qui récupère les données du serveur


api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")

client = Client(api_key, api_secret)


@connexion
def donnée(symbol: str, début: str, fin: str, longueur: int) -> pandas.DataFrame:
    """
    Fonction qui prend en argument un symbol de type "BTCEUR" ou encore "ETHEUR" etc...
    Et qui renvoie les données sous forme d'une dataframe pandas
    Ex param :
    symbol : 'BTCEUR'
    début : "200 min ago UTC" 
    fin : "0 min ago UTC" ...
    longueur : 40 données ...
    """
    donnée_historique = []
    # Tant que l'on a pas la bonne quantité de donnée on continue
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
def prix_temps_reel(symbol: str) -> float:
    """
    Fonction qui récupère le prix en temps réel d'un symbol voulu
    Ex param :
    symbol : BTCEUR
    """

    return float(client.get_ticker(symbol=symbol)['lastPrice'])


@connexion
def all_data(symbol: str) -> dict:
    """
    Fonction qui prend en argument un symbol
    Et renvoie toutes les données de tous les jetons (ceux avec effet de levier aussi) sous forme d'un seul dictionnaire
    """
    # Création du dictionnaire que recevra toutes les dataframes avec les données
    manager = Manager()
    dico = manager.dict()

    def requete(sl: str, limit: str, dictionnaire: dict, position_list: int):
        """
        Fonction qui récupère les données d'une crypto de façon asyncrone
        """
        api = """https://api.binance.com/api/v3/klines"""

        param = {'symbol': sl,
                 'interval': '15m',
                 'limit': limit}

        donnee = requests.get(api, params=param)

        data = donnee.json()

        for i in range(len(data)):
            data[i] = data[i][:7]

        data = pandas.DataFrame(data)

        data.columns = ['timestart', 'open', 'high', 'low',
                        'close', 'volume', 'timeend']

        # On enregistre les données qui ont 40 pour longeur

        dictionnaire[position_list] = data

        # Puis on vient enregistrer les données qui ont 15 pour longueur
        # On renomme les lignes pour que ça commence à partir de zéro

        data_15 = data[25:].rename(index=lambda x: x - 25)

        # Les données avec 15 de longueur on rajoute 3 à la clé pour garder l'ordre par rapport aux trois cryptos
        # BTC 40
        # BTCUP 40
        # BTCDOWN 40
        # BTC 15
        # BTCUP 15
        # BTCDOWN 15

        dictionnaire[position_list + 3] = data_15

        return dictionnaire

    p = Process(target=requete, args=(f"{symbol}USDT", 40, dico, 0,))
    p2 = Process(target=requete, args=(f"{symbol}UPUSDT", 40, dico, 1,))
    p3 = Process(target=requete, args=(f"{symbol}DOWNUSDT", 40, dico, 2,))

    p.start()
    p2.start()
    p3.start()

    p.join()
    p2.join()
    p3.join()

    dico = dict(sorted(dico.items()))

    return dico

# KUCOIN


api = "https://api.kucoin.com"

kucoin_api_key = os.getenv("KUCOIN_API_KEY")
kucoin_api_secret = os.getenv("KUCOIN_API_SECRET")
kucoin_phrase_securite = os.getenv("KUCOIN_PHRASE_SECURITE")


def montant_compte(symbol: str or list) -> float or list:
    """
    Fonction qui renvoie le montant que possède le compte selon le ou les symbols voulus
    """

    endpoint = '/api/v1/accounts'

    now = int(time.time() * 1000)

    str_to_sign = str(now) + 'GET' + endpoint

    signature = base64.b64encode(
        hmac.new(kucoin_api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())

    passphrase = base64.b64encode(hmac.new(kucoin_api_secret.encode(
        'utf-8'), kucoin_phrase_securite.encode('utf-8'), hashlib.sha256).digest())

    headers = {
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": str(now),
        "KC-API-KEY": kucoin_api_key,
        "KC-API-PASSPHRASE": passphrase,
        "KC-API-KEY-VERSION": "2",
        "Content-Type": "application/json"
    }

    argent = ast.literal_eval(requests.get(api + endpoint,
                                           headers=headers).content.decode('utf-8'))['data']

    montant = 0

    if symbol == 'USDT':
        for elt in argent:
            if elt['currency'] == 'USDT' and elt['type'] == 'trade':
                montant = float(elt['available'])

    elif symbol == 'BTCUP':
        for elt in argent:
            if elt['currency'] == 'BTC3L' and elt['type'] == 'trade':
                montant = float(elt['available'])

    elif symbol == 'BTCDOWN':
        for elt in argent:
            if elt['currency'] == 'BTC3S' and elt['type'] == 'trade':
                montant = float(elt['available'])

    return montant
