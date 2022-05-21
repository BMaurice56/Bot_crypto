from datetime import datetime
from main import *
import locale

symbol = sys.argv[1]
dodo = 60*14 + 58
effet_levier = 100


json_file = open(f'Modèle_bdd/{symbol}/modele.json', 'r')
loaded_model_json = json_file.read()
json_file.close()

loaded_model = model_from_json(loaded_model_json)
loaded_model.load_weights(f"Modèle_bdd/{symbol}/modele.h5")

loaded_model.compile(
    loss='mean_squared_logarithmic_error', optimizer='adam')


# Définition de la zone pour l'horodatage car la date était en anglais avec le module datetime
locale.setlocale(locale.LC_TIME, '')

argent = 150

while True:
    date = datetime.now().strftime("%A %d %B %Y %H:%M:%S")

    data = donnée(symbol, "600 min ago UTC", "0 min ago UTC", 40)
    rsi_vwap_cmf = donnée(symbol, "225 min ago UTC", "0 min ago UTC", 15)

    prix = prix_temps_reel(symbol)

    prediction = prédiction_keras(data, rsi_vwap_cmf, loaded_model)

    état = f"programme toujours en cour d'exécution le : {date}"
    infos = f"prix de la crypto : {prix}, prix de la prédiction : {prediction}"

    msg = état + "\n" + infos

    message_webhook_état_bot(msg)
