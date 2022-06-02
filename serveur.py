from flask import Flask
from multiprocessing import Process
from main import *
import os
import csv

app = Flask(__name__)

app.secret_key = os.urandom(20)

argents = 5000
effet_levier = 2

prix_btc = 0

symbol = sys.argv[1]

@app.route('/')
def home():
    """"""

    return "toto"


@app.route('/prise_position')
def prise_position():
    """
    Fonction qui écrit la position prise dans le csv
    """
    data = request.form

    montant = int(data["montant"]) * effet_levier
    prix_pos = data["prix_pos"]
    stop_loss = data["stop_loss"]

    global argents
    argents = argents - (montant / effet_levier)

    fichier = open("position.csv", "w")

    writer = csv.writer(fichier)
    writer.writerow([montant, prix_pos, stop_loss])

    fichier.close()

    return "succes"


@app.route('/vente_position')
def vente_position():
    """
    Fonction qui vend la position prise
    """
    fichier = open("position.csv", "r")

    data = [x for x in csv.reader(fichier)][0]

    global prix_btc
    prix_btc = prix_temps_reel(f"{symbol}USDT")

    global argents
    argents = argents + ((prix_btc *
                         float(data[0])) / float(data[1]) / effet_levier)

    open("position.csv", "w")

    return f"{prix_btc};{data[1]};{argents}"


@app.route('/presence_position')
def presence_position():
    """
    Fonction qui vérifie s'il y a une position de prise ou non
    """
    fichier = open("position.csv")

    data = [x for x in csv.reader(fichier)]

    if data == []:
        return "None"
    else:
        return str(data[0])


@app.route("/argent")
def argent():
    """
    Fonction qui renvoie le montant en argent restant
    """

    return str(argents)


def check_position():
    """
    Fonction qui vérifie si le stop_loss n'a pas été atteint
    Et si c'est le cas, alors on vend la position
    """
    while True:
        fichier = open("position.csv", "r")
        data = [x for x in csv.reader(fichier)]
        if data != []:
            data = ast.literal_eval(data[0])
            global prix_btc
            prix_btc = prix_temps_reel(f"{symbol}USDT")
            if prix_btc < data[-1]:
                vente_position()
        sleep(1)



p = Process(target=check_position)
p.start()

app.run()
