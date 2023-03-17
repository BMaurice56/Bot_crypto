from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from keras.models import Sequential, model_from_json
from sklearn.model_selection import train_test_split
from keras_tuner import RandomSearch
from keras.layers import Dense
from database import *


class IA:
    """
    Classe qui contient l'entrainement ainsi la prédiction des modèles d'ia
    """

    def __init__(self, symbol: str) -> None:
        """
        Initialise un objet IA permet d'interagir avec ou de les créer

        Ex param :
        symbol : "BTC"
        """
        self.symbol = symbol
        self.input = 65

    def training(self, l1: float, l2: float) -> None:
        """
        Entraine les neurones et les sauvegardes

        Ex params:
        l1 (première ligne de neurones) : 50
        l2 (deuxième ligne) : 10
        """
        # Création du modèle
        modele = Sequential()

        # Récupération et séparation des données
        X, y = select_donnée_bdd("numpy")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42)

        # Ajout des couches
        modele.add(Dense(l1, input_dim=self.input, activation='relu'))
        modele.add(Dense(l2, activation='relu'))
        modele.add(Dense(1, activation='relu'))

        modele.compile(loss='mean_squared_logarithmic_error',
                       optimizer='adam')

        modele.fit(X_train, y_train, epochs=50, batch_size=6)

        # Sauvegarde du modèle
        self.save_modele(modele)

        # Test du modèle
        self.test_modele(X_test, y_test, modele)

    def training_2(self) -> None:
        """
        recherche la meilleur combinaison de neurone et sauvegarde le modèle
        """
        # Récupération et séparation des données
        X, y = select_donnée_bdd("numpy")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42)

        def build_model(hp):
            model = Sequential()
            model.add(Dense(units=hp.Int('units', min_value=5,
                                         max_value=256, step=8), activation='relu', input_dim=self.input))
            model.add(Dense(units=hp.Int('units', min_value=2,
                                         max_value=256, step=8), activation='relu'))
            model.add(Dense(units=1, activation='relu'))
            model.compile(optimizer='adam',
                          loss='mean_squared_logarithmic_error')
            return model

        tuner = RandomSearch(
            build_model,
            objective='val_loss',
            max_trials=20,
            executions_per_trial=2,
            directory="my_dir",
            project_name="helloworld"
        )

        tuner.search_space_summary()

        tuner.search(X_train, y_train,
                     epochs=50,
                     validation_data=(X_test, y_test))

        best_model = tuner.get_best_models(num_models=1)[0]

        # Sauvegarde du modèle
        self.save_modele(best_model)

        # Test du modèle
        self.test_modele(X_test, y_test, best_model)

        # Suppression du dossier de test des neurones
        os.system("rm -r my_dir")

    def save_modele(self, modele) -> None:
        """
        Sauvegarde le modèle
        """
        modele_json = modele.to_json()

        # Sauvegarde du modèle
        with open("modele.json", "w") as json_file:
            json_file.write(modele_json)

        # Sauvegarde des poids
        modele.save_weights("modele.h5")

        print("Modèle sauvegarder !")

    def test_modele(self, X_test, y_test, modele) -> None:
        """
        Test le modèle passé en argument
        """
        # prédire les valeurs pour les données de test
        y_pred = modele.predict(X_test)

        # calcule des indices de fiabilités du modèle
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # affiche les indices et l'évaluation du modèle sur les données de test
        print(f"Mean Squared Error (MSE): {mse}")
        print(f"Mean Absolute Error (MAE): {mae}")
        print(f'Coefficient R² : {r2}')
        print(modele.evaluate(X_test, y_test))

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
        emplacement = f"Modele_1h/SPOT_USDT/{self.symbol}/"
        emplacement_up = emplacement[:-1] + "UP/"
        emplacement_down = emplacement[:-1] + "DOWN/"

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
            if self.symbol == "BTC" and prediction_up - prix_up >= 0.045 and prediction_down <= 0.03:
                return 1

            elif self.symbol == "ETH":
                return 1

            elif self.symbol == "BNB":
                return 1

        if prix > prediction and prix_up > prediction_up and prix_down < prediction_down:
            if self.symbol == "BTC" and prix_up - prediction_up >= 0.045 and prediction_down >= 0.0245:
                return 0

            elif self.symbol == "ETH":
                return 0

            elif self.symbol == "BNB":
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
