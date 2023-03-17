from main import IA, insert_data_historique_bdd, select_donnée_bdd, Process

# reste a faire : XRP, ADA, SOL
# nickel : BTC, ETH, BNB

ia = IA("XRP")

insert_data_historique_bdd("XRPUSDT", 50_000)

ia.training_2()

"""
loaded_model, loaded_model_up, loaded_model_down = ia.chargement_modele()

X, y = select_donnée_bdd("numpy")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42)

fichier_json = "modele.json"
fichier_h5 = "modele.h5"

with open(fichier_json, "r") as f:
    modele = model_from_json(f.read())

modele.load_weights(fichier_h5)

modele.compile(
    loss='mean_squared_logarithmic_error', optimizer='adam')

ia.test_modele(X_test, y_test, loaded_model_down)
"""
