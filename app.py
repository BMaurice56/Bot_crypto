from datetime import datetime
from main import *
import locale

# symbol = sys.argv[1]
symbol = "BTC"
dodo = 60*59 + 58

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
        if btcup > 2:
            pass
        elif btcdown > 2:
            # Vente de la crypto descendante
            info = {"montant": btcdown,
                    "symbol": "BTC3S-USDT", "achat_vente": False}

            ordre = prise_position(info)

            data_ordre = information_ordre(ordre)

            argent = montant_compte('USDT')

            msg = f"Vente de position au prix de {float(data_ordre['price'])}$, il reste {argent} usdt"
            message_prise_position(msg, False)
            ########################################################################

            # Achat de la crypto montante
            info2 = {"montant": argent,
                     "symbol": "BTC3L-USDT", "achat_vente": True}

            ordre2 = prise_position(info2)

            data_ordre2 = information_ordre(ordre2)

            msg = f"Prise de position avec {argent} usdt au prix de {float(data_ordre2['price'])}$, il reste {montant_compte('USDT')} usdt"
            message_prise_position(msg, True)
            ########################################################################

        else:
            info = {"montant": argent,
                    "symbol": "BTC3L-USDT", "achat_vente": True}

            ordre = prise_position(info)

            data_ordre = information_ordre(ordre)

            msg = f"Prise de position avec {argent} usdt au prix de {float(data_ordre['price'])}$, il reste {montant_compte('USDT')} usdt"
            message_prise_position(msg, True)

    elif prix > prediction and prix_up > prediction_up and prix_down < prediction_down:
        if btcdown > 2:
            pass
        elif btcup > 2:
            # Vente de la crypto montant
            info = {"montant": btcup,
                    "symbol": "BTC3L-USDT", "achat_vente": False}

            ordre = prise_position(info)

            data_ordre = information_ordre(ordre)

            argent = montant_compte('USDT')

            msg = f"Vente de position au prix de {float(data_ordre['price'])}$, il reste {argent} usdt"
            message_prise_position(msg, False)
            ########################################################################

            # Achat de la crypto descendante
            info2 = {"montant": argent,
                     "symbol": "BTC3S-USDT", "achat_vente": True}

            ordre2 = prise_position(info2)

            data_ordre2 = information_ordre(ordre2)

            msg = f"Prise de position avec {argent} usdt au prix de {float(data_ordre2['price'])}$, il reste {montant_compte('USDT')} usdt"
            message_prise_position(msg, True)
            ########################################################################

        else:
            info = {"montant": argent,
                    "symbol": "BTC3S-USDT", "achat_vente": True}

            ordre = prise_position(info)

            data_ordre = information_ordre(ordre)

            msg = f"Prise de position avec {argent} usdt au prix de {float(data_ordre['price'])}$, il reste {montant_compte('USDT')} usdt"
            message_prise_position(msg, True)

    btcup = montant_compte("BTC3L")
    btcdown = montant_compte("BTC3S")

    if btcup > 2:
        remonter_stoploss("BTC3L-USDT", 30)

    elif btcdown > 2:
        remonter_stoploss("BTC3S-USDT", 30)

    sleep(28)
