from main import *


"""
toto = False

if toto == True:
    money = montant_compte('USDT')

    info = {"montant": money, "symbol": "BTC3S-USDT", "achat_vente": True}

    print(prise_position(info))
else:
    money = montant_compte('BTC3S')

    info = {"montant": money, "symbol": "BTC3S-USDT", "achat_vente": False}

    print(prise_position(info))

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
"""

"""
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
"""
