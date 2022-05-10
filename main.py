from discord_webhook import DiscordWebhook, DiscordEmbed
from time import sleep, perf_counter
from multiprocessing import Process
from subprocess import Popen, PIPE
from binance.client import Client
from sklearn import linear_model
from dotenv import load_dotenv
from functools import wraps
from dessinBDD import *
import locale
import pandas
import talib
import numpy
import copy
import math
import ast
import sys
import os


# Définition de la zone pour l'horodatage car la date était en anglais avec le module datetime
locale.setlocale(locale.LC_TIME, '')


# Chargement des clés

load_dotenv(dotenv_path="config")

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


# Fonctions qui renvoient sous forme d'un entier ou décimal


def croisement(liste1: list, liste2: list) -> int:
    """
    Fonction qui prend en argument deux listes de float
    Et qui renvoie les croisements (lorsque tracé sur un graphique, les courbes se croisent)
    """

    if len(liste1) != len(liste2):
        raise Exception("Les listes doivent être de la même taille")
    elif True in list(map(math.isnan, liste1)):
        raise Exception("Présence de nan dans la liste 1")
    elif True in list(map(math.isnan, liste2)):
        raise Exception("Présence de nan dans la liste 2")

    cr = 0

    # Vue qu'on itere sur les listes, cette variable permet d'avoir l'indice de l'élément en cour
    compteur = 0

    # On vérifie que l'élement n de la première liste est supérieur ou inférieur a celui de l'autre liste
    # Et l'élément n+1 est inversement supérieur ou inférieur
    for element in liste1:
        if compteur < len(liste1)-1:
            if element >= liste2[compteur] and liste1[compteur + 1] <= liste2[compteur + 1]:
                cr += 1

            elif element <= liste2[compteur] and liste1[compteur + 1] >= liste2[compteur + 1]:
                cr += 1

        compteur += 1

    return cr


def RSI(donnée_rsi: pandas.DataFrame) -> float:
    """
    Fonction qui prend en argument une dataframe pandas et une durée qui est un entier
    Et renvoie le rsi sous forme d'un float
    """
    # On récupère les données de la colonne close
    data = [float(x) for x in donnée_rsi.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    fl_data = numpy.array(data)

    # On récupère le temps (nombre de données) et on fait -1 car sinon cela ne marche pas (renvoie que des nan)
    # Et on garde le dernier élément que renvoie la fonction (car les autres sont que des nan)
    # Et on le transforme en float

    rsi = float(talib.RSI(fl_data, len(fl_data) - 1)[-1])

    return rsi


def VWAP(donnée_vwap: pandas.DataFrame) -> float:
    """
    Fonction qui prend en argument une dataframe pandas
    Et qui renvoie le vwap sous forme d'une float
    """

    haut = [float(x) for x in donnée_vwap.high.values]
    bas = [float(x) for x in donnée_vwap.low.values]
    fermeture = [float(x) for x in donnée_vwap.close.values]
    volume = [float(x) for x in donnée_vwap.volume.values]

    somme_pr_t_x_volume = 0
    for i in range(len(haut)):
        prix_typique = (haut[i] + bas[i] + fermeture[i])/3
        somme_pr_t_x_volume += prix_typique * volume[i]

    vwap = somme_pr_t_x_volume / sum(volume)

    return vwap


def chaikin_money_flow(donnée_cmf: pandas.DataFrame) -> float:
    """
    Fonction qui prend en argument une dataframe pandas
    Et qui renvoie le cmf sous forme d'un float
    Daily Money Flow = [((Close – Low) – (High – Close)) / (High – Low)] * Volume
    Chaikin Money Flow = 21-Day Average of Daily Money Flow / 21-Day Average of Volume
    """
    moyenne_flow = []
    moyenne_volume = []
    for i in range(len(donnée_cmf)):
        close = float(donnée_cmf.close.values[i])
        low = float(donnée_cmf.low.values[i])
        high = float(donnée_cmf.high.values[i])
        volumme = float(donnée_cmf.volume.values[i])
        numérateur = (close - low) - (high - close)
        dénominateur = (high - low)
        if dénominateur == 0:
            dénominateur = 1
        flow = (numérateur / dénominateur) * volumme
        moyenne_flow.append(flow)
        moyenne_volume.append(volumme)

    result = moyenne(moyenne_flow) / moyenne(moyenne_volume)

    return result


# Fonctions qui renvoient sous forme d'une liste


def SMA(donnée_sma: pandas.DataFrame) -> list:
    """
    Fonction qui prend en argument une dataframe pandas et une durée qui est un entier
    Et renvoie le sma sous forme d'une liste
    """
    # On récupère les données de la colonne close
    data = [float(x) for x in donnée_sma.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    fl_data = numpy.array(data)

    # On récupère le retour de la fonction sma sur les valeurs données
    sma = talib.SMA(fl_data)

    # Et on enlève les nan
    sma = [float(x) for x in sma if math.isnan(x) == False]

    return sma


def EMA(donnée_ema: pandas.DataFrame) -> list:
    """
    Fonction qui prend en argument une dataframe pandas et une durée qui est un entier
    Et renvoie le ema sous forme d'une liste
    """

    # On récupère les données de la colonne close
    data = [float(x) for x in donnée_ema.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    fl_data = numpy.array(data)

    # On récupère le retour de la fonction ema sur les valeurs données
    ema = talib.EMA(fl_data)

    # Et on enlève les nan
    ema = [float(x) for x in ema if math.isnan(x) == False]

    return ema


def MACD(donnée_macd: pandas.DataFrame) -> list:
    """
    Fonction qui prend en argument une dataframe pandas
    Et renvoie le MACD sous forme d'une liste de trois listes
    """

    # On récupère les données de la colonne close
    data = [float(x) for x in donnée_macd.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    fl_data = numpy.array(data)

    # On récupère le retour de la fonction macd sur les valeurs données
    macd, signal, hist = talib.MACD(fl_data)

    # Et on enlève les nan
    macd = [float(x) for x in macd if math.isnan(x) == False]
    signal = [float(x) for x in signal if math.isnan(x) == False]
    hist = [float(x) for x in hist if math.isnan(x) == False]

    return [macd, signal, hist]


def stochRSI(donnée_stochrsi: pandas.DataFrame) -> list:
    """
    Fonction qui prend en argument une dataframe pandas
    Et qui renvoie le stochRSI sous forme de deux listes
    On utilise pas la fonction par défaut stochrsi de talib car 
    celle-ci applique stochf à rsi et non pas stoch à rsi
    """
    # On récupère les données de la colonne close
    data = [float(x) for x in donnée_stochrsi.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    fl_data = numpy.array(data)

    # On récupère le retour de la fonction rsi sur les valeurs données
    rsi = talib.RSI(fl_data)

    # Et on applique stoch dessus
    stochrsi, signal = talib.STOCH(rsi, rsi, rsi)

    # Enfin, on enlève les nan
    stochrsi = [float(x) for x in stochrsi if math.isnan(x) == False]
    signal = [float(x) for x in signal if math.isnan(x) == False]

    return [stochrsi, signal]


def bandes_bollinger(donnée_bandes: pandas.DataFrame) -> list:
    """
    Fonction qui prend en argument une dataframe pandas
    Et qui renvoie les bandes de bollinger sous forme d'une liste de trois listes
    """

    # On récupère les données de la colonne close
    data = [float(x) for x in donnée_bandes.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    fl_data = numpy.array(data)

    # On récupère le retour de la fonction bbands sur les valeurs données
    up, middle, low = talib.BBANDS(fl_data)

    # Et on enlève les nan
    up = [float(x) for x in up if math.isnan(x) == False]
    middle = [float(x) for x in middle if math.isnan(x) == False]
    low = [float(x) for x in low if math.isnan(x) == False]

    return [up, middle, low]


# Fonctions BDD

# Connexion à la bdd et créaton du curseur pour interagire avec
con = sqlite3.connect('data_base.db')

cur = con.cursor()

ls_requete_data = []
ls_requete_rsi = []


def insert_bdd(table: str, symbol: str, data: pandas.DataFrame, empty_list=True, insert_commit=True) -> None:
    """
    Fonction qui prend en argument la table et les données à inserer
    Et insert les données dans la bdd
    Ex param :
    table : data
    symbol : 'BTCEUR' ....
    data : dataframe des données du serveur
    empty_list : vide les listes (par défaut activer, désactiver si insertion de nombreuses données comme au lancement par ex)
    insert_commit : True ou false (par défaut, con.commit() est executé)
    """
    # Vidage des listes avant l'execution des autres parties de la fonction
    if empty_list == True:
        ls_requete_data.clear()
        ls_requete_rsi.clear()

    # Insertion normale des valeurs dans la table data
    # On transforme en str qu'au dernier moment car la liste
    # Est utilisé lors de l'insertion des données dans la bdd au lancement
    if table == "data":
        ls = [str(SMA(data)), str(EMA(data)), str(MACD(data)), str(stochRSI(data)), str(bandes_bollinger(
            data)), float(data.close.values[-1])]

        ls_requete_data.append(ls)

        if insert_commit == True:
            cur.executemany(
                "insert into data (sma, ema, macd, stochrsi, bande_bollinger, prix_fermeture) values (?,?,?,?,?,?)", ls_requete_data)

            con.commit()

    # Insertion normale des valeurs dans la table rsi____
    elif table == "rsi_vwap_cmf":
        ls = [RSI(data), VWAP(data), chaikin_money_flow(
            data), float(data.close.values[-1])]

        ls_requete_rsi.append(ls)

        if insert_commit == True:
            cur.executemany(
                "insert into rsi_vwap_cmf (rsi, vwap, cmf, prix_fermeture) values (?,?,?,?)", ls_requete_rsi)

            con.commit()


def insert_data_historique_bdd(symbol: str) -> None:
    """
    Fonction qui permet de charger les x dernières minutes/heures (avec un espace de x min/heure pour chaque jeux de données)
    Dans la base de donnée
    Ex param :
    symbol : 'BTCEUR'
    """
    # On enlève tout dans la bdd
    bdd_data()
    bdd_rsi_vwap_cmf()

    # A chaque tour de boucle, on récupère les données sur une durée précise
    # Et on vient appliquer toutes les fonctions dessus pour ensuite rentrer les données dans la bdd
    def data(symbol: str) -> None:

        for i in range(3600, 40*15, -15):

            data = donnée_bis(symbol, f"{i} min ago UTC",
                              f"{i - 40*15} min ago UTC", 40, client2)

            if i == 615:
                insert_bdd("data", symbol, data, False)
            else:
                insert_bdd("data", symbol, data, False, False)

    def data2(symbol: str) -> None:

        for i in range(3225, 15*15, -15):

            data = donnée_bis(symbol, f"{i} min ago UTC",
                              f"{i - 15*15} min ago UTC", 15, client3)

            if i == 240:
                insert_bdd("rsi_vwap_cmf", symbol, data, False)
            else:
                insert_bdd("rsi_vwap_cmf", symbol, data, False, False)

    p1 = Process(target=data, args=(symbol,))
    p2 = Process(target=data2, args=(symbol, ))

    p1.daemon = True
    p2.daemon = True

    p1.start()
    p2.start()

    p1.join()
    p2.join()


def select_donnée_bdd() -> (pandas.DataFrame, pandas.DataFrame):
    """
    Fonction qui récupère toutes les données de la bdd
    Renvoie toutes les données et les prix sous forme de dataframe
    Première dataframe : toutes les données
    Deuxième dataframe : les prix
    """
    donnée_bdd = cur.execute("""
    SELECT data.sma, data.ema, data.macd, data.stochrsi, data.bande_bollinger, rsi_vwap_cmf.rsi,
    rsi_vwap_cmf.vwap, rsi_vwap_cmf.cmf
    FROM data
    INNER JOIN rsi_vwap_cmf ON rsi_vwap_cmf.id = data.id
    """).fetchall()

    prix = cur.execute("""
    SELECT prix_fermeture FROM data
    """).fetchall()

    prix = pandas.DataFrame([x[0] for x in prix])

    # On vient retransformer les données dans leur état d'origine
    # Et on remet le tout dans une dataframe
    donnée_dataframe = []
    for row in donnée_bdd:
        temp = []
        cpt = 1
        for element in row:
            if cpt <= 2:
                elt = ast.literal_eval(str(element))
                for nb in elt:
                    temp.append(nb)
            elif cpt <= 5:
                elt = ast.literal_eval(str(element))
                for liste in elt:
                    for nb in liste:
                        temp.append(nb)
            else:
                temp.append(float(element))
            cpt += 1

        donnée_dataframe.append(temp)

    dp = pandas.DataFrame(donnée_dataframe)

    return (dp, prix)


# Fonctions de prédiction

def prédiction(donnée_serveur_data: pandas.DataFrame, donnée_serveur_rsi: pandas.DataFrame) -> float:
    """
    Fonction qui prédit le future prix de la crypto
    """
    X, y = select_donnée_bdd()

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
