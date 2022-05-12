from multiprocessing import Process
from indices_techniques import *
from données_serveur import *
import sqlite3
import ast


# création de la base DB
connexion = sqlite3.connect("data_base.db")
# création du curseur
curseur = connexion.cursor()


def bdd_data():
    curseur.execute("DROP TABLE IF EXISTS data")
    curseur.execute("""
    CREATE TABLE data 
    (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sma TEXT, 
    ema TEXT,
    evening_star TEXT,
    harami TEXT,
    doji TEXT,
    adx TEXT,
    kama TEXT,
    t3 TEXT,
    trima TEXT,
    ppo TEXT,
    u_oscilator TEXT,
    macd TEXT,
    stochrsi TEXT, 
    bande_bollinger TEXT,
    prix_fermeture REAL
    )
    """)

    connexion.commit()


def bdd_rsi_vwap_cmf():
    curseur.execute("DROP TABLE IF EXISTS rsi_vwap_cmf")
    curseur.execute("""
    CREATE TABLE rsi_vwap_cmf 
    (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rsi REAL,
    vwap REAL,
    cmf REAL,
    cci REAL,
    mfi REAL,
    linearregression REAL,
    tsf REAL,
    a_oscilator REAL,
    w_r REAL,
    roc TEXT,
    obv TEXT,
    mom TEXT,
    prix_fermeture REAL
    )
    """)

    connexion.commit()

# Fonctions BDD

# Connexion à la bdd et créaton du curseur pour interagire avec


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
    insert_commit : True ou false (par défaut, connexion.commit() est executé)
    """
    # Vidage des listes avant l'execution des autres parties de la fonction
    if empty_list == True:
        ls_requete_data.clear()
        ls_requete_rsi.clear()

    # Insertion normale des valeurs dans la table data
    # On transforme en str qu'au dernier moment car la liste
    # Est utilisé lors de l'insertion des données dans la bdd au lancement
    if table == "data":
        ls = [str(SMA(data)), str(EMA(data)), str(evening_star(data)), str(harami(data)),
              str(doji(data)), str(ADX(data)), str(
                  KAMA(data)), str(T3(data)), str(TRIMA(data)),
              str(PPO(data)), str(ultimate_oscilator(data)),
              str(MACD(data)), str(stochRSI(data)), str(bandes_bollinger(
                  data)), float(data.close.values[-1])]

        ls_requete_data.append(ls)

        if insert_commit == True:
            curseur.executemany("""
            insert into data (sma, ema, evening_star, harami,
            doji, adx, kama, t3, trima, ppo, u_oscilator,
            macd, stochrsi, bande_bollinger, prix_fermeture) 
            values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, ls_requete_data)

            connexion.commit()

    # Insertion normale des valeurs dans la table rsi____
    elif table == "rsi_vwap_cmf":
        ls = [RSI(data), VWAP(data), chaikin_money_flow(
            data), CCI(data), MFI(data), LinearRegression(
            data), TSF(data), aroon_oscilator(data), williams_R(
            data), str(ROC(data)), str(OBV(data)), str(MOM(data)), float(data.close.values[-1])]

        ls_requete_rsi.append(ls)

        if insert_commit == True:
            curseur.executemany("""
            insert into rsi_vwap_cmf 
            (rsi, vwap, cmf, cci, mfi, linearregression,
            tsf, a_oscilator, w_r, roc, obv, mom, prix_fermeture) 
            values (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, ls_requete_rsi)

            connexion.commit()


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

        for i in range(15600, 40*15, -15):

            data = donnée_bis(symbol, f"{i} min ago UTC",
                              f"{i - 40*15} min ago UTC", 40, client2)

            if i == 615:
                insert_bdd("data", symbol, data, False)
            else:
                insert_bdd("data", symbol, data, False, False)

    def data2(symbol: str) -> None:

        for i in range(15225, 15*15, -15):

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


def select_donnée_bdd(df_numpy: str) -> [pandas.DataFrame, pandas.DataFrame] or [numpy.array, numpy.array]:
    """
    Fonction qui récupère toutes les données de la bdd
    Renvoie toutes les données et les prix sous forme de dataframe
    Première dataframe : toutes les données
    Deuxième dataframe : les prix
    Ex param :
    df_numpy : dataframe ou numpy
    """
    donnée_bdd = curseur.execute("""
    SELECT data.sma, data.ema, data.evening_star, data.harami, data.doji, 
    data.adx, data.kama, data.t3, data.trima, data.ppo, data.u_oscilator,
    data.macd, data.stochrsi, data.bande_bollinger, 
    rsi_vwap_cmf.rsi, rsi_vwap_cmf.vwap, rsi_vwap_cmf.cmf,
    rsi_vwap_cmf.cci, rsi_vwap_cmf.mfi, rsi_vwap_cmf.linearregression,
    rsi_vwap_cmf.tsf, rsi_vwap_cmf.a_oscilator, rsi_vwap_cmf.w_r,
    rsi_vwap_cmf.roc, rsi_vwap_cmf.obv, rsi_vwap_cmf.mom
    FROM data
    INNER JOIN rsi_vwap_cmf ON rsi_vwap_cmf.id = data.id
    """).fetchall()

    prix = curseur.execute("""
    SELECT prix_fermeture FROM data
    """).fetchall()

    prix = [x[0] for x in prix]

    # On vient retransformer les données dans leur état d'origine
    # Et on remet le tout dans une dataframe
    donnée_dataframe = []
    for row in donnée_bdd:
        temp = []
        cpt = 1
        for element in row:
            if cpt <= 11 or cpt >= 24:
                elt = ast.literal_eval(str(element))
                for nb in elt:
                    temp.append(nb)
            elif cpt <= 14:
                elt = ast.literal_eval(str(element))
                for liste in elt:
                    for nb in liste:
                        temp.append(nb)
            elif cpt <= 23:
                temp.append(float(element))

            cpt += 1

        donnée_dataframe.append(temp)

    if df_numpy == "dataframe":
        dp = pandas.DataFrame(donnée_dataframe)
        prix_df = pandas.DataFrame(prix)
        return [dp, prix_df]

    elif df_numpy == "numpy":
        np = numpy.array(donnée_dataframe)
        prix_np = numpy.array(prix)

        return [np, prix_np]


if __name__ == "__main__":
    bdd_data()
    bdd_rsi_vwap_cmf()
