from keras.models import Sequential, model_from_json
from time import perf_counter
from keras.layers import Dense
from database import *
import sys


# Fonction d'entrainement
def training_keras() -> None:
    """
    Fonction qui entraine les neurones et les sauvegardes
    """

    X, y = select_donnée_bdd("numpy")

    modele = Sequential()

    modele.add(Dense(50, input_dim=378, activation='relu'))
    modele.add(Dense(15, input_dim=378, activation='relu'))

    modele.compile(loss='mean_squared_logarithmic_error',
                   optimizer='adam')

    modele.fit(X, y, epochs=50, batch_size=4)

    modele_json = modele.to_json()

    with open("modele.json", "w") as json_file:
        json_file.write(modele_json)

    modele.save_weights("modele.h5")

    print("Modèle sauvegarder !")


# Fonction de prédiction
def prédiction_keras(donnée_serveur_data: pandas.DataFrame, donnée_serveur_rsi: pandas.DataFrame, Modèle) -> float:
    """
    Fonction qui fait les prédiction et renvoie le prix potentiel de la crypto
    """

    ls = [SMA(donnée_serveur_data), EMA(donnée_serveur_data), harami(donnée_serveur_data),
          doji(donnée_serveur_data), ADX(donnée_serveur_data),
          KAMA(donnée_serveur_data), T3(
              donnée_serveur_data), TRIMA(donnée_serveur_data),
          PPO(donnée_serveur_data), ultimate_oscilator(donnée_serveur_data),
          MACD(donnée_serveur_data), stochRSI(donnée_serveur_data), bandes_bollinger(donnée_serveur_data)]

    ls += [RSI(donnée_serveur_rsi), VWAP(donnée_serveur_rsi), chaikin_money_flow(
        donnée_serveur_rsi), CCI(donnée_serveur_rsi), MFI(donnée_serveur_rsi), LinearRegression(
        donnée_serveur_rsi), TSF(donnée_serveur_rsi), aroon_oscilator(donnée_serveur_rsi), williams_R(
        donnée_serveur_rsi), ROC(donnée_serveur_rsi), OBV(donnée_serveur_rsi), MOM(donnée_serveur_rsi)]

    donnée_prédiction = []

    cpt = 1
    for element in ls:
        if cpt <= 10 or cpt >= 23:
            for nb in element:
                donnée_prédiction.append(nb)
        elif cpt <= 13:
            for liste in element:
                for nb in liste:
                    donnée_prédiction.append(nb)
        elif cpt <= 22:
            donnée_prédiction.append(element)

        cpt += 1

    np_liste = numpy.array([donnée_prédiction])

    predic = moyenne(Modèle.predict(np_liste)[0])

    return predic


# Fonction de chargement des modèles
def chargement_modele(symbol):
    """
    Fonction qui charge et renvoie les trois modèles
    """

    json_file = open(f'Modèle_1h/SPOT/{symbol}USDT/modele.json', 'r')
    json_file_up = open(
        f'Modèle_1h/SPOT_EFFET_LEVIER/{symbol}UPUSDT/modele.json', 'r')
    json_file_down = open(
        f'Modèle_1h/SPOT_EFFET_LEVIER/{symbol}DOWNUSDT/modele.json', 'r')

    loaded_model_json = json_file.read()
    loaded_model_json_up = json_file_up.read()
    loaded_model_json_down = json_file_down.read()

    json_file.close()
    json_file_up.close()
    json_file_down.close()

    loaded_model = model_from_json(loaded_model_json)
    loaded_model_up = model_from_json(loaded_model_json_up)
    loaded_model_down = model_from_json(loaded_model_json_down)

    loaded_model.load_weights(f"Modèle_1h/SPOT/{symbol}USDT/modele.h5")
    loaded_model_up.load_weights(
        f"Modèle_1h/SPOT_EFFET_LEVIER/{symbol}UPUSDT/modele.h5")
    loaded_model_down.load_weights(
        f"Modèle_1h/SPOT_EFFET_LEVIER/{symbol}DOWNUSDT/modele.h5")

    loaded_model.compile(
        loss='mean_squared_logarithmic_error', optimizer='adam')
    loaded_model_up.compile(
        loss='mean_squared_logarithmic_error', optimizer='adam')
    loaded_model_down.compile(
        loss='mean_squared_logarithmic_error', optimizer='adam')

    return loaded_model, loaded_model_up, loaded_model_down
