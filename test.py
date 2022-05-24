#from main import *
import requests
#balance_usdt = client.get_asset_balance(asset='USDT')['free']
donnée = {"montant" : 3000, "prix_pos" : 36000, "stop_loss" : 35950}
#toto = requests.get("http://127.0.0.1:5000/prise_position", data=donnée)
#toto2 = requests.get("http://127.0.0.1:5000/argent", data=donnée)
#toto3 = requests.get("http://127.0.0.1:5000/vente_position", data=donnée)
#print("toto.content", toto2.content, "toto3.content")

pos = requests.get("http://127.0.0.1:5000/presence_position")
pos = pos.content
print(pos.decode("utf-8"))


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