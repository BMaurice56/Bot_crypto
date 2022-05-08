from discord.ext import commands
from main import *
import traceback
import runpy


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
                runpy.run_path(path_name="app.py")
            except:
                erreur = traceback.format_exc()
                message_status_général(erreur)
                message_status_général("Le bot s'est arrêté")

        @self.command(name="del")
        async def delete(ctx, nb_messages: int):
            """
            Fonction qui supprime les n derniers messages de la conversation
            """
            messages = await ctx.channel.history(limit=nb_messages + 1).flatten()

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

            del n : supprime les n derniers messages de la conversation

            launch : lance le bot

            stop : arrête le bot

            prix : donne le prix actuel de la cryptomonnaie

            """

            await ctx.channel.send(commandes)

        @self.command(name="prix")
        async def prix(ctx):
            """
            Fonction qui affiche le prix en temps réel de la crypto
            """
            await ctx.channel.send(f"Le prix de la crypto est de : {prix_temps_reel('BTCEUR')}")

        @self.command(name="launch")
        async def launch(ctx):
            """
            Fonction qui lance en processus le bot de crypto
            Permet de ne pas bloquer le bot discord et donc d'executre d'autre commandes à coté
            Comme l'arrêt du bot ou le relancer, le prix à l'instant T, etc...
            """
            process = Process(target=lancement_bot)
            process.start()

        @self.command(name="stop")
        async def stop(ctx):
            """
            Fonction qui stop le bot
            Tue le processus du bot ainsi que les processus qui chargent la bdd si ce n'est pas fini
            """
            proc = Popen("""ps -aux | grep "/bin/python3" | grep "bot_discord.py"| awk -F " " '{ print $2 }' """,
                         shell=True, stdout=PIPE, stderr=PIPE)

            sortie, autre = proc.communicate()

            processus = sortie.decode('utf-8').split("\n")[1:-2]

            for elt in processus:
                os.system(f"kill -9 {elt}")

            await ctx.channel.send("Bot arrêté")

    async def on_ready(self):
        """
        Fonction qui affiche dans la console "Bot crypto est prêt" lorsqu'il est opérationnel 
        """
        print(f"{self.user.display_name} est prêt")


if __name__ == "__main__":
    os.system("clear")
    bot = Botcrypto()
    bot.run(os.getenv("TOKEN_BOT"))
