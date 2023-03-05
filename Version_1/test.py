from main import IA, select_donnée_bdd, insert_data_historique_bdd, model_from_json
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

# reste à faire : BNBDOWN, ETHDOWN

#insert_data_historique_bdd("XRPUSDT", 50_000)

X, y = select_donnée_bdd("numpy")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

ia = IA("XRP")

ia.training_keras(1000, 200, X_train, y_train)

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

"""
for i in range(90, 121, 10):
for j in range(5, 51, 5):

    with open(f"modele_{i}_{j}.json", "r") as f:
        loaded_model = model_from_json(f.read())
        loaded_model.load_weights(f"modele_{i}_{j}.h5")
        loaded_model.compile(
            loss='mean_squared_logarithmic_error', optimizer='adam')

    print(f"modele_{i}_{j}.json")
    print(loaded_model.evaluate(X, y))
"""

