from main import *


def prise_position(info: dict):
    """
    Fonction qui prend une position soit d'achat soit de vente et place un stoploss
    Ex paramètres :
    info : {
    "montant" : "50",
    "symbol" : "BTC3S-USDT",
    "achat_vente" : "True" (pour achat)
    }
    """

    id_position = randint(0, 100_000_000)

    endpoint = "/api/v1/orders"

    if info["achat_vente"] == True:
        achat = "buy"
        type_achat = "funds"
    else:
        achat = "sell"
        type_achat = "size"

    param = {"clientOid": id_position,
             "side": achat,
             "symbol": info["symbol"],
             'type': "market",
             type_achat: str(info["montant"])}

    param = json.dumps(param)

    now = int(time.time() * 1000)

    str_to_sign = str(now) + 'POST' + endpoint + param

    signature = base64.b64encode(
        hmac.new(kucoin_api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())

    passphrase = base64.b64encode(hmac.new(kucoin_api_secret.encode(
        'utf-8'), kucoin_phrase_securite.encode('utf-8'), hashlib.sha256).digest())

    headers = {
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": str(now),
        "KC-API-KEY": kucoin_api_key,
        "KC-API-PASSPHRASE": passphrase,
        "KC-API-KEY-VERSION": "2",
        "Content-Type": "application/json"
    }

    prise_position = requests.post(api + endpoint, headers=headers, data=param)

    sleep(1)

    if info["achat_vente"] == True:
        id_stoploss = randint(0, 100_000_000)

        fichier = open("stoploss.txt", "w")
        fichier.write(str(id_stoploss))
        fichier.close()

        endpoint2 = "/api/v1/stop-order"

        symbol = info["symbol"].split("-")[0]

        money = montant_compte(symbol)

        prix = prix_temps_reel_kucoin(info["symbol"])

        param = {"clientOid": id_stoploss,
                 "side": "sell",
                 "symbol": info["symbol"],
                 'stop': "loss",
                 "stopPrice": str(arrondi(prix * 0.996)),
                 "price": str(arrondi(prix * 0.991)),
                 "size": str(arrondi(money))}

        param = json.dumps(param)

        now = int(time.time() * 1000)

        str_to_sign = str(now) + 'POST' + endpoint2 + param

        signature = base64.b64encode(
            hmac.new(kucoin_api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())

        passphrase = base64.b64encode(hmac.new(kucoin_api_secret.encode(
            'utf-8'), kucoin_phrase_securite.encode('utf-8'), hashlib.sha256).digest())

        headers = {
            "KC-API-SIGN": signature,
            "KC-API-TIMESTAMP": str(now),
            "KC-API-KEY": kucoin_api_key,
            "KC-API-PASSPHRASE": passphrase,
            "KC-API-KEY-VERSION": "2",
            "Content-Type": "application/json"
        }

        prise_position = requests.post(
            api + endpoint2, headers=headers, data=param)

        return prise_position, prise_position.content


money = arrondi(montant_compte('USDT'))

info = {"montant": money, "symbol": "BTC3S-USDT", "achat_vente": True}

print(prise_position(info))

"""


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
