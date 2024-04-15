from technical_indicators import *
from server_data import *
from functools import wraps
import sqlite3


def get_db(f):
    """
    Créer la connexion avec la base de donnée
    """

    @wraps(f)
    def connexion(*args, **kwargs):
        # création de la base DB
        con = sqlite3.connect("data_base.db")
        # création du curseur
        cur = con.cursor()
        return f(curseur=cur, connexion=con, *args, **kwargs)

    return connexion


@get_db
def bdd_data(curseur, connexion):
    curseur.execute("DROP TABLE IF EXISTS data")
    curseur.execute("""
    CREATE TABLE data 
    (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sma TEXT, 
    ema TEXT,
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


@get_db
def bdd_rsi_vwap_cmf(curseur, connexion):
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


@get_db
def insert_data_historique_bdd(symbol: str, number_data: int, curseur, connexion) -> None:
    """
    Permet de charger les x dernières minutes/heures (avec un espace de x min/heure pour chaque jeu de données)
    Dans la base de donnée

    Ex params :
    symbol : 'BTC'
    number_data : 1000
    """
    # On enlève tout dans la bdd
    bdd_data()
    bdd_rsi_vwap_cmf()

    # On récupère toutes les données en 1 seule requête (car sinon beaucoup trop long)
    # Puis on vient itérer sur ces données

    binance = Binance(symbol)

    data_server = binance.data(f"{number_data} day ago UTC", "0 day ago UTC")

    print("Données reçus")
    print(f"Taille des données : {len(data_server)}")

    liste_data = []
    liste_rsi = []

    middle = (len(data_server) - 40) // 2
    middle_first = middle // 2
    middle_third = middle + middle_first

    for i in range(0, len(data_server) - 40):
        data = data_server[i:i + 40]

        # Calcul les indices techniques + ajout du prix
        ls = list(calcul_indice_40_donnees(data) + [float(data.close.values[-1])])

        # Transformation en string des sous-listes
        for j in range(len(ls) - 1):
            ls[j] = str(ls[j])

        liste_data.append(ls)

        if i == middle or i == middle_first or i == middle_third:
            curseur.executemany("""
                           insert into data (sma, ema, adx, kama, t3, trima, ppo, u_oscilator,
                           macd, stochrsi, bande_bollinger, prix_fermeture) 
                           values (?,?,?,?,?,?,?,?,?,?,?,?)
                           """, liste_data)

            liste_data.clear()

    curseur.executemany("""
                insert into data (sma, ema, adx, kama, t3, trima, ppo, u_oscilator,
                macd, stochrsi, bande_bollinger, prix_fermeture) 
                values (?,?,?,?,?,?,?,?,?,?,?,?)
                """, liste_data)

    liste_data.clear()
    print("Calcul data effectué et insérer")

    middle = (len(data_server) - 15) // 2
    middle_first = middle // 2
    middle_third = middle + middle_first

    for h in range(25, len(data_server) - 15):
        data = data_server[h:h + 15]

        # Calcul les indices techniques + ajout du prix
        ls = list(calcul_indice_15_donnees(data) + [float(data.close.values[-1])])

        # Transformation en string des sous-listes
        ls[-4], ls[-3], ls[-2] = str(ls[-4]), str(ls[-3]), str(ls[-2])

        liste_rsi.append(ls)

        if h == middle or h == middle_first or h == middle_third:
            curseur.executemany("""
                        insert into rsi_vwap_cmf 
                        (rsi, vwap, cmf, cci, mfi, linearregression,
                        tsf, a_oscilator, w_r, roc, obv, mom, prix_fermeture) 
                        values (?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """, liste_rsi)

            liste_rsi.clear()

    curseur.executemany("""
            insert into rsi_vwap_cmf 
            (rsi, vwap, cmf, cci, mfi, linearregression,
            tsf, a_oscilator, w_r, roc, obv, mom, prix_fermeture) 
            values (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, liste_rsi)

    liste_rsi.clear()
    print("Calcul rsi effectué et insérer")

    connexion.commit()

    print("Commit effectué")


@get_db
def select_data_bdd(curseur, connexion) -> (numpy.array, numpy.array):
    """
    Récupère toutes les données de la bdd
    Renvoie toutes les données et les prix sous forme de dataframe

    Première dataframe : toutes les données

    Deuxième dataframe : les prix

    Ex param :
    df_numpy : dataframe ou numpy
    """

    def my_process(data_bdd_process: list, dictionary: dict, order: int):
        data_process = []
        for row_process in data_bdd_process:
            data_process.append(one_liste(row_process, True))

        dictionary[order] = numpy.array(data_process)

    data_bdd = curseur.execute("""
    SELECT data.sma, data.ema, data.adx, data.kama, data.t3, data.trima, data.ppo, data.u_oscilator,
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

    connexion.commit()

    print("Lecture base de donnée faite")

    prix = [x[0] for x in prix]

    # On vient retransformer les données dans leur état d'origine
    # Et on remet le tout dans une dataframe
    taille_donnee = len(data_bdd)
    bloc_donne = taille_donnee // 4

    manager = Manager()
    dico = manager.dict()

    p1 = Process(target=my_process, args=(data_bdd[0:bloc_donne], dico, 0))
    p2 = Process(target=my_process, args=(data_bdd[bloc_donne:bloc_donne * 2], dico, 1))
    p3 = Process(target=my_process, args=(data_bdd[bloc_donne * 2:bloc_donne * 3], dico, 2))
    p4 = Process(target=my_process, args=(data_bdd[bloc_donne * 3:taille_donnee], dico, 3))

    p1.start()
    p2.start()
    p3.start()
    p4.start()

    p1.join()
    p2.join()
    p3.join()
    p4.join()

    print("Transformation donnée état d'origine faite")

    np = dico[0]
    del dico[0]

    for i in range(1, 4):
        np = numpy.concatenate((np, dico[i]))
        del dico[i]

    prix_np = numpy.array(prix)

    prix.clear()

    return np, prix_np


if __name__ == "__main__":
    bdd_data()
    bdd_rsi_vwap_cmf()
