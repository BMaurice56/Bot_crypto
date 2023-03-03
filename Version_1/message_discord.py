from discord_webhook import DiscordWebhook, DiscordEmbed
from typing import Optional


class Message_discord:
    """
    Classe qui contient les fonctions d'envoi de message sur discord via webhook
    """

    def __init__(self) -> None:
        """
        Initialise un objet message pour l'envoi de ceux-ci
        """
        # Adresse du webhook discord
        self.adr_webhook_prise_position = "https://discord.com/api/webhooks/973269614874214410/UPyGLXDE2MbjvtmehG8cAAxx3zXtU3Kt-mN4TolLo1golSuHUp9AiCal0jrvIu3C6E6_"
        self.adr_webhook_état_bot = "https://discord.com/api/webhooks/972545553210695731/zLBkaDU4SPyyLoVXz5E-tv-4PkhfrZH6gipWwSI-1cAqwxFlrbYjKsxxRc2i9zioINIh"
        self.adr_webhook_général = "https://discordapp.com/api/webhooks/969652904959045674/KdVNf9INCcZ3O4V1NnzCsJfhwiAgy4cy1GMjaPZI7spmAAeIkS7sQSYGuKMT5YyAyLza"

        self.nom = "Jimmy"

    def message_canal_general(self, message: str, titre: Optional[str] = None):
        """
        Envoi un message sur le canal général
        """
        webhook = DiscordWebhook(
            url=self.adr_webhook_général, username=self.nom, content=message)

        if titre != None:
            embed = DiscordEmbed(title=titre, color="03b2f8")

            embed.add_embed_field(name="Message :", value=message)

            webhook.add_embed(embed)
            webhook.content = None

        webhook.execute()

    def message_canal_etat_bot(self, message: str, titre: Optional[str] = None):
        """
        Envoi un message sur le canal général
        """
        webhook = DiscordWebhook(
            url=self.adr_webhook_état_bot, username=self.nom, content=message)

        if titre != None:
            embed = DiscordEmbed(title=titre, color="03b2f8")

            embed.add_embed_field(name="Message :", value=message)

            webhook.add_embed(embed)
            webhook.content = None

        webhook.execute()

    def message_canal_prise_position(self, message: str, titre: Optional[str] = None):
        """
        Envoi un message sur le canal général
        """
        webhook = DiscordWebhook(
            url=self.adr_webhook_prise_position, username=self.nom, content=message)

        if titre != None:
            embed = DiscordEmbed(title=titre, color="03b2f8")

            embed.add_embed_field(name="Message :", value=message)

            webhook.add_embed(embed)
            webhook.content = None

        webhook.execute()

    def message_erreur(self, erreur: str, emplacement_erreur: str) -> None:
        """
        S'occupe de recevoir une erreur et de l'envoyer sur le canal discord
        """
        fichier = open("fichier_log/log_erreur.txt", "a")

        fichier.write(f"{emplacement_erreur} ; {erreur} \n")

        # On envoie l'emplacement de l'erreur, où elle s'est produite
        # Et si cela arrête le programme ou non
        self.message_canal_general(emplacement_erreur)

        # Si l'erreur est trop grande, alors on la coupe en plusieurs morceaux
        if len(erreur) > 2000:
            while len(erreur) >= 2000:
                self.message_canal_general(erreur[:2000])
                erreur = erreur[2000:]
            if erreur != "":
                self.message_canal_general(erreur)
        else:
            self.message_canal_general(erreur)
