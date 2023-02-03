from main import *

symbol = "BTC"
dodo = 60*60

# Création d'un objet binance et kucoin pour interagir avec leurs serveurs
binance = Binance()
kucoin = Kucoin(symbol)

# Message discord
msg_discord = Message_discord()

# Chargement des modèles d'ia pour les prédictions
loaded_model, loaded_model_up, loaded_model_down = IA.chargement_modele(symbol)

# Info pour la fonction stoploss manuel
symbol_stoploss = ""
prix_stoploss = 0.0

# Création de la variable avec le processus de stoploss manuel
p2 = Process(target=kucoin.stoploss_manuel, args=[
             symbol_stoploss, prix_stoploss])

# On récupère l'état précédent du bot (Heure et divergence)
etat = IA.etat_bot("lecture")

# S'il y a bien un état inscrit dans le fichier (fichier non vide)
# alors on peut vérifier si le bot ne s'est pas arrêté avant l'heure
if len(etat) > 0:

    etat = etat.split(";")

    # Conversion de l'ancienne date sauvegarder et de la date actuelle en seconde
    ancienne_date = datetime.strptime(etat[0], "%A %d %B %Y %H:%M:%S")

    ancienne_date = int(ancienne_date.strftime("%s"))

    # Suite à un bug faisant que la conversion directe en seconde donnait -1
    # On transforme la date en format lisible (le même que d'habitude) -> format str
    # On retransforme la date en format date
    # Puis on vient enfin la mettre en seconde
    date = datetime.now(tz=ZoneInfo("Europe/Paris")
                        ).strftime("%A %d %B %Y %H:%M:%S")

    date = datetime.strptime(date, "%A %d %B %Y %H:%M:%S")

    date = int(date.strftime("%s"))

    crypto_up = kucoin.montant_compte(kucoin.symbol_up_simple)
    crypto_down = kucoin.montant_compte(kucoin.symbol_down_simple)

    # S'il y a bien un état dans le fichier, alors on peut attribuer les valeurs aux variables
    if etat[1] != "" and etat[2] != "":
        symbol_stoploss = etat[1]
        prix_stoploss = float(etat[2])

    # S'il y a des cryptos en cours, alors on relance le stoploss
    if crypto_up > kucoin.minimum_crypto_up or crypto_down > kucoin.minimum_crypto_down:
        if symbol_stoploss != "" and prix_stoploss != 0.0:
            p2.start()

    # Si le bot n'a pas attendu l'heure, alors il attend
    if date - ancienne_date < 3600:
        temps_dodo = 3600 - (date - ancienne_date)
        sleep(temps_dodo)

# Variable pour modifier le pourcentage de variation de la crypto sur le marché de base
# Sert pour le stoploss : si variation supérieur à ces deux bornes, on vend la crypto
pourcentage_stoploss_up = 0.98
pourcentage_stoploss_down = 1.02

while True:
    t1 = perf_counter()

    argent = kucoin.montant_compte("USDT")
    crypto_up = kucoin.montant_compte(kucoin.symbol_up_simple)
    crypto_down = kucoin.montant_compte(kucoin.symbol_down_simple)

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

    prediction = IA.prédiction_keras(data, rsi_vwap_cmf, loaded_model)
    prediction_up = IA.prédiction_keras(
        data_up, rsi_vwap_cmf_up, loaded_model_up)
    prediction_down = IA.prédiction_keras(
        data_down, rsi_vwap_cmf_down, loaded_model_down)

    état = f"programme toujours en cour d'exécution le : {date}\n" + \
        f"prix de la crypto : {prix}, prix de la prédiction : {prediction}\n" + \
        f"prix crypto up : {prix_up}, prix de la prédiction : {prediction_up}\n" + \
        f"prix crypto down : {prix_down}, prix de la prédiction : {prediction_down}"

    msg_discord.message_état_bot(état)

    if validation_achat(prix, prix_up, prix_down, prediction, prediction_up, prediction_down, True):
        if crypto_up < kucoin.minimum_crypto_up:
            # Si le processus du stoploss est toujours en vie
            # On l'arrête avant d'en créer un nouveau
            kill_process(p2)

            if crypto_down > kucoin.minimum_crypto_down:
                # Vente de la crypto descendante
                kucoin.achat_vente(crypto_down, kucoin.symbol_down, False)

                argent = kucoin.montant_compte("USDT")

            symbol_stoploss = kucoin.symbol_up
            prix_stoploss = prix * pourcentage_stoploss_up

            # Achat de la crypto montante
            kucoin.achat_vente(argent, kucoin.symbol_up, True)

            # On vient recréer un processus manuel et qu'on vient démarrer
            # Gère le stoploss de façon manuel
            p2 = Process(target=kucoin.stoploss_manuel, args=[
                symbol_stoploss, prix_stoploss])
            p2.start()

    elif validation_achat(prix, prix_up, prix_down, prediction, prediction_up, prediction_down, False):
        if crypto_down < kucoin.minimum_crypto_down:
            # Si le processus du stoploss est toujours en vie
            # On l'arrête avant d'en créer un nouveau
            kill_process(p2)

            if crypto_up > kucoin.minimum_crypto_up:

                # Vente de la crypto montant
                kucoin.achat_vente(crypto_up, kucoin.symbol_up, False)

                argent = kucoin.montant_compte("USDT")

            symbol_stoploss = kucoin.symbol_down
            prix_stoploss = prix * pourcentage_stoploss_down

            # Achat de la crypto descendante
            kucoin.achat_vente(argent, kucoin.symbol_down, True)

            # On vient recréer un processus manuel et qu'on vient démarrer
            # Gère le stoploss de façon manuel
            p2 = Process(target=kucoin.stoploss_manuel, args=[
                symbol_stoploss, prix_stoploss])
            p2.start()

    else:
        # Si le prix est supérieur a la prédiction (ou inversement)
        # Et que on a pas acheté et qu'on a des cryptos
        # Alors on vend
        if (prix > prediction or prix_up > prediction_up or prix_down < prediction_down) and crypto_up > kucoin.minimum_crypto_up:
            kill_process(p2)

            kucoin.achat_vente(crypto_up, kucoin.symbol_up, False)

        if (prix < prediction or prix_up < prediction_up or prix_down > prediction_down) and crypto_down > kucoin.minimum_crypto_down:
            kill_process(p2)

            kucoin.achat_vente(crypto_down, kucoin.symbol_down, False)

    # On enregistre l'état du bot (dernière heure et divergence)
    # Pour que si le bot est arrêté et repart, qu'il soit au courant
    # S'il doit attendre ou non
    state = f"{date};{symbol_stoploss};{prix_stoploss}"
    IA.etat_bot("écriture", state)

    t2 = perf_counter()

    sleep(dodo - int(t2 - t1) - 1)
