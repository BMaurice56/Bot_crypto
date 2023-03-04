from main import IA, insert_data_historique_bdd, select_donnée_bdd, model_from_json

# insert_data_historique_bdd("BNBDOWNUSDT", 50_000)

ia = IA("BNB")

X, y = select_donnée_bdd("numpy")

ia.training_keras(117, 15, X, y)

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

# 110, 10/15
# 120, 10
