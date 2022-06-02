from datetime import datetime
from main import *
import locale

symbol = sys.argv[1]
dodo = 60*14 + 58
effet_levier = 100


loaded_model, loaded_model_up, loaded_model_down = chargement_modele(symbol)

# Définition de la zone pour l'horodatage car la date était en anglais avec le module datetime
locale.setlocale(locale.LC_TIME, '')

argent = 150

while True:
    argent = requests.get("http://127.0.0.1:5000/argent")
    argent = int(argent.content.decode("utf-8"))

    date = datetime.now().strftime("%A %d %B %Y %H:%M:%S")

    datas = all_data(symbol)

    data = datas[0]
    data_up = datas[1]
    data_down = datas[2]

    rsi_vwap_cmf = datas[3]
    rsi_vwap_cmf_up = datas[4]
    rsi_vwap_cmf_down = datas[5]

    prix = data['close'][39]
    prix_up = data_up['close'][39]
    prix_down = data_down['close'][39]

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

    if prix < prediction and prix_up < prediction_up and prix_down > prediction_down:
        pos = requests.get("http://127.0.0.1:5000/presence_position")
        pos = pos.content.decode("utf-8")
        if pos == "None":
            ar = argent * 0, 5
            donnée = {"montant": ar, "prix_pos": prix,
                      "stop_loss": (prix * 0, 9983)}
            requests.get("http://127.0.0.1:5000/prise_position", data=donnée)
            msg = f"Prise de position avec {ar} euros * {2} au prix de {prix} euros, il reste {argent - ar}€"
            message_prise_position(msg, True)
        else:
            pos = ast.literal_eval(pos)
            prix = prix_temps_reel(symbol + "USDT")
            donnée = {"montant": pos[0], "prix_pos": pos[1],
                      "stop_loss": (prix * 0, 9983)}
            if pos[2] < donnée["stop_loss"]:
                requests.get(
                    "http://127.0.0.1:5000/prise_position", data=donnée)
    else:
        pos = requests.get("http://127.0.0.1:5000/presence_position")
        pos = pos.content.decode("utf-8")
        if pos != "None":
            pr = requests.get("http://127.0.0.1:5000/vente_position")
            pr = pr.content.decode("utf-8").split(";")
            msg = f"Vente de position au prix de {pr[0]}€, prix avant : {pr[1]}€, il reste {pr[2]}€"
            message_prise_position(msg, False)

    sleep(dodo)
