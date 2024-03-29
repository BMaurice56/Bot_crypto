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

    liste_data = []
    liste_rsi = []

    for i in range(0, len(data_server) - 40):
        data = data_server[i:i + 40]

        # Calcul les indices techniques + ajout du prix
        ls = list(calcul_indice_40_donnees(data) + [float(data.close.values[-1])])

        # Transformation en string des sous-listes
        for j in range(len(ls) - 1):
            ls[j] = str(ls[j])

        liste_data.append(ls)

    for h in range(25, len(data_server) - 15):
        data = data_server[h:h + 15]

        # Calcul les indices techniques + ajout du prix
        ls = list(calcul_indice_15_donnees(data) + [float(data.close.values[-1])])

        # Transformation en string des sous-listes
        ls[-4], ls[-3], ls[-2] = str(ls[-4]), str(ls[-3]), str(ls[-2])

        liste_rsi.append(ls)

    curseur.executemany("""
            insert into data (sma, ema, adx, kama, t3, trima, ppo, u_oscilator,
            macd, stochrsi, bande_bollinger, prix_fermeture) 
            values (?,?,?,?,?,?,?,?,?,?,?,?)
            """, liste_data)

    curseur.executemany("""
            insert into rsi_vwap_cmf 
            (rsi, vwap, cmf, cci, mfi, linearregression,
            tsf, a_oscilator, w_r, roc, obv, mom, prix_fermeture) 
            values (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, liste_rsi)

    connexion.commit()


@get_db
def select_data_bdd(df_numpy: str, curseur, connexion) -> Union[pandas.DataFrame, pandas.DataFrame] or \
                                                          Union[numpy.array, numpy.array]:
    """
    Récupère toutes les données de la bdd
    Renvoie toutes les données et les prix sous forme de dataframe

    Première dataframe : toutes les données

    Deuxième dataframe : les prix

    Ex param :
    df_numpy : dataframe ou numpy
    """

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

    prix = [x[0] for x in prix]

    # On vient retransformer les données dans leur état d'origine
    # Et on remet le tout dans une dataframe
    data = []
    for row in data_bdd:
        data.append(one_liste(row, True))

    if df_numpy == "dataframe":
        dp = pandas.DataFrame(data)
        prix_df = pandas.DataFrame(prix)

        return [dp, prix_df]

    elif df_numpy == "numpy":
        np = numpy.array(data)
        prix_np = numpy.array(prix)

        return [np, prix_np]


if __name__ == "__main__":
    bdd_data()
    bdd_rsi_vwap_cmf()
