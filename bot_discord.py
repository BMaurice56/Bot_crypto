from main import Kucoin, Message_discord, os, Process, kill_process
from discord.ext import commands, tasks
from subprocess import Popen
from discord import Intents
import logging
import asyncio
import runpy


class Bot_Discord(commands.Bot):

    def __init__(self):
        """
        Initialise le bot discord
        """
        super().__init__(command_prefix="!", intents=Intents.all(), case_insensitive=True)

        # Objet Kucoin pour interagir avec le serveur
        self.kucoin = Kucoin("Discord", False)

        # Message discord
        self.msg_discord = Message_discord()

        # Temps de chaque tour de boucle des fonctions async
        self.time_loop = 60 * 60 * 12

        # Stocke tous les bots lancer
        self.processus_bot = Process()

        def bot_startup(symbol):
            """
            Starts the bot
            """
            try:
                self.msg_discord.message_canal(
                    "général", f"Bot {symbol} lancé !")
                runpy.run_path("bot.py")
            except Exception as error:
                self.msg_discord.message_erreur(
                    error, f"Erreur survenue au niveau du bot {symbol}, arrêt du programme")

                self.msg_discord.message_canal("général",
                                               "Le bot s'est arrêté !")

        @self.command(name="del")
        async def delete(ctx):
            """
            Supprime tous les messages de la conversation
            """
            await ctx.channel.purge()

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

            statut : affiche le statut du bot discord et du bot crypto

            vente : vend toutes les cryptomonnaie du compte

            montant : renvoie le montant des cryptos du compte

            restart : redémarre le bot en mettant à jour les fichiers de celui-ci

            estimation : donne le prix estimer de l'ordre limite sur le marché de base

            """

            await ctx.send(commandes)

        @self.command(name="prix")
        async def prix(ctx):
            """
            Affiche le prix en temps réel de la crypto
            """

            await ctx.send(f"Le prix de BTC est de : {self.kucoin.prix_temps_reel_kucoin(f'BTC-USDT')}")

        @self.command(name="start")
        async def start():
            """
            Lance en processus le bot de crypto
            Permet de ne pas bloquer le bot discord et donc d'exécuter d'autres commandes à côté
            Comme l'arrêt du bot ou le relancer, le prix à l'instant T, etc...
            """

            crypto = "BTC"

            self.processus_bot = Process(target=bot_startup, name=crypto, args=[crypto])

            self.processus_bot.start()

        @self.command(name="stop")
        async def stop(ctx):
            """
            Stop le bot (tue son processus)
            """

            kill_process(self.processus_bot)

            await ctx.send("Bot arrêté !")

        @self.command(name="statut")
        async def statut(ctx):
            """
            Renvoie le statut du bot discord et celui de trading
            """
            await ctx.send("Bot discord toujours en cours d'exécution !")

            # Regarde s'il y a des bots lancés ou non
            if self.processus_bot.is_alive():
                await ctx.send(f"Bot BTC lancé !")
            else:
                await ctx.send("Aucun Bot lancé !")

        @self.command(name="vente")
        async def vente(ctx):
            """
            Permet de vendre les cryptomonnaies du bot à distance
            Sans devoir accéder à la platform
            """
            # On regarde le montant des deux cryptos
            crypto_up = self.kucoin.montant_compte("BTC3L")
            crypto_down = self.kucoin.montant_compte("BTC3S")

            kucoin_vente = Kucoin("BTC", False)

            # Et on vend la ou les cryptos en supprimant les ordres placés
            if crypto_up > kucoin_vente.minimum_crypto_up:
                kucoin_vente.achat_vente(
                    crypto_up, "BTC3L-USDT", False)

                await ctx.send(f"{crypto_up} crypto up vendu !")

            if crypto_down > kucoin_vente.minimum_crypto_down:
                kucoin_vente.achat_vente(
                    crypto_down, "BTC3S-USDT", False)

                await ctx.send(f"{crypto_down} crypto down vendu !")

            # Et on renvoie les nouveaux montants sur le discord
            await montant(ctx)

        @self.command(name="montant")
        async def montant(ctx):
            """
            Renvoie le montant du compte des cryptos
            """

            argent = self.kucoin.montant_compte(self.kucoin.devise, None)
            await ctx.send(f"Le compte possède {argent} USDT")

            crypto_up = self.kucoin.montant_compte("BTC3L")
            crypto_down = self.kucoin.montant_compte("BTC3S")

            await ctx.send(f"Le compte possède {crypto_up} BTCUP, {crypto_down} BTCDOWN")

        @self.command(name="restart")
        async def restart():
            """
            Redémarre le bot discord et met à jour ses fichiers
            """
            Popen("nohup python3.10 restart.py >/dev/null 2>&1", shell=True)

        @self.command(name="estimation")
        async def estimation(ctx):
            """
            Renvoi le prix estimé de vente de la crypto
            """
            prix_estimer = None

            # On parcourt le dictionnaire à la recherche de prix estimé
            for cle, valeur in self.kucoin.dico_partage.items():
                if "prix_estimer" in self.kucoin.dico_partage.keys():
                    crypto = cle.split("_")[-1]
                    await ctx.send(f"Le prix de vente estimer de {crypto} est de {valeur}")
                    await ctx.send(f"Le prix de marché est de {self.kucoin.prix_temps_reel_kucoin(f'{crypto}-USDT')}")

                    # S'il y a bien un prix estimé, alors le message d'en dessous ne sert à rien
                    prix_estimer = True

            if prix_estimer is None:
                await ctx.send("Il n'y a pas de position prise à l'heure actuel ou de prix enregistrer")

        @self.command(name="analyse")
        async def analyse(ctx):
            """
            Analyse every logs
            """

            kk = Kucoin("BTC", False)
            kk.analyse_fichier(False)

            await ctx.send("Tous les logs ont été analysés !")

    @staticmethod
    async def delete_message_channel(channel):
        """
        Supprime les messages d'un canal
        """
        # Récupération des messages
        messages = [message async for message in channel.history()][10:]

        if messages:
            messages.reverse()

            # Puis, on les supprime
            for msg in messages:
                await msg.delete()
                await asyncio.sleep(0.5)

    async def suppression_auto_message(self):
        """
        Automatically deletes messages if there is more than 10 messages
        """
        await self.wait_until_ready()

        @tasks.loop(seconds=self.time_loop)
        async def start_delete_message_state_bot():
            """
            Start the delete function on the state bot channel
            """
            id_state_bot = 972545416786751488
            state_bot = self.get_channel(id_state_bot)

            await self.delete_message_channel(state_bot)

        @tasks.loop(seconds=self.time_loop)
        async def start_delete_message_prise_position():
            """
            Start the delete function on the taking position channel
            """
            id_prise_position = 973269585547653120
            prise_position = self.get_channel(id_prise_position)

            await self.delete_message_channel(prise_position)

        # Start deletion on the two channels
        start_delete_message_state_bot.start()
        start_delete_message_prise_position.start()

    async def on_ready(self):
        """
        Affiche dans le canal général "Bot Discord démarré !" lorsqu'il est opérationnel
        """
        self.msg_discord.message_canal("général", "Bot Discord démarré !")

        asyncio.create_task(self.suppression_auto_message())


if __name__ == "__main__":
    os.system("clear")
    bot = Bot_Discord()
    try:
        handler = logging.FileHandler(filename="log_files/discord_log.log", encoding='utf-8', mode='w')

        bot.run("OTcyNDY0NDAwNzY4MzM1ODkz.YnZcDA.LYfcnXeeBB2aEO0-ZX7bNvM1T-8", log_handler=handler)
    except Exception as e:
        # Stop all started bots

        message_discord = Message_discord()

        message_discord.message_erreur(
            e, "Erreur survenue dans le bot discord, arrêt du bot")
