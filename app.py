from datetime import datetime
from main import *
import locale

symbol = sys.argv[1]
dodo = 60*14 + 57
effet_levier = 100

# Définition de la zone pour l'horodatage car la date était en anglais avec le module datetime
locale.setlocale(locale.LC_TIME, '')

insert_data_historique_bdd(symbol)

argent = 150
position = {}

while True:
    date = datetime.now().strftime("%A %d %B %Y %H:%M:%S")

    data = donnée(symbol, "600 min ago UTC", "0 min ago UTC", 40)
    rsi_vwap_cmf = donnée(symbol, "225 min ago UTC", "0 min ago UTC", 15)

    prix = prix_temps_reel(symbol)

    data.close.values[-1] = prix
    rsi_vwap_cmf.close.values[-1] = prix

    insert_bdd("data", symbol, data)
    insert_bdd("rsi_vwap_cmf", symbol, rsi_vwap_cmf)

    prediction = prédiction(data, rsi_vwap_cmf)

    état = f"programme toujours en cour d'exécution le : {date}"
    infos = f"prix de la crypto : {prix}, prix de la prédiction : {prediction}"

    msg = état + "\n" + infos

    message_webhook_état_bot(msg)

    if prediction > prix:
        if position == {}:
            depense = argent * 0.5
            argent = argent - depense
            position[depense * effet_levier] = prix
            msg = f"Prise de position avec {depense} euros * {effet_levier} au prix de {prix} euros, il reste {argent}€"
            message_prise_position(msg, True)
            surveil = surveillance(
                symbol, argent, position, dodo, effet_levier)
            if surveil != None:
                argent = surveil
                position = {}

        else:
            sleep(dodo)
    else:
        if position != {}:
            for elt in position.items():
                argent_pos, prix_pos = elt

            gain = ((prix * argent_pos) / prix_pos) - argent_pos
            argent += argent_pos / effet_levier + gain
            msg = f"Vente de position au prix de {prix}€, prix avant : {prix_pos}€, gain de {gain}, il reste {argent}€"
            message_prise_position(msg, False)
            position = {}
            sleep(dodo)

        else:
            sleep(dodo)
