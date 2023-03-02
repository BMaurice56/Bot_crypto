from main import Kucoin, Message_discord, os, Process, traceback, kill_process
from subprocess import Popen, PIPE
from discord.ext import commands
import asyncio
import runpy
import sys

# A réactiver et à mettre en premier si le bot discord est un cran au dessus
# dans l'arborescence de fichier pour gérer les deux versions du bot
"""
import sys
sys.path[:0] = ['Version_1/']
"""


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

        # Stocke tous les bots lancés
        self.liste_bot_lancé = []
        self.liste_symbol_bot_lancé = []

        # Boucle qui permet de lancer la suppression automatique des messages
        self.loop = asyncio.get_event_loop_policy().get_event_loop()

        # Liste des cryptos supportées
        with open("Autre_fichiers/crypto_supporter.txt", "r") as f:
            self.crypto_supporter = f.read().split(";")

        def lancement_bot(symbol):
            """
            Fonction qui permet de lancer le bot
            Et de renvoyer l'erreur sur le serveur s'il y en a une qui apparait
            """
            try:
                self.msg_discord.message_canal_general("Le bot est lancé !")
                sys.argv = ['', symbol]
                runpy.run_path("app.py")
            except:
                erreur = traceback.format_exc()

                self.msg_discord.message_erreur(
                    erreur, "Erreur survenue au niveau du bot, arrêt du programme")

                self.msg_discord.message_canal_general(
                    "Le bot s'est arrêté !")

        def arret_manuel_bot(symbol):
            """
            Fonction qui arrête le bot
            """
            for p in self.liste_bot_lancé:
                if p.name == symbol:
                    # On supprime le processus des listes
                    self.liste_bot_lancé.remove(p)
                    self.liste_symbol_bot_lancé.remove(symbol)

                    # On récupère l'id du processus du bot et on l'arrête
                    os.kill(p.ident, 9)

                    break

        async def arret_auto_bot():
            """
            Fonction qui supprime automatiquement de la liste les processus arrêté
            """
            while True:
                for process in self.liste_bot_lancé:
                    if process.exitcode != None:
                        symbol = process.name

                        kill_process(process)

                        self.liste_bot_lancé.remove(process)
                        self.liste_symbol_bot_lancé.remove(symbol)

                await asyncio.sleep(2)

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
            self.loop.create_task(suppression_messages(etat_bot))
            self.loop.create_task(suppression_messages(prise_position))

        # Démarrage tache async
        self.loop.create_task(suppression_auto_message())
        self.loop.create_task(arret_auto_bot())

        @ self.command(name="del")
        async def delete(ctx):
            """
            Fonction qui supprime tous les messages de la conversation
            """
            messages = await ctx.channel.history().flatten()

            for each_message in messages:
                await each_message.delete()
                await asyncio.sleep(0.2)

        @ self.command(name="aide")
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

            statut : affiche le statut du bot discord et du bot crypto

            vente : vend toutes les cryptomonnais du compte

            montant : renvoie le montant des cryptos du compte

            redemarrage : redémarre le bot en mettant à jour les fichiers de celui-ci

            estimation : donne le prix estimer de l'ordre limite sur le marché de base

            """

            await ctx.send(commandes)

        @ self.command(name="prix")
        async def prix(ctx):
            """
            Fonction qui affiche le prix en temps réel de la crypto
            """
            for crypto in self.crypto_supporter:
                await ctx.send(f"Le prix de {crypto} est de : {self.kucoin.prix_temps_reel_kucoin(crypto)}")

        @ self.command(name="start")
        async def start(ctx):
            """
            Fonction qui lance en processus le bot de crypto
            Permet de ne pas bloquer le bot discord et donc d'executre d'autre commandes à coté
            Comme l'arrêt du bot ou le relancer, le prix à l'instant T, etc...
            """
            question = "Sur quelles crypto trader ? BTC ? BNB ?"

            await ctx.send(question)

            # Vérifie que le message n'est pas celui envoyé par le bot
            def check(m):
                return m.content != question and m.channel == ctx.channel

            # On attend la réponse
            msg = await bot.wait_for("message", check=check)

            # On récupère la crypto
            crypto = msg.content

            # Si elle est supporter et pas lancé, alors on lance le bot
            if crypto in self.crypto_supporter:
                if crypto not in self.liste_symbol_bot_lancé:
                    p = Process(target=lancement_bot,
                                name=crypto, args=[crypto])

                    # Puis on ajoute le processus du bot dans les listes pour garder une trace de tous les bots lancés
                    self.liste_bot_lancé.append(p)
                    self.liste_symbol_bot_lancé.append(crypto)

                    p.start()

                else:
                    await ctx.send("Le bot est déjà lancé !")

            else:
                await ctx.send("Le bot n'existe pas !")

        @ self.command(name="stop")
        async def stop(ctx):
            """
            Fonction qui stop le bot
            Tue le processus du bot ainsi que les processus qui chargent la bdd si ce n'est pas fini
            """
            question = "Quel bot arrêté ?"
            bot_lancé = "Bot lancé : "

            # On récupère tous les bots déjà lancés
            for symbol in self.liste_symbol_bot_lancé:
                bot_lancé += f"{symbol} "

            await ctx.send(question)
            await ctx.send(bot_lancé)

            # Vérifie que le message n'est pas celui envoyé par le bot
            def check(m):
                return m.content not in [question, bot_lancé] and m.channel == ctx.channel

            # On attend la réponse
            msg = await bot.wait_for("message", check=check)

            # On récupère la crypto
            crypto = msg.content

            # Puis on l'arrête si le bot est lancé
            if crypto in self.crypto_supporter:
                if crypto in self.liste_symbol_bot_lancé:
                    arret_manuel_bot(crypto)

                    await ctx.send("Bot arrêté !")
                else:
                    await ctx.send("Bot déjà à l'arrêt !")

            else:
                await ctx.send("Bot inexistant !")

        @ self.command(name="statut")
        async def statut(ctx):
            """
            Fonction qui renvoie le statut du bot discord et celui de la crypto
            """
            await ctx.send("Bot discord toujours en cours d'exécution !")

            # Regarde s'il y a des bots lancés ou non
            if self.liste_symbol_bot_lancé != []:
                crypto = ""

                for symbol in self.liste_symbol_bot_lancé:
                    crypto += f"{symbol} "

                await ctx.send(f"Bot lancé : {crypto}")
            else:
                await ctx.send("Aucun Bot lancé !")

        @ self.command(name="vente")
        async def vente(ctx):
            """
            Fonction qui permet de vendre les cryptomonaies du bot à distance
            Sans devoir accéder à la platforme
            """
            question = "Quelle crypto ? BTC ? BNB ?"

            await ctx.send(question)

            # Vérifie que le message n'est pas celui envoyé par le bot
            def check(m):
                return m.content != question and m.channel == ctx.channel

            # On attend la réponse
            msg = await bot.wait_for("message", check=check)

            # On récupère la crypto
            crypto_symbol = msg.content

            # On regarde le montant des deux cryptos
            crypto_up = self.kucoin.montant_compte(f"{crypto_symbol}3L")
            crypto_down = self.kucoin.montant_compte(f"{crypto_symbol}3S")

            kucoin = Kucoin(crypto_symbol, False)

            # Et on vend la ou les cryptos en supprimant les ordres placés
            if crypto_up > self.kucoin.minimum_crypto_up:
                kucoin.achat_vente(crypto_up, f"{crypto_symbol}3L-USDT", False)

                await ctx.send(f"{crypto_up} crypto up vendu !")

            if crypto_down > self.kucoin.minimum_crypto_down:
                kucoin.achat_vente(
                    crypto_down, f"{crypto_symbol}3S-USDT", False)

                await ctx.send(f"{crypto_down} crypto down vendu !")

            # Et on renvoie les nouveaux montants sur le discord
            await montant(ctx)

        @ self.command(name="montant")
        async def montant(ctx):
            """
            Fonction qui renvoie le montant du compte des cryptos
            """

            argent = self.kucoin.montant_compte(self.kucoin.devise)
            await ctx.send(f"Le compte possède {argent} USDT")

            for crypto in self.crypto_supporter:
                crypto_up = self.kucoin.montant_compte(f"{crypto}3L")
                crypto_down = self.kucoin.montant_compte(f"{crypto}3S")

                await ctx.send(f"Le compte possède {crypto_up} {crypto}_UP, {crypto_down} {crypto}_DOWN")

        @ self.command(name="redemarrage")
        async def redemarrage(ctx):
            """
            Fonction qui redemarre le bot discord et met à jour ses fichiers
            """

            Popen("nohup python3.10 redemarrage.py >/dev/null 2>&1", shell=True)

        @ self.command(name="message")
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

        @ self.command(name="estimation")
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
        self.msg_discord.message_canal_general("Bot démarré !")


if __name__ == "__main__":
    os.system("clear")
    bot = Botcrypto()
    bot.run("OTcyNDY0NDAwNzY4MzM1ODkz.YnZcDA.LYfcnXeeBB2aEO0-ZX7bNvM1T-8")
