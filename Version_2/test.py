from import_module_version1 import *
from tensorflow.keras.utils import to_categorical
import keras
import tensorflow as tf

#donnee_bdd, prix_bdd = select_donnée_bdd("numpy")


"""
datas = all_data("BTC")

data = datas[0]
rsi = datas[3]
"""


class Environnement:
    """
    Class qui définie l'environnement de l'ia
    """

    def __init__(self):
        """
        Initialise l'environnement de l'ia
        """
        # TODO

    class Action:
        """
        Class action qui possède les actions possibles pour l'ia    
        """

        def __init__(self):
            """
            Initialise la classe action
            """
            self.prix_position = None
            self.montant_position = None

        def prise_position(self, montant: int, position: int) -> None:
            """
            Fonction qui simule une prise de position de l'ia
            """
            self.montant_position = montant
            self.prix_position = position

        def vente_position(self, prix_vente: int) -> str or bool:
            """
            Fonction qui simule la vente d'une position de l'ia
            Renvoie True ou false si gain suite à la transaction ou non
            """

            if self.prix_position == None:
                return "pas de position prise !"

            gain = (prix_vente * self.montant_position) / self.prix_position
            resultat = (gain >= self.montant_position)

            self.prix_position = None
            self.montant_position = None

            return resultat


############################ ChatGPT ################################


class CustomEnv:
    def __init__(self):
        # Initialisation de l'environnement
        self.current_state = 0
        self.action_space = [0, 1]  # Actions possibles : 0 ou 1

    def step(self, action):
        # Mise à jour de l'environnement en fonction de l'action choisie
        if action == 0:
            self.current_state += 1
        else:
            self.current_state -= 1

        # Détermination de la récompense en fonction de l'état actuel
        if self.current_state == 10:
            reward = 1
            done = True
        elif self.current_state == -10:
            reward = -1
            done = True
        else:
            reward = 0
            done = False

        # Conversion de l'état en format compatible avec Keras
        state = to_categorical(self.current_state, 20)

        return state, reward, done


class Agent:
    def __init__(self, action_size=1, state_size=378):
        # Initialisation de l'agent
        self.state_size = state_size  # Activation 1 ou 0, renvoie 1 ou 9
        self.action_size = action_size  # Nombre d'entrées du bot (378 données)

        # Création du modèle de réseau de neurones
        self.model = self._build_model()

    def _build_model(self):
        # Création du modèle
        model = Sequential()
        model.add(Dense(50, input_dim=self.state_size, activation='relu'))
        model.add(Dense(15, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse', optimizer=keras.optimizers.Adam(lr=0.001))
        return model

    def act(self, state):
        # Prédiction de l'action à effectuer en fonction de l'état
        action = self.model.predict(state)
        return numpy.argmax(action[0])

    def train(self, state, action, reward, next_state, done):
        # Mise à jour des connaissances de l'agent en utilisant l'expérience acquise
        target = reward
        if not done:
            target = reward + 0.95 * \
                numpy.amax(self.model.predict(next_state)[0])
        target_f = self.model.predict(state)
        target_f[0][action] = target
        self.model.fit(state, target_f, epochs=1, verbose=0)
