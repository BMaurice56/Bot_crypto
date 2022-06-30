from datetime import datetime
from main import *
import locale

#symbol = sys.argv[1]
symbol = "BTC"
dodo = 60*14 + 58

loaded_model, loaded_model_up, loaded_model_down = chargement_modele(symbol)

# Définition de la zone pour l'horodatage car la date était en anglais avec le module datetime
locale.setlocale(locale.LC_TIME, '')

api = "https://api.kucoin.com"
kucoin_api_key = os.getenv("KUCOIN_API_KEY")
kucoin_api_secret = os.getenv("KUCOIN_API_SECRET")

while True:
    argent = montant_compte("USDT")
    btcup = montant_compte("BTC3L")
    btcdown = montant_compte("BTC3S")

    position_up = ""
    position_down = ""

    date = datetime.now().strftime("%A %d %B %Y %H:%M:%S")

    datas = all_data(symbol)

    data = datas[0]
    data_up = datas[1]
    data_down = datas[2]

    rsi_vwap_cmf = datas[3]
    rsi_vwap_cmf_up = datas[4]
    rsi_vwap_cmf_down = datas[5]

    prix = float(data['close'][39])
    prix_up = float(data_up['close'][39])
    prix_down = float(data_down['close'][39])

    prediction = prédiction_keras(data, rsi_vwap_cmf, loaded_model)
    prediction_up = prédiction_keras(data_up, rsi_vwap_cmf_up, loaded_model_up)
    prediction_down = prédiction_keras(
        data_down, rsi_vwap_cmf_down, loaded_model_down)

    état = f"programme toujours en cour d'exécution le : {date}"
    infos = f"prix de la crypto : {prix}, prix de la prédiction : {prediction}"
    up = f"prix crypto up : {prix_up}, prix de la prédiction : {prediction_up}"
    down = f"prix crypto down : {prix_down}, prix de la prédiction : {prediction_down}"

    msg = état + "\n" + infos + "\n" + up + "\n" + down

    message_webhook_état_bot(msg)

    sleep(dodo)
