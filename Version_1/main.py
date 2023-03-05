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
        self.symbol = symbol

    def training_keras(self, l1: float, l2: float, X: numpy.array, y: numpy.array) -> None:
        """
        Entraine les neurones et les sauvegardes

        Ex params:
        l1 (première ligne de neurones) : 50
        l2 (deuxième ligne) : 10
        X : valeur à entrainer (utiliser pour la prédiction)
        y : valeur à entrainer (valeur prédite)
        """
        # Création du modèle
        modele = Sequential()

        # Ajout des couches
        modele.add(Dense(l1, input_dim=298, activation='relu'))
        modele.add(Dense(l2, activation='relu'))
        modele.add(Dense(10, activation='relu'))
        modele.add(Dense(1, activation='relu'))

        modele.compile(loss='mean_squared_logarithmic_error',
                       optimizer='adam')

        modele.fit(X, y, epochs=50, batch_size=8)

        modele_json = modele.to_json()

        with open("modele.json", "w") as json_file:
            json_file.write(modele_json)

        modele.save_weights("modele.h5")

        print("Modèle sauvegarder !")

    def prédiction_keras(self, donnée_serveur_data: pandas.DataFrame, donnée_serveur_rsi: pandas.DataFrame, Modèle) -> float:
        """
        Fait les prédiction et renvoie le prix potentiel de la crypto
        """

        ls = calcul_indice_40_donnees(
            donnée_serveur_data) + calcul_indice_15_donnees(donnée_serveur_rsi)

        donnée_prédiction = one_liste(ls)

        np_liste = numpy.array([donnée_prédiction])

        predic = float(Modèle.predict(np_liste)[0][0])

        return predic

    def chargement_modele(self) -> None:
        """
        Charge et renvoie les trois modèles
        """
        # Emplacement des réseaux de neuronnes
        emplacement = f"Modele_1h_2.0/SPOT/{self.symbol}USDT/"
        emplacement_up = f"Modele_1h_2.0/SPOT_EFFET_LEVIER/{self.symbol}UPUSDT/"
        emplacement_down = f"Modele_1h_2.0/SPOT_EFFET_LEVIER/{self.symbol}DOWNUSDT/"

        # Fichiers
        fichier_json = "modele.json"
        fichier_h5 = "modele.h5"

        # Chargement de la configuration du réseau
        with open(emplacement + fichier_json, "r") as f:
            loaded_model = model_from_json(f.read())

        with open(emplacement_up + fichier_json, "r") as f_up:
            loaded_model_up = model_from_json(f_up.read())

        with open(emplacement_down + fichier_json, "r") as f_down:
            loaded_model_down = model_from_json(f_down.read())

        # Chargement des poids
        loaded_model.load_weights(emplacement + fichier_h5)
        loaded_model_up.load_weights(emplacement_up + fichier_h5)
        loaded_model_down.load_weights(emplacement_down + fichier_h5)

        # Configurations des modèles
        loaded_model.compile(
            loss='mean_squared_logarithmic_error', optimizer='adam')
        loaded_model_up.compile(
            loss='mean_squared_logarithmic_error', optimizer='adam')
        loaded_model_down.compile(
            loss='mean_squared_logarithmic_error', optimizer='adam')

        return loaded_model, loaded_model_up, loaded_model_down

    def etat_bot(self, lecture_ecriture: str, to_write: Optional[str] = None) -> str or None:
        """
        Ecrit ou lit dans un fichier l'état du bot (prédiction, heure)
        Pour que quand le bot démarre, sait s'il doit attendre l'heure et si on sors d'une divergence

        Ex params :
        lecture_ecriture : lecture ou écriture
        to_write (optionnel) : élément à écrire dans le fichier
        """
        fichier = f"etat_bot_{self.symbol}.txt"

        if lecture_ecriture == "lecture":
            # On utilise try dans le cas où le fichier n'existe pas
            try:
                fichier = open(fichier, "r")

                elt = fichier.read()

                fichier.close()

                return elt
            except:
                return ""

        elif lecture_ecriture == "écriture":
            fichier = open(fichier, "w")

            fichier.write(to_write)

            fichier.close()

    def différence_prix(self, prix_1: float, prix_2: float) -> float:
        """
        Renvoie la différence entre deux prix
        """
        return prix_1 - prix_2

    def validation_achat(self, prix: float, prix_up: float, prix_down: float, prediction: float, prediction_up: float, prediction_down: float) -> int or None:
        """
        Valide ou non l'achat d'une crypto
        """
        if prix < prediction and prix_up < prediction_up and prix_down > prediction_down:
            if self.symbol == "BTC":
                if prediction_up - prix_up >= 0.045 and prediction_down <= 0.03:
                    return 1
            else:
                return 1

        if prix > prediction and prix_up > prediction_up and prix_down < prediction_down:
            if self.symbol == "BTC":
                if prix_up - prediction_up >= 0.045 and prediction_down >= 0.0245:
                    return 0
            else:
                return 0

        return None


def kill_process(p: Process) -> None:
    """
    Tue le processus passé en argument
    """
    # Etat du processus
    statut = p.is_alive()

    # S'il est en vie, on le tue
    if statut == True:
        p.kill()


def kill_thread(th: Thread, event: Event) -> None:
    """
    Tue le thread passé en argument
    """
    # Etat du thread
    statut = th.is_alive()

    # S'il est en vie, on l'arrête
    if statut == True:
        event.set()

        th.join()

        event.clear()
