from main import Kucoin, Message_discord, os, Process, traceback
from subprocess import Popen, PIPE
from discord.ext import commands
import asyncio
import runpy

# A réactiver et à mettre en premier si le bot discord est un cran au dessus
# dans l'arborescence de fichier pour gérer les deux versions du bot
"""
import sys
sys.path[:0] = ['Version_1/']
"""

# Commande d'arret des programmes
commande_bot_terminale = """ps -aux | grep "bot_discord.py"| awk -F " " '{ print $2 }' """
commande_redemarrage_terminale = """ps -aux | grep "redemarrage.py"| awk -F " " '{ print $2 }' """

# Boucle qui permet de lancer la suppression automatique des messages
loop = asyncio.get_event_loop()


class Botcrypto(commands.Bot):

    def __init__(self):
        """
        Initialise le bot discord
        """
        super().__init__(command_prefix="!")

        # Objet Kucoin pour interagir avec le serveur
        self.kucoin = Kucoin("Discord", False)

        # Message discord
        self.msg_discord = Message_discord()

        # Variable qui permet de savoir si le bot est déjà lancé ou non
        self.statut_bot_crypto = False

        fichier = open("Autre_fichiers/crypto.txt", "r")
        text = fichier.read()

        self.listes_crypto = text.split(";")

        def arret_bot():
            """
            Fonction qui arrête le bot
            """
            proc = Popen(commande_bot_terminale,
                         shell=True, stdout=PIPE, stderr=PIPE)

            sortie, autre = proc.communicate()

            processus = sortie.decode('utf-8').split("\n")[2:-1]

            for elt in processus:
                os.system(f"kill -9 {elt}")

            # Une fois le bot arrêté, on peut passer la variable a False
            self.statut_bot_crypto = False

        def lancement_bot():
            """
            Fonction qui permet de lancer le bot
            Et de renvoyer l'erreur sur le serveur s'il y en a une qui apparait
            """
            try:
                self.msg_discord.message_canal_general("Le bot est lancé !")
                runpy.run_path("app.py")
            except:
                erreur = traceback.format_exc()

                self.msg_discord.message_erreur(
                    erreur, "Erreur survenue au niveau du bot, arrêt du programme")

                arret_bot()

                self.msg_discord.message_canal_general(
                    "Le bot s'est arrêté !")

        async def suppression_auto_message():
            """
            Fonction qui supprime automatiquement les messages sur les canal état-bot et prise-position
            s'il y a plus de 10 messages
            Evite que les canaux soient trop chargé par les messages du bot 
            Evite la suppresion manuel et total des messages
            """
            id_etat_bot = 972545416786751488
            id_prise_position = 973269585547653120

            # On attend que le client soit prêt
            # sinon get_channel renvoit none
            await self.wait_until_ready()

            etat_bot = self.get_channel(id_etat_bot)
            prise_position = self.get_channel(id_prise_position)

            async def suppression_messages(channel):
                """
                Fonction interne qui supprime les messages d'un canal
                """
                while True:
                    # Récupération des messages
                    messages = await channel.history().flatten()

                    # S'il y en a plus de 10
                    # Alors on inverse la liste pour avoir les anciens messages en premier
                    if len(messages) > 10:
                        messages.reverse()

                        # On ne garde que les plus anciens
                        messages = messages[:len(messages) - 10]

                        # Puis on les supprime
                        for msg in messages[:10]:
                            await msg.delete()
                            await asyncio.sleep(0.2)

                    # Et enfin on attend une heure soit le temps d'attente du bot
                    await asyncio.sleep(60 * 60)

            # Démarrage suppression dans les deux canaux
            loop.create_task(suppression_messages(etat_bot))
            loop.create_task(suppression_messages(prise_position))

        # Démarrage tache suppression auto message
        loop.create_task(suppression_auto_message())

        @self.command(name="del")
        async def delete(ctx):
            """
            Fonction qui supprime tous les messages de la conversation
            """
            messages = await ctx.channel.history().flatten()

            for each_message in messages:
                await each_message.delete()
                await asyncio.sleep(0.2)

        @self.command(name="aide")
        async def aide(ctx):
            """
            Fonction complémentaire de la fonction de base "help" de discord
            """
            commandes = """
            Voici les commandes disponibles :

            aide / help : affiche l'aide soit de la commande aide du bot/soit de discord

            del : supprime tous les messages de la conversation

            start : lance le bot sur la crypto voulus

            stop : arrête le bot

            prix : donne le prix actuel de la cryptomonnaie voulus

            liste : liste les pairs de cryptomonnais possible

            statut : affiche le statut du bot discord et du bot crypto

            vente : vend toutes les cryptomonnais du compte

            montant : renvoie le montant des cryptos du compte

            redemarrage : redémarre le bot en mettant à jour les fichiers de celui-ci

            """

            await ctx.send(commandes)

        @self.command(name="prix")
        async def prix(ctx):
            """
            Fonction qui affiche le prix en temps réel de la crypto
            """
            """
            await ctx.send("Quelles crypto ? BTCEUR ? ETHEUR ? BATBUSD ?")

            # Vérifie que le message n'est pas celui envoyé par le bot
            def check(m):
                return m.content != "Quelles crypto ? BTCEUR ? ETHEUR ? BATBUSD ?" and m.channel == ctx.channel

            # On attend la réponse
            msg = await self.wait_for("message", check=check)

            # Puis on vérifie que la cryptomonnaie existe bien
            crypto = msg.content
            if crypto in listes_crypto:
                await ctx.send(f"Le prix de la crypto est de : {self.kucoin.prix_temps_reel_kucoin(crypto)}")
            else:
                await ctx.send("La cryptomonnaie n'existe pas")
            """
            crypto = "BTC-USDT"

            await ctx.send(f"Le prix de la crypto est de : {self.kucoin.prix_temps_reel_kucoin(crypto)}")

        @self.command(name="start")
        async def start(ctx):
            """
            Fonction qui lance en processus le bot de crypto
            Permet de ne pas bloquer le bot discord et donc d'executre d'autre commandes à coté
            Comme l'arrêt du bot ou le relancer, le prix à l'instant T, etc...
            """
            """
            await ctx.send("Sur quelles crypto trader ? BTC ou BNB ?")

            # Vérifie que le message n'est pas celui envoyé par le bot
            def check(m):
                return m.content != "Sur quelles crypto trader ? BTC ou BNB ?" and m.channel == ctx.channel

            # On attend la réponse
            msg = await bot.wait_for("message", check=check)

            # Puis on vérifie que la cryptomonnaie existe bien
            crypto = msg.content
            """
            """
            crypto = 'BTC'
            if crypto in ['BTC', 'BNB']:
                sys.argv = ['', crypto]
            
            else:
                await ctx.send("La cryptomonnaie n'existe pas")
            """

            if self.statut_bot_crypto == False:
                self.statut_bot_crypto = True
                process = Process(target=lancement_bot)
                process.start()

            else:
                await ctx.send("Le bot est déjà lancé !")

        @self.command(name="stop")
        async def stop(ctx):
            """
            Fonction qui stop le bot
            Tue le processus du bot ainsi que les processus qui chargent la bdd si ce n'est pas fini
            """
            arret_bot()

            await ctx.send("Bot arrêté")

        @self.command(name="liste")
        async def crypto(ctx):
            """
            Fonction qui permet de lister les cryptos voulus
            """
            await ctx.send("Quelles pair de crypto voulus ? BTC ? ETH ? BAT ? LUNA ? EUR ?")

            # Vérifie que le message n'est pas celui envoyé par le bot
            def check(m):
                return m.content != "Quelles pair de crypto voulus ? BTC ? ETH ? BAT ? LUNA ? EUR ?" and m.channel == ctx.channel

            # On attend la réponse
            msg = await bot.wait_for("message", check=check)

            # Puis on vérifie que la cryptomonnaie existe bien
            crypto = msg.content

            crypto_voulu = ""
            for cr in self.listes_crypto:
                if crypto in cr:
                    crypto_voulu += cr + ", "

            if crypto_voulu == "":
                await ctx.send("Aucune crypto de ce type")
            else:
                crypto_voulu = crypto_voulu[:-2]
                await ctx.send("Voici les cryptomonnais disponibles : ")
                if len(crypto_voulu) < 2000:
                    await ctx.send(crypto_voulu)
                else:
                    liste_crypto_voulu = []

                    while len(crypto_voulu) >= 2000:
                        liste_crypto_voulu.append(crypto_voulu[:2000])
                        crypto_voulu = crypto_voulu[2000:]

                    liste_crypto_voulu.append(crypto_voulu)
                    for elt in liste_crypto_voulu:
                        await ctx.send(elt)

        @self.command(name="statut")
        async def statut(ctx):
            """
            Fonction qui renvoie le statut du bot discord et celui de la crypto
            """
            await ctx.send("Bot discord toujours en cours d'exécution !")

            proc = Popen(commande_bot_terminale,
                         shell=True, stdout=PIPE, stderr=PIPE)

            sortie, autre = proc.communicate()

            processus = sortie.decode('utf-8').split("\n")[2:-3]

            if processus != []:
                await ctx.send("Bot crypto lancé !")
            else:
                await ctx.send("Bot crypto arrêté !")

        @self.command(name="vente")
        async def vente(ctx):
            """
            Fonction qui permet de vendre les cryptomonaies du bot à distance
            Sans devoir accéder à la platforme
            """
            # On regarde le montant des deux cryptos
            btcup = self.kucoin.montant_compte("BTC3L")
            btcdown = self.kucoin.montant_compte("BTC3S")

            kk = Kucoin("BTC", False)

            # Et on vend la ou les cryptos en supprimant les ordres placés
            if btcup > self.kucoin.minimum_crypto_up:
                kk.achat_vente(btcup, "BTC3L-USDT", False)

                await ctx.send(f"{btcup} crypto up vendu !")

            if btcdown > self.kucoin.minimum_crypto_down:
                kk.achat_vente(btcdown, "BTC3S-USDT", False)

                await ctx.send(f"{btcdown} crypto down vendu !")

            # Et on renvoie les nouveaux montants sur le discord
            await montant(ctx)

        @self.command(name="montant")
        async def montant(ctx):
            """
            Fonction qui renvoie le montant du compte des cryptos
            """

            argent = self.kucoin.montant_compte("USDT")
            btcup = self.kucoin.montant_compte("BTC3L")
            btcdown = self.kucoin.montant_compte("BTC3S")

            await ctx.send(f"Le compte possède {argent} USDT, {btcup} crypto up, {btcdown} crypto down !")

        @self.command(name="redemarrage")
        async def redemarrage(ctx):
            """
            Fonction qui redemarre le bot discord et met à jour ses fichiers
            """

            Popen("nohup python3 redemarrage.py >/dev/null 2>&1", shell=True)

        @self.command(name="message")
        async def message(ctx):
            """
            Fonction qui permet d'enregistrer l'état du bot, des prédictions ainsi que le prix des cryptos
            """

            messages = await ctx.channel.history().flatten()

            ls = []

            for each_message in messages:
                toto = each_message.embeds
                if len(toto) > 0:
                    toto2 = str(toto[0].fields[0])[36:-14]
                    ls.append(toto2)

            fichier = open("message_discord.txt", "w")

            for elt in ls:
                fichier.write(elt)

        @self.command(name="estimation")
        async def estimation(ctx):
            """
            Fonction qui renvoi le prix estimer de vente de la crypto
            """
            if "prix_estimer" in self.kucoin.dico_partage:
                await ctx.send(f"Le prix de vente estimer est de {self.kucoin.dico_partage['prix_estimer']}")
                await ctx.send(f"Le prix de marché est de {self.kucoin.prix_temps_reel_kucoin('BTC-USDT')}")
            else:
                await ctx.send("Il n'y a pas de position prise à l'heure actuel ou de prix enregistrer")

    async def on_ready(self):
        """
        Fonction qui affiche dans la console "Bot crypto est prêt" lorsqu'il est opérationnel 
        Et enlève des processus le code python redemarrage si le programme est redémarré
        """
        # D'abord on tue le ou les processus de redémarrage
        proc = Popen(commande_redemarrage_terminale,
                     shell=True, stdout=PIPE, stderr=PIPE)

        sortie, autre = proc.communicate()

        processus = sortie.decode('utf-8').split("\n")[:-1]

        for elt in processus:
            os.system(f"kill -9 {elt}")

        self.msg_discord.message_canal_general("Bot démarré !")


if __name__ == "__main__":
    os.system("clear")
    bot = Botcrypto()
    bot.run("OTcyNDY0NDAwNzY4MzM1ODkz.YnZcDA.LYfcnXeeBB2aEO0-ZX7bNvM1T-8")
