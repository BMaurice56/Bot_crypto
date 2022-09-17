from tenacity import retry, retry_if_exception_type, stop_after_attempt
from multiprocessing import Process, Manager
from decimal import Decimal, ROUND_DOWN
from indices_techniques import moyenne
from time import sleep, perf_counter
from subprocess import Popen, PIPE
from binance.client import Client
from message_discord import *
from functools import wraps
from typing import Optional
from random import randint
import requests
import hashlib
import base64
import pandas
import time
import hmac
import json
import ccxt


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


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
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


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
def prix_temps_reel(symbol: str) -> float:
    """
    Fonction qui récupère le prix en temps réel d'un symbol voulu
    Ex param :
    symbol : BTCEUR
    """

    return float(client.get_ticker(symbol=symbol)['lastPrice'])


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
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
                 'interval': '1h',
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


def arrondi(valeur: float or str, zero_apres_virgule: Optional[float] = None) -> float:
    """
    Fonction qui prend en argument un décimal et renvoie ce décimal arrondi à 0,00001
    """
    # On transforme la valeur reçu en objet décimal
    val = Decimal(str(valeur))

    # S'il y a pas de nombre après la virgule spécifié, on change rien
    # Puis on arrondi vers le bas le nombre que l'on renvoit sous forme d'un float
    if zero_apres_virgule != None:
        return float(val.quantize(Decimal(str(zero_apres_virgule)), ROUND_DOWN))
    return float(val.quantize(Decimal('0.0001'), ROUND_DOWN))


def headers(methode: str, endpoint: str, param: Optional[str] = None) -> dict:
    """
    Fonction qui fait l'entête de la requête http
    Ex paramètre :
    methode : 'GET'
    endpoint : 'api/v1/orders'
    param : none ou dict sous forme json.dumps() -> str
    """
    now = str(int(time.time() * 1000))

    if methode == 'GET':
        str_to_sign = now + 'GET' + endpoint

    elif methode == 'POST':
        str_to_sign = now + 'POST' + endpoint + param

    elif methode == 'DELETE':
        str_to_sign = now + 'DELETE' + endpoint

    signature = base64.b64encode(
        hmac.new(kucoin_api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())

    passphrase = base64.b64encode(hmac.new(kucoin_api_secret.encode(
        'utf-8'), kucoin_phrase_securite.encode('utf-8'), hashlib.sha256).digest())

    headers = {
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": now,
        "KC-API-KEY": kucoin_api_key,
        "KC-API-PASSPHRASE": passphrase,
        "KC-API-KEY-VERSION": "2",
        "Content-Type": "application/json"
    }

    return headers


def lecture_fichier() -> str or None:
    """
    Fonction qui lit ce qu'il y a dans le fichier 
    Et renvoie le contenu ou None s'il y a rien
    """

    fichier = open("ordre_limit.txt", "r")

    elt = fichier.read()

    fichier.close()

    if elt == "":
        return None
    return elt


def écriture_fichier(str_to_write: Optional[str] = None) -> None:
    """
    Fonction qui écrit ou écrase le fichier
    Ex param :
    str_to_write : id de l'ordre
    """

    fichier = open("ordre_limit.txt", "w")

    if str_to_write != None:
        fichier.write(str_to_write)

    fichier.close()


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
def montant_compte(symbol: str) -> float:
    """
    Fonction qui renvoie le montant que possède le compte selon le ou les symbols voulus
    Ex paramètre :
    symbol : USDT
    """
    # On défini la terminaison de la requête
    endpoint = f"/api/v1/accounts?currency={symbol}&type=trade"

    # On crée l'entête
    entête = headers('GET', endpoint)

    # Puis on execute la requête que l'on retransforme en dictionnaire (car reçu au format str)
    argent = json.loads(requests.get(
        api + endpoint, headers=entête).content.decode('utf-8'))["data"]

    # S'il le compte possède le symbol voulu, on renvoit le nombre
    # Avec seulement 99,9% de sa quantité initiale car pour l'achat des cryptos
    # -> aucun problème avec le nb de chiffres après la virgule et les frais de la platforme
    if argent != []:
        money = arrondi(float(argent[0]['balance']) * 0.999)
        return money
    else:
        return 0


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
def prix_temps_reel_kucoin(symbol: str) -> float:
    """
    Fonction qui renvoie le prix de la crypto en temps réel
    Ex paramètre : 
    symbol : BTC3S-USDT
    """
    # On défini la terminaison de la requête
    endpoint = f"/api/v1/market/orderbook/level1?symbol={symbol}"

    # On crée l'entête
    entête = headers('GET', endpoint)

    # Puis on execute la requête que l'on retransforme en dictionnaire (car reçu au format str)
    # Et on garde que le prix voulu
    argent = float(json.loads(requests.get(
        api + endpoint, headers=entête).content.decode('utf-8'))["data"]["price"])

    return argent


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
def prise_position(info: dict) -> str:
    """
    Fonction qui prend une position soit d'achat soit de vente et place un stoploss
    Quand on achète on place automatiquement un stoploss
    Et quand on vend, on retire le stoploss et/ou l'ordre s'il n'a pas été exécuté
    Renvoie l'id de la position prise
    Ex paramètres :
    info : {
    "montant" : "50",
    "symbol" : "BTC3S-USDT",
    "achat_vente" : "True" (pour achat)
    }
    Sortie de la fonction :
    "vs9o2om08lvqav06000s2u7e"
    """
    # Lorsque l'on vend, on enlève l'ordre limit car soit il a été exécuté, soit il est toujours là
    if info["achat_vente"] == False:
        suppression_ordre()

    # Besoin d'un id pour l'achat des cryptos
    id_position = randint(0, 100_000_000)

    # Point de terminaison de la requête
    endpoint = "/api/v1/orders"

    # Soit on achète tant de crypto avec de l'usdt
    # Soit on vend tant de la crypto en question
    if info["achat_vente"] == True:
        achat = "buy"
        type_achat = "funds"
    else:
        achat = "sell"
        type_achat = "size"

    # Définition de tous les paramètres nécessaires
    param = {"clientOid": id_position,
             "side": achat,
             "symbol": info["symbol"],
             'type': "market",
             type_achat: str(info["montant"])}

    param = json.dumps(param)

    # Création de l'entête
    entête = headers('POST', endpoint, param)

    # On prend la position sur le serveur
    prise_position = requests.post(api + endpoint, headers=entête, data=param)

    # S'il on vient d'acheter, on place un ordre limit
    if info["achat_vente"] == True:
        ordre_vente_seuil(info["symbol"])


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
def presence_position(symbol: str) -> dict or None:
    """
    Fonction qui renvoie les positions en cours sur une pair de crypto précis
    Ex paramètre :
    symbol : BTC3S-USDT

    Sortie de la fonction :
    {'id': '62d6e3303896050001788d36', 'symbol': 'BTC3L-USDT', 'opType': 'DEAL', 'type': 'limit', 'side': 'sell', 
    'price': '0.007', 'size': '6791.3015', 'funds': '0', 'dealFunds': '0', 'dealSize': '0', 'fee': '0', 
    'feeCurrency': 'USDT', 'stp': '', 'stop': '', 'stopTriggered': False, 'stopPrice': '0', 'timeInForce': 'GTC', 
    'postOnly': False, 'hidden': False, 'iceberg': False, 'visibleSize': '0', 'cancelAfter': 0, 'channel': 'IOS', 
    'clientOid': None, 'remark': None, 'tags': None, 'isActive': True, 'cancelExist': False, 'createdAt': 1658250032352, 
    'tradeType': 'TRADE'}
    """
    # On crée le point de terminaison
    endpoint = f"/api/v1/orders?status=active&symbol={symbol}"

    # Création de l'entête
    entête = headers("GET", endpoint)

    # On envoie la requête
    position = requests.get(api + endpoint, headers=entête)

    # Puis on récupère le résultat et on le transforme en dictionnaire (car reçu au format str)
    resultat = json.loads(position.content.decode("utf-8"))['data']['items']

    # S'il y a un ordre on renvoie les informations sur celui-ci
    if resultat == []:
        return None
    else:
        return resultat[0]


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
def suppression_ordre() -> None:
    """
    Fonction qui supprime un ordre selon qu'il soit un stoploss ou un simple ordre
    """
    id_ordre = lecture_fichier()

    endpoint = f"/api/v1/orders/{id_ordre}"

    # Création de l'entête
    entête = headers('DELETE', endpoint)

    # Puis on vient envoyer la requête pour supprimer l'ordre du serveur
    supression_position = requests.delete(
        api + endpoint, headers=entête)

    écriture_fichier()


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
def achat_vente(montant: int or float, symbol: str, achat_ou_vente: bool) -> None:
    """
    Fonction qui achète ou vente les cryptomonnaies
    Ex param :
    montant : 50
    symbol : "BTC3S-USDT
    achat_vente : True ou False
    """
    # On créer un dictionnaire avec toutes les informations nécessaires
    info = {"montant": montant,
            "symbol": symbol, "achat_vente": achat_ou_vente}

    # On prend la position sur le serveur
    prise_position(info)

    # On récupère le prix en temps réel de la crypto que l'on vient d'acheter
    prix = prix_temps_reel_kucoin("BTC-USDT")

    # Puis on vient envoyer un message sur le discord
    if achat_ou_vente == True:
        msg = f"Prise de position avec {montant} usdt au prix de {prix}$, il reste {montant_compte('USDT')} usdt, crypto : {symbol}"
        message_prise_position(msg, True)

    else:
        global argent
        argent = montant_compte('USDT')

        msg = f"Vente de position au prix de {prix}$, il reste {argent} usdt"
        message_prise_position(msg, False)


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
def ordre_vente_seuil(symbol: str) -> None:
    """
    Fonction qui place l'ordre limite de vente
    """

    prix = prix_temps_reel_kucoin(symbol)

    zero_apres_virgule = "0.0001"

    if symbol == "BTC3L-USDT":
        zero_apres_virgule = '0.000001'

    nv_prix = arrondi(str(prix * 1.0250), zero_apres_virgule)

    # Besoin d'un id pour l'achat des cryptos
    id_position = randint(0, 100_000_000)

    # Point de terminaison de la requête
    endpoint = "/api/v1/orders"

    montant = montant_compte(symbol.split("-")[0])

    # Définition de tous les paramètres nécessaires
    param = {"clientOid": id_position,
             "side": "sell",
             "symbol": symbol,
             "price": str(nv_prix),
             "size": str(montant)}

    param = json.dumps(param)

    # Création de l'entête
    entête = headers('POST', endpoint, param)

    # On prend la position sur le serveur
    prise_position = requests.post(api + endpoint, headers=entête, data=param)

    content = json.loads(prise_position.content.decode('utf-8'))

    if content["code"] != "200000":
        message_état_bot(f"{str(content)}")

    # Puis on vient écrire l'id de l'ordre dans un fichier pour faciliter la suppresion de celui-ci
    écriture_fichier(content["data"]["orderId"])


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
def stoploss_manuel(symbol: str, prix_stop: float) -> None:
    """
    Fonction qui fait office de stoploss mais de façon manuel
    """
    while True:
        prix = prix_temps_reel_kucoin("BTC-USDT")

        if symbol == "BTC3L-USDT":

            if prix <= prix_stop:

                montant = montant_compte(symbol.split("-")[0])

                achat_vente(montant, symbol, False)

                break

        elif symbol == "BTC3S-USDT":
            if prix >= prix_stop:

                montant = montant_compte(symbol.split("-")[0])

                achat_vente(montant, symbol, False)

                break

        sleep(5)

# Fonction qui tourne en continue


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
def update_id_ordre_limite() -> None:
    """
    Fonction qui maintien à jour l'id de l'ordre limite dans le fichier
    S'il l'ordre a été executé alors on vire l'id du fichier
    """
    while True:
        sl_3S = presence_position("BTC3S-USDT")
        sl_3L = presence_position("BTC3L-USDT")

        # S'il y a aucun stoploss, par sécurité on vide le fichier
        if sl_3L == None and sl_3S == None:
            écriture_fichier()

        # Sinon par sécurité, on remet l'id du stoploss dans le fichier
        elif sl_3L != None:
            écriture_fichier(sl_3L['id'])

        # De même pour ici
        elif sl_3S != None:
            écriture_fichier(sl_3S['id'])

        sleep(20)