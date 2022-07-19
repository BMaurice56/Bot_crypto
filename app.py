from datetime import datetime
from main import *
import locale

# symbol = sys.argv[1]
symbol = "BTC"
dodo = 60*59 + 28

loaded_model, loaded_model_up, loaded_model_down = chargement_modele(symbol)

# Définition de la zone pour l'horodatage car la date était en anglais avec le module datetime
locale.setlocale(locale.LC_TIME, '')

while True:
    argent = montant_compte("USDT")
    btcup = montant_compte("BTC3L")
    btcdown = montant_compte("BTC3S")

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

    if prix < prediction and prix_up < prediction_up and prix_down > prediction_down and prediction_down < 0.3:
        if btcup > 30:
            pass
        elif btcdown > 2:
            # Vente de la crypto descendante
            achat_vente(btcdown, "BTC3S-USDT", False)

            # Achat de la crypto montante
            achat_vente(argent, "BTC3L-USDT", True)

        else:
            achat_vente(argent, "BTC3L-USDT", True)

    elif prix > prediction and prix_up > prediction_up and prix_down < prediction_down:
        if btcdown > 2:
            pass
        elif btcup > 30:
            # Vente de la crypto montant
            achat_vente(btcup, "BTC3L-USDT", False)

            # Achat de la crypto descendante
            achat_vente(argent, "BTC3S-USDT", True)

        else:
            achat_vente(argent, "BTC3S-USDT", True)

    btcup = montant_compte("BTC3L")
    btcdown = montant_compte("BTC3S")

    if btcup > 30:
        remonter_stoploss("BTC3L-USDT", 30)

    elif btcdown > 2:
        remonter_stoploss("BTC3S-USDT", 30)

    else:
        sleep(dodo)

    sleep(28)
