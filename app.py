from main import *
from datetime import datetime

symbol = sys.argv[1]
dodo = 60*14 + 56
effet_levier = 100

insert_data_historique_bdd(symbol)

argent = 150
position = {}

while True:
    date = datetime.now().strftime("%A %d %B %Y %H:%M:%S")

    donnée_bdd_rsi = select_rsi_vwap_cmf_bdd()
    donnée_bdd_data = select_data_bdd()

    rsi_vwap_cmf = donnée(symbol, "225 min ago UTC", "0 min ago UTC", 15)
    data = donnée(symbol, "600 min ago UTC", "0 min ago UTC", 40)

    insert_bdd("rsi_vwap_cmf", symbol, rsi_vwap_cmf)
    insert_bdd("data", symbol, data)

    liste_all = []
    liste_2_to_5 = []

    predic1 = prediction_rsi_wvap_cmf(donnée_bdd_rsi, rsi_vwap_cmf)
    predic2 = prediction_liste_sma_ema(donnée_bdd_data, data)
    predic3 = prediction_liste_macd(donnée_bdd_data, data)
    predic4 = prediction_liste_stochrsi(donnée_bdd_data, data)
    predic5 = prediction_liste_bandes_b(donnée_bdd_data, data)

    for elt in predic1:
        liste_all.append(elt)
    for elt in predic2:
        liste_all.append(elt)
        liste_2_to_5.append(elt)
    for elt in predic3:
        liste_all.append(elt)
        liste_2_to_5.append(elt)
    for elt in predic4:
        liste_all.append(elt)
        liste_2_to_5.append(elt)
    for elt in predic5:
        liste_all.append(elt)
        liste_2_to_5.append(elt)

    predic6 = prediction_historique(select_prediction_hist_all(), [
                                    moyenne(liste_2_to_5), moyenne(predic1)])

    liste_all.append(predic6)

    moyenne_liste = moyenne(liste_all)

    prix = prix_temps_reel(symbol)

    état = f"programme toujours en cour d'exécution le : {date}"
    infos = f"prix de la crypto : {prix}, moyenne des prédictions : {moyenne_liste}"

    msg = état + "\n" + infos

    message_webhook_état_bot(msg)

    if moyenne_liste > prix:
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

    prix_temps_r = prix_temps_reel(symbol)

    liste_bdd = [moyenne_liste] + liste_all + [prix_temps_r]

    insert_bdd("résultat", symbol, liste_bdd)
    insert_bdd("simple_insert_predic_data", symbol, [
               moyenne(liste_2_to_5), prix_temps_r])
    insert_bdd("simple_insert_predic_rsi", symbol,
               [moyenne(predic1), prix_temps_r])
