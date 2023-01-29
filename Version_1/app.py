from main import *

symbol = "BTC"
symbol_up_kucoin = "BTC3L-USDT"
symbol_down_kucoin = "BTC3S-USDT"
dodo = 60*60

# Création d'un objet binance et kucoin pour interagir avec leurs serveurs
binance = Binance()
kucoin = Kucoin()

# Message discord
msg_discord = Message_discord()

# Chargement des modèles d'ia pour les prédictions
loaded_model, loaded_model_up, loaded_model_down = IA.chargement_modele(symbol)

# On lance la fonction qui permet de garder à jour l'id de l'ordre limite dans le fichier
p = Process(target=kucoin.update_id_ordre_limite)
p.start()

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

    # Si il y a bien eu 1 heure d'attente, on peut passer au prédiction
    # Sinon on attend jusqu'a l'heure prévu tout en relancent le stoploss manuel si présence de crypto
    if date - ancienne_date < 3600:
        btcup = kucoin.montant_compte("BTC3L")
        btcdown = kucoin.montant_compte("BTC3S")

        if btcup > kucoin.minimum_crypto_up or btcdown > kucoin.minimum_crypto_down:
            symbol_stoploss = etat[1]
            prix_stoploss = float(etat[2])

            p2.start()

        temps_dodo = 3600 - (date - ancienne_date)
        sleep(temps_dodo)

# Variable pour modifier le pourcentage de variation de la crypto sur le marché de base
# Sert pour le stoploss : si variation supérieur à ces deux bornes, on vend la crypto
pourcentage_stoploss_up = 0.98
pourcentage_stoploss_down = 1.02

while True:
    t1 = perf_counter()

    achat_vente = False

    argent = kucoin.montant_compte("USDT")
    btcup = kucoin.montant_compte("BTC3L")
    btcdown = kucoin.montant_compte("BTC3S")

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

    état = f"programme toujours en cour d'exécution le : {date}"
    infos = f"prix de la crypto : {prix}, prix de la prédiction : {prediction}"
    up = f"prix crypto up : {prix_up}, prix de la prédiction : {prediction_up}"
    down = f"prix crypto down : {prix_down}, prix de la prédiction : {prediction_down}"

    msg = état + "\n" + infos + "\n" + up + "\n" + down

    msg_discord.message_état_bot(msg)

    if prix < prediction and prix_up < prediction_up and prix_down > prediction_down and prediction_down <= 0.03 and prediction_up - prix_up >= 0.045:
        if btcup > kucoin.minimum_crypto_up:
            pass

        else:
            # Si le processus du stoploss est toujours en vie
            # On l'arrête avant d'en créer un nouveau
            kill_process(p2)

            if btcdown > kucoin.minimum_crypto_down:
                # Vente de la crypto descendante
                kucoin.achat_vente(btcdown, symbol_down_kucoin, False)

                argent = kucoin.montant_compte("USDT")

            symbol_stoploss = symbol_up_kucoin
            prix_stoploss = prix * pourcentage_stoploss_up

            # Achat de la crypto montante
            kucoin.achat_vente(argent, symbol_up_kucoin, True)

            # On vient recréer un processus manuel et qu'on vient démarrer
            # Gère le stoploss de façon manuel
            p2 = Process(target=kucoin.stoploss_manuel, args=[
                symbol_stoploss, prix_stoploss])
            p2.start()

            achat_vente = True

    elif prix > prediction and prix_up > prediction_up and prix_down < prediction_down:
        if btcdown > kucoin.minimum_crypto_down:
            pass

        else:
            # Si le processus du stoploss est toujours en vie
            # On l'arrête avant d'en créer un nouveau
            kill_process(p2)

            if btcup > kucoin.minimum_crypto_up:

                # Vente de la crypto montant
                kucoin.achat_vente(btcup, symbol_up_kucoin, False)

                argent = kucoin.montant_compte("USDT")

            symbol_stoploss = symbol_down_kucoin
            prix_stoploss = prix * pourcentage_stoploss_down

            # Achat de la crypto descendante
            kucoin.achat_vente(argent, symbol_down_kucoin, True)

            # On vient recréer un processus manuel et qu'on vient démarrer
            # Gère le stoploss de façon manuel
            p2 = Process(target=kucoin.stoploss_manuel, args=[
                symbol_stoploss, prix_stoploss])
            p2.start()

            achat_vente = True

    else:
        # Si le prix est supérieur a la prédiction
        # Et que on a pas acheté et qu'on a des cryptos
        # Alors on vend
        if prix > prediction or prix_up > prediction_up or prix_down < prediction_down:
            if achat_vente == False and btcup > kucoin.minimum_crypto_up:
                kucoin.achat_vente(btcup, symbol_up_kucoin, False)

                kill_process(p2)

        if prix < prediction or prix_up < prediction_up or prix_down > prediction_down:
            if achat_vente == False and btcdown > kucoin.minimum_crypto_down:
                kucoin.achat_vente(btcdown, symbol_up_kucoin, False)

                kill_process(p2)

    # On enregistre l'état du bot (dernière heure et divergence)
    # Pour que si le bot est arrêté et repart, qu'il soit au courant
    # S'il doit attendre ou non
    state = date + ";" + symbol_stoploss + ";" + str(prix_stoploss)
    IA.etat_bot("écriture", state)

    t2 = perf_counter()

    sleep(dodo - int(t2 - t1) - 1)
