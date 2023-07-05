from tenacity import retry, retry_if_exception_type, stop_after_attempt
from shared_memory_dict import SharedMemoryDict
from multiprocessing import Process, Manager
from decimal import Decimal, ROUND_DOWN
from threading import Thread, Event
from binance.client import Client
from zoneinfo import ZoneInfo
from datetime import datetime
from message_discord import *
from time import time, sleep
from random import randint
import requests
import hashlib
import base64
import pandas
import locale
import hmac
import json
import os

# Définition de la zone pour l'horodatage, car la date était en anglais avec le module datetime
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')


# BINANCE
# Fonctions qui récupèrent les données du serveur


class Binance:
    """
    Classe Binance qui permet l'interaction avec les serveurs de binance
    """

    def __init__(self, symbol) -> None:
        """
        Initialise un objet binance

        Ex param :
        symbol : "BTC"
        """

        self.api_key = "eUFWHXCMrNKoP4LURDCOW0faPCyzm2teZLU3eBYUM2AoNM3wvr8F4d3IjeJuDipd"
        self.api_secret = "AZM89mot3fJNk2ODEGomItIkWyP6pTazXj6W2SHfSRoRL3CTyIUQvcmXTIi6edRy"

        self.client = Client(self.api_key, self.api_secret)

        self.interval = self.client.KLINE_INTERVAL_1DAY

        self.symbol = symbol
        self.devise = "USDT"

    def data(self, start: str, end: str) -> pandas.DataFrame:
        """
        Prend en argument un symbol de type "BTCUSDT" ou encore "ETHUSDT" ...
        Renvoie les données sous forme d'une dataframe pandas

        Ex params :
        début : "40 day ago UTC"
        fin : "0 day ago UTC" ...
        """

        symbol = self.symbol + self.devise

        # Récupération des données de la crypto
        if end[0] == "0":
            historical_data = self.client.get_historical_klines(
                symbol, self.interval, start)

        else:
            historical_data = self.client.get_historical_klines(
                symbol, self.interval, start, end)

        # On enlève les données pas nécessaires
        for i in range(len(historical_data)):
            historical_data[i] = historical_data[i][:7]

        # Création de la df et nommage des colonnes
        data = pandas.DataFrame(historical_data)

        data.columns = ['timestart', 'open', 'high', 'low',
                        'close', 'volume', 'timeend']

        return data

    def all_data(self) -> dict:
        """
        Prend en argument un symbol
        Renvoie un dictionnaire avec toutes les données (+ ceux avec effet de levier)

        Ex param :
        symbol : "BTC"
        """
        # Création du dictionnaire que recevra toutes les dataframes avec les données
        manager = Manager()
        dico = manager.dict()

        @retry(retry=retry_if_exception_type((requests.exceptions.SSLError, requests.exceptions.ConnectionError)),
               stop=stop_after_attempt(3))
        def request(sl: str, limit: str, dictionary: dict, position_list: int):
            """
            Récupère les données d'une crypto de façon parallèle

            Ex params :
            sl : "BTCUSDT"
            limit : 40
            dictionary : dictionnaire qui gère le stockage multiprocess
            position_liste : Emplacement dans le dictionnaire
            """
            api = """https://api.binance.com/api/v3/klines"""

            param = {'symbol': sl,
                     'interval': self.interval,
                     'limit': limit}

            donnee = requests.get(api, params=param)

            data = donnee.json()

            for i in range(len(data)):
                data[i] = data[i][:7]

            data = pandas.DataFrame(data)

            data.columns = ['timestart', 'open', 'high', 'low',
                            'close', 'volume', 'timeend']

            # On enregistre les données qui ont 40 pour longueur

            dictionary[position_list] = data

            # Puis, on vient enregistrer les données qui ont 15 pour longueur
            # On renomme les lignes pour que ça commence à partir de zéro

            data_15 = data[25:].rename(index=lambda x: x - 25)

            # Les données avec 15 de longueur, on rajoute 3 à la clé pour garder l'ordre par rapport aux trois cryptos
            # BTC 40
            # BTCUP 40
            # BTCDOWN 40
            # BTC 15
            # BTCUP 15
            # BTCDOWN 15

            dictionary[position_list + 3] = data_15

            return dictionary

        p = Process(target=request, args=(f"{self.symbol}{self.devise}", 40, dico, 0))
        p2 = Process(target=request, args=(f"{self.symbol}UP{self.devise}", 40, dico, 1))
        p3 = Process(target=request, args=(f"{self.symbol}DOWN{self.devise}", 40, dico, 2))

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

    def __init__(self, crypto: str, thread: Optional[bool] = None) -> None:
        """
        Initialise un objet kucoin pour interagir avec leurs serveurs

        Ex params :
        crypto : "BTC", "BNB" ...
        thread (optionnel) : False pour ne pas activer les fonctions continues
        """

        self.api = "https://api.kucoin.com"

        self.kucoin_api_key = "63cffd08f8686d000140987a"
        self.kucoin_api_secret = "d125b0df-e2eb-4532-8ed1-049d01dc18b8"
        self.kucoin_security_sentence = "c5%Pnp8o$FE%^CEM7jwFp9PaTtW4kq"

        self.pourcentage_gain = 0.0175
        self.previous_gain = 0.0175

        # symbol des crypto
        self.symbol_base = crypto
        self.symbol = f"{crypto}-USDT"
        self.symbol_up = f"{crypto}3L-USDT"
        self.symbol_down = f"{crypto}3S-USDT"

        self.symbol_up_simple = f"{crypto}3L"
        self.symbol_down_simple = f"{crypto}3S"
        self.devise = "USDT"

        # Variable vente manuelle dictionnaire partagé
        self.vente_manuelle = f"vente_manuelle_{self.symbol_base}"

        # Donne le symbol simple
        self.dico_symbol_simple = {self.symbol_up: self.symbol_up_simple,
                                   self.symbol_down: self.symbol_down_simple}

        # Dictionnaire minimum des cryptos
        self.dictionnaire_minimum_up = {
            "ADA": 5, "BNB": 10, "BTC": 1500, "ETH": 2000, "XRP": 3000}
        self.dictionnaire_minimum_down = {
            "ADA": 50, "BNB": 5, "BTC": 5, "ETH": 10000, "XRP": 2}

        # Prix des cryptos de kucoin -> l'inverse de binance
        if self.symbol_base != "Discord":
            self.minimum_crypto_up = self.dictionnaire_minimum_up[self.symbol_base]
            self.minimum_crypto_down = self.dictionnaire_minimum_down[self.symbol_base]

        # On récupère le priceIncrement de chaque crypto
        with open("Other_files/priceIncrement.txt", "r") as f:
            self.dico_priceIncrement = json.loads(f.read())

        # Around price
        self.zero_after_coma = '0.0001'

        # Crypto supportées et leurs nombres
        with open("Other_files/supported_crypto.txt", "r") as f:
            self.crypto_supported = f.read().split(";")
            self.nb_crypto_supported = len(self.crypto_supported)

        # Message discord
        self.msg_discord = Message_discord()

        # Dictionnaire partagé entre programme
        self.dico_partage = SharedMemoryDict(name="dico", size=1024)

        # Permet de savoir si le bot a fini de démarrer (démarrage multiple)
        self.dico_partage[f"{self.symbol_base}_started"] = True

        # Dossier fichiers logs
        self.dir_log = "log_files"

        # Chemin des fichiers logs
        self.path_log = f"/home/Bot_crypto/{self.dir_log}"

        # Si on crée un objet Kucoin en dehors de discord → bot de trading
        # Permet de garder l'id à jour dans le fichier et analyser les fichiers logs
        if thread is None:
            th = Thread(target=self.update_id_ordre_limite)
            th.start()

            th2 = Thread(target=self.analyse_fichier)
            th2.start()

    @staticmethod
    def arrondi(valeur: float or str, zero_apres_virgule: str) -> float:
        """
        Prend en argument un décimal 
        Renvoie un décimal arrondi

        Ex params :
        valeur : 56.36 ou "56.36"
        """
        # On transforme la valeur reçue en objet décimal
        val = Decimal(str(valeur))

        # Puis, on arrondit vers le bas le nombre que l'on renvoie sous forme d'un float
        return float(val.quantize(Decimal(str(zero_apres_virgule)), ROUND_DOWN))

    def headers(self, methode: str, endpoint: str, param: Optional[str] = None) -> dict:
        """
        Créer l'entête de la requête http

        Ex params :
        methode : 'GET'
        endpoint : 'api/v1/orders'
        param : none ou dict sous forme json.dumps() -> str
        """
        now = str(int(time() * 1000))

        str_to_sign = now + methode + endpoint

        if param is not None:
            str_to_sign += param

        signature = base64.b64encode(
            hmac.new(self.kucoin_api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())

        passphrase = base64.b64encode(hmac.new(self.kucoin_api_secret.encode(
            'utf-8'), self.kucoin_security_sentence.encode('utf-8'), hashlib.sha256).digest())

        headers = {
            "KC-API-SIGN": signature,
            "KC-API-TIMESTAMP": now,
            "KC-API-KEY": self.kucoin_api_key,
            "KC-API-PASSPHRASE": passphrase,
            "KC-API-KEY-VERSION": "2",
            "Content-Type": "application/json"
        }

        return headers

    @staticmethod
    def comparaisons(valeur_1: float, valeur_2: float, sens_comparaison: bool) -> bool:
        """
        Compare deux décimaux
        Sens_comparaison définit le sens dans lequel les deux valeurs doivent être comparées
        Si True : valeur_1 >= valeur_2
        Sinon : valeur_1 <= valeur_2
        """
        if sens_comparaison is True:
            return valeur_1 >= valeur_2

        return valeur_1 <= valeur_2

    def lecture_fichier_ordre_limit(self) -> str or None:
        """
        Lit le contenu du fichier ordre_limit
        Renvoie le contenu ou None
        """
        # On utilise try dans le cas où le fichier n'existe pas
        try:
            with open(f"order_limit_{self.symbol_base}.txt", "r") as f:
                elt = f.read()

                if elt == "":
                    return None

                return elt
        except FileNotFoundError:
            return None

    def write_file_limit_order(self, str_to_write: Optional[str] = None) -> None:
        """
        Écrit ou écrase le fichier

        Ex param :
        str_to_write (optionnel) : id de l'ordre
        """
        with open(f"order_limit_{self.symbol_base}.txt", "w") as f:
            if str_to_write is not None:
                f.write(str_to_write)

    def write_request(self, request: str, emplacement: str) -> None:
        """
        Écrit toutes les requêtes dans un fichier (résultat)
        Ainsi que la date

        Ex params :
        request : données de la requête
        emplacement : "requete", "presence_position", "stoploss"
        """
        date = datetime.now(tz=ZoneInfo("Europe/Paris")
                            ).strftime("%A %d %B %Y %H:%M:%S")

        fichier_log = {
            "requete": "request",
            "presence_position": "update_id_position",
            "stoploss": "stop_loss_manuel"
        }

        pwd = f"{self.dir_log}/log_{fichier_log[emplacement]}_{self.symbol_base}.txt"

        with open(pwd, "a") as f:
            f.write(f"{date};{request}\n")

    def analyse_fichier(self, stop: Optional[bool] = None) -> None:
        """
        Analyse les fichiers log
        Écrit toutes les erreurs dans un fichier
        """
        fichier_en_cours = ""
        try:
            # Les noms des trois fichiers log de requêtes
            nom = [f"log_request_{self.symbol_base}.txt", f"log_stop_loss_manuel_{self.symbol_base}.txt",
                   f"log_update_id_position_{self.symbol_base}.txt"]

            while True:
                for elt in nom:
                    fichier_en_cours = elt
                    if os.path.exists(f"{self.dir_log}/{elt}"):
                        with open(f"{self.dir_log}/{elt}", "r") as f:
                            # On vient lire le contenu du fichier
                            fichier_content = f.read()

                            # S'il y a bien une requête dans le fichier, alors on peut l'analyser
                            if len(fichier_content) > 25:
                                # On sépare chaque ligne entre elles (-1, car retour a la ligne à la fin)
                                contenue = fichier_content[1:-1].split("\n")

                                # On ne garde que la requête sans la date
                                requete = [elt.split(";")[1]
                                           for elt in contenue]

                                list_date = [elt.split(";")[0]
                                             for elt in contenue]

                                requete_trie = []
                                result = []

                                date_trie = []
                                result_date = []

                                # Si problème de longueur, on ne garde pas la requête
                                for j in range(len(requete)):
                                    if len(requete[j]) > 10:
                                        requete_trie.append(
                                            json.loads(requete[j]))
                                        date_trie.append(list_date[j])

                                # Enfin, on parcourt toutes les requêtes → vérifie s'il y en a une qui n'a pas abouti
                                # Ou qu'il y a un quelconque problème
                                for k in range(len(requete_trie)):
                                    if requete_trie[k]['code'] != '200000':
                                        result.append(requete_trie[k])
                                        result_date.append(date_trie[k])

                                    elif requete_trie[k]['data'] is None:
                                        result.append(requete_trie[k])
                                        result_date.append(date_trie[k])

                                if len(result) > 0:
                                    date = datetime.now(tz=ZoneInfo("Europe/Paris")
                                                        ).strftime("%A %d %B %Y %H:%M:%S")

                                    final_result = []

                                    for i in range(len(result)):
                                        final_result.append(({result_date[i]}, {result[i]}))

                                    with open(f"{self.dir_log}/log_recap.txt", "a") as file:
                                        file.write(
                                            f"Bot : {self.symbol_base}, analyse du {date} : {final_result} \n")

                # Puis, on vient vider les fichiers (ou les créer)
                os.system(
                    f'echo > {self.path_log}/log_request_{self.symbol_base}.txt')
                os.system(
                    f'echo > {self.path_log}/log_stop_loss_manuel_{self.symbol_base}.txt')
                os.system(
                    f'echo > {self.path_log}/log_update_id_position_{self.symbol_base}.txt')

                if stop is None:
                    # Et faire dormir le programme
                    sleep(60 * 60 * 3)
                else:
                    break

        except Exception as error:
            msg = "Erreur survenu dans la fonction analyse_log, fonction laissée arrêter, " + \
                  f"bot toujours en cours d'exécution\nfichier qui pose problème : {fichier_en_cours}"

            # On envoi sur le canal discord
            self.msg_discord.message_erreur(error, msg)

    @retry(retry=retry_if_exception_type(
        (requests.exceptions.SSLError, requests.exceptions.ConnectionError, json.decoder.JSONDecodeError, Exception)),
        stop=stop_after_attempt(3))
    def requete(self, get_post_del: str, endpoint: str, log: str, param: Optional[str] = None) -> dict:
        """
        Exécute la requête sur le serveur
        Renvoi un dictionnaire

        Ex params : 
        get_post_del : 'GET', 'POST', 'DELETE'
        endpoint : '/api/v1/accounts...'
        log : 'requete', 'stoploss', 'presence_position'
        param (optionnel) : données pour la requête POST
        """

        # Création de l'entête
        header = self.headers(get_post_del, endpoint, param)

        # Création de l'url
        url = self.api + endpoint

        requete = requests.Response

        # On exécute la requête selon son type
        if get_post_del == 'GET':
            requete = requests.get(url, headers=header)

        elif get_post_del == 'POST':
            requete = requests.post(url, headers=header, data=param)

        elif get_post_del == 'DELETE':
            requete = requests.delete(url, headers=header)

        # On encode le résultat de la requête en str
        content = requete.content.decode("utf-8")

        # On écrit la requête sur le fichier log correspondant
        if self.symbol_base != "Discord":
            self.write_request(content, log)

        result = json.loads(content)

        if result["code"] != '200000':
            raise Exception(f"Code de la requête différent de 200000\nmessage : {result['msg']}")

        # Puis, on retourne les données
        return result

    def montant_compte(self, symbol: str, type_requete: Optional[str] = None) -> float:
        """
        Renvoie le montant que possède le compte selon le symbol voulus

        Ex params :
        symbol : USDT ou BTC3L
        type_requete (optionnel) : "requete" ou "stoploss"
        total (optionnel) : total d'usdt désiré
        """
        # On définit la terminaison de la requête
        endpoint = f"/api/v1/accounts?currency={symbol}&type=trade"

        # On change l'emplacement de l'écriture de la requete sur le fichier log
        log = "requete"
        if type_requete is not None:
            log = "stoploss"

        result = self.requete('GET', endpoint, log)

        # On ne garde que les données
        argent = result["data"]

        if argent:
            argent = float(argent[0]['balance'])

            if symbol == self.devise:
                argent *= 0.999

            money = self.arrondi(argent, self.zero_after_coma)

            return money

        return 0

    def prix_temps_reel_kucoin(self, symbol: str, type_requete: Optional[str] = None) -> float:
        """
        Renvoie le prix de la crypto en temps réel

        Ex params : 
        symbol : BTC3S-USDT
        type_requete (optionnel) : "requete" ou "stoploss"
        """
        # On définit la terminaison de la requête
        endpoint = f"/api/v1/market/orderbook/level1?symbol={symbol}"

        # On change l'emplacement de l'écriture de la requete sur le fichier log
        log = "requete"
        if type_requete is not None:
            log = "stoploss"

        result = self.requete('GET', endpoint, log)

        return float(result["data"]["price"])

    def prise_position(self, montant: float, symbol: str, achat_vente: bool) -> None:
        """
        Prend une position soit d'achat, soit de vente et place un stop loss (si achat)
        Lorsque qu'on vend, on retire l'ordre

        Ex params :
        montant : "20",
        symbol : "BTC3S-USDT",
        achat_vente : "True" (pour achat)
        """
        # Lorsque l'on vend, on enlève l'ordre limit car soit il a été exécuté, soit il est toujours là
        if achat_vente is False:
            # Sert à savoir si c'est une vente manuelle ou l'ordre limite qui est exécuté
            self.dico_partage[self.vente_manuelle] = True

            self.suppression_ordre()

        # Besoin d'un id pour l'achat des cryptos
        id_position = randint(0, 100_000_000)

        # Point de terminaison de la requête
        endpoint = "/api/v1/orders"

        # Soit, on achète tant de crypto avec de l'usdt,
        # Soit on vend tant de la crypto en question
        achat = "buy"
        type_achat = "funds"

        if achat_vente is False:
            achat = "sell"
            type_achat = "size"

        # Définition de tous les paramètres nécessaires
        param = {"clientOid": id_position,
                 "side": achat,
                 "symbol": symbol,
                 'type': "market",
                 type_achat: str(montant)}

        param = json.dumps(param)

        # On exécute la requête
        self.requete('POST', endpoint, "requete", param)

        # Si on vient d'acheter, on place un ordre limite
        if achat_vente is True:
            self.ordre_vente_seuil(symbol)

            # On repasse la variable a False pour l'ordre limite
            if self.vente_manuelle in self.dico_partage:
                del self.dico_partage[self.vente_manuelle]

    def presence_position(self, symbol: str) -> dict or None:
        """
        Renvoie les positions en cours sur une pair de crypto précis

        Ex params :
        symbol : BTC3S-USDT

        Sortie de la fonction (si position):
        {'id': '62d6e3303896050001788d36', 'symbol': 'BTC3L-USDT', 'opType': 'DEAL', 'type': 'limit', 'side': 'sell',
        'price': '0.007', 'size': '6791.3015', 'funds': '0', 'dealFunds': '0', 'dealSize': '0', 'fee': '0', 
        'feeCurrency': 'USDT', 'stp': '', 'stop': '', 'stopTriggered': False, 'stopPrice': '0', 'timeInForce': 'GTC', 
        'postOnly': False, 'hidden': False, 'iceberg': False, 'visibleSize': '0', 'cancelAfter': 0, 'channel': 'IOS', 
        'clientOid': None, 'remark': None, 'tags': None, 'isActive': True, 'cancelExist': False,
        'createdAt': 1658250032352, 'tradeType': 'TRADE'}
        """
        # On crée le point de terminaison
        endpoint = f"/api/v1/orders?status=active&symbol={symbol}"

        # On exécute la requête
        position = self.requete("GET", endpoint, "presence_position")

        # Puis, on récupère le résultat et on le transforme en dictionnaire (car reçu au format str)
        result = position['data']['items']

        # S'il y a un ordre, on renvoie les informations sur celui-ci
        if result:
            return result[0]

        return None

    def presence_position_all(self) -> list or None:
        """
        Renvoi toutes les positions de toutes les cryptomonnaies supportées
        """
        # Stock les cryptos ayant des positions
        cryptos_position = []

        # Parcours toutes les cryptos supportées
        for symbol in self.crypto_supported:
            list_symbol = [f"{symbol}3L-USDT", f"{symbol}3S-USDT"]

            # Parcours les deux marchés
            for position_symbol in list_symbol:
                pos = self.presence_position(position_symbol)

                # S'il y a bien une position, alors on stocke le symbol de la crypto
                if pos is not None:
                    cryptos_position.append(position_symbol)

        if cryptos_position:
            return cryptos_position

        return None

    def suppression_ordre(self) -> None:
        """
        Supprime l'ordre s'il existe
        """
        # On récupère l'id de l'ordre
        id_ordre = self.lecture_fichier_ordre_limit()

        # Si le fichier n'est pas vide, alors on peut supprimer l'ordre
        if id_ordre is not None:
            # On crée le point de terminaison de l'url
            endpoint = f"/api/v1/orders/{id_ordre}"

            # Enfin, on exécute la requête
            self.requete('DELETE', endpoint, "requete")

        # Enfin, on supprime l'id du fichier
        # Créer le fichier s'il n'existe pas
        self.write_file_limit_order()

    def achat_vente(self, montant: float, symbol: str, achat_ou_vente: bool) -> None:
        """
        Achète ou vente les cryptomonnaies

        Ex params :
        Achat : montant : 200 (USDT), symbol : "BTC3L-USDT, achat_vente : True
        Vente : montant : 48 (BTC3L-USDT), "BTC3L-USDT", achat_vente : False
        """

        # On prend la position sur le serveur
        self.prise_position(montant, symbol, achat_ou_vente)

        # On récupère le prix en temps réel de la crypto que l'on vient d'acheter
        prix = self.prix_temps_reel_kucoin(self.symbol)

        # Puis, on vient envoyer un message sur le discord
        if achat_ou_vente:
            msg = f"Prise de position avec {montant} usdt au prix de {prix}$, crypto : {symbol}"
            self.msg_discord.message_canal("prise_position",
                                           msg, 'Prise de position')

        else:
            argent = self.montant_compte(self.devise, None)

            msg = f"Vente de position au prix de {prix}$, il reste {argent} usdt\n" + \
                  f"Crypto : {symbol}"
            self.msg_discord.message_canal("prise_position",
                                           msg, 'Vente de position')

    def ordre_vente_seuil(self, symbol: str, nouveau_gain: Optional[float] = None) -> None:
        """
        Place l'ordre limite de vente

        Ex params :
        symbol : BTC3S-USDT
        nouveau_gain (optionnel) : 0.002, 0.0175...
        """
        # Calcul du prix de l'ordre ################################################
        # Récupération des prix de marchés
        prix = self.prix_temps_reel_kucoin(symbol)

        # On récupère le priceIncrement de la crypto en question
        zero_apres_virgule = self.dico_priceIncrement[symbol]

        # On stocke le pourcentage de gain actuel dans une variable
        gain = self.pourcentage_gain

        # Calcul du prix de vente de l'ordre
        nv_prix = self.arrondi(
            str(prix * (1 + gain)), zero_apres_virgule)

        ##################################################################################

        # Calcul de la baisse de l'ordre si descente souhaité #############################
        if nouveau_gain is not None:
            gain = nouveau_gain

            # On récupère l'ancien prix pour le calcul de la descente
            ancien_prix = float(self.presence_position(symbol)["price"])

            # Calcul du nouveau prix
            nv_prix = self.arrondi(
                str(((1 + gain) * ancien_prix) / (1 + self.previous_gain)), zero_apres_virgule)

            # Si le nouveau prix est inférieur au prix de la crypto
            # Alors, on vend directement au lieu de placer un nouvel ordre
            if nv_prix <= prix:
                self.msg_discord.message_canal("prise_position",
                                               "Le nouveau prix étant inférieur, une vente directe est effectué",
                                               "Vente directe via baisse du stop loss")

                # On récupère le montant du compte pour pouvoir vendre
                montant = self.montant_compte(self.dico_symbol_simple[symbol])

                self.achat_vente(montant, symbol, False)

                return

            # On le met à True pour que quand on replace l'ordre.
            # Il n'y a pas entre temps un message de vente de l'ordre limite
            self.dico_partage[self.vente_manuelle] = True

            # On supprime l'ancien ordre limite
            self.suppression_ordre()

            # Envoi d'un message sur le canal discord
            msg = "Baisse de l'ordre limite, l'estimation du prix de revente risque d'être fausse !\n" + \
                  f"Nouveau gain : {gain}"
            self.msg_discord.message_canal("prise_position",
                                           msg, "Modification de l'ordre limite")

        ###################################################################################

        # Puis, on garde en mémoire le precedent gain, au cas où on souhaite baisser le prix
        self.previous_gain = gain

        # Calcul prix de vente estimer ##################################################
        prix_marche = self.prix_temps_reel_kucoin(self.symbol)

        # On stocke dans le dictionnaire partagé le prix estimé de vente sur le marché de base
        if "3L" in symbol:
            self.dico_partage[f"prix_estimer_{self.symbol_base}"] = prix_marche * \
                                                                    (1 + (self.pourcentage_gain / 3))
        else:
            self.dico_partage[f"prix_estimer_{self.symbol_base}"] = prix_marche * \
                                                                    (1 - (self.pourcentage_gain / 3))

        ##################################################################################

        # Requête ########################################################################
        # Besoin d'un id pour l'achat des cryptos
        id_position = randint(0, 100_000_000)

        # Point de terminaison de la requête
        endpoint = "/api/v1/orders"

        # On récupère le montant du compte pour pouvoir placer l'ordre
        montant = self.montant_compte(self.dico_symbol_simple[symbol])

        # Définition de tous les paramètres nécessaires
        param = {"clientOid": id_position,
                 "side": "sell",
                 "symbol": symbol,
                 "price": str(nv_prix),
                 "size": str(montant)}

        param = json.dumps(param)

        # On exécute la requête
        content = self.requete('POST', endpoint, "requete", param)

        ##################################################################################

        # Puis, on vient écrire l'id de l'ordre dans un fichier pour faciliter la suppression de celui-ci
        self.write_file_limit_order(content["data"]["orderId"])

        # Et on supprime la valeur du dictionnaire (si descente de l'ordre limite)
        if self.vente_manuelle in self.dico_partage:
            del self.dico_partage[self.vente_manuelle]

    # Fonction qui tourne en continu
    def stoploss_manuel(self, symbol: str, prix_stop: float, event: Event) -> Thread:
        """
        Fait office de stop loss mais de façon manuel
        Basé sur le prix du marché normal, pas celui des jetons à effet de levier

        Ex params : 
        symbol : BTC3S-USDT
        prix_stop : 23450.2463
        start (optionnel) : True pour démarrer ou laisser à None
        """

        def stoploss_thread(symbol_thread: str, price_stop: float, event_flag: Event) -> None:
            try:
                # Dictionnaire qui donne les bonnes valeurs et symbol au stop loss
                dico_type_market = {self.symbol_up: True,
                                    self.symbol_down: False}

                dico_minimum = {self.symbol_up: self.minimum_crypto_up,
                                self.symbol_down: self.minimum_crypto_down}

                # On est attribut les bonnes valeurs aux variables
                type_marche = dico_type_market[symbol_thread]

                minimum = dico_minimum[symbol_thread]

                symbol_simple = self.dico_symbol_simple[symbol_thread]

                while True:
                    # Stop le thread sur demande
                    if event_flag.is_set():
                        break

                    # On vérifie s'il y a toujours une crypto, si elle a été vendue, on peut arrêter la fonction
                    crypto = self.montant_compte(symbol_simple, "stoploss")

                    if crypto < minimum:
                        break

                    # On récupère le prix du marché
                    prix = self.prix_temps_reel_kucoin(self.symbol, "stoploss")

                    # Si la crypto dépasse le stop loss fixé, alors on vend
                    if not self.comparaisons(prix, price_stop, type_marche):
                        # Message sur le discord
                        self.msg_discord.message_canal("prise_position",
                                                       f"Vente de {symbol_thread} via le stop loss",
                                                       "Exécution du stop loss")

                        self.achat_vente(crypto, symbol_thread, False)

                        break

                    sleep(5)
            except Exception as error:
                msg = "Erreur survenu dans la fonction stop loss_manuel, " + \
                      "aucune interruption du programme, fonction relancée"

                # Puis, on l'envoie sur le canal discord
                self.msg_discord.message_erreur(error, msg)

                # Et enfin on relance la fonction
                stoploss_thread(symbol_thread, price_stop, event_flag)

        th = Thread(target=stoploss_thread, args=[
            symbol, prix_stop, event])

        th.start()

        return th

    def update_id_ordre_limite(self) -> None:
        """
        Maintien à jour l'id de l'ordre limite dans le fichier
        Si l'ordre a été exécuté alors, on enlève l'id du fichier
        """
        try:
            # Stock l'id de l'ordre
            id_limit_order = ""
            symbol = ""

            while True:
                sl_3l = self.presence_position(self.symbol_up)
                sl_3s = self.presence_position(self.symbol_down)

                # S'il n'y a aucun stop loss, par sécurité, on vide le fichier
                if sl_3l is None and sl_3s is None:
                    self.write_file_limit_order()

                    # S'il y avait bien un id avant
                    if id_limit_order != "":
                        id_limit_order = ""

                        # alors soit l'ordre est exécuté
                        if self.vente_manuelle not in self.dico_partage:
                            montant = self.montant_compte(
                                self.devise, None)

                            msg = f"Exécution de l'ordre limite, il reste {montant} USDT !\n" + \
                                  f"Crypto : {symbol}"

                            self.msg_discord.message_canal(
                                "prise_position", msg, "Exécution de l'ordre limite")

                        # Soit c'est une vente manuelle
                        else:
                            del self.dico_partage[self.vente_manuelle]

                # Sinon par sécurité, on remet l'id du stop loss dans le fichier
                elif sl_3l is not None:
                    self.write_file_limit_order(sl_3l['id'])
                    id_limit_order = sl_3l['id']
                    symbol = self.symbol_up

                # De même pour ici
                elif sl_3s is not None:
                    self.write_file_limit_order(sl_3s['id'])
                    id_limit_order = sl_3s['id']
                    symbol = self.symbol_down

                sleep(20)

        except Exception as error:
            msg = "Erreur survenu dans la fonction update_id_ordre_limite, " + \
                  "aucune interruption du programme, fonction relancée"

            # Puis, on l'envoie sur le canal discord
            self.msg_discord.message_erreur(error, msg)

            # Et enfin on relance la fonction
            self.update_id_ordre_limite()
