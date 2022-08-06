from discord.ext import commands
from main import *
import traceback
import runpy

fichier = open("crypto.txt", "r")
text = fichier.read()
listes_crypto = text.split(";")

commande_bot_terminale = """ps -aux | grep "bot_discord.py"| awk -F " " '{ print $2 }' """
commande_redemarrage_terminale = """ps -aux | grep "redemarrage.py"| awk -F " " '{ print $2 }' """


class Botcrypto(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix="!")

        def lancement_bot():
            """
            Fonction qui permet de lancer le bot
            Et de renvoyer l'erreur sur le serveur s'il y en a une qui apparait
            """
            try:
                message_status_général("Le bot est lancé !")
                runpy.run_path("app.py")
            except:
                erreur = traceback.format_exc()
                if len(erreur) > 2000:
                    while len(erreur) >= 2000:
                        message_status_général(erreur[:2000])
                        erreur = erreur[2000:]
                    if erreur != "":
                        message_status_général(erreur)
                else:
                    message_status_général(erreur)
                arret_bot()
                message_status_général("Le bot s'est arrêté")

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

        @self.command(name="del")
        async def delete(ctx):
            """
            Fonction qui supprime tous les messages de la conversation
            """
            messages = await ctx.channel.history().flatten()

            for each_message in messages:
                await each_message.delete()

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
            """
            crypto = "BTC-USDT"
            if crypto in listes_crypto:
                await ctx.send(f"Le prix de la crypto est de : {prix_temps_reel_kucoin(crypto)}")
            else:
                await ctx.send("La cryptomonnaie n'existe pas")

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
            crypto = 'BTC'
            if crypto in ['BTC', 'BNB']:
                sys.argv = ['', crypto]
                process = Process(target=lancement_bot)

                process.start()

            else:
                await ctx.send("La cryptomonnaie n'existe pas")

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
            for cr in listes_crypto:
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
            btcup = montant_compte("BTC3L")
            btcdown = montant_compte("BTC3S")

            # Et on vend la ou les cryptos en supprimant les ordres placés
            if btcup > 30:
                achat_vente(btcup, "BTC3L-USDT", False)

                presence_market = presence_position("market", "BTC3L-USDT")

                if presence_market == None:
                    suppression_ordre("stoploss")

                else:
                    id_market = presence_market['id']

                    suppression_ordre("market", id_market)

                await ctx.send(f"{btcup} crypto up vendu !")

            if btcdown > 2:
                achat_vente(btcdown, "BTC3S-USDT", False)

                presence_market = presence_position("market", "BTC3S-USDT")

                if presence_market == None:
                    suppression_ordre("stoploss")

                else:
                    id_market = presence_market['id']

                    suppression_ordre("market", id_market)

                await ctx.send(f"{btcdown} crypto down vendu !")

            # Et on renvoie les nouveaux montants sur le discord
            await montant(ctx)

        @self.command(name="montant")
        async def montant(ctx):
            """
            Fonction qui renvoie le montant du compte des cryptos
            """

            argent = montant_compte("USDT")
            btcup = montant_compte("BTC3L")
            btcdown = montant_compte("BTC3S")

            await ctx.send(f"Le compte possède {argent} USDT, {btcup} crypto up, {btcdown} crypto down !")

        @self.command(name="redemarrage")
        async def redemarrage(ctx):
            """
            Fonction qui redemarre le bot discord et met à jour ses fichiers
            """

            Popen("python3 redemarrage.py", shell=True)

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

        print(f"{self.user.display_name} est prêt")

        message_status_général("Bot démarré !")


if __name__ == "__main__":
    os.system("clear")
    bot = Botcrypto()
    bot.run(os.getenv("TOKEN_BOT"))
