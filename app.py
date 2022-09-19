from backports.zoneinfo import ZoneInfo
from datetime import datetime
from main import *
import locale

# symbol = sys.argv[1]
symbol = "BTC"
symbol_up_kucoin = "BTC3L-USDT"
symbol_down_kucoin = "BTC3S-USDT"
dodo = 60*60

loaded_model, loaded_model_up, loaded_model_down = chargement_modele(symbol)

# Définition de la zone pour l'horodatage car la date était en anglais avec le module datetime
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

# On lance la fonction qui permet de garder à jour l'id de l'ordre limite dans le fichier
p = Process(target=update_id_ordre_limite)
p.start()

symbol_stoploss = ""
prix_stoploss = 0.0

p2 = Process(target=stoploss_manuel, args=[symbol_stoploss, prix_stoploss])


# On récupère l'état précédent du bot (Heure et divergence)
etat = etat_bot("lecture").split(";")

# Conversion de l'ancienne date sauvegarder et de la date actuelle en seconde
ancienne_date = datetime.strptime(etat[0], "%A %d %B %Y %H:%M:%S")

ancienne_date = int(ancienne_date.strftime("%s"))

# Suite à un bug faisant que la conversion directe en seconde donnait -1
# On transforme la date en format lisible (le même que d'habitude) -> format str
# On retransforme la date en format date
# Puis on vient enfin la mettre en seconde
date = datetime.now(tz=ZoneInfo("Europe/Paris")
                    ).strftime("%A %d %B %Y %H:%M:%S")

date = datetime.strptime(date, "%A %d %B %Y %H:%M:%S")

date = int(date.strftime("%s"))

# Si il y a bien eu 1 heure d'attente, on peut passer au prédiction
# Sinon on attend jusqu'a l'heure prévu
if date - ancienne_date < 3600:
    btcup = montant_compte("BTC3L")
    btcdown = montant_compte("BTC3S")
    if btcup > 50 or btcdown > 5:
        symbol_stoploss = etat[1]
        prix_stoploss = float(etat[2])

        p2.start()

    temps_dodo = 3600 - (date - ancienne_date)
    sleep(temps_dodo)


compteur_position_heure = 0


while True:
    t1 = perf_counter()

    compteur_position_heure += 1

    argent = montant_compte("USDT")
    btcup = montant_compte("BTC3L")
    btcdown = montant_compte("BTC3S")

    # Si l'on a plus de trois heures avec la même position qui ne s'est pas exécutés
    # Alors on vend pour repartir de plus belle
    if compteur_position_heure >= 3:
        compteur_position_heure = 0

        statut_p2 = p2.is_alive()
        if statut_p2 == True:
            p2.kill()

        if btcup > 50:
            achat_vente(btcup, symbol_up_kucoin, False)

        if btcdown > 5:
            achat_vente(btcdown, symbol_down_kucoin, False)

        argent = montant_compte("USDT")
        btcup = montant_compte("BTC3L")
        btcdown = montant_compte("BTC3S")

    date = datetime.now(tz=ZoneInfo("Europe/Paris")
                        ).strftime("%A %d %B %Y %H:%M:%S")

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

    if prix < prediction and prix_up < prediction_up and prix_down > prediction_down and prediction_down <= 0.03 and prediction_up - prix_up >= 0.045:
        if btcup > 50:
            pass

        elif btcdown > 5:
            statut_p2 = p2.is_alive()
            if statut_p2 == True:
                p2.kill()

            # Vente de la crypto descendante
            achat_vente(btcdown, symbol_down_kucoin, False)

            argent = montant_compte("USDT")

            symbol_stoploss = symbol_up_kucoin
            prix_stoploss = prix * 0.97

            # Achat de la crypto montante
            achat_vente(argent, symbol_up_kucoin, True)

            compteur_position_heure = 0

            p2.start()

        else:
            statut_p2 = p2.is_alive()
            if statut_p2 == True:
                p2.kill()

            symbol_stoploss = symbol_up_kucoin
            prix_stoploss = prix * 0.97

            achat_vente(argent, symbol_up_kucoin, True)

            compteur_position_heure = 0

            p2.start()

    elif prix > prediction and prix_up > prediction_up and prix_down < prediction_down:
        if btcdown > 5:
            pass

        elif btcup > 50:
            statut_p2 = p2.is_alive()
            if statut_p2 == True:
                p2.kill()

            # Vente de la crypto montant
            achat_vente(btcup, symbol_up_kucoin, False)

            symbol_stoploss = symbol_down_kucoin
            prix_stoploss = prix * 1.03

            argent = montant_compte("USDT")

            # Achat de la crypto descendante
            achat_vente(argent, symbol_down_kucoin, True)

            compteur_position_heure = 0

            p2.start()

        else:
            symbol_stoploss = symbol_down_kucoin
            prix_stoploss = prix * 1.03

            statut_p2 = p2.is_alive()
            if statut_p2 == True:
                p2.kill()

            achat_vente(argent, symbol_down_kucoin, True)

            compteur_position_heure = 0

            p2.start()

    # On enregistre l'état du bot (dernière heure et divergence)
    # Pour que si le bot est arrêté et repart, qu'il soit au courant
    # S'il doit attendre ou non
    state = date + ";" + symbol_stoploss + ";" + str(prix_stoploss)
    etat_bot("écriture", state)

    t2 = perf_counter()

    sleep(dodo - int(t2 - t1) - 2)
