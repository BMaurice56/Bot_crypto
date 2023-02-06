from import_module_version1 import *
from tensorflow.keras.utils import to_categorical
import tensorflow as tf
from random import randint


def prise_position_gain(self, donnees: numpy.array, indice: int) -> bool:
    """
    Fonction qui simule une prise de position de l'ia
    Renvoie True ou false si la prise de position de l'ia a mené à un gain
    """


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
    def __init__(self, action_size=1, state_size=298):
        # Initialisation de l'agent
        self.action_size = action_size  # Activation 1 ou 0, renvoie 1 ou 0
        self.state_size = state_size  # Nombre d'entrées du bot (378 données)

        # Création du modèle de réseau de neurones
        self.model = self._build_model()

    def _build_model(self):
        # Création du modèle
        model = Sequential()
        model.add(Dense(50, input_dim=self.state_size, activation='relu'))
        model.add(Dense(15, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mean_squared_logarithmic_error', optimizer='adam')
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


def _build_model():
    # Création du modèle
    model = Sequential()
    model.add(Dense(50, input_dim=298, activation='relu'))
    model.add(Dense(15, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(loss='mean_squared_logarithmic_error', optimizer='adam')
    return model


donnee_bdd, prix_bdd = select_donnée_bdd("numpy")

modele = _build_model()

