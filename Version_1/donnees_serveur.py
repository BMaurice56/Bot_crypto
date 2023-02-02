from tenacity import retry, retry_if_exception_type, stop_after_attempt
from shared_memory_dict import SharedMemoryDict
from multiprocessing import Process, Manager
from decimal import Decimal, ROUND_DOWN
from indices_techniques import moyenne
from time import sleep, perf_counter
from subprocess import Popen, PIPE
from binance.client import Client
from zoneinfo import ZoneInfo
from datetime import datetime
from message_discord import *
from functools import wraps
from typing import Optional
from random import randint
import traceback
import requests
import hashlib
import base64
import pandas
import locale
import time
import hmac
import json
import ccxt

# Définition de la zone pour l'horodatage car la date était en anglais avec le module datetime
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

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


class Binance:
    """
    Classe qui permet d'interagir avec les données des serveurs de binance
    """

    def __init__(self) -> None:
        """
        Initialise un objet binance
        """

        self.api_key = "eUFWHXCMrNKoP4LURDCOW0faPCyzm2teZLU3eBYUM2AoNM3wvr8F4d3IjeJuDipd"
        self.api_secret = "AZM89mot3fJNk2ODEGomItIkWyP6pTazXj6W2SHfSRoRL3CTyIUQvcmXTIi6edRy"

        self.client = Client(self.api_key, self.api_secret)

    @retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
    def donnée(self, symbol: str, début: str, fin: str) -> pandas.DataFrame:
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

        # Récupération des données de la crypto
        if fin[0] == "0":
            donnée_historique = self.client.get_historical_klines(
                symbol, self.client.KLINE_INTERVAL_1HOUR, début)

        else:
            donnée_historique = self.client.get_historical_klines(
                symbol, self.client.KLINE_INTERVAL_1HOUR, début, fin)

        # On enlève les données pas nécessaire
        for i in range(len(donnée_historique)):
            donnée_historique[i] = donnée_historique[i][:7]

        # Création de la df et nommage des colonnes
        data = pandas.DataFrame(donnée_historique)

        data.columns = ['timestart', 'open', 'high', 'low',
                        'close', 'volume', 'timeend']

        return data

    @retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
    def prix_temps_reel(self, symbol: str) -> float:
        """
        Fonction qui récupère le prix en temps réel d'un symbol voulu
        Ex param :
        symbol : BTCEUR
        """

        return float(self.client.get_ticker(symbol=symbol)['lastPrice'])

    @retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
    def all_data(self, symbol: str) -> dict:
        """
        Fonction qui prend en argument un symbol
        Et renvoie toutes les données de tous les jetons (ceux avec effet de levier aussi) sous forme d'un seul dictionnaire
        Ex param :
        symbol : BTC
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


class Kucoin:
    """
    Classe qui permet d'interagir avec les données des serveurs de kucoin
    """

    def __init__(self) -> None:
        """
        Initialise un objet kucoin pour interagir avec leurs serveurs
        """

        self.api = "https://api.kucoin.com"

        self.kucoin_api_key = "63cffd08f8686d000140987a"
        self.kucoin_api_secret = "d125b0df-e2eb-4532-8ed1-049d01dc18b8"
        self.kucoin_phrase_securite = "c5%Pnp8o$FE%^CEM7jwFp9PaTtW4kq"

        self.pourcentage_gain = 0.02

        self.minimum_crypto_up = 5000
        self.minimum_crypto_down = 4

        # Message discord
        self.msg_discord = Message_discord()

        # Diction partagé entre programme
        self.dico_partage = SharedMemoryDict(name="dico", size=1024)

    def arrondi(self, valeur: float or str, zero_apres_virgule: Optional[float] = None) -> float:
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

    def headers(self, methode: str, endpoint: str, param: Optional[str] = None) -> dict:
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
            hmac.new(self.kucoin_api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())

        passphrase = base64.b64encode(hmac.new(self.kucoin_api_secret.encode(
            'utf-8'), self.kucoin_phrase_securite.encode('utf-8'), hashlib.sha256).digest())

        headers = {
            "KC-API-SIGN": signature,
            "KC-API-TIMESTAMP": now,
            "KC-API-KEY": self.kucoin_api_key,
            "KC-API-PASSPHRASE": passphrase,
            "KC-API-KEY-VERSION": "2",
            "Content-Type": "application/json"
        }

        return headers

    def comparaisons(self, valeur_1: float, valeur_2: float, sens_comparaison: bool) -> bool:
        """
        Fonction qui compare deux décimaux entre eux
        Sens_comparaison définit le sens dans lequel les deux valeurs doivent être comparées
        Si True : valeur_1 >= valeur_2
        Sinon : valeur_1 <= valeur_2
        """
        if sens_comparaison == True:
            return valeur_1 >= valeur_2

        return valeur_1 <= valeur_2

    def lecture_fichier(self) -> str or None:
        """
        Fonction qui lit ce qu'il y a dans le fichier 
        Et renvoie le contenu ou None s'il y a rien
        """
        # On utilise try dans le cas où le fichier n'existe pas
        try:
            fichier = open("ordre_limit.txt", "r")

            elt = fichier.read()

            fichier.close()

            if elt == "":
                return None
            return elt
        except:
            return None

    def écriture_fichier(self, str_to_write: Optional[str] = None) -> None:
        """
        Fonction qui écrit ou écrase le fichier
        Ex param :
        str_to_write : id de l'ordre
        """

        fichier = open("ordre_limit.txt", "w")

        if str_to_write != None:
            fichier.write(str_to_write)

        fichier.close()

    def écriture_requete(self, requete, emplacement) -> None:
        """
        Fonction qui écrit toutes les requêtes dans un fichier (leur résultat)
        Ainsi que la date
        """
        date = datetime.now(tz=ZoneInfo("Europe/Paris")
                            ).strftime("%A %d %B %Y %H:%M:%S")

        if emplacement == "requete":
            pwd = "fichier_log/log_requete.txt"

        elif emplacement == "presence_position":
            pwd = "fichier_log/log_update_id_position.txt"

        elif emplacement == "stoploss":
            pwd = "fichier_log/log_stoploss_manuel.txt"

        fichier = open(pwd, "a")

        fichier.write(f"{date} ; {requete} \n")

        fichier.close()

    @retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
    def montant_compte(self, symbol: str, type_requete: Optional[str] = None) -> float:
        """
        Fonction qui renvoie le montant que possède le compte selon le ou les symbols voulus
        Ex paramètre :
        symbol : USDT ou BTC3L
        """
        # On défini la terminaison de la requête
        endpoint = f"/api/v1/accounts?currency={symbol}&type=trade"

        # On crée l'entête
        entête = self.headers('GET', endpoint)

        # Puis on execute la requête
        requete = requests.get(self.api + endpoint,
                               headers=entête).content.decode("utf-8")

        # On écrit le résultat de la requete dans le fichier
        if type_requete == None:
            self.écriture_requete(requete, "requete")
        else:
            self.écriture_requete(requete, "stoploss")

        # On la retransforme au format dict car reçu au format str
        # Puis on ne garde que les données
        argent = json.loads(requete)["data"]

        # S'il le compte possède le symbol voulu, on renvoit le nombre
        # Avec seulement 99,9% de sa quantité initiale car pour l'achat des cryptos
        # -> aucun problème avec le nb de chiffres après la virgule et les frais de la platforme
        if argent != []:
            money = self.arrondi(float(argent[0]['balance']) * 0.999)
            return money
        else:
            return 0

    @retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
    def prix_temps_reel_kucoin(self, symbol: str, type_requete: Optional[str] = None) -> float:
        """
        Fonction qui renvoie le prix de la crypto en temps réel
        Ex paramètre : 
        symbol : BTC3S-USDT
        """
        # On défini la terminaison de la requête
        endpoint = f"/api/v1/market/orderbook/level1?symbol={symbol}"

        # On crée l'entête
        entête = self.headers('GET', endpoint)

        # Puis on execute la requête
        requete = requests.get(self.api + endpoint,
                               headers=entête).content.decode('utf-8')

        # On écrit le résultat de la requete dans le fichier
        if type_requete == None:
            self.écriture_requete(requete, "requete")
        else:
            self.écriture_requete(requete, "stoploss")

        # On la retransforme en dictionnaire (car reçu au format str)
        # Et on garde que le prix voulu
        argent = float(json.loads(requete)["data"]["price"])

        return argent

    @retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
    def prise_position(self, info: dict) -> None:
        """
        Fonction qui prend une position soit d'achat soit de vente et place un stoploss
        Quand on achète on place automatiquement un stoploss
        Et quand on vend, on retire le stoploss et/ou l'ordre s'il n'a pas été exécuté
        Renvoie l'id de la position prise
        Ex paramètres :
        info : {
        "montant" : "20",
        "symbol" : "BTC3S-USDT",
        "achat_vente" : "True" (pour achat)
        }
        Sortie de la fonction :
        "vs9o2om08lvqav06000s2u7e"
        """
        # Lorsque l'on vend, on enlève l'ordre limit car soit il a été exécuté, soit il est toujours là
        if info["achat_vente"] == False:
            self.suppression_ordre()
            sleep(1)

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
        entête = self.headers('POST', endpoint, param)

        # On prend la position sur le serveur
        requete = requests.post(
            self.api + endpoint, headers=entête, data=param).content.decode('utf-8')

        # On écrit le résultat de la requete dans le fichier
        self.écriture_requete(requete, "requete")

        # S'il on vient d'acheter, on place un ordre limit
        if info["achat_vente"] == True:
            self.ordre_vente_seuil(info["symbol"])

    @retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
    def presence_position(self, symbol: str) -> dict or None:
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
        entête = self.headers("GET", endpoint)

        # On envoie la requête
        position = requests.get(self.api + endpoint,
                                headers=entête).content.decode("utf-8")

        # On écrit le résultat de la requete dans le fichier
        self.écriture_requete(position, "presence_position")

        # Puis on récupère le résultat et on le transforme en dictionnaire (car reçu au format str)
        resultat = json.loads(position)['data']['items']

        # S'il y a un ordre on renvoie les informations sur celui-ci
        if resultat == []:
            return None
        else:
            return resultat[0]

    @retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
    def suppression_ordre(self) -> None:
        """
        Fonction qui supprime un ordre selon qu'il soit un stoploss ou un simple ordre
        """
        # On récupère l'id de l'ordre
        id_ordre = self.lecture_fichier()

        # Si le fichier n'est pas vide, alors on peut supprimer l'ordre
        if id_ordre != None:

            # On créer le point de terminaison de l'url
            endpoint = f"/api/v1/orders/{id_ordre}"

            # Création de l'entête
            entête = self.headers('DELETE', endpoint)

            # Puis on vient envoyer la requête pour supprimer l'ordre du serveur
            requete = requests.delete(
                self.api + endpoint, headers=entête).content.decode('utf-8')

            # On écrit le résultat de la requete dans le fichier
            self.écriture_requete(requete, "requete")

        # Enfin on supprime l'id du fichier
        # Créer le fichier s'il n'existe pas
        self.écriture_fichier()

    @retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
    def achat_vente(self, montant: int or float, symbol: str, achat_ou_vente: bool) -> None:
        """
        Fonction qui achète ou vente les cryptomonnaies
        Ex param :
        Achat : montant : 200 (USDT), symbol : "BTC3L-USDT, achat_vente : True
        Vente : montant : 48 (BTC3L-USDT), "BTC3L-USDT", achat_vente : False
        """
        # On créer un dictionnaire avec toutes les informations nécessaires
        info = {"montant": montant,
                "symbol": symbol, "achat_vente": achat_ou_vente}

        # On prend la position sur le serveur
        self.prise_position(info)

        # On récupère le prix en temps réel de la crypto que l'on vient d'acheter
        prix = self.prix_temps_reel_kucoin("BTC-USDT")

        # Puis on vient envoyer un message sur le discord
        if achat_ou_vente == True:
            msg = f"Prise de position avec {montant} usdt au prix de {prix}$, il reste {self.montant_compte('USDT')} usdt, crypto : {symbol}"
            self.msg_discord.message_prise_position(msg, True)

        else:
            argent = self.montant_compte('USDT')

            msg = f"Vente de position au prix de {prix}$, il reste {argent} usdt"
            self.msg_discord.message_prise_position(msg, False)

    @retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
    def ordre_vente_seuil(self, symbol: str) -> None:
        """
        Fonction qui place l'ordre limite de vente
        """
        # Récupération des prix de marchés
        prix = self.prix_temps_reel_kucoin(symbol)
        prix_marche = self.prix_temps_reel_kucoin(
            f"{symbol.split('3')[0]}-USDT")

        zero_apres_virgule = "0.0001"

        # Si crypto montante, elle autorise un nombre chiffre après virgule plus importante
        if "3L" in symbol:
            zero_apres_virgule = '0.000001'

        # Calcul du prix de vente de l'ordre
        nv_prix = self.arrondi(
            str(prix * (1 + self.pourcentage_gain)), zero_apres_virgule)

        # On stock dans le dictionaire partagé le prix estimer de vente sur le marché de base
        if "3L" in symbol:
            self.dico_partage["prix_estimer"] = prix_marche * \
                (1 + (self.pourcentage_gain/3))
        else:
            self.dico_partage["prix_estimer"] = prix_marche * \
                (1 - (self.pourcentage_gain/3))

        # Besoin d'un id pour l'achat des cryptos
        id_position = randint(0, 100_000_000)

        # Point de terminaison de la requête
        endpoint = "/api/v1/orders"

        montant = self.montant_compte(symbol.split("-")[0])

        # Définition de tous les paramètres nécessaires
        param = {"clientOid": id_position,
                 "side": "sell",
                 "symbol": symbol,
                 "price": str(nv_prix),
                 "size": str(montant)}

        param = json.dumps(param)

        # Création de l'entête
        entête = self.headers('POST', endpoint, param)

        # On prend la position sur le serveur
        prise_position = requests.post(
            self.api + endpoint, headers=entête, data=param).content.decode('utf-8')

        # On écrit le résultat de la requete dans le fichier
        self.écriture_requete(prise_position, "requete")

        # On retransforme en dict car reçu au format str
        content = json.loads(prise_position)

        if content["code"] != "200000":
            self.msg_discord.message_erreur(
                f"{str(content)}", "Echec placement de l'ordre limite")

        # Puis on vient écrire l'id de l'ordre dans un fichier pour faciliter la suppresion de celui-ci
        self.écriture_fichier(content["data"]["orderId"])

    @retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
    def stoploss_manuel(self, symbol: str, prix_stop: float) -> None:
        """
        Fonction qui fait office de stoploss mais de façon manuel
        Basé sur le prix du marché normal, pas celui des jetons à effet de levier
        """
        try:
            # Par défaut, on est sur le marché montant
            type_marche = True
            minimum = self.minimum_crypto_up

            # On garde que le nom de la crypto
            symbol_simple = symbol.split("-")[0]

            # Si on est sur le marché descendant, alors on change les paramètres
            if "3S" in symbol:
                type_marche = False
                minimum = self.minimum_crypto_down

            while True:
                # On vérifie s'il y a toujours une crypto, s'il elle a été vendu on peut arrêter la fonction
                crypto = self.montant_compte(symbol_simple, "stoploss")

                if crypto < minimum:
                    break

                # On récupère le prix du marché
                prix = self.prix_temps_reel_kucoin("BTC-USDT", "stoploss")

                # Si la crypto dépasse le stoploss fixé, alors on vend
                if self.comparaisons(prix, prix_stop, type_marche) == False:

                    self.achat_vente(crypto, symbol, False)

                    break

                sleep(5)
        except:
            # On récupère l'erreur
            erreur = traceback.format_exc()

            # Puis on l'envoi sur le canal discord
            self.msg_discord.message_erreur(
                erreur, "Erreur survenu dans la fonction stoploss_manuel, aucune interruption du programme, fonction relancée")

            # Et enfin on relance la fonction
            self.stoploss_manuel(symbol, prix_stop)
    # Fonction qui tourne en continue au lancement du programme

    @retry(retry=retry_if_exception_type(ccxt.NetworkError), stop=stop_after_attempt(3))
    def update_id_ordre_limite(self) -> None:
        """
        Fonction qui maintien à jour l'id de l'ordre limite dans le fichier
        S'il l'ordre a été executé alors on enlève l'id du fichier
        """
        try:
            while True:
                sl_3S = self.presence_position("BTC3S-USDT")
                sl_3L = self.presence_position("BTC3L-USDT")

                # S'il y a aucun stoploss, par sécurité on vide le fichier
                if sl_3L == None and sl_3S == None:
                    self.écriture_fichier()

                # Sinon par sécurité, on remet l'id du stoploss dans le fichier
                elif sl_3L != None:
                    self.écriture_fichier(sl_3L['id'])

                # De même pour ici
                elif sl_3S != None:
                    self.écriture_fichier(sl_3S['id'])

                sleep(20)
        except:
            # On récupère l'erreur
            erreur = traceback.format_exc()

            # Puis on l'envoi sur le canal discord
            self.msg_discord.message_erreur(
                erreur, "Erreur survenu dans la fonction update_id_ordre_limite, aucune interruption du programme, fonction relancée")

            # Et enfin on relance la fonction
            self.update_id_ordre_limite()
