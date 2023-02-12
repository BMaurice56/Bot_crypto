from main import *

symbol = "BTC"
dodo = 60*60

# Création d'un objet binance et kucoin pour interagir avec leurs serveurs
# Création d'un objet ia
binance = Binance()
kucoin = Kucoin(symbol)
ia = IA(symbol)

# dictionnaire qui stocke les deux symboles pour passer de l'un à l'autre facilement
dico_symbol = {1: kucoin.symbol_up, 0: kucoin.symbol_down}
dico_minimum = {1: kucoin.minimum_crypto_up, 0: kucoin.minimum_crypto_down}
dico_pourcentage_stoploss = {1: 0.98, 0: 1.02}  # Prix stoploss up et down

# Message discord
msg_discord = Message_discord()

# Chargement des modèles d'ia pour les prédictions
loaded_model, loaded_model_up, loaded_model_down = ia.chargement_modele()

# Info pour la fonction stoploss manuel
symbol_stoploss = ""
prix_stoploss = 0.0

# Création de la variable avec le processus de stoploss manuel
process = kucoin.stoploss_manuel(symbol_stoploss, prix_stoploss)

# On récupère l'état précédent du bot (Heure et stoploss)
etat = ia.etat_bot("lecture")

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
    if etat[1] != "" and etat[2] != "0.0":
        symbol_stoploss = etat[1]
        prix_stoploss = float(etat[2])

    # S'il y a des cryptos en cours, alors on relance le stoploss
    if crypto_up > kucoin.minimum_crypto_up or crypto_down > kucoin.minimum_crypto_down:
        if symbol_stoploss != "" and prix_stoploss != 0.0:
            process = kucoin.stoploss_manuel(
                symbol_stoploss, prix_stoploss, True)

    # Si le bot n'a pas attendu l'heure, alors il attend
    if date - ancienne_date < 3600:
        temps_dodo = 3600 - (date - ancienne_date) - 1
        sleep(temps_dodo)

# Stock le temps depuis la dernière position prise
# Si plusieurs heures passent sans l'exécution de l'ordre limite, alors on le baisse
temps_derniere_position = -1
gain_ordrelimite = kucoin.pourcentage_gain

while True:
    t1 = perf_counter()

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

    prediction = ia.prédiction_keras(data, rsi_vwap_cmf, loaded_model)
    prediction_up = ia.prédiction_keras(
        data_up, rsi_vwap_cmf_up, loaded_model_up)
    prediction_down = ia.prédiction_keras(
        data_down, rsi_vwap_cmf_down, loaded_model_down)

    état = f"programme toujours en cour d'exécution le : {date}\n" + \
        f"prix de la crypto : {prix}, prix de la prédiction : {prediction}\n" + \
        f"prix crypto up : {prix_up}, prix de la prédiction : {prediction_up}\n" + \
        f"prix crypto down : {prix_down}, prix de la prédiction : {prediction_down}"

    msg_discord.message_état_bot(état)

    # On augmente de 1 le temps qu'on a de position
    # Remis à zéro après si achat ou aucune crypto
    temps_derniere_position += 1

    résultat_achat = ia.validation_achat(
        prix, prix_up, prix_down, prediction, prediction_up, prediction_down)

    # S'il y a bien un signal d'achat, alors on peut passer à la suite
    if résultat_achat != None:
        if dico_montant[résultat_achat] < dico_minimum[résultat_achat]:
            # Si le processus du stoploss est toujours en vie
            # On l'arrête avant d'en créer un nouveau
            kill_process(process)

            # Si on possède toujours de l'autre crypto, on la vend
            if dico_montant[not résultat_achat] > dico_minimum[not résultat_achat]:
                kucoin.achat_vente(
                    dico_montant[not résultat_achat], dico_symbol[not résultat_achat], False)

                argent = kucoin.montant_compte(kucoin.devise)

            # Définition des variables pour le stoploss
            symbol_stoploss = dico_symbol[résultat_achat]
            prix_stoploss = prix * dico_pourcentage_stoploss[résultat_achat]

            # Achat de la crypto voulu
            kucoin.achat_vente(argent, dico_symbol[résultat_achat], True)

            # Gère le stoploss de façon manuel
            process = kucoin.stoploss_manuel(
                symbol_stoploss, prix_stoploss, True)

            buy_sell = True

    else:
        # Si le prix est supérieur a la prédiction (ou inversement)
        # Et que on a pas acheté et qu'on a des cryptos
        # Alors on vend
        if (prix > prediction or prix_up > prediction_up or prix_down < prediction_down) and crypto_up > kucoin.minimum_crypto_up:
            kill_process(process)

            kucoin.achat_vente(crypto_up, kucoin.symbol_up, False)
            buy_sell = True

        if (prix < prediction or prix_up < prediction_up or prix_down > prediction_down) and crypto_down > kucoin.minimum_crypto_down:
            kill_process(process)

            kucoin.achat_vente(crypto_down, kucoin.symbol_down, False)
            buy_sell = True

    # Si plus de crypto ou achat, alors on remet a zéro les variables
    if buy_sell == True or crypto_up < kucoin.minimum_crypto_up and crypto_down < kucoin.minimum_crypto_down:
        temps_derniere_position = 0
        gain_ordrelimite = kucoin.pourcentage_gain

    # Si cela fait trop longtemps que l'ordre a été placé sans être vendu, on le descent
    if temps_derniere_position >= 5:
        gain_ordrelimite -= 0.0025

        # Si on arrive au moment où il se produit 0.0075 - 0.0025
        # Cela donne un chiffre inexacte et donc on le remet sur une valeur fixe
        if gain_ordrelimite == 0.004999999999999999:
            gain_ordrelimite = 0.005

        # Si on descent à zéro, alors on ne replace plus l'ordre
        if gain_ordrelimite > 0.0:

            kucoin.ordre_vente_seuil(
                symbol_stoploss, gain_ordrelimite)

            temps_derniere_position = 0

    # On enregistre l'état du bot (dernière heure et stoploss)
    # Pour que si le bot est arrêté et repart, qu'il soit au courant
    # S'il doit attendre ou non, et s'il doit relancer le stoploss
    state = f"{date};{symbol_stoploss};{prix_stoploss}"
    ia.etat_bot("écriture", state)

    t2 = perf_counter()

    sleep(dodo - int(t2 - t1) - 1)
