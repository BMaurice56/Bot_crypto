from tenacity import retry, retry_if_exception_type, stop_after_attempt
from shared_memory_dict import SharedMemoryDict
from multiprocessing import Process, Manager
from decimal import Decimal, ROUND_DOWN
from threading import Thread, Event
from binance.client import Client
from zoneinfo import ZoneInfo
from datetime import datetime
from message_discord import *
from random import randint
from time import sleep
import traceback
import requests
import hashlib
import base64
import pandas
import locale
import time
import hmac
import json
import os

# Définition de la zone pour l'horodatage car la date était en anglais avec le module datetime
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')


# BINANCE
# Fonctions qui récupère les données du serveur


class Binance:
    """
    Classe Binance qui permet l'interaction avec les serveurs de binance
    """

    def __init__(self) -> None:
        """
        Initialise un objet binance
        """

        self.api_key = "eUFWHXCMrNKoP4LURDCOW0faPCyzm2teZLU3eBYUM2AoNM3wvr8F4d3IjeJuDipd"
        self.api_secret = "AZM89mot3fJNk2ODEGomItIkWyP6pTazXj6W2SHfSRoRL3CTyIUQvcmXTIi6edRy"

        self.client = Client(self.api_key, self.api_secret)

    def donnée(self, symbol: str, début: str, fin: str) -> pandas.DataFrame:
        """
        Prend en argument un symbol de type "BTCUSDT" ou encore "ETHUSDT" ...
        Renvoie les données sous forme d'une dataframe pandas

        Ex params :
        symbol : "BTCUSDT"
        début : "40 hour ago UTC" 
        fin : "0 hour ago UTC" ...
        """
        donnée_historique = []

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

    def all_data(self, symbol: str) -> dict:
        """
        Prend en argument un symbol
        Renvoie un dictionnaire de avec toutes les données (+ ceux avec effet de levier)

        Ex param :
        symbol : "BTC"
        """
        # Création du dictionnaire que recevra toutes les dataframes avec les données
        manager = Manager()
        dico = manager.dict()

        @retry(retry=retry_if_exception_type((requests.exceptions.SSLError, requests.exceptions.ConnectionError)), stop=stop_after_attempt(3))
        def requete(sl: str, limit: str, dictionnaire: dict, position_list: int):
            """
            Récupère les données d'une crypto de façon parallèle

            Ex params:
            sl : "BTCUSDT"
            limit : 40
            dictionnaire : dictionnaire qui gère le stockage multiprocess
            position_liste : Emplacement dans le dictionnaire
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

    def __init__(self, crypto: str, thread: Optional[bool] = None) -> None:
        """
        Initialise un objet kucoin pour interagir avec leurs serveurs

        Ex params:
        crypto : "BTC", "BNB" ...
        thread (optionnel) : False pour ne pas activer les fonctions continues
        """

        self.api = "https://api.kucoin.com"

        self.kucoin_api_key = "63cffd08f8686d000140987a"
        self.kucoin_api_secret = "d125b0df-e2eb-4532-8ed1-049d01dc18b8"
        self.kucoin_phrase_securite = "c5%Pnp8o$FE%^CEM7jwFp9PaTtW4kq"

        self.pourcentage_gain = 0.015
        self.precedant_gain = 0.015

        # Prix des cryptos de kucoin -> l'inverse de binance
        self.minimum_crypto_up = 5000
        self.minimum_crypto_down = 5

        # Symbol des crypto
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

        # On récupère le priceIncrement de chaque crypto
        with open("Autre_fichiers/priceIncrement.txt", "r") as f:
            self.dico_priceIncrement = json.loads(f.read())

        # Crypto supportées et leurs nombres
        with open("Autre_fichiers/crypto_supporter.txt", "r") as f:
            self.crypto_supporter = f.read().split(";")
            self.nb_crypto_supporté = len(self.crypto_supporter)

        # Message discord
        self.msg_discord = Message_discord()

        # Dictionnaire partagé entre programme
        self.dico_partage = SharedMemoryDict(name="dico", size=1024)

        # Permet de savoir si le bot a fini de démarrer (démarrage multiple)
        self.dico_partage[f"{self.symbol_base}_started"] = True

        # Dossier fichiers logs
        self.dir_log = "fichier_log"

        # Chemin des fichiers logs
        self.path_log = f"/home/Bot_crypto/{self.dir_log}"

        # Si on créer un objet Kucoin en dehors de discord -> bot de trading
        # Permet de garder l'id à jour dans le fichier et analyser les fichiers logs
        if thread == None:
            th = Thread(target=self.update_id_ordre_limite)
            th.start()

            th2 = Thread(target=self.analyse_fichier)
            th2.start()

    def arrondi(self, valeur: float or str, zero_apres_virgule: str) -> float:
        """
        Prend en argument un décimal 
        Renvoie un décimal arrondi

        Ex params:
        valeur : 56.36 ou "56.36"
        """
        # On transforme la valeur reçu en objet décimal
        val = Decimal(str(valeur))

        # Puis on arrondi vers le bas le nombre que l'on renvoit sous forme d'un float
        return float(val.quantize(Decimal(str(zero_apres_virgule)), ROUND_DOWN))

    def headers(self, methode: str, endpoint: str, param: Optional[str] = None) -> dict:
        """
        Créer l'entête de la requête http

        Ex params :
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
        Compare deux décimaux entre eux
        Sens_comparaison définit le sens dans lequel les deux valeurs doivent être comparées
        Si True : valeur_1 >= valeur_2
        Sinon : valeur_1 <= valeur_2
        """
        if sens_comparaison == True:
            return valeur_1 >= valeur_2

        return valeur_1 <= valeur_2

    def lecture_fichier_ordre_limit(self) -> str or None:
        """
        Lit le contenu du ficher ordre_limit
        Renvoie le contenu ou None
        """
        # On utilise try dans le cas où le fichier n'existe pas
        try:
            with open(f"ordre_limit_{self.symbol_base}.txt", "r") as f:
                elt = f.read()

            if elt == "":
                return None
            return elt
        except:
            return None

    def écriture_fichier_ordre_limit(self, str_to_write: Optional[str] = None) -> None:
        """
        Ecrit ou écrase le fichier

        Ex param :
        str_to_write (optionnel) : id de l'ordre
        """

        fichier = open(f"ordre_limit_{self.symbol_base}.txt", "w")

        if str_to_write != None:
            fichier.write(str_to_write)

        fichier.close()

    def écriture_requete(self, requete: str, emplacement: str) -> None:
        """
        Ecrit toutes les requêtes dans un fichier (résultat)
        Ainsi que la date

        Ex params :
        requete : données de la requête
        emplacement : "requete", "presence_position", "stoploss"
        """
        date = datetime.now(tz=ZoneInfo("Europe/Paris")
                            ).strftime("%A %d %B %Y %H:%M:%S")

        if emplacement == "requete":
            pwd = f"{self.dir_log}/log_requete_{self.symbol_base}.txt"

        elif emplacement == "presence_position":
            pwd = f"{self.dir_log}/log_update_id_position_{self.symbol_base}.txt"

        elif emplacement == "stoploss":
            pwd = f"{self.dir_log}/log_stoploss_manuel_{self.symbol_base}.txt"

        with open(pwd, "a") as f:
            f.write(f"{date};{requete}\n")

    def analyse_fichier(self) -> None:
        """
        Aanalyse les fichiers log
        Ecrit toutes les erreurs dans un fichier
        """
        fichier_en_cours = ""
        try:
            # Les noms des trois fichiers log de requêtes
            nom = [f"log_requete_{self.symbol_base}.txt", f"log_stoploss_manuel_{self.symbol_base}.txt",
                   f"log_update_id_position_{self.symbol_base}.txt"]

            while True:
                for elt in nom:
                    fichier_en_cours = elt
                    if os.path.exists(f"{self.dir_log}/{elt}") == True:
                        # On vient lire le contenue du fichier
                        fichier = open(f"{self.dir_log}/{elt}", "r").read()

                        # S'il y a bien une requête dans le fichier, alors on peut l'analyser
                        if len(fichier) > 25:
                            # On sépare chaque ligne entre elles (-1 car on ne garde pas le dernier retoure a la ligne)
                            contenue = fichier[1:-1].split("\n")

                            # On ne garde que la requête sans la date
                            requete = [elt.split(";")[1] for elt in contenue]

                            requete_trie = []
                            résultat = []

                            # Puis on retransforme la requête en un objet python sans les espaces de début et fin
                            # Si problème de longueur, on la stocke dans la liste de problème
                            for j in range(len(requete)):
                                if len(requete[j]) < 10:
                                    résultat.append(requete[j])
                                else:
                                    requete_trie.append(
                                        json.loads(requete[j]))

                            # Enfin on parcours toutes les requêtes pour vérifier s'il y en a une qui n'a pas abouti
                            # Ou qu'il y a un quelconque problème
                            for k in range(len(requete_trie)):
                                if requete_trie[k]['code'] != '200000':
                                    résultat.append(requete_trie[k])

                                elif requete_trie[k]['data'] == None:
                                    résultat.append(requete_trie[k])

                                elif len(requete_trie[k]['data']) == 0:
                                    résultat.append(requete_trie[k])

                            if len(résultat) > 0:
                                date = datetime.now(tz=ZoneInfo("Europe/Paris")
                                                    ).strftime("%A %d %B %Y %H:%M:%S")

                                with open(f"{self.dir_log}/log_recap.txt", "a") as f:
                                    f.write(
                                        f"Bot : {self.symbol_base}, erreur du {date} : {résultat} \n")

                # Puis on vient vider les fichiers (ou les créer)
                os.system(
                    f'echo > {self.path_log}/log_requete_{self.symbol_base}.txt')
                os.system(
                    f'echo > {self.path_log}/log_stoploss_manuel_{self.symbol_base}.txt')
                os.system(
                    f'echo > {self.path_log}/log_update_id_position_{self.symbol_base}.txt')

                # Et faire dormir le programme
                sleep(60 * 60 * 3)
        except:
            # On récupère l'erreur
            erreur = traceback.format_exc()

            # Puis on l'envoi sur le canal discord
            self.msg_discord.message_erreur(
                erreur, f"Erreur survenu dans la fonction analyse_log, fonction laissée arrêter, bot toujours en cours d'exécution\nfichier qui pose problème : {fichier_en_cours}")

    @retry(retry=retry_if_exception_type((requests.exceptions.SSLError, requests.exceptions.ConnectionError, json.decoder.JSONDecodeError)), stop=stop_after_attempt(3))
    def requete(self, get_post_del: str, endpoint: str, log: str, param: Optional[dict] = None) -> dict:
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
        entête = self.headers(get_post_del, endpoint, param)

        # Création de l'url
        url = self.api + endpoint

        # On exécute la requête selon son type
        if get_post_del == 'GET':
            requete = requests.get(url, headers=entête)

        elif get_post_del == 'POST':
            requete = requests.post(url, headers=entête, data=param)

        elif get_post_del == 'DELETE':
            requete = requests.delete(url, headers=entête)

        # On encode le résultat de la requête en str
        content = requete.content.decode("utf-8")

        # On écrit la requête sur le fichier log correspondant
        self.écriture_requete(content, log)

        # Puis on retourne les données
        return json.loads(content)

    def montant_compte(self, symbol: str, type_requete: Optional[str] = None, total: Optional[bool] = None) -> float:
        """
        Renvoie le montant que possède le compte selon le symbol voulus

        Ex params :
        symbol : USDT ou BTC3L
        type_requete (optionnel) : "requete" ou "stoploss"
        """
        # On défini la terminaison de la requête
        endpoint = f"/api/v1/accounts?currency={symbol}&type=trade"

        # On change l'emplacement de l'écriture de la requete sur le fichier log
        log = "requete"
        if type_requete != None:
            log = "stoploss"

        resultat = self.requete('GET', endpoint, log)

        # On ne garde que les données
        argent = resultat["data"]

        # S'il le compte possède le symbol voulu, on renvoit le nombre
        # Avec seulement 99,9% de sa quantité initiale car pour l'achat des cryptos
        # -> aucun problème avec le nb de chiffres après la virgule et les frais de la platforme
        if argent != []:
            argent = float(argent[0]['balance'])

            # renvoit l'usdt disponible pour chaque bot
            if symbol == self.devise and total == None:
                # Si présence du total d'usdt dans le dictionnaire
                # On met à jour le max s'il est supérieur à celui enregistrer (gain des bots)
                if "quantite_usdt" in self.dico_partage:
                    # S'il y a plus d'argent (gain), alors on met à jour
                    if argent >= self.dico_partage["quantite_usdt"]:
                        self.dico_partage["quantite_usdt"] = argent
                    else:
                        # S'il n'y a pas de position et que le montant est plus faible (perte)
                        # Alors on met à jour
                        position_all = self.présence_position_all()
                        if position_all == None:
                            self.dico_partage["quantite_usdt"] = argent

                else:
                    self.dico_partage["quantite_usdt"] = argent

                # Max d'usdt pour chaque bot
                argent_bot = self.dico_partage["quantite_usdt"] / \
                    self.nb_crypto_supporté

                # S'il y a plus d'usdt que prévu pour chaque bot
                # Alors le bot ne prend que sa part
                if argent > argent_bot:
                    argent = argent_bot

            money = self.arrondi(float(argent[0]['balance']) * 0.999, '0.0001')

            return money
        else:
            return 0

    def prix_temps_reel_kucoin(self, symbol: str, type_requete: Optional[str] = None) -> float:
        """
        Renvoie le prix de la crypto en temps réel

        Ex params : 
        symbol : BTC3S-USDT
        type_requete (optionnel) : "requete" ou "stoploss"
        """
        # On défini la terminaison de la requête
        endpoint = f"/api/v1/market/orderbook/level1?symbol={symbol}"

        # On change l'emplacement de l'écriture de la requete sur le fichier log
        log = "requete"
        if type_requete != None:
            log = "stoploss"

        resultat = self.requete('GET', endpoint, log)

        # On la retransforme en dictionnaire (car reçu au format str)
        # Et on garde que le prix voulu
        argent = float(resultat["data"]["price"])

        return argent

    def prise_position(self, info: dict) -> None:
        """
        Prend une position soit d'achat soit de vente et place un stoploss
        Place automatiquement un stoploss
        Lorsque qu'on vend, on retire l'ordre
        Renvoie l'id de la position prise

        Ex params :
        info : {
        "montant" : "20",
        "symbol" : "BTC3S-USDT",
        "achat_vente" : "True" (pour achat)
        }
        """
        # Lorsque l'on vend, on enlève l'ordre limit car soit il a été exécuté, soit il est toujours là
        if info["achat_vente"] == False:
            # Sert a savoir si c'est une vente manuelle ou l'ordre limite qui est exécuté
            self.dico_partage[self.vente_manuelle] = True

            self.suppression_ordre()

        # Besoin d'un id pour l'achat des cryptos
        id_position = randint(0, 100_000_000)

        # Point de terminaison de la requête
        endpoint = "/api/v1/orders"

        # Soit on achète tant de crypto avec de l'usdt
        # Soit on vend tant de la crypto en question
        achat = "buy"
        type_achat = "funds"

        if info["achat_vente"] == False:
            achat = "sell"
            type_achat = "size"

        # Définition de tous les paramètres nécessaires
        param = {"clientOid": id_position,
                 "side": achat,
                 "symbol": info["symbol"],
                 'type': "market",
                 type_achat: str(info["montant"])}

        param = json.dumps(param)

        # On exécute la requête
        self.requete('POST', endpoint, "requete", param)

        # S'il on vient d'acheter, on place un ordre limite
        if info["achat_vente"] == True:
            self.ordre_vente_seuil(info["symbol"])

            # On repasse la variable a False pour l'ordre limite
            if self.vente_manuelle in self.dico_partage:
                del self.dico_partage[self.vente_manuelle]

    def présence_position(self, symbol: str) -> dict or None:
        """
        Renvoie les positions en cours sur une pair de crypto précis

        Ex params :
        symbol : BTC3S-USDT

        Sortie de la fonction (si position):
        {'id': '62d6e3303896050001788d36', 'symbol': 'BTC3L-USDT', 'opType': 'DEAL', 'type': 'limit', 'side': 'sell', 
        'price': '0.007', 'size': '6791.3015', 'funds': '0', 'dealFunds': '0', 'dealSize': '0', 'fee': '0', 
        'feeCurrency': 'USDT', 'stp': '', 'stop': '', 'stopTriggered': False, 'stopPrice': '0', 'timeInForce': 'GTC', 
        'postOnly': False, 'hidden': False, 'iceberg': False, 'visibleSize': '0', 'cancelAfter': 0, 'channel': 'IOS', 
        'clientOid': None, 'remark': None, 'tags': None, 'isActive': True, 'cancelExist': False, 'createdAt': 1658250032352, 
        'tradeType': 'TRADE'}
        """
        # On crée le point de terminaison
        endpoint = f"/api/v1/orders?status=active&symbol={symbol}"

        # On exécute la requête
        position = self.requete("GET", endpoint, "presence_position")

        # Puis on récupère le résultat et on le transforme en dictionnaire (car reçu au format str)
        resultat = position['data']['items']

        # S'il y a un ordre on renvoie les informations sur celui-ci
        if resultat == []:
            return None
        else:
            return resultat[0]

    def présence_position_all(self) -> list or None:
        """
        Renvoi toutes les positions de toutes les cyptomonnaies supportées
        """
        # Stock les cryptos ayant des positions
        cryptos_position = []

        # Parcour toutes les cryptos supportées
        for symbol in self.crypto_supporter:
            liste_symbole = [f"{symbol}3L-USDT", f"{symbol}3S-USDT"]

            # Parcour les deux marchés
            for position_symbol in liste_symbole:
                pos = self.présence_position(position_symbol)

                # S'il y a bien une position, alors on stocke le symbole de la crypto
                if pos != None:
                    cryptos_position.append(position_symbol)

        if cryptos_position == []:
            return None

        return cryptos_position

    def suppression_ordre(self) -> None:
        """
        Supprime l'ordre s'il existe
        """
        # On récupère l'id de l'ordre
        id_ordre = self.lecture_fichier_ordre_limit()

        # Si le fichier n'est pas vide, alors on peut supprimer l'ordre
        if id_ordre != None:

            # On créer le point de terminaison de l'url
            endpoint = f"/api/v1/orders/{id_ordre}"

            # Enfin on exécute la requête
            self.requete('DELETE', endpoint, "requete")

        # Enfin on supprime l'id du fichier
        # Créer le fichier s'il n'existe pas
        self.écriture_fichier_ordre_limit()

    def achat_vente(self, montant: float, symbol: str, achat_ou_vente: bool) -> None:
        """
        Achète ou vente les cryptomonnaies

        Ex params :
        Achat : montant : 200 (USDT), symbol : "BTC3L-USDT, achat_vente : True
        Vente : montant : 48 (BTC3L-USDT), "BTC3L-USDT", achat_vente : False
        """
        # On créer un dictionnaire avec toutes les informations nécessaires
        info = {"montant": montant,
                "symbol": symbol, "achat_vente": achat_ou_vente}

        # On prend la position sur le serveur
        self.prise_position(info)

        # On récupère le prix en temps réel de la crypto que l'on vient d'acheter
        prix = self.prix_temps_reel_kucoin(self.symbol)

        # Puis on vient envoyer un message sur le discord
        if achat_ou_vente == True:
            msg = f"Prise de position avec {montant} usdt au prix de {prix}$, crypto : {symbol}"
            self.msg_discord.message_canal("prise_position",
                                           msg, 'Prise de position')

        else:
            argent = self.montant_compte(self.devise, None, True)

            msg = f"Vente de position au prix de {prix}$, il reste {argent} usdt"
            self.msg_discord.message_canal("prise_position",
                                           msg, 'Vente de position')

    def ordre_vente_seuil(self, symbol: str, nouveau_gain: Optional[float] = None) -> None:
        """
        Place l'ordre limite de vente

        Ex params :
        symbol : BTC3S-USDT
        nouveau_gain (optionnel) : 0.002, 0.0175...
        """
        ###################### Calcul du prix de l'ordre ###############################
        # Récupération des prix de marchés
        prix = self.prix_temps_reel_kucoin(symbol)

        # On récupère le priceIncrement de la crypto en question
        zero_apres_virgule = self.dico_priceIncrement[symbol]

        # On stock le pourcentage de gain actuel dans une variable
        gain = self.pourcentage_gain

        # Calcul du prix de vente de l'ordre
        nv_prix = self.arrondi(
            str(prix * (1 + gain)), zero_apres_virgule)

        ##################################################################################

        ############ Calcul de la baisse de l'ordre si descente souhaité##################
        if nouveau_gain != None:
            gain = nouveau_gain

            # On récupère l'ancien prix pour le calcul de la descente
            ancien_prix = float(self.présence_position(symbol)["price"])

            # Calcul du nouveau prix
            nv_prix = self.arrondi(
                str(((1 + gain) * ancien_prix) / (1 + self.precedant_gain)), zero_apres_virgule)

            # Si le nouveau prix est inférieur au prix de la crypto
            # Alors on vend directement au lieu de placer un nouvel ordre
            if nv_prix <= prix:
                # On récupère le montant du compte pour pouvoir vendre
                montant = self.montant_compte(self.dico_symbol_simple[symbol])

                self.achat_vente(montant, symbol, False)

                return

            # On le met a True pour que quand on replace l'ordre
            # Il n'y a pas entre temps un message de vente de l'ordre limite
            self.dico_partage[self.vente_manuelle] = True

            # On supprime l'ancien ordre limite
            self.suppression_ordre()

            # Envoit d'un message sur le canal discord
            msg = "Baisse de l'ordre limite, l'estimation du prix de revente risque d'être fausse !\n" + \
                f"Nouveau gain : {gain}"
            self.msg_discord.message_canal("prise_position",
                                           msg, "Modification de l'ordre limite")

        ###################################################################################

        # Puis on garde en mémoire le précedant gain, au cas où on souhaite baisser le prix
        self.precedant_gain = gain

        #################### Calcul prix de vente estimer ###############################
        prix_marche = self.prix_temps_reel_kucoin(self.symbol)

        # On stock dans le dictionaire partagé le prix estimer de vente sur le marché de base
        if "3L" in symbol:
            self.dico_partage[f"prix_estimer_{self.symbol_base}"] = prix_marche * \
                (1 + (self.pourcentage_gain/3))
        else:
            self.dico_partage[f"prix_estimer_{self.symbol_base}"] = prix_marche * \
                (1 - (self.pourcentage_gain/3))

        ##################################################################################

        ################################# Requête ########################################
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

        if content["code"] != "200000":
            self.msg_discord.message_erreur(
                f"{str(content)}", "Echec du placement de l'ordre limite")

        # Puis on vient écrire l'id de l'ordre dans un fichier pour faciliter la suppresion de celui-ci
        self.écriture_fichier_ordre_limit(content["data"]["orderId"])

        # Et on supprime la valeur du dictionnaire (si descente de l'ordre limite)
        if self.vente_manuelle in self.dico_partage:
            del self.dico_partage[self.vente_manuelle]

    # Fonction qui tourne en continue
    def stoploss_manuel(self, symbol: str, prix_stop: float, event: Event, start: Optional[bool] = None) -> Thread:
        """
        Fait office de stoploss mais de façon manuel
        Basé sur le prix du marché normal, pas celui des jetons à effet de levier

        Ex params : 
        symbol : BTC3S-USDT
        prix_stop : 23450.2463
        start (optionnel) : True pour démarrer ou laisser à None
        """

        def stoploss_thread(symbol: str, prix_stop: float, event: Event):
            try:
                # Dictionnaire qui donne les bonnes valeurs et symbol au stoploss
                dico_type_marché = {self.symbol_up: True,
                                    self.symbol_down: False}

                dico_minimum = {self.symbol_up: self.minimum_crypto_up,
                                self.symbol_down: self.minimum_crypto_down}

                # On attribut les bonnes valeurs aux variables
                type_marche = dico_type_marché[symbol]

                minimum = dico_minimum[symbol]

                symbol_simple = self.dico_symbol_simple[symbol]

                while True:
                    # Stop le thread sur demande
                    if event.is_set():
                        break

                    # On vérifie s'il y a toujours une crypto, s'il elle a été vendu on peut arrêter la fonction
                    crypto = self.montant_compte(symbol_simple, "stoploss")

                    if crypto < minimum:
                        break

                    # On récupère le prix du marché
                    prix = self.prix_temps_reel_kucoin(self.symbol, "stoploss")

                    # Si la crypto dépasse le stoploss fixé, alors on vend
                    if self.comparaisons(prix, prix_stop, type_marche) == False:
                        # Message sur le discords
                        self.msg_discord.message_canal("prise_position",
                                                       "Vente des cryptos via le stoploss", "Exécution du stoploss")

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

        th = Thread(target=stoploss_thread, args=[
            symbol, prix_stop, event])

        if start != None:
            th.start()

        return th

    def update_id_ordre_limite(self) -> None:
        """
        Maintien à jour l'id de l'ordre limite dans le fichier
        S'il l'ordre a été executé alors on enlève l'id du fichier
        """
        try:
            # Stock l'id de l'ordre
            id_ordrelimite = ""
            while True:
                sl_3L = self.présence_position(self.symbol_up)
                sl_3S = self.présence_position(self.symbol_down)

                # S'il y a aucun stoploss, par sécurité on vide le fichier
                if sl_3L == None and sl_3S == None:
                    self.écriture_fichier_ordre_limit()

                    # S'il y avait bien un id avant
                    if id_ordrelimite != "":
                        id_ordrelimite = ""

                        # alors soit l'ordre est exécuté
                        if self.vente_manuelle not in self.dico_partage:
                            montant = self.montant_compte(
                                self.devise, None, True)

                            self.msg_discord.message_canal("prise_position",
                                                           f"Exécution de l'ordre limite, il reste {montant} USDT !", "Exécution de l'ordre limite")

                        # Soit c'est une vente manuelle
                        else:
                            del self.dico_partage[self.vente_manuelle]

                # Sinon par sécurité, on remet l'id du stoploss dans le fichier
                elif sl_3L != None:
                    self.écriture_fichier_ordre_limit(sl_3L['id'])
                    id_ordrelimite = sl_3L['id']

                # De même pour ici
                elif sl_3S != None:
                    self.écriture_fichier_ordre_limit(sl_3S['id'])
                    id_ordrelimite = sl_3S['id']

                sleep(20)

        except:
            # On récupère l'erreur
            erreur = traceback.format_exc()

            # Puis on l'envoi sur le canal discord
            self.msg_discord.message_erreur(
                erreur, "Erreur survenu dans la fonction update_id_ordre_limite, aucune interruption du programme, fonction relancée")

            # Et enfin on relance la fonction
            self.update_id_ordre_limite()
