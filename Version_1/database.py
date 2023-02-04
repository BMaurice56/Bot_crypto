from indices_techniques import *
from donnees_serveur import *
import sqlite3
import ast


def get_db(f):
    """
    Fonction qui créer la connexion avec la base de donnée
    """
    @wraps(f)
    def connexion(*args, **kwargs):
        # création de la base DB
        connexion = sqlite3.connect("data_base.db")
        # création du curseur
        curseur = connexion.cursor()
        return f(curseur=curseur, connexion=connexion, *args, **kwargs)

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

# Fonctions BDD

# Connexion à la bdd et créaton du curseur pour interagire avec


@get_db
def insert_bdd(table: str, data: pandas.DataFrame, curseur, connexion) -> None:
    """
    Fonction qui prend en argument la table et les données à inserer
    Et insert les données dans la bdd
    Ex param :
    table : data ou rsi_vwap_cmf
    data : dataframe des données du serveur
    """

    # Insertion normale des valeurs dans la table data
    # On transforme en str qu'au dernier moment car la liste
    # Est utilisé lors de l'insertion des données dans la bdd au lancement
    if table == "data":
        ls = [str(SMA(data)), str(EMA(data)), str(ADX(data)), str(
            KAMA(data)), str(T3(data)), str(TRIMA(data)),
            str(PPO(data)), str(ultimate_oscilator(data)),
            str(MACD(data)), str(stochRSI(data)), str(bandes_bollinger(
                data)), float(data.close.values[-1])]

        curseur.execute("""
        insert into data (sma, ema, adx, kama, t3, trima, ppo, u_oscilator,
        macd, stochrsi, bande_bollinger, prix_fermeture) 
        values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, ls)

        connexion.commit()

    # Insertion normale des valeurs dans la table rsi____
    elif table == "rsi_vwap_cmf":
        ls = [RSI(data), VWAP(data), chaikin_money_flow(
            data), CCI(data), MFI(data), LinearRegression(
            data), TSF(data), aroon_oscilator(data), williams_R(
            data), str(ROC(data)), str(OBV(data)), str(MOM(data)), float(data.close.values[-1])]

        curseur.execute("""
        insert into rsi_vwap_cmf 
        (rsi, vwap, cmf, cci, mfi, linearregression,
        tsf, a_oscilator, w_r, roc, obv, mom, prix_fermeture) 
        values (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, ls)

        connexion.commit()


@get_db
def insert_data_historique_bdd(symbol: str, nombre_données: int, curseur, connexion) -> None:
    """
    Fonction qui permet de charger les x dernières minutes/heures (avec un espace de x min/heure pour chaque jeux de données)
    Dans la base de donnée
    Ex param :
    symbol : 'BTCUSDT'
    nombres_données : 1000
    """
    # On enlève tout dans la bdd
    bdd_data()
    bdd_rsi_vwap_cmf()

    # On récupère toutes les données en 1 seule requête (car sinon beaucoup trop long)
    # Puis on vient itérer sur ces données

    binance = Binance()

    données_serveur = binance.donnée(
        symbol, f"{nombre_données} hour ago UTC", "0 hour ago UTC")

    liste_data = []
    liste_rsi = []

    for i in range(0, len(données_serveur)-40):

        data = données_serveur[i:i+40]

        ls = [str(SMA(data)), str(EMA(data)),  str(ADX(data)), str(
            KAMA(data)), str(T3(data)), str(TRIMA(data)),
            str(PPO(data)), str(ultimate_oscilator(data)),
            str(MACD(data)), str(stochRSI(data)), str(bandes_bollinger(
                data)), float(data.close.values[-1])]

        liste_data.append(ls)

    for j in range(25, len(données_serveur)-15):
        data = données_serveur[j:j+15]

        ls = [RSI(data), VWAP(data), chaikin_money_flow(
            data), CCI(data), MFI(data), LinearRegression(
            data), TSF(data), aroon_oscilator(data), williams_R(
            data), str(ROC(data)), str(OBV(data)), str(MOM(data)), float(data.close.values[-1])]

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
def select_donnée_bdd(df_numpy: str, curseur, connexion) -> Union[pandas.DataFrame, pandas.DataFrame] or Union[numpy.array, numpy.array]:
    """
    Fonction qui récupère toutes les données de la bdd
    Renvoie toutes les données et les prix sous forme de dataframe
    Première dataframe : toutes les données
    Deuxième dataframe : les prix
    Ex param :
    df_numpy : dataframe ou numpy
    """
    donnée_bdd = curseur.execute("""
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

    prix = [x[0] for x in prix]

    # On vient retransformer les données dans leur état d'origine
    # Et on remet le tout dans une dataframe
    donnée = []
    for row in donnée_bdd:
        temp = []
        cpt = 1
        for element in row:
            if cpt <= 8 or cpt >= 21:
                elt = ast.literal_eval(str(element))
                for nb in elt:
                    temp.append(nb)
            elif cpt <= 11:
                elt = ast.literal_eval(str(element))
                for liste in elt:
                    for nb in liste:
                        temp.append(nb)
            elif cpt <= 20:
                temp.append(float(element))

            cpt += 1

        donnée.append(temp)

    if df_numpy == "dataframe":
        dp = pandas.DataFrame(donnée)
        prix_df = pandas.DataFrame(prix)

        return [dp, prix_df]

    elif df_numpy == "numpy":
        np = numpy.array(donnée)
        prix_np = numpy.array(prix)

        return [np, prix_np]


if __name__ == "__main__":
    bdd_data()
    bdd_rsi_vwap_cmf()
