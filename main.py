from discord_webhook import DiscordWebhook, DiscordEmbed
from keras.models import Sequential, model_from_json
from time import perf_counter
from keras.layers import Dense
from database import *
import sys


# Fonction d'entrainement
def training_keras() -> None:
    """
    Fonction qui entraine les neurones et les sauvegardes
    """

    X, y = select_donnée_bdd("numpy")

    modele = Sequential()

    modele.add(Dense(50, input_dim=378, activation='relu'))
    modele.add(Dense(15, input_dim=378, activation='relu'))

    modele.compile(loss='mean_squared_logarithmic_error',
                   optimizer='adam')

    modele.fit(X, y, epochs=50, batch_size=4)

    modele_json = modele.to_json()

    with open("modele.json", "w") as json_file:
        json_file.write(modele_json)

    modele.save_weights("modele.h5")

    print("Modèle sauvegarder !")


# Fonction de prédiction
def prédiction_keras(donnée_serveur_data: pandas.DataFrame, donnée_serveur_rsi: pandas.DataFrame, Modèle) -> float:
    """
    Fonction qui fait les prédiction et renvoie le prix potentiel de la crypto
    """

    ls = [SMA(donnée_serveur_data), EMA(donnée_serveur_data), harami(donnée_serveur_data),
          doji(donnée_serveur_data), ADX(donnée_serveur_data),
          KAMA(donnée_serveur_data), T3(
              donnée_serveur_data), TRIMA(donnée_serveur_data),
          PPO(donnée_serveur_data), ultimate_oscilator(donnée_serveur_data),
          MACD(donnée_serveur_data), stochRSI(donnée_serveur_data), bandes_bollinger(donnée_serveur_data)]

    ls += [RSI(donnée_serveur_rsi), VWAP(donnée_serveur_rsi), chaikin_money_flow(
        donnée_serveur_rsi), CCI(donnée_serveur_rsi), MFI(donnée_serveur_rsi), LinearRegression(
        donnée_serveur_rsi), TSF(donnée_serveur_rsi), aroon_oscilator(donnée_serveur_rsi), williams_R(
        donnée_serveur_rsi), ROC(donnée_serveur_rsi), OBV(donnée_serveur_rsi), MOM(donnée_serveur_rsi)]

    donnée_prédiction = []

    cpt = 1
    for element in ls:
        if cpt <= 10 or cpt >= 23:
            for nb in element:
                donnée_prédiction.append(nb)
        elif cpt <= 13:
            for liste in element:
                for nb in liste:
                    donnée_prédiction.append(nb)
        elif cpt <= 22:
            donnée_prédiction.append(element)

        cpt += 1

    np_liste = numpy.array([donnée_prédiction])

    predic = moyenne(Modèle.predict(np_liste)[0])

    return predic


# Fonction de chargement des modèles
def chargement_modele(symbol):
    """
    Fonction qui charge et renvoie les trois modèles
    """

    json_file = open(f'Modèle/SPOT/{symbol}/{symbol}USDT/modele.json', 'r')
    json_file_up = open(
        f'Modèle/SPOT_EFFET_LEVIER/{symbol}/{symbol}UPUSDT/modele.json', 'r')
    json_file_down = open(
        f'Modèle/SPOT_EFFET_LEVIER/{symbol}/{symbol}DOWNUSDT/modele.json', 'r')

    loaded_model_json = json_file.read()
    loaded_model_json_up = json_file_up.read()
    loaded_model_json_down = json_file_down.read()

    json_file.close()
    json_file_up.close()
    json_file_down.close()

    loaded_model = model_from_json(loaded_model_json)
    loaded_model_up = model_from_json(loaded_model_json_up)
    loaded_model_down = model_from_json(loaded_model_json_down)

    loaded_model.load_weights(f"Modèle/SPOT/{symbol}/{symbol}USDT/modele.h5")
    loaded_model_up.load_weights(
        f"Modèle/SPOT_EFFET_LEVIER/{symbol}/{symbol}UPUSDT/modele.h5")
    loaded_model_down.load_weights(
        f"Modèle/SPOT_EFFET_LEVIER/{symbol}/{symbol}DOWNUSDT/modele.h5")

    loaded_model.compile(
        loss='mean_squared_logarithmic_error', optimizer='adam')
    loaded_model_up.compile(
        loss='mean_squared_logarithmic_error', optimizer='adam')
    loaded_model_down.compile(
        loss='mean_squared_logarithmic_error', optimizer='adam')

    return loaded_model, loaded_model_up, loaded_model_down


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
