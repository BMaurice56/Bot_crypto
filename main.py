from discord_webhook import DiscordWebhook, DiscordEmbed
from time import sleep, perf_counter
from database import *
import copy
import sys

from keras.models import Sequential
from keras.layers import Dense


# Fonctions de prédiction


def prédiction_keras(donnée_serveur_data: pandas.DataFrame, donnée_serveur_rsi: pandas.DataFrame) -> float:
    """"""
    X, y = select_donnée_bdd("numpy")

    modele = Sequential()

    modele.add(Dense(100, input_dim=378, activation='relu'))
    modele.add(Dense(80, activation='relu'))
    modele.add(Dense(60, activation='relu'))
    modele.add(Dense(40, activation='relu'))
    modele.add(Dense(20, activation='relu'))

    modele.compile(loss='mean_squared_logarithmic_error',
                   optimizer='adam')

    modele.fit(X, y, epochs=100, batch_size=1)

    accuracy = modele.evaluate(X, y)

    print(f'Accuracy: {accuracy}')

    """
    sma = SMA(donnée_serveur_data)
    ema = EMA(donnée_serveur_data)
    macd = MACD(donnée_serveur_data)
    stochrsi = stochRSI(donnée_serveur_data)
    bb = bandes_bollinger(donnée_serveur_data)

    rsi = RSI(donnée_serveur_rsi)
    vwap = VWAP(donnée_serveur_rsi)
    cmf = chaikin_money_flow(donnée_serveur_rsi)

    ls = []

    for elt in sma:
        ls.append(elt)

    for elt in ema:
        ls.append(elt)

    for element in macd:
        for elt in element:
            ls.append(elt)

    for element in stochrsi:
        for elt in element:
            ls.append(elt)

    for element in bb:
        for elt in element:
            ls.append(elt)

    ls.append(rsi)
    ls.append(vwap)
    ls.append(cmf)

    df_liste = numpy.array(ls)

    predic = modele.predict(df_liste)

    return predic
    """


# Fonctions de surveillance de position


def surveillance(symbol: str, argent: int, position: dict, temps_execution: int, effet_levier: int) -> None or float:
    """
    Fonction qui prend en argument un symbol, l'argent du compte, la prise de position ou non et le temps d'execution de la fonction
    Et renvoie soit None soit l'argent sous forme d'un float si la position a été vendue
    Ex param :
    symbol : 'BTCEUR'
    argent : 150 euros
    position : {75 : 37000}
    temps_execution : 15*60 secondes
    effet_levier : 5
    """
    t1 = perf_counter()
    for elt in position.items():
        argent_pos, prix_pos = elt

    sleep(50)

    historique_prix = [prix_temps_reel(symbol)]
    while True:
        t2 = perf_counter()
        if t2 - t1 >= temps_execution:
            break
        elif t2 - t1 + 2*60 >= temps_execution:
            sleep(temps_execution - (t2 - t1))
            break

        prix = prix_temps_reel(symbol)

        if prix_pos <= prix and historique_prix[-1] <= prix:
            historique_prix.append(prix)
            sleep(2*60)
        if len(historique_prix) >= 2:
            if historique_prix[-2] > historique_prix[-1] > prix:
                gain = ((prix * argent_pos) / prix_pos) - argent_pos
                argent += argent_pos / effet_levier + gain
                msg = f"Vente de position au prix de {prix}€, prix avant : {prix_pos}€, gain de {gain}, il reste {argent}€"
                message_prise_position(msg, False)
                sleep(temps_execution - (t2 - t1))
                return argent

    return None


# Adresse du webhook discord
adr_webhook_prise_position = os.getenv("ADR_WEBHOOK_PRISE_POSITION")
adr_webhook_état_bot = os.getenv("ADR_WEBHOOK_ETAT_BOT")
adr_webhook_général = os.getenv("ADR_WEBHOOK_GENERAL")


def message_prise_position(message: str, prise_position: bool) -> None:
    """
    Fonction qui envoie un message au serveur discord au travers d'un webhook sur le canal de prise de position
    Envoie la prise ou vente de position, les gains, etc...
    Ex param :
    message : "vente d'une position etc...
    prise_position : True pour un achat et False pour une vente
    """
    webhook = DiscordWebhook(
        url=adr_webhook_prise_position, username="Bot crypto")

    if prise_position == True:
        embed = DiscordEmbed(title='Prise de position', color="03b2f8")
    else:
        embed = DiscordEmbed(title='Vente de position', color="03b2f8")

    embed.add_embed_field(name="Message :", value=message)
    webhook.add_embed(embed)
    webhook.execute()


def message_webhook_état_bot(message: str) -> None:
    """
    Fonction qui envoie un message au serveur discord au travers d'un webhook sur le canal éta bot
    Envoie l'état en cours du bot
    Ex param :
    message : "Bot toujours en cours d'execution ..."
    """
    webhook = DiscordWebhook(
        url=adr_webhook_état_bot, username="Bot crypto")

    embed = DiscordEmbed(title='Etat du bot !', color="03b2f8")
    embed.add_embed_field(name="Message :", value=message)
    webhook.add_embed(embed)
    webhook.execute()


def message_status_général(message: str) -> None:
    """
    Fonction qui envoie un message au serveur discord au travers d'un webhook sur le canal général
    Ex param :
    message : "Bot crypto est lancé"
    """
    webhook = DiscordWebhook(
        url=adr_webhook_général, username="Bot crypto", content=message)

    webhook.execute()
