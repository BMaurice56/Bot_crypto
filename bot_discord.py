from multiprocessing import Process
from discord.ext import commands
from main import *
import traceback
import runpy


fichier = open("crypto.txt", "r")
text = fichier.read()
listes_crypto = text.split(";")


class Botcrypto(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix="!")

        def lancement_bot(symbol):
            """
            Fonction qui permet de lancer le bot
            Et de renvoyer l'erreur sur le serveur s'il y en a une qui apparait
            """
            try:
                message_status_général("Le bot est lancé !")
                sys.argv = ['', symbol]
                runpy.run_path("app.py")
            except:
                erreur = traceback.format_exc()
                message_status_général(erreur)
                arret_bot()
                message_status_général("Le bot s'est arrêté")

        def arret_bot():
            """
            Fonction qui arrête le bot et l'insertion des données dans la bdd
            """
            proc = Popen("""ps -aux | grep "/bin/python3" | grep "bot_discord.py"| awk -F " " '{ print $2 }' """,
                         shell=True, stdout=PIPE, stderr=PIPE)

            sortie, autre = proc.communicate()

            processus = sortie.decode('utf-8').split("\n")[1:-2]

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

            """

            await ctx.send(commandes)

        @self.command(name="prix")
        async def prix(ctx):
            """
            Fonction qui affiche le prix en temps réel de la crypto
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
                await ctx.send(f"Le prix de la crypto est de : {prix_temps_reel(crypto)}")
            else:
                await ctx.send("La cryptomonnaie n'existe pas")

        @self.command(name="start")
        async def start(ctx):
            """
            Fonction qui lance en processus le bot de crypto
            Permet de ne pas bloquer le bot discord et donc d'executre d'autre commandes à coté
            Comme l'arrêt du bot ou le relancer, le prix à l'instant T, etc...
            """
            await ctx.send("Sur quelles crypto trader ? BTC ou BNB ?")

            # Vérifie que le message n'est pas celui envoyé par le bot
            def check(m):
                return m.content != "Sur quelles crypto trader ? BTC ou BNB ?" and m.channel == ctx.channel

            # On attend la réponse
            msg = await bot.wait_for("message", check=check)

            # Puis on vérifie que la cryptomonnaie existe bien
            crypto = msg.content
            if crypto in ['BTC', 'BNB']:
                process = Process(target=lancement_bot, args=(crypto,))
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

        @self.command(name="message")
        async def message(ctx):
            """"""
            messages = await ctx.channel.history().flatten()

            fichier = open("messages.txt", "a")
            
            for each_message in messages:
                fichier.write(each_message.content)

    async def on_ready(self):
        """
        Fonction qui affiche dans la console "Bot crypto est prêt" lorsqu'il est opérationnel 
        """
        print(f"{self.user.display_name} est prêt")


if __name__ == "__main__":
    os.system("clear")
    bot = Botcrypto()
    bot.run(os.getenv("TOKEN_BOT"))
