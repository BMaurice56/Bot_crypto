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

stopPrice = 0.97
price = 0.9675

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
    Fonction qui prend en argument un décimal et renvoie ce décimal arrondi à 0,0001
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

    fichier = open("stoploss.txt", "r")

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

    fichier = open("stoploss.txt", "w")

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
        money = arrondi(float(argent[0]['available']) * 0.999)
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
    # Lorsque l'on vend, on vérifie s'il y a toujours le stoploss ou
    # si celui-ci a placé un ordre mais que cet ordre n'a pas été exécuté
    if info["achat_vente"] == False:
        presence_market = presence_position("market", info["symbol"])

        if presence_market == None:
            suppression_ordre("stoploss")

        else:
            id_market = presence_market['id']

            suppression_ordre("market", id_market)

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

    # On attend 1 seconde pour être sur que l'achat a bient été effectué
    sleep(1)

    # S'il on vient d'acheter, on place un stoploss
    if info["achat_vente"] == True:
        création_stoploss(info["symbol"], stopPrice, price)

    # Puis on renvoie l'id de l'ordre d'achat placé pour le message sur discord
    return json.loads(prise_position.content.decode('utf-8'))["data"]["orderId"]


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
def presence_position(type_ordre: str, symbol: str) -> dict or None:
    """
    Fonction qui renvoie les positions en cours sur une pair de crypto précis
    Ex paramètre :
    type_ordre : market ou stoploss
    symbol : BTC3S-USDT

    Sortie de la fonction :
    {'id': 'vs9o2om0ejjhbdd5000qjne9', 'symbol': 'BTC3S-USDT', 'userId': '62b59916f4913f0001954877', 
    'status': 'NEW', 'type': 'limit', 'side': 'sell', 'price': '3.44060000000000000000', 'size': '14.06590000000000000000',
    'funds': None, 'stp': None, 'timeInForce': 'GTC', 'cancelAfter': -1, 'postOnly': False, 'hidden': False, 
    'iceberg': False, 'visibleSize': None, 'channel': 'API', 'clientOid': '94598129', 'remark': None, 'tags': None, 
    'orderTime': 1656780007654000020, 'domainId': 'kucoin', 'tradeSource': 'USER', 'tradeType': 'TRADE', 
    'feeCurrency': 'USDT', 'takerFeeRate': '0.00100000000000000000', 'makerFeeRate': '0.00100000000000000000',
    'createdAt': 1656780007655, 'stop': 'loss', 'stopTriggerTime': None, 'stopPrice': '3.45800000000000000000'}

    {'id': '62d6e3303896050001788d36', 'symbol': 'BTC3L-USDT', 'opType': 'DEAL', 'type': 'limit', 'side': 'sell', 
    'price': '0.007', 'size': '6791.3015', 'funds': '0', 'dealFunds': '0', 'dealSize': '0', 'fee': '0', 
    'feeCurrency': 'USDT', 'stp': '', 'stop': '', 'stopTriggered': False, 'stopPrice': '0', 'timeInForce': 'GTC', 
    'postOnly': False, 'hidden': False, 'iceberg': False, 'visibleSize': '0', 'cancelAfter': 0, 'channel': 'IOS', 
    'clientOid': None, 'remark': None, 'tags': None, 'isActive': True, 'cancelExist': False, 'createdAt': 1658250032352, 
    'tradeType': 'TRADE'}

    {'id': 'vs9o0ommsug8gqo1000mufin', 'symbol': 'BTC3L-USDT', 'userId': '62b59916f4913f0001954877', 'status': 'NEW', 
    'type': 'limit', 'side': 'sell', 'price': '0.00550000000000000000', 'size': '6810.55620000000000000000', 'funds': None, 
    'stp': None, 'timeInForce': 'GTC', 'cancelAfter': 0, 'postOnly': False, 'hidden': False, 'iceberg': False, 
    'visibleSize': None, 'channel': 'IOS', 'clientOid': None, 'remark': None, 'tags': None, 'orderTime': 1658251168517790156, 
    'domainId': 'kucoin', 'tradeSource': 'USER', 'tradeType': 'TRADE', 'feeCurrency': 'USDT', 
    'takerFeeRate': '0.00100000000000000000', 'makerFeeRate': '0.00100000000000000000', 'createdAt': 1658251168518, 
    'stop': 'loss', 'stopTriggerTime': None, 'stopPrice': '0.00580000000000000000'}
    """
    # On crée le point de terminaison selon le type de marché
    if type_ordre == "market":
        endpoint = "/api/v1/orders?status=active"

    elif type_ordre == "stoploss":
        endpoint = "/api/v1/stop-order?status=active"

    # On lui rajoute le symbol voulu
    endpoint += f"&symbol={symbol}"

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
def information_ordre(id_ordre: str) -> dict:
    """
    Fonction qui renvoie les informations sur un ordre passé
    Ex param :
    id_ordre : vs9o2om08lvqav06000s2u7e
    Sortie de la fonction :
    {"id":"vs9o2om08lvqav06000s2u7e","symbol":"BTC3S-USDT","opType":"DEAL",
    "type":"limit","side":"sell","price":"3.4136","size":"14.4306","funds":null,"dealFunds":"0",
    "dealSize":"0","fee":"0","feeCurrency":"USDT","stp":null,"stop":"loss","stopTriggered":false,
    "stopPrice":"3.4309","timeInForce":"GTC","postOnly":false,"hidden":false,"iceberg":false,"visibleSize":null,
    "cancelAfter":-1,"channel":"API","clientOid":"30688036","remark":null,
    "tags":null,"isActive":false,"cancelExist":true,"createdAt":1656767871013,"tradeType":"TRADE"}
    """
    # On crée le point de terminaison
    endpoint = f"/api/v1/orders/{id_ordre}"

    # Création de l'entête
    entête = headers("GET", endpoint)

    # On envoie la requête au serveur
    info_ordre = requests.get(api + endpoint, headers=entête)

    # Puis on retourne les informations de l'ordre voulu
    return json.loads(info_ordre.content.decode('utf-8'))['data']


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
def remonter_stoploss(symbol: str, dodo: int, stopP: float, Pr: float) -> None:
    """
    Fonction qui remonte le stoploss s'il y a eu une augmentation par rapport au précédent stoploss
    Ex paramètre :
    symbol : BTC3S-USDT
    """
    # On execute 120 fois car 30 secondes * 120 = 60 minutes
    for i in range(120):
        stoploss = presence_position("stoploss", symbol)

        # S'il y a toujours le stoploss, on vérifie si celui-ci a les bons prix
        if stoploss != None:
            # On calcule ce que donnerait le prix du nouveau stoploss
            prix = prix_temps_reel_kucoin(symbol)

            sp = arrondi(stoploss["stopPrice"])

            nouveau_stopPrice = arrondi(prix * stopP)

            # S'il est supérieur à l'ancien prix, on enlève le stoploss et on en remet un nouveau
            if sp < nouveau_stopPrice:
                # On enlève le précédent ordre
                suppression_ordre("stoploss")

                # Puis on remet un nouveau stoploss
                création_stoploss(symbol, stopP, Pr)

        # Puis on attend 30 secondes avant de revérifier
        sleep(dodo)


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
def création_stoploss(symbol: str, stopP: float, Pr: float) -> None:
    """
    Fonction qui crée un stoploss
    Ex param :
    symbol : "BTC3L-USDT"
    """
    # Besoin d'un id pour l'ordre
    id_stoploss = randint(0, 100_000_000)

    # Point de terminaison de la requête
    endpoint = "/api/v1/stop-order"

    # On enregistre le symbol dans une autre variable car après on doit séparer la paire
    # Et garder que la crypto
    sb = symbol

    crypto = sb.split("-")[0]

    # On récupère le montant du compte pour savoir combien de la crypto on doit vendre
    money = montant_compte(crypto)

    # On récupère le prix en temps réel pour ensuite placer les prix du stoploss
    prix = prix_temps_reel_kucoin(symbol)

    # Création des paramètres pour la requête
    param = {"clientOid": id_stoploss,
             "side": "sell",
             "symbol": symbol,
             'stop': "loss",
             "stopPrice": str(arrondi(prix * stopP)),
             "price": str(arrondi(prix * Pr)),
             "size": str(arrondi(money))}

    param = json.dumps(param)

    # Création de l'entête
    entête = headers('POST', endpoint, param)

    # On envoie la requête au serveur
    prise_position = requests.post(
        api + endpoint, headers=entête, data=param)

    # Puis on vient écrire l'id du stoploss dans un fichier pour faciliter la remonter de celui-ci
    # quand le cour de la crypto remonte
    message_état_bot(
        f"{str(prise_position)}, {str(prise_position.content.decode('utf-8'))}, stopPrice : {stopP}, price : {Pr}")

    écriture_fichier(json.loads(
        prise_position.content.decode('utf-8'))["data"]["orderId"])


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
def suppression_ordre(type_ordre: str, id_ordre: Optional[str] = None) -> None:
    """
    Fonction qui supprime un ordre selon qu'il soit un stoploss ou un simple ordre
    Ex param :
    type_ordre : stoploss ou market ou stoploss_manuel
    id_ordre : None par défaut ou l'id de l'ordre en question à supprimer
    """
    # Si c'est un stoploss, l'id de l'ordre doit être dans le fichier
    # Et on l'efface de celui-ci
    if type_ordre == "stoploss":
        id_stls = lecture_fichier()

        endpoint = f"/api/v1/stop-order/{id_stls}"

        écriture_fichier()

    # Sinon si c'est un ordre market, on supprime l'ordre avec l'id fourni
    elif type_ordre == "market":
        endpoint = f"/api/v1/orders{id_ordre}"

    # Sinon si on veut supprimer un ordre stoploss manuellement, on fournit l'id et on le supprime
    elif type_ordre == "stoploss_manuel":
        endpoint = f"/api/v1/stop-order/{id_ordre}"

    # Création de l'entête
    entête = headers('DELETE', endpoint)

    # Puis on vient envoyer la requête pour supprimer l'ordre du serveur
    supression_position = requests.delete(
        api + endpoint, headers=entête)


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
    prix = prix_temps_reel_kucoin(symbol)

    # Puis on vient envoyer un message sur le discord
    if achat_ou_vente == False:
        global argent
        argent = montant_compte('USDT')

        msg = f"Vente de position au prix de {prix}$, il reste {argent} usdt"
        message_prise_position(msg, False)

    else:
        msg = f"Prise de position avec {montant} usdt au prix de {prix}$, il reste {montant_compte('USDT')} usdt"
        message_prise_position(msg, True)


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
def continuation_prediction(symbol: str, divergence: bool) -> None:
    """
    Fonction qui vérifie les stoploss lorsque que l'on achète pas et que l'on continue a attendre que ça monte ou descende
    Ex param :
    symbol : BTC3L-USDT
    divergence : True ou False
    """
    # On vérifie si il y a présence ou non d'ordre
    stoploss = presence_position("stoploss", symbol)
    market = presence_position("market", symbol)

    if divergence == True:
        global divergence_stoploss
        divergence_stoploss = False

        if stoploss != None:
            # On récupère l'ancien stopPrice et le price
            ancien_prix_stoploss = float(stoploss['stopPrice'])
            ancien_prix = float(stoploss['price'])

            # On calcule le nouveau stopPrice et price avec le stopPrice et price par défaut hors divergence
            # Le prix qu'on aurait eu si on avait utiliser le stopPrice et price par défaut (0.97 et 0.9675)
            nouveau_stopPrice = 97 * ancien_prix_stoploss / 99
            nouveau_prix = 96.75 * ancien_prix / 98.75

            # On calcule en pourcentage le nouveau stopPrice et price selon le prix en cour de la crypto
            # Puis on divise par 100 pour l'avoir en décimale
            nv_stoprice_pourcentage = nouveau_stopPrice * \
                100 / prix_temps_reel_kucoin(symbol) / 100
            nv_prix_pourcentage = nouveau_prix * 100 / \
                prix_temps_reel_kucoin(symbol) / 100

            # Si le prix a augmenté et donc le stopPrice calculé est plus faible
            # Alors on place un stoploss directement avec les bonnes valeurs
            if nv_stoprice_pourcentage <= stopPrice:
                suppression_ordre("stoploss")
                création_stoploss(symbol, stopPrice, price)
            # Sinon on place le stoploss avec les valeurs calculé pour compenser la baisse du prix
            # Mais pour garder le même prix final qu'on aurait eu avec le stopPrice et price de base
            else:
                suppression_ordre("stoploss")
                création_stoploss(
                    symbol, nv_stoprice_pourcentage, nv_prix_pourcentage)

        else:
            # Comme on a que le price, on le récupère et calcul le stopPrice à partir de celui-ci
            ancien_prix = float(market['price'])

            ancien_prix_stoploss = 99 * ancien_prix / 98.75

            # On calcule le nouveau stopPrice et price avec le stopPrice et price par défaut hors divergence
            # Le prix qu'on aurait eu si on avait utiliser le stopPrice et price par défaut (0.97 et 0.9675)
            nouveau_stopPrice = 97 * ancien_prix_stoploss / 99
            nouveau_prix = 96.75 * ancien_prix / 98.75

            # On calcule en pourcentage le nouveau stopPrice et price selon le prix en cour de la crypto
            # Puis on divise par 100 pour l'avoir en décimale
            nv_stoprice_pourcentage = nouveau_stopPrice * \
                100 / prix_temps_reel_kucoin(symbol) / 100
            nv_prix_pourcentage = nouveau_prix * 100 / \
                prix_temps_reel_kucoin(symbol) / 100

            # Si le prix a augmenté et donc le stopPrice calculé est plus faible
            # Alors on place un stoploss directement avec les bonnes valeurs
            if nv_stoprice_pourcentage <= stopPrice:
                suppression_ordre("market", market['id'])
                création_stoploss(symbol, stopPrice, price)
            # Sinon on place le stoploss avec les valeurs calculé pour compenser la baisse du prix
            # Mais pour garder le même prix final qu'on aurait eu avec le stopPrice et price de base
            else:
                création_stoploss(
                    symbol, nv_stoprice_pourcentage, nv_prix_pourcentage)

    else:
        # Sinon s'il y a qu'un ordre limite market, on check si lorsqu'on place un stoploss
        # si le prix du stoploss est supérieur ou non à l'ordre limite
        if market != None:
            prix_position = float(market['price'])

            nouveau_prix = arrondi(
                prix_temps_reel_kucoin(symbol) * price)

            if prix_position < nouveau_prix:
                suppression_ordre("market", market['id'])
                création_stoploss(symbol, stopPrice, price)


# @connexion
@retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
def update_id_stoploss() -> None:
    """
    Fonction qui maintien à jour l'id du stoploss dans le fichier
    S'il le stoploss a été executé alors on vire l'id du fichier
    """
    while True:
        st_3S = presence_position("stoploss", "BTC3S-USDT")
        st_3L = presence_position("stoploss", "BTC3L-USDT")

        # S'il y a aucun stoploss, par sécurité on vide le fichier
        if st_3L == None and st_3S == None:
            écriture_fichier()

        # Sinon par sécurité, on remet l'id du stoploss dans le fichier
        elif st_3L != None and st_3S == None:
            écriture_fichier(st_3L['id'])

        # De même pour ici
        elif st_3L == None and st_3S != None:
            écriture_fichier(st_3S['id'])

        # S'il y a deux stoploss, on regarde la présence de crypto
        else:
            btcup = montant_compte("BTC3L")
            btcdown = montant_compte("BTC3S")

            # S'il y a une crypto, on supprime l'ordre sur l'autre crypto
            if btcup > 30:
                suppression_ordre("stoploss_manuel", st_3S['id'])
                écriture_fichier(st_3L['id'])

            elif btcdown > 2:
                suppression_ordre("stoploss_manuel", st_3L['id'])
                écriture_fichier(st_3S['id'])

            # Sinon on supprime les deux
            else:
                suppression_ordre("stoploss_manuel", st_3S['id'])
                suppression_ordre("stoploss_manuel", st_3L['id'])
                écriture_fichier()

        sleep(30)
