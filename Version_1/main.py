from keras.models import Sequential, model_from_json
from keras.layers import Dense
from database import *


class IA:
    """
    Classe qui contient l'entrainement ainsi la prédiction des modèles d'ia
    """

    def __init__(self, symbol) -> None:
        """
        Initialise un objet IA permet d'interagir avec ou de les créer
        Ex param :
        symbol : "BTC"
        """
        self.symbol_base = symbol
        self.symbol = f"{symbol}-USDT"
        self.symbol_up = f"{symbol}3L-USDT"
        self.symbol_down = f"{symbol}3S-USDT"

    # Fonction d'entrainement

    def training_keras(self) -> None:
        """
        Fonction qui entraine les neurones et les sauvegardes
        """

        X, y = select_donnée_bdd("numpy")

        modele = Sequential()

        modele.add(Dense(30, input_dim=298, activation='relu'))
        modele.add(Dense(15, activation='relu'))
        # 30, 15 pour le marché normal et up
        # 30, 16 pour le marché down

        modele.compile(loss='mean_squared_logarithmic_error',
                       optimizer='adam')

        modele.fit(X, y, epochs=50, batch_size=6)

        modele_json = modele.to_json()

        with open("modele.json", "w") as json_file:
            json_file.write(modele_json)

        modele.save_weights("modele.h5")

        print("Modèle sauvegarder !")

    # Fonction de prédiction

    def prédiction_keras(self, donnée_serveur_data: pandas.DataFrame, donnée_serveur_rsi: pandas.DataFrame, Modèle) -> float:
        """
        Fonction qui fait les prédiction et renvoie le prix potentiel de la crypto
        """

        ls = [SMA(donnée_serveur_data), EMA(donnée_serveur_data), ADX(donnée_serveur_data),
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
            if cpt <= 8 or cpt >= 21:
                for nb in element:
                    donnée_prédiction.append(nb)
            elif cpt <= 11:
                for liste in element:
                    for nb in liste:
                        donnée_prédiction.append(nb)
            elif cpt <= 20:
                donnée_prédiction.append(element)

            cpt += 1

        np_liste = numpy.array([donnée_prédiction])

        predic = moyenne(Modèle.predict(np_liste)[0])

        return predic

    # Fonction de chargement des modèles

    def chargement_modele(self):
        """
        Fonction qui charge et renvoie les trois modèles
        Ex param :
        symbol : "BTC"
        """

        json_file = open(
            f'Modele_1h_2.0/SPOT/{self.symbol_base}USDT/modele.json', 'r')
        json_file_up = open(
            f'Modele_1h_2.0/SPOT_EFFET_LEVIER/{self.symbol_base}UPUSDT/modele.json', 'r')
        json_file_down = open(
            f'Modele_1h_2.0/SPOT_EFFET_LEVIER/{self.symbol_base}DOWNUSDT/modele.json', 'r')

        loaded_model_json = json_file.read()
        loaded_model_json_up = json_file_up.read()
        loaded_model_json_down = json_file_down.read()

        json_file.close()
        json_file_up.close()
        json_file_down.close()

        loaded_model = model_from_json(loaded_model_json)
        loaded_model_up = model_from_json(loaded_model_json_up)
        loaded_model_down = model_from_json(loaded_model_json_down)

        loaded_model.load_weights(
            f"Modele_1h_2.0/SPOT/{self.symbol_base}USDT/modele.h5")
        loaded_model_up.load_weights(
            f"Modele_1h_2.0/SPOT_EFFET_LEVIER/{self.symbol_base}UPUSDT/modele.h5")
        loaded_model_down.load_weights(
            f"Modele_1h_2.0/SPOT_EFFET_LEVIER/{self.symbol_base}DOWNUSDT/modele.h5")

        loaded_model.compile(
            loss='mean_squared_logarithmic_error', optimizer='adam')
        loaded_model_up.compile(
            loss='mean_squared_logarithmic_error', optimizer='adam')
        loaded_model_down.compile(
            loss='mean_squared_logarithmic_error', optimizer='adam')

        return loaded_model, loaded_model_up, loaded_model_down

    def etat_bot(self, lecture_ecriture: str, to_write: Optional[str] = None) -> str or None:
        """
        Fonction qui écrit ou lit dans un fichier l'état du bot (prédiction, heure)
        Pour que quand le bot démarre, sait s'il doit attendre l'heure et si on sors d'une divergence
        Ex param :
        lecture_ecriture : lecture ou écriture
        """

        if lecture_ecriture == "lecture":
            # On utilise try dans le cas où le fichier n'existe pas
            try:
                fichier = open(f"etat_bot_{self.symbol_base}.txt", "r")

                elt = fichier.read()

                fichier.close()

                return elt
            except:
                return ""

        elif lecture_ecriture == "écriture":
            fichier = open(f"etat_bot_{self.symbol_base}.txt", "w")

            fichier.write(to_write)

            fichier.close()

    def validation_achat(self, prix: float, prix_up: float, prix_down: float, prediction: float, prediction_up: float, prediction_down: float) -> int or None:
        """
        Fonction qui valide ou non l'achat d'une crypto
        """
        if prix < prediction and prix_up < prediction_up and prix_down > prediction_down:
            if prediction_up - prix_up >= 0.045 and prediction_down <= 0.03:
                return 1

        if prix > prediction and prix_up > prediction_up and prix_down < prediction_down:
            if prix_up - prediction_up >= 0.045 and prediction_down >= 0.0245:
                return 0

        return None


def kill_process(p: Process) -> None:
    """
    Fonction qui tue le processus passé en argument
    """
    # Etat du processus
    statut = p.is_alive()

    # S'il est en vie, on le tue
    if statut == True:
        p.kill()
