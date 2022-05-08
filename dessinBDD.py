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

    curseur.execute("DROP TABLE IF EXISTS prédiction_data")
    curseur.execute("""
    CREATE TABLE prédiction_data 
    (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prix_prédiction REAL, 
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

    curseur.execute("DROP TABLE IF EXISTS prédiction_rsi")
    curseur.execute("""
    CREATE TABLE prédiction_rsi 
    (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prix_prédiction REAL, 
    prix_fermeture REAL
    )
    """)

    connexion.commit()


def résultat():
    curseur.execute("DROP TABLE IF EXISTS résultat")
    curseur.execute("""
    CREATE TABLE résultat 
    (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    moyenne_prédiction REAL, 
    prédiction_rsi REAL,
    prédiction_vwap REAL,
    prédiction_cmf REAL,
    prédiction_sma REAL,
    prédiction_ema REAL,
    prédiction_macd1 REAL,
    prédiction_macd2 REAL,
    prédiction_macd3 REAL,
    prédiction_stochrsi1 REAL, 
    prédiction_stochrsi2 REAL,
    prédiction_bb1 REAL,
    prédiction_bb2 REAL,
    prédiction_bb3 REAL,
    prédiction_historique REAL, 
    prix_final REAL
    )
    """)


if __name__ == "__main__":
    bdd_data()
    bdd_rsi_vwap_cmf()
    résultat()
