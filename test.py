from main import *


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
