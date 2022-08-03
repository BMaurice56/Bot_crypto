from datetime import datetime
from main import *
import locale

# symbol = sys.argv[1]
symbol = "BTC"
symbol_up_kucoin = "BTC3L-USDT"
symbol_down_kucoin = "BTC3S-USDT"
dodo = 60*59 + 40

loaded_model, loaded_model_up, loaded_model_down = chargement_modele(symbol)

# Définition de la zone pour l'horodatage car la date était en anglais avec le module datetime
locale.setlocale(locale.LC_TIME, '')

while True:
    argent = montant_compte("USDT")
    btcup = montant_compte("BTC3L")
    btcdown = montant_compte("BTC3S")

    divergence = False

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

    if prix < prediction and prix_up < prediction_up and prix_down > prediction_down and prediction_down < 0.3 and prediction_up - prix_up >= 0.05:
        if btcup > 30:
            # On vérifie si il y a présence ou non d'ordre
            stoploss = presence_position("stoploss", symbol_up_kucoin)
            market = presence_position("market", symbol_up_kucoin)

            # S'il y en aucun, on place un stoploss par sécurité
            if stoploss == None and market == None:
                création_stoploss(symbol_up_kucoin)

            # Sinon s'il y a qu'un ordre limite market, on check si lorsqu'on place un stoploss
            # si le prix du stoploss est supérieur ou non à l'ordre limite
            elif stoploss == None and market != None:
                prix_position = float(market['price'])

                nouveau_prix = arrondi(
                    prix_temps_reel_kucoin(symbol_up_kucoin) * price)

                if prix_position < nouveau_prix:
                    suppression_ordre("market", market['id'])
                    création_stoploss(symbol_up_kucoin)
                else:
                    pass

            # Sinon s'il y a un stoploss et un ordre market
            # on regarde lequel on garde
            elif stoploss != None and market != None:
                if float(stoploss['price']) >= float(market['price']):
                    suppression_ordre("market", market['id'])
                else:
                    suppression_ordre("stoploss")

            else:
                pass

        elif btcdown > 2:
            # Vente de la crypto descendante
            achat_vente(btcdown, symbol_down_kucoin, False)

            # Achat de la crypto montante
            achat_vente(argent, symbol_up_kucoin, True)

        else:
            achat_vente(argent, symbol_up_kucoin, True)

    elif prix > prediction and prix_up > prediction_up and prix_down < prediction_down:
        if btcdown > 2:
            # On vérifie si il y a présence ou non d'ordre
            stoploss = presence_position("stoploss", symbol_down_kucoin)
            market = presence_position("market", symbol_down_kucoin)

            # S'il y en aucun, on place un stoploss par sécurité
            if stoploss == None and market == None:
                création_stoploss(symbol_down_kucoin)

            # Sinon s'il y a qu'un ordre limite market, on check si lorsqu'on place un stoploss
            # si le prix du stoploss est supérieur ou non à l'ordre limite
            elif stoploss == None and market != None:
                prix_position = float(market['price'])

                nouveau_prix = arrondi(
                    prix_temps_reel_kucoin(symbol_down_kucoin) * price)

                if prix_position < nouveau_prix:
                    suppression_ordre("market", market['id'])
                    création_stoploss(symbol_down_kucoin)
                else:
                    pass

            # Sinon s'il y a un stoploss et un ordre market
            # on regarde lequel on garde
            elif stoploss != None and market != None:
                if float(stoploss['price']) >= float(market['price']):
                    suppression_ordre("market", market['id'])
                else:
                    suppression_ordre("stoploss")

            else:
                pass

        elif btcup > 30:
            # Vente de la crypto montant
            achat_vente(btcup, symbol_up_kucoin, False)

            # Achat de la crypto descendante
            achat_vente(argent, symbol_down_kucoin, True)

        else:
            achat_vente(argent, symbol_down_kucoin, True)

    else:
        divergence = True

    # Après le passage de l'achat/vente, on regarde combien on a au final
    # Et après on lance la fonction qui remonte le stoploss
    btcup = montant_compte("BTC3L")
    btcdown = montant_compte("BTC3S")

    if divergence == False:
        if btcup > 30:
            remonter_stoploss(symbol_up_kucoin, 30, stopPrice, price)

        elif btcdown > 2:
            remonter_stoploss(symbol_down_kucoin, 30, stopPrice, price)

        else:
            sleep(dodo)

    else:
        if btcup > 30:
            remonter_stoploss(symbol_up_kucoin, 30, 0.99, 0.9875)

        elif btcdown > 2:
            remonter_stoploss(symbol_down_kucoin, 30, 0.99, 0.9875)

        else:
            sleep(dodo)
