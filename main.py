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

ls_requete_predic_data = []
ls_requete_predic_rsi = []


def insert_bdd(table: str, symbol: str, data: pandas.DataFrame or list, empty_list=True, insert_commit=True) -> None:
    """
    Fonction qui prend en argument la table et les données à inserer
    Et insert les données dans la bdd
    Ex param :
    table : data
    symbol : 'BTCEUR' ....
    data : dataframe des données du serveur ou une liste
    empty_list : vide les listes (par défaut activer, désactiver si insertion de nombreuses données comme au lancement par ex)
    insert_commit : True ou false (par défaut, con.commit() est executé)
    """
    # Vidage des listes avant l'execution des autres parties de la fonction
    if empty_list == True:
        ls_requete_data.clear()
        ls_requete_rsi.clear()

        ls_requete_predic_data.clear()
        ls_requete_predic_rsi.clear()

    # Insertion normale des valeurs dans la table data
    # On transforme en str qu'au dernier moment car la liste
    # Est utilisé lors de l'insertion des données dans la bdd au lancement
    if table == "data":
        ls = [SMA(data), EMA(data), MACD(data), stochRSI(data), bandes_bollinger(
            data), float(data.close.values[-1])]

        ls_requete_data.append(ls)

        if insert_commit == True:
            liste = copy.deepcopy(ls_requete_data)
            for rq in liste:
                rq[0] = str(rq[0])
                rq[1] = str(rq[1])
                rq[2] = str(rq[2])
                rq[3] = str(rq[3])
                rq[4] = str(rq[4])
                cur.execute(
                    "insert into data (sma, ema, macd, stochrsi, bande_bollinger, prix_fermeture) values (?,?,?,?,?,?)", rq)

            con.commit()

    # Calcul des prédictions qui peuvent etre fait sur la table data
    # On fait la moyenne et on l'insert dans la bdd
    elif table == "prédiction_data":
        # On transforme en dataframe car c'est ce que prend les fonctions de prédiction
        dataframe_temp = pandas.DataFrame(ls_requete_data)

        dataframe_temp.columns = ['SMA', 'EMA', 'MACD', 'STOCHRSI',
                                  'BB', 'PRIX_FERMETURE']

        predic2 = prediction_liste_sma_ema(dataframe_temp, data)
        predic3 = prediction_liste_macd(dataframe_temp, data)
        predic4 = prediction_liste_stochrsi(dataframe_temp, data)
        predic5 = prediction_liste_bandes_b(dataframe_temp, data)

        ls = []

        for elt in predic2:
            ls.append(elt)
        for elt in predic3:
            ls.append(elt)
        for elt in predic4:
            ls.append(elt)
        for elt in predic5:
            ls.append(elt)

        my_liste = moyenne(ls)

        # On enregistre en décalé car d'abord on enregistre la moyenne des prédictions
        # Puis on enregistre le prix réel passé les 15 minutes
        if ls_requete_predic_data == []:
            ls_requete_predic_data.append([my_liste, None])
        else:
            ls_requete_predic_data[len(ls_requete_predic_data) -
                                   1][1] = float(data.close.values[-1])
            ls_requete_predic_data.append([my_liste, None])

        # A la fin, on récupère le prix réel final, on le met dans la liste
        # Et on insert le tout dans la bdd
        if insert_commit == True:

            data_serveur = donnée_bis(
                symbol, "600 min ago UTC", "0 min ago UTC", 40, client2)

            ls_requete_predic_data[-1][1] = float(
                data_serveur.close.values[-1])

            cur.executemany(
                "insert into predic_data (prix_prédiction, prix_fermeture) values (?,?)", ls_requete_predic_data)

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

    # Calcul des prédictions qui peuvent être fait sur la table rsi______
    # On fait la moyenne des trois valeurs de la fonction de prédiction et on l'insert dans la bdd
    elif table == "prédiction_rsi_vwap_cmf":
        # On transforme en dataframe car c'est ce que prend les fonctions de prédiction
        dataframe_temp = pandas.DataFrame(ls_requete_rsi)
        dataframe_temp.columns = ['RSI', 'VWAP', 'CMF', 'PRIX_FERMETURE']

        predic1 = prediction_rsi_wvap_cmf(dataframe_temp, data)

        my_liste = moyenne(predic1)

        # On enregistre en décalé car d'abord on enregistre la moyenne des prédictions
        # Puis on enregistre le prix réel passé les 15 minutes
        if ls_requete_predic_rsi == []:
            ls_requete_predic_rsi.append([my_liste, None])
        else:
            ls_requete_predic_rsi[len(ls_requete_predic_rsi) -
                                  1][1] = float(data.close.values[-1])
            ls_requete_predic_rsi.append([my_liste, None])

        # A la fin, on récupère le prix réel final, on le met dans la liste
        # Et on insert le tout dans la bdd
        if insert_commit == True:
            data_serveur = donnée_bis(
                symbol, "225 min ago UTC", "0 min ago UTC", 15, client3)

            ls_requete_predic_rsi[-1][1] = float(data_serveur.close.values[-1])

            cur.executemany(
                "insert into predic_rsi (prix_prédiction, prix_fermeture) values (?,?)", ls_requete_predic_rsi)

            con.commit()

    # Insertion de tous les résultats dans la bdd
    elif table == "résultat":
        requete = "insert into résultat (moyenne_prédiction, prédiction_rsi, prédiction_vwap, prédiction_cmf," + \
            " prédiction_sma, prédiction_ema, prédiction_macd1, prédiction_macd2," + \
            " prédiction_macd3, prédiction_stochrsi1, prédiction_stochrsi2, prédiction_bb1, prédiction_bb2, prédiction_bb3, prédiction_historique, prix_final)" + \
            " values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        cur.execute(requete, data)

        con.commit()

    # Insertion des prédictions déja faite dans les tables prédiction_etc...
    elif table == "simple_insert_predic_data":
        cur.execute(
            "insert into predic_data (prix_prédiction, prix_fermeture) values (?,?)", data)

        con.commit()

    elif table == "simple_insert_predic_rsi":
        cur.execute(
            "insert into predic_rsi (prix_prédiction, prix_fermeture) values (?,?)", data)

        con.commit()
    #########################################################


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
        cpt = 0
        for i in range(3600, 40*15, -15):

            data = donnée_bis(symbol, f"{i} min ago UTC",
                              f"{i - 40*15} min ago UTC", 40, client2)

            if i == 615:
                insert_bdd("data", symbol, data, False)
            else:
                insert_bdd("data", symbol, data, False, False)

            # Calcul des prédictions
            if cpt >= 20:
                if i == 615:
                    insert_bdd("prédiction_data", symbol, data, False)
                else:
                    insert_bdd("prédiction_data", symbol, data, False, False)

            cpt += 1

    def data2(symbol: str) -> None:
        cpt = 0
        for i in range(3225, 15*15, -15):

            data = donnée_bis(symbol, f"{i} min ago UTC",
                              f"{i - 15*15} min ago UTC", 15, client3)

            if i == 240:
                insert_bdd("rsi_vwap_cmf", symbol, data, False)
            else:
                insert_bdd("rsi_vwap_cmf", symbol, data, False, False)

            # Calcul des prédictions
            if cpt >= 20:
                if i == 240:
                    insert_bdd("prédiction_rsi_vwap_cmf", symbol, data, False)
                else:
                    insert_bdd("prédiction_rsi_vwap_cmf",
                               symbol, data, False, False)

            cpt += 1

    p1 = Process(target=data, args=(symbol,))
    p2 = Process(target=data2, args=(symbol, ))

    p1.daemon = True
    p2.daemon = True

    p1.start()
    p2.start()

    p1.join()
    p2.join()


def select_data_bdd() -> pandas.DataFrame:
    """
    Fonction qui récupère toutes les données de la bdd de la table data
    """
    donnée_bdd = cur.execute("SELECT * FROM data")

    # On vient retransformer les données dans leut état d'origine
    # Et on remet le tout dans une dataframe
    donnée_dataframe = []
    for row in donnée_bdd:
        temp = []
        cpt = 0
        for element in row:
            if cpt == 0:
                temp.append(int(element))
            elif cpt == 6:
                temp.append(float(element))
            else:
                elt = ast.literal_eval(str(element))
                temp.append(elt)
            cpt += 1

        donnée_dataframe.append(temp)

    dp = pandas.DataFrame(donnée_dataframe)

    dp.columns = ['ID', 'SMA', 'EMA', 'MACD', 'STOCHRSI',
                  'BB', 'PRIX_FERMETURE']

    return dp


def select_rsi_vwap_cmf_bdd() -> pandas.DataFrame:
    """
    Fonction qui récupère toutes les données de la bdd de la table rsi_vwap_cmf
    """
    donnée_bdd = cur.execute("SELECT * FROM rsi_vwap_cmf")

    # On vient retransformer les données dans leut état d'origine
    # Et on remet le tout dans une dataframe
    donnée_dataframe = []
    for row in donnée_bdd:
        temp = []
        cpt = 0
        for element in row:
            if cpt == 0:
                temp.append(int(element))
            else:
                temp.append(float(element))
            cpt += 1

        donnée_dataframe.append(temp)

    dp = pandas.DataFrame(donnée_dataframe)

    dp.columns = ['ID', 'RSI', 'VWAP', 'CMF', 'PRIX_FERMETURE']

    return dp


def select_prediction_hist_all() -> pandas.DataFrame:
    """
    Fonction qui renvoie les predictions faites sur les valeurs antérieurs
    Dans la table data, ce sont la moyenne des predictions faites sur les valeurs qui la compose
    Et dans la table rsi_etc..., c'est la moyenne des trois valeurs de la fonction prediction
    Et renvoie le tout sous forme d'une dataframe pandas
    """
    # Liaison par un inner join obligatoire car cela créait des couples de valeurs*
    # Chaque valeur dans la première table était couplé avec chacune des autres valeurs de l'autre table
    # Lors d'un select, au départ il y a 80 données dans chacune des deux tables et donc cela donnait 80x80 = 6400 couples
    predic = cur.execute(
        """SELECT predic_data.prix_prédiction, predic_rsi.prix_prédiction, predic_data.prix_fermeture
    FROM predic_data
    INNER JOIN predic_rsi ON predic_data.id = predic_rsi.id
    """)

    ls = []

    for row in predic:
        ls.append([row[0], row[1], row[2]])

    df = pandas.DataFrame(ls)
    df.columns = ['PRIX_DATA', 'PRIX_RSI', 'PRIX_F']

    return df


# Fonctions de prédiction


def prediction_rsi_wvap_cmf(donnée_bdd: pandas.DataFrame, data: pandas.DataFrame) -> (float, float, float):
    """
    Fonction qui prend en arguement une dataframe pandas des données de la base de donnée
    Ainsi que les dernieres données du serveur
    Et renvoie une prédiction (avec le rsi et le vwap) 
    Ex param :
    donnée_bdd : donnée de la bdd ancienne (sous forme d'une dataframe pandas)
    data : dernières données du serveur (sous forme d'une dataframe pandas)
    """

    # On transforme les données en une liste puis on remet de nouveau dans une dataframe
    # Comme ça, il n'y a pas de nom de colonne et donc pas d'erreur
    df_rsi_bdd = pandas.DataFrame(list(donnée_bdd['RSI']), dtype=float)
    df_vwap_bdd = pandas.DataFrame(list(donnée_bdd['VWAP']), dtype=float)
    df_cmf_bdd = pandas.DataFrame(list(donnée_bdd['CMF']), dtype=float)
    y = donnée_bdd['PRIX_FERMETURE']

    # On crée le module linéaire
    regr = linear_model.LinearRegression()
    regr2 = linear_model.LinearRegression()
    regr3 = linear_model.LinearRegression()

    # On lui donne les données en argument de la bdd et on les fit avec les prix de fermeture
    regr.fit(df_rsi_bdd, y)
    regr2.fit(df_vwap_bdd, y)
    regr3.fit(df_cmf_bdd, y)

    # On calcul les deux indices qu'on met dans une liste pour qu'ils puissent être transformer en dataframe pandas
    rsi = pandas.DataFrame([RSI(data)])
    vwap = pandas.DataFrame([VWAP(data)])
    cmf = pandas.DataFrame([chaikin_money_flow(data)])

    # Et enfin on prédit la potentiel valeur de la crypto
    predic = regr.predict(rsi)
    predic2 = regr2.predict(vwap)
    predic3 = regr3.predict(cmf)

    return float(predic[0]), float(predic2[0]), float(predic3[0])


def prediction_liste_sma_ema(donnée_bdd: pandas.DataFrame, data: pandas.DataFrame) -> (float, float):
    """
    Fonction qui prend en arguement une dataframe pandas des données de la base de donnée
    Ainsi que les dernieres données du serveur
    Et renvoie une prédiction (avec le sma et le ema) 
    Ex param :
    donnée_bdd : donnée de la bdd ancienne (sous forme d'une dataframe pandas)
    data : dernières données du serveur (sous forme d'une dataframe pandas)
    """

    # Comme les données sont sous forme d'une liste à chaque fois
    # On dispatch chaque valeur de la liste dans une colonne
    # Et on revient recréer la dataframe avec les valeurs dans les colonnes
    df_bdd_sma = pandas.DataFrame(list(donnée_bdd['SMA']), dtype=float)
    df_bdd_ema = pandas.DataFrame(list(donnée_bdd['EMA']), dtype=float)

    y = donnée_bdd['PRIX_FERMETURE']

    # On calcul le sma et le ema et on met les valeurs de la liste dans chaque colonnes d'une dataframe
    sma = [SMA(data)]
    df_sma = pandas.DataFrame(sma)

    ema = [EMA(data)]
    df_ema = pandas.DataFrame(ema)

    # On crée le module linéaire pour le sma et le ema
    regr = linear_model.LinearRegression()
    regr2 = linear_model.LinearRegression()

    # On lui fit les données de la bdd et les prix de fermeture
    regr.fit(df_bdd_sma, y)
    regr2.fit(df_bdd_ema, y)

    # Et enfin on prédit la potentiel valeur de la crypto
    predic = regr.predict(df_sma)
    predic2 = regr2.predict(df_ema)

    return float(predic[0]), float(predic2[0])


def prediction_liste_macd(donnée_bdd: pandas.DataFrame, data: pandas.DataFrame) -> (float, float, float):
    """
    Fonction qui prend en arguement une dataframe pandas des données de la base de donnée
    Ainsi que les dernieres données du serveur
    Et renvoie une prédiction (avec le macd) 
    Ex param :
    donnée_bdd : donnée de la bdd ancienne (sous forme d'une dataframe pandas)
    data : dernières données du serveur (sous forme d'une dataframe pandas)
    """
    # On récupère toutes les valeurs de la bdd
    # Puis on sépare chaque listes entre elles
    # Et enfin on vient créer une dataframe pour chaque
    all_valeur = list(donnée_bdd['MACD'])
    macd_bdd = []
    signal_bdd = []
    hist_bdd = []
    for element in all_valeur:
        macd_bdd.append(element[0])
        signal_bdd.append(element[1])
        hist_bdd.append(element[2])

    # Chaques valeurs des listes de chaque liste seront dispatchées dans une colonne chacune
    df_bdd_macd = pandas.DataFrame(macd_bdd, dtype=float)
    df_bdd_signal = pandas.DataFrame(signal_bdd, dtype=float)
    df_bdd_hist = pandas.DataFrame(hist_bdd, dtype=float)

    # On récupère les prix de fermeture
    y = donnée_bdd['PRIX_FERMETURE']

    # On calcul le macd et on sépare les trois données en trois variables
    macd, signal, hist = MACD(data)

    # Puis on vient les transformer en dataframe
    df_macd = pandas.DataFrame([macd])
    df_signal = pandas.DataFrame([signal])
    df_hist = pandas.DataFrame([hist])

    # Et enfin on vient prédire les valeurs
    regr = linear_model.LinearRegression()
    regr2 = linear_model.LinearRegression()
    regr3 = linear_model.LinearRegression()

    # On lui fit les données de la bdd et les prix de fermeture
    regr.fit(df_bdd_macd, y)
    regr2.fit(df_bdd_signal, y)
    regr3.fit(df_bdd_hist, y)

    # Et enfin on prédit la potentiel valeur de la crypto
    predic = regr.predict(df_macd)
    predic2 = regr2.predict(df_signal)
    predic3 = regr.predict(df_hist)

    return float(predic[0]), float(predic2[0]), float(predic3[0])


def prediction_liste_stochrsi(donnée_bdd: pandas.DataFrame, data: pandas.DataFrame) -> (float, float):
    """
    Fonction qui prend en arguement une dataframe pandas des données de la base de donnée
    Ainsi que les dernieres données du serveur
    Et renvoie une prédiction (avec le stochrsi) 
    Ex param :
    donnée_bdd : donnée de la bdd ancienne (sous forme d'une dataframe pandas)
    data : dernières données du serveur (sous forme d'une dataframe pandas)
    """
    # On récupère toutes les valeurs de la bdd
    # Puis on sépare chaque listes entre elles
    # Et enfin on vient créer une dataframe pour chaque
    all_data = list(donnée_bdd['STOCHRSI'])
    ligne1_bdd = []
    ligne2_bdd = []
    for element in all_data:
        ligne1_bdd.append(element[0])
        ligne2_bdd.append(element[1])

    # On récupère les prix de fermeture
    y = donnée_bdd['PRIX_FERMETURE']

    # Chaques valeurs des listes de chaque liste seront dispatchées dans une colonne chacune
    df_bdd_ligne1 = pandas.DataFrame(ligne1_bdd)
    df_bdd_ligne2 = pandas.DataFrame(ligne2_bdd)

    # On vient créer les modules de prédiction
    regr = linear_model.LinearRegression()
    regr2 = linear_model.LinearRegression()

    # On lui fit les données de la bdd et les prix de fermeture
    regr.fit(df_bdd_ligne1, y)
    regr2.fit(df_bdd_ligne2, y)

    # On calcul le stochrsi et on sépare les deux données en deux variables
    ligne1, ligne2 = stochRSI(data)

    # Puis on vient les transformer en dataframe
    df_ligne1 = pandas.DataFrame([ligne1])
    df_ligne2 = pandas.DataFrame([ligne2])

    # Et enfin on vient prédire les valeurs
    predic = regr.predict(df_ligne1)
    predic2 = regr2.predict(df_ligne2)

    return float(predic[0]), float(predic2[0])


def prediction_liste_bandes_b(donnée_bdd: pandas.DataFrame, data: pandas.DataFrame) -> (float, float, float):
    """
    Fonction qui prend en arguement une dataframe pandas des données de la base de donnée
    Ainsi que les dernieres données du serveur
    Et renvoie une prédiction (avec les bandas de bollinger) 
    Ex param :
    donnée_bdd : donnée de la bdd ancienne (sous forme d'une dataframe pandas)
    data : dernières données du serveur (sous forme d'une dataframe pandas)
    """
    # On récupère toutes les valeurs de la bdd
    # Puis on sépare chaque listes entre elles
    # Et enfin on vient créer une dataframe pour chaque
    all_data = list(donnée_bdd['BB'])
    up_bdd = []
    middle_bdd = []
    low_bdd = []
    for element in all_data:
        up_bdd.append(element[0])
        middle_bdd.append(element[1])
        low_bdd.append(element[2])

    # Chaques valeurs des listes de chaque liste seront dispatchées dans une colonne chacune
    df_bdd_up = pandas.DataFrame(up_bdd, dtype=float)
    df_bdd_middle = pandas.DataFrame(middle_bdd, dtype=float)
    df_bdd_low = pandas.DataFrame(low_bdd, dtype=float)

    # On récupère les prix de fermeture
    y = donnée_bdd['PRIX_FERMETURE']

    # On vient créer les modules de prédiction
    regr = linear_model.LinearRegression()
    regr2 = linear_model.LinearRegression()
    regr3 = linear_model.LinearRegression()

    # On lui fit les données de la bdd et les prix de fermeture
    regr.fit(df_bdd_up, y)
    regr2.fit(df_bdd_middle, y)
    regr3.fit(df_bdd_low, y)

    # On calcul les bb et on sépare les trois données en trois variables
    up, middle, low = bandes_bollinger(data)

    # Puis on vient les transformer en dataframe
    df_up = pandas.DataFrame([up])
    df_middle = pandas.DataFrame([middle])
    df_low = pandas.DataFrame([low])

    # Et enfin on vient prédire les valeurs
    predic = regr.predict(df_up)
    predic2 = regr2.predict(df_middle)
    predic3 = regr3.predict(df_low)

    return float(predic[0]), float(predic2[0]), float(predic3[0])


def prediction_historique(donnée_bdd: pandas.DataFrame, moyenne_predic: list) -> float:
    """
    Fonction qui prend en argument les données des prédictions de la bdd
    Et une liste composé de la moyenne des predic de data et de la predic du rsi____
    Et renvoie la prédiction des prédic de l'historique
    La fonctions calcul le prix potentiel par rapport au prédiction faite par les autres fonctions de prediction
    Ex param :
    donnée_bdd : données des prédiction historique
    moyenne_prédic : [moyenne des prédictions de la table data, moyenne des prédictions de la fonctions de prédic rsi]
    """
    # On récupère les données qu'on transforme en liste
    prix_data = list(donnée_bdd['PRIX_DATA'])
    prix_rsi = list(donnée_bdd['PRIX_RSI'])

    # On  vient les aujouter deux à deux dans une liste pou rensuite recréer une dataframe pandas sans nom de colonne
    predic = []

    for i in range(len(prix_data)):
        predic.append([prix_data[i], prix_rsi[i]])

    predic = pandas.DataFrame(predic)

    # Après on créer le module, on lui fit les données et on prédit la prix de la crypto
    y = donnée_bdd['PRIX_F']

    regr = linear_model.LinearRegression()

    regr.fit(predic, y)

    prediction = regr.predict([moyenne_predic])

    return float(prediction[0])


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
