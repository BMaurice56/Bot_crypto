"""
import matplotlib.pyplot as plt
from datetime import datetime


symbol = 'BTCEUR'
interval = client.KLINE_INTERVAL_15MINUTE
fin = "0 min ago UTC"

data = donnée(symbol, interval, "30000 min ago UTC", fin, 2000)
#data = select_data_bdd()


close = data.close.values

for i in range(len(close)):
    close[i] = float(close[i])


minimum = float('inf')
maximum = float('-inf')

indice_min = 0
indice_max = 0

for i in range(1, len(close) - 1):
    if close[i-1] > close[i] and close[i] < close[i+1] and minimum > close[i]:
        minimum = close[i]
        indice_min = i
    elif close[i-1] < close[i] and close[i] > close[i+1] and maximum < close[i]:
        maximum = close[i]
        indice_max = i

ratio_desc = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
ratio_asc = ratio_desc.copy()
ratio_asc.reverse()

diff = maximum - minimum

ls = []
if indice_max > indice_min:
    for elt in ratio_asc:
        ls.append(minimum + (diff * elt))
else:
    for elt in ratio_desc:
        ls.append(maximum - (diff * elt))
couleurs = ["black","r","g","b","cyan","magenta","yellow", "black"]
cpt = 0
for element in ls:
    plt.hlines(element, 2, len(close), couleurs[cpt], "dashed", f"{ratio_asc[cpt] * 100}")
    cpt += 1

plt.plot(close)
plt.scatter(indice_min, minimum)
plt.scatter(indice_max, maximum)
plt.show()

"""
from main import *

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
    if table == "data":
        ls = [SMA(data), EMA(data), MACD(data), stochRSI(data), bandes_bollinger(
            data), float(data.close.values[-1])]

        ls_requete_data.append(ls)

        if insert_commit == True:
            liste = ls_requete_data.copy()
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

        if ls_requete_predic_data == []:
            ls_requete_predic_data.append([my_liste, None])
        else:
            ls_requete_predic_data[len(ls_requete_predic_data) -
                                   1][1] = float(data.close.values[-1])
            ls_requete_predic_data.append([my_liste, None])

        if insert_commit == True:

            data_serveur = donnée_bis(
                symbol, "600 min ago UTC", "0 min ago UTC", 40, client2)

            ls_requete_predic_data[-1][1] = float(
                data_serveur.close.values[-1])

            cur.executemany(
                "insert into prédiction_data (prix_prédiction, prix_fermeture) values (?,?)", ls_requete_predic_data)

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

    # Calcul des prédictions qui peuvent etre fait sur la table rsi______
    # On fait la moyenne des trois valeurs de la fonction de prédiction et on l'insert dans la bdd
    elif table == "prédiction_rsi_vwap_cmf":

        dataframe_temp = pandas.DataFrame(ls_requete_rsi)
        dataframe_temp.columns = ['RSI', 'VWAP', 'CMF', 'PRIX_FERMETURE']

        predic1 = prediction_rsi_wvap_cmf(dataframe_temp, data)

        my_liste = moyenne(predic1)

        if ls_requete_predic_rsi == []:
            ls_requete_predic_rsi.append([my_liste, None])
        else:
            ls_requete_predic_rsi[len(ls_requete_predic_rsi) -
                                  1][1] = float(data.close.values[-1])
            ls_requete_predic_rsi.append([my_liste, None])

        if insert_commit == True:
            data_serveur = donnée_bis(
                symbol, "225 min ago UTC", "0 min ago UTC", 15, client3)

            ls_requete_predic_rsi[-1][1] = float(data_serveur.close.values[-1])

            cur.executemany(
                "insert into prédiction_rsi (prix_prédiction, prix_fermeture) values (?,?)", ls_requete_predic_rsi)

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
            "insert into prédiction (prix_prédiction, prix_fermeture) values (?,?)", data)

        con.commit()

    elif table == "simple_insert_predic_rsi":
        cur.execute(
            "insert into prédiction (prix_prédiction, prix_fermeture) values (?,?)", data)
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
        for i in range(2100, 40*15, -15):

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
        for i in range(1725, 15*15, -15):

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


t1 = perf_counter()

insert_data_historique_bdd('BTCEUR')

t2 = perf_counter()

print(t2 - t1)
