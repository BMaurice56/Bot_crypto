from main import *
import sys

symbol = sys.argv[1]
dodo = 60 * 60

# Création d'un objet binance et kucoin pour interagir avec leurs serveurs
# Création d'un objet ia
binance = Binance()
kucoin = Kucoin(symbol)
ia = IA(symbol)

# Waiting for every bot starting to count their number
sleep(10)

# dictionnaire qui stocke les deux symboles pour passer de l'un à l'autre facilement
dico_symbol = {1: kucoin.symbol_up, 0: kucoin.symbol_down}
dico_minimum = {1: kucoin.minimum_crypto_up, 0: kucoin.minimum_crypto_down}
dico_pourcentage_stop_loss = {1: 0.98, 0: 1.02}  # Prix stop-loss up et down

# Message discord
msg_discord = Message_discord()

# Drapeau qui permet de stopper les threads
event = Event()

# Info pour la fonction stop-loss manuel
symbol_stop_loss = ""
prix_stop_loss = 0.0

# Création de la variable avec le thread de stop-loss manuel
thread = Thread()

# On récupère l'état précédent du bot (Heure et stop-loss)
state = ia.state_bot("lecture")

# S'il y a bien un état inscrit dans le fichier (fichier non vide)
# alors, on peut vérifier si le bot ne s'est pas arrêté avant l'heure
if len(state) > 0:

    state = state.split(";")

    # Conversion de l'ancienne date sauvegardée et de la date actuelle en seconde
    ancienne_date = datetime.strptime(state[0], "%A %d %B %Y %H:%M:%S")

    ancienne_date = int(ancienne_date.strftime("%s"))

    # Suite à un bug faisant que la conversion directe en seconde donnait -1
    # On transforme la date en format lisible (le même que d'habitude) → format str
    # On retransforme la date en format date
    # Puis on vient enfin la mettre en seconde
    date = datetime.now(tz=ZoneInfo("Europe/Paris")
                        ).strftime("%A %d %B %Y %H:%M:%S")

    date = datetime.strptime(date, "%A %d %B %Y %H:%M:%S")

    date = int(date.strftime("%s"))

    crypto_up = kucoin.montant_compte(kucoin.symbol_up_simple)
    crypto_down = kucoin.montant_compte(kucoin.symbol_down_simple)

    # S'il y a bien un état dans le fichier, alors on peut attribuer les valeurs aux variables
    if state[1] != "" and state[2] != "0.0":
        symbol_stop_loss = state[1]
        prix_stop_loss = float(state[2])

        # S'il y a des cryptos en cours, alors on relance le stop loss
        if crypto_up > kucoin.minimum_crypto_up or crypto_down > kucoin.minimum_crypto_down:
            thread = kucoin.stoploss_manuel(
                symbol_stop_loss, prix_stop_loss, event)

    # Si le bot n'a pas attendu l'heure, alors il attend
    if date - ancienne_date < 3600:
        temps_dodo = 3600 - (date - ancienne_date) - 1
        sleep(temps_dodo)

# Stock le temps depuis la dernière position prise
# Si plusieurs heures passent sans l'exécution de l'ordre limite, alors on le baisse
time_last_position = -1
gain_limit_order = kucoin.pourcentage_gain

while True:
    t1 = time()

    buy_sell = False

    argent = kucoin.montant_compte(kucoin.devise)
    crypto_up = kucoin.montant_compte(kucoin.symbol_up_simple)
    crypto_down = kucoin.montant_compte(kucoin.symbol_down_simple)

    dico_montant = {1: crypto_up, 0: crypto_down}

    date = datetime.now(tz=ZoneInfo("Europe/Paris")
                        ).strftime("%A %d %B %Y %H:%M:%S")

    datas = binance.all_data(symbol)

    data = datas[0]
    data_up = datas[1]
    data_down = datas[2]

    rsi_vwap_cmf = datas[3]
    rsi_vwap_cmf_up = datas[4]
    rsi_vwap_cmf_down = datas[5]

    prix = float(data['close'][39])
    prix_up = float(data_up['close'][39])
    prix_down = float(data_down['close'][39])

    prediction = ia.prediction_keras(data, rsi_vwap_cmf, True)
    prediction_up = ia.prediction_keras(
        data_up, rsi_vwap_cmf_up, False)
    prediction_down = ia.prediction_keras(
        data_down, rsi_vwap_cmf_down, None)

    state_message = f"Bot {symbol} toujours en cour d'exécution le : {date}\n" + \
                    f"prix de la crypto : {prix}, prix de la prédiction : {prediction}\n" + \
                    f"prix crypto up : {prix_up}, prix de la prédiction : {prediction_up}\n" + \
                    f"prix crypto down : {prix_down}, prix de la prédiction : {prediction_down}"

    # msg_discord.message_canal("état_bot", state_message, 'état du bot !')

    # On augmente de 1 le temps qu'on a de position
    # Remis à zéro après si achat ou aucune crypto
    time_last_position += 1

    result_purchase = ia.validation_achat(
        prix, prix_up, prix_down, prediction, prediction_up, prediction_down)

    # S'il y a bien un signal d'achat, alors on peut passer à la suite
    if result_purchase is not None:
        if dico_montant[result_purchase] < dico_minimum[result_purchase]:
            # Si le thread du stop loss est toujours en vie
            # On l'arrête avant d'en créer un nouveau
            kill_thread(thread, event)

            # Si on possède toujours de l'autre crypto, on la vend
            if dico_montant[not result_purchase] > dico_minimum[not result_purchase]:
                kucoin.achat_vente(
                    dico_montant[not result_purchase], dico_symbol[not result_purchase], False)

                argent = kucoin.montant_compte(kucoin.devise)

            # Définition des variables pour le stop loss
            symbol_stop_loss = dico_symbol[result_purchase]
            prix_stop_loss = prix * dico_pourcentage_stop_loss[result_purchase]

            # Achat de la crypto voulu
            kucoin.achat_vente(argent, dico_symbol[result_purchase], True)

            # Gère le stop loss de façon manuel
            thread = kucoin.stoploss_manuel(
                symbol_stop_loss, prix_stop_loss, event)

            buy_sell = True
    """
    else:
        # Si le prix est supérieur à la prédiction (ou inversement)
        # Et qu'on n'a pas acheté et qu'on a des cryptos
        # Alors on vend
        if prix > prediction or prix_up > prediction_up or prix_down < prediction_down:
            if crypto_up > kucoin.minimum_crypto_up:
                kill_thread(thread, event)

                kucoin.achat_vente(crypto_up, kucoin.symbol_up, False)
                buy_sell = True

        if prix < prediction or prix_up < prediction_up or prix_down > prediction_down:
            if crypto_down > kucoin.minimum_crypto_down:
                kill_thread(thread, event)

                kucoin.achat_vente(crypto_down, kucoin.symbol_down, False)
                buy_sell = True
    """
    # Si plus de crypto ou achat, alors on remet à zéro les variables
    if buy_sell or crypto_up < kucoin.minimum_crypto_up and crypto_down < kucoin.minimum_crypto_down:
        time_last_position = 0
        gain_limit_order = kucoin.pourcentage_gain

    # Si cela fait trop longtemps que l'ordre a été placé sans être vendu, on le descend
    if time_last_position >= 4:
        gain_limit_order -= 0.0025

        # On a arrondi à la troisième décimale pour éviter toute une suite de zéro
        gain_limit_order = round(gain_limit_order, 4)

        # Si on descend à zéro, alors on ne replace plus l'ordre
        if gain_limit_order > 0.0:
            kucoin.ordre_vente_seuil(
                symbol_stop_loss, gain_limit_order)

        time_last_position = 0

    # On enregistre l'état du bot (dernière heure et stop loss)
    # Pour que si le bot soit arrêté et repart, qu'il soit au courant
    # S'il doit attendre ou non, et s'il doit relancer le stop loss
    state = f"{date};{symbol_stop_loss};{prix_stop_loss}"
    ia.state_bot("écriture", state)

    t2 = time()

    sleep(dodo - int(t2 - t1) - 1)
