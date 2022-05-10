import sqlite3

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
    prix_fermeture REAL
    )
    """)

    connexion.commit()


if __name__ == "__main__":
    bdd_data()
    bdd_rsi_vwap_cmf()
