from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from keras.models import Sequential, model_from_json
from sklearn.model_selection import train_test_split
from keras_tuner import RandomSearch
from keras.layers import Dense
from database import *
from typing import Any


class IA:
    """
    Classe qui contient l'entrainement ainsi la prédiction des modèles d'intelligences artificielles
    """

    def __init__(self, symbol: str) -> None:
        """
        Initialise un objet IA permet d'interagir avec ou de les créer

        Ex param :
        symbol : "BTC"
        """
        self.symbol = symbol
        self.input = 65

        # Chargement des modèles d'intelligences artificielles pour les prédictions
        self.model, self.model_up, self.model_down = self.loading_model()

    def training(self, l1: float, l2: float) -> None:
        """
        Entraine les neurones et les sauvegardes

        Ex params :
        l1 (première ligne de neurones) : 50
        l2 (deuxième ligne) : 10
        """
        # Création du modèle
        model = Sequential()

        # Récupération et séparation des données
        x, y = select_data_bdd("numpy")

        x_train, x_test, y_train, y_test = train_test_split(
            x, y, test_size=0.2, random_state=42)

        # Ajout des couches
        model.add(Dense(l1, input_dim=self.input, activation='relu'))
        model.add(Dense(l2, activation='relu'))
        model.add(Dense(1, activation='relu'))

        model.compile(loss='mean_squared_logarithmic_error',
                      optimizer='adam')

        model.fit(x_train, y_train, epochs=50, batch_size=6)

        # Sauvegarde du modèle
        self.save_model(model)

        # Test du modèle
        self.test_model(x_test, y_test, model)

    def training_2(self) -> None:
        """
        Recherche la meilleure combinaison de neurone et sauvegarde le modèle
        """
        # Récupération et séparation des données
        x, y = select_data_bdd("numpy")

        x_train, x_test, y_train, y_test = train_test_split(
            x, y, test_size=0.2, random_state=42)

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

        tuner.search(x_train, y_train,
                     epochs=50,
                     validation_data=(x_test, y_test))

        best_model = tuner.get_best_models(num_models=1)[0]

        # Sauvegarde du modèle
        self.save_model(best_model)

        # Test du modèle
        self.test_model(x_test, y_test, best_model)

        # Suppression du dossier de test des neurones
        os.system("rm -r my_dir")

    @staticmethod
    def save_model(model) -> None:
        """
        Sauvegarde le modèle
        """
        model_json = model.to_json()

        # Sauvegarde du modèle
        with open("model.json", "w") as json_file:
            json_file.write(model_json)

        # Sauvegarde des poids
        model.save_weights("model.h5")

        print("Modèle sauvegarder !")

    @staticmethod
    def test_model(x_test, y_test, model) -> None:
        """
        Test le modèle passé en argument
        """
        # prédire les valeurs pour les données de test
        y_prediction = model.predict(x_test)

        # calcule des indices de fiabilités du modèle
        mse = mean_squared_error(y_test, y_prediction)
        mae = mean_absolute_error(y_test, y_prediction)
        r2 = r2_score(y_test, y_prediction)

        # affiche les indices et l'évaluation du modèle sur les données de test
        print(f"Mean Squared Error (MSE): {mse}")
        print(f"Mean Absolute Error (MAE): {mae}")
        print(f'Coefficient R² : {r2}')
        print(model.evaluate(x_test, y_test))

    def prediction_keras(self, data_server_40: pandas.DataFrame, data_server_15: pandas.DataFrame,
                         model: bool or None) -> float:
        """
        Fait les prédictions et renvoie le prix potentiel de la crypto

        Ex params :
        data_server_40 : Dataframe des données de 40 de longueurs
        data_server_15 : Dataframe des données de 15 de longueurs
        model : True, False, None -> sélection du modèle voulu
        """

        ls = calcul_indice_40_donnees(
            data_server_40) + calcul_indice_15_donnees(data_server_15)

        data_prediction = one_liste(ls)

        np_liste = numpy.array([data_prediction])

        if model is True:
            prediction = float(self.model.predict(np_liste)[0][0])
        elif model is False:
            prediction = float(self.model_up.predict(np_liste)[0][0])
        else:
            prediction = float(self.model_down.predict(np_liste)[0][0])

        return prediction

    def loading_model(self) -> Union[Any, Any, Any]:
        """
        Charge et renvoie les trois modèles
        """
        # Emplacement des réseaux de neurones
        emplacement = f"Model_1h/{self.symbol}/"
        emplacement_up = emplacement[:-1] + "UP/"
        emplacement_down = emplacement[:-1] + "DOWN/"

        # Fichiers
        fichier_json = "model.json"
        fichier_h5 = "model.h5"

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

    def state_bot(self, read_write: str, to_write: Optional[str] = None) -> str or None:
        """
        Écrit ou lit dans un fichier l'état du bot (prédiction, heure)
        Pour que quand le bot démarre, sait s'il doit attendre l'heure et si on sort d'une divergence

        Ex params :
        read_write : lecture ou écriture
        to_write (optionnel) : élément à écrire dans le fichier
        """
        fichier = f"state_bot_{self.symbol}.txt"

        if read_write == "lecture":
            # On utilise try dans le cas où le fichier n'existe pas
            try:
                with open(fichier, "r") as f:
                    elt = f.read()

                return elt
            except FileNotFoundError:
                return ""

        elif read_write == "écriture":
            with open(fichier, "w") as f:
                f.write(to_write)

    def write_prediction(self, prix: float, prix_up: float, prix_down: float, prediction: float,
                         prediction_up: float, prediction_down: float, date: str) -> None:
        """
        Écrit dans un fichier les prédictions et les prix de la crypto ainsi que la date
        """
        # Liste des valeurs
        liste_valeur = [prix, prediction, prix_up,
                        prediction_up, prix_down, prediction_down, date]

        # Écriture dans le fichier
        with open(f"Autre_fichiers/prediction_bot_{self.symbol}.txt", "a") as f:
            f.write(f"{str(liste_valeur)}\n")

    def validation_achat(self, prix: float, prix_up: float, prix_down: float, prediction: float, prediction_up: float,
                         prediction_down: float) -> int or None:
        """
        Valide ou non l'achat d'une crypto
        Si pas de condition d'achat → valeur inconnue
        """
        if prix < prediction and prix_up < prediction_up and prix_down > prediction_down:
            if self.symbol == "ADA":
                if prediction - prix <= 0.0009 and prediction_up - prix_up <= 0.0032:
                    if prix_down - prediction_down <= 0.0005:
                        return 1

            elif self.symbol == "BNB":
                if prediction - prix <= 1.57 and prediction_up - prix_up <= 0.32:
                    if prix_down - prediction_down <= 0.0064:
                        return 1

            elif self.symbol == "BTC":
                return 1

            elif self.symbol == "ETH":
                if prediction - prix <= 3 and prediction_up - prix_up <= 0.028:
                    if prix_down - prediction_down <= 0.008:
                        return 1

            elif self.symbol == "XRP":
                if prediction - prix <= 0.0027 and prediction_up - prix_up <= 0.0031:
                    if prix_down - prediction_down <= 0.00018:
                        return 1

        elif prix > prediction and prix_up > prediction_up and prix_down < prediction_down:
            if self.symbol == "ADA":
                if prix - prediction <= 0.0011 and prix_up - prediction_up <= 0.0018:
                    if prediction_down - prix_down <= 0.0003:
                        return 0

            elif self.symbol == "BNB":
                return 0

            elif self.symbol == "BTC":
                if prix - prediction <= 35 and prix_up - prediction_up <= 0.031:
                    if prediction_down - prix_down <= 0.0024:
                        return 0

            elif self.symbol == "ETH":
                return 0

            elif self.symbol == "XRP":
                return 0

        return None


def kill_process(p: Process) -> None:
    """
    Tue le processus passé en argument
    """
    # état du processus
    statut = p.is_alive()

    # S'il est en vie, on le tue
    if statut:
        p.kill()


def kill_thread(th: Thread, event: Event) -> None:
    """
    Tue le thread passé en argument
    """
    # état du thread
    statut = th.is_alive()

    # S'il est en vie, on l'arrête
    if statut:
        event.set()

        th.join()

        event.clear()
