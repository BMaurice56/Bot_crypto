
import tensorflow as tf
from tensorflow import keras
from keras import layers
from keras_tuner import RandomSearch
from main import IA, select_donnée_bdd, insert_data_historique_bdd, model_from_json
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

insert_data_historique_bdd("ADADOWNUSDT", 50_000)

X, y = select_donnée_bdd("numpy")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42)


def build_model(hp):
    model = keras.Sequential()
    model.add(layers.Dense(units=hp.Int('units', min_value=5,
              max_value=256, step=16), activation='relu', input_dim=298))
    model.add(layers.Dense(units=hp.Int('units', min_value=2,
              max_value=256, step=16), activation='relu'))
    model.add(layers.Dense(units=1, activation='relu'))
    model.compile(optimizer='adam', loss='mean_squared_logarithmic_error')
    return model


tuner = RandomSearch(
    build_model,
    objective='val_loss',
    max_trials=20,
    executions_per_trial=2,
    directory='my_dir',
    project_name='helloworld'
)

tuner.search_space_summary()

tuner.search(X_train, y_train,
             epochs=50,
             validation_data=(X_test, y_test))

best_model = tuner.get_best_models(num_models=1)[0]

modele_json = best_model.to_json()

with open("modele.json", "w") as json_file:
    json_file.write(modele_json)

best_model.save_weights("modele.h5")

# prédire les valeurs pour les données de test
y_pred = best_model.predict(X_test)

# calculer le coefficient R²
r2 = r2_score(y_test, y_pred)

# afficher le coefficient R²
print('Coefficient R² : {:.2f}'.format(r2))

"""
from main import IA, select_donnée_bdd, insert_data_historique_bdd, model_from_json
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

# reste a faire : sol, solup, soldown

#insert_data_historique_bdd("XRPUSDT", 50_000)

X, y = select_donnée_bdd("numpy")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42)

ia = IA("XRP")

ia.training_keras(100, 15, X_train, y_train)

with open(f"modele.json", "r") as f:
    loaded_model = model_from_json(f.read())
    loaded_model.load_weights(f"modele.h5")
    loaded_model.compile(
        loss='mean_squared_logarithmic_error', optimizer='adam')


# prédire les valeurs pour les données de test
y_pred = loaded_model.predict(X_test)

# calculer le coefficient R²
r2 = r2_score(y_test, y_pred)

# afficher le coefficient R²
print('Coefficient R² : {:.2f}'.format(r2))
print(loaded_model.evaluate(X_train, y_train))
"""
