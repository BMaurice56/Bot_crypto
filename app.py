from datetime import datetime
from backports.zoneinfo import ZoneInfo
from main import *
import locale

# symbol = sys.argv[1]
symbol = "BTC"
symbol_up_kucoin = "BTC3L-USDT"
symbol_down_kucoin = "BTC3S-USDT"
dodo = 60*59 + 55
dodo_remonter_stoploss = 29

loaded_model, loaded_model_up, loaded_model_down = chargement_modele(symbol)

# Définition de la zone pour l'horodatage car la date était en anglais avec le module datetime
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

# Variable gloable qui permet de savoir s'il y a eu une divergence ou non juste avant
divergence_stoploss = False

# On lance en parallèle la fonction qui maintien à jour l'id du stoploss dans le fichier
p = Process(target=update_id_stoploss)
p.start()

while True:
    argent = montant_compte("USDT")
    btcup = montant_compte("BTC3L")
    btcdown = montant_compte("BTC3S")

    divergence = False
    achat = False

    date = datetime.now(tz=ZoneInfo("Europe/Paris")).strftime("%A %d %B %Y %H:%M:%S")

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

    message_état_bot(msg)

    if prix < prediction and prix_up < prediction_up and prix_down > prediction_down and prediction_down < 0.3 and prediction_up - prix_up >= 0.05:
        if btcup > 30:
            continuation_prediction(symbol_up_kucoin)

        elif btcdown > 2:
            # Vente de la crypto descendante
            achat_vente(btcdown, symbol_down_kucoin, False)

            # Achat de la crypto montante
            achat_vente(argent, symbol_up_kucoin, True)

            achat = True

            divergence_stoploss = False

        else:
            achat_vente(argent, symbol_up_kucoin, True)

            achat = True

            divergence_stoploss = False

    elif prix > prediction and prix_up > prediction_up and prix_down < prediction_down:
        if btcdown > 2:
            continuation_prediction(symbol_down_kucoin)

        elif btcup > 30:
            # Vente de la crypto montant
            achat_vente(btcup, symbol_up_kucoin, False)

            # Achat de la crypto descendante
            achat_vente(argent, symbol_down_kucoin, True)

            achat = True

            divergence_stoploss = False

        else:
            achat_vente(argent, symbol_down_kucoin, True)

            achat = True

            divergence_stoploss = False

    else:
        divergence = True
        divergence_stoploss = True

    # Après le passage de l'achat/vente, on regarde combien on a au final
    # Et après on lance la fonction qui remonte le stoploss
    btcup = montant_compte("BTC3L")
    btcdown = montant_compte("BTC3S")

    if divergence == False:
        if btcup > 30:
            # S'il n'y a pas eu d'achat et divergence stoploss est a True,
            # Alors on sort d'une divergence dont l'achat a été fait avant
            if achat == False and divergence_stoploss == True:
                stoploss_sortie_divergence(symbol_up_kucoin)

            remonter_stoploss(symbol_up_kucoin,
                              dodo_remonter_stoploss, stopPrice, price)

        elif btcdown > 2:
            # S'il n'y a pas eu d'achat et divergence stoploss est a True,
            # Alors on sort d'une divergence dont l'achat a été fait avant
            if achat == False and divergence_stoploss == True:
                stoploss_sortie_divergence(symbol_down_kucoin)

            remonter_stoploss(symbol_down_kucoin,
                              dodo_remonter_stoploss, stopPrice, price)

    else:
        if btcup > 30:
            remonter_stoploss(symbol_up_kucoin,
                              dodo_remonter_stoploss, 0.99, 0.9875)

        elif btcdown > 2:
            remonter_stoploss(symbol_down_kucoin,
                              dodo_remonter_stoploss, 0.99, 0.9875)

        else:
            sleep(dodo)
