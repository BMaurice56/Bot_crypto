from main import *


def presence_position(type_ordre: str) -> None or dict:
    """
    Fonction qui renvoie les positions en cours sur une pair de crypto précis
    Ex paramètre :
    type_ordre : market ou stoploss
    """
    if type_ordre == "market":
        endpoint = "/api/v1/orders?status=active"
    
    elif type_ordre == "stoploss":
        endpoint = "/api/v1/stop-order?status=active"

    entête = headers("GET", endpoint)

    position = requests.get(api + endpoint, headers=entête)

    resultat = json.loads(position.content.decode("utf-8"))['data']['items']

    if resultat == []:
        return None
    else:
        return resultat[0]


def supression_position():
    """
    Fonction qui supprime une ou plusieurs positions
    """

"""
money = montant_compte('USDT')

info = {"montant": money, "symbol": "BTC3S-USDT", "achat_vente": True}

prise_position(info)
"""
toto = presence_position("market")

print(toto)

toto = presence_position("stoploss")

print(toto, type(toto))


"""
toto = False

if toto == True:
    money = montant_compte('USDT')

    info = {"montant": money, "symbol": "BTC3S-USDT", "achat_vente": True}

    prise_position(info)
else:
    money = montant_compte('BTC3S')

    info = {"montant": money, "symbol": "BTC3S-USDT", "achat_vente": False}

    prise_position(info)

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
