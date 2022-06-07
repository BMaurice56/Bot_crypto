#from main import *
fichier = open("messages.txt", "r")

text = fichier.read().split(chr(32))

fichier.close()

for i in range(5):
    for ch in text:
        if ch == ":" or ch == "crypto" or ch == "up" or ch == "down" or ch == "prix" or ch == "de" or ch == "la" or ch == "prédiction":
            text.remove(ch)
        elif "\n" in ch:
            element = ch.split("\n")[0]
            index = text.index(ch)
            text[index] = element

for i in range(5):
    for element in text:
        if "programme" in element:
            index = text.index(element)
            index_p = element.index("p")
            text[index] = element[:index_p]
            text = text[:index + 1] + text[index + 11:]

for i in range(5):
    for elt in text:
        if "," in elt:
            indice = text.index(elt)
            text[indice] = elt[:-1]

for i in range(len(text)):
    text[i] = float(text[i])

fh = open("messages.txt", "w")

for element in text:
    fh.write(str(element) + "\n")

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
