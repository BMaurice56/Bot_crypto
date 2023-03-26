from discord_webhook import DiscordWebhook, DiscordEmbed
from typing import Optional
import traceback


class Message_discord:
    """
    Classe qui contient les fonctions d'envoi de message sur discord via webhook
    """

    def __init__(self) -> None:
        """
        Initialise un objet message pour l'envoi de ceux-ci
        """
        # Adresse du webhook discord
        self.adr_webhook_general = "https://discordapp.com/api/webhooks/969652904959045674" + \
                                   "/KdVNf9INCcZ3O4V1NnzCsJfhwiAgy4cy1GMjaPZI7spmAAeIkS7sQSYGuKMT5YyAyLza"
        self.adr_webhook_state_bot = "https://discord.com/api/webhooks/972545553210695731/" + \
                                     "zLBkaDU4SPyyLoVXz5E-tv-4PkhfrZH6gipWwSI-1cAqwxFlrbYjKsxxRc2i9zioINIh"
        self.adr_webhook_prise_position = "https://discord.com/api/webhooks/973269614874214410/" + \
                                          "UPyGLXDE2MbjvtmehG8cAAxx3zXtU3Kt-mN4TolLo1golSuHUp9AiCal0jrvIu3C6E6_"

        self.nom = "Jimmy"

    def message_canal(self, canal: str, message: str, titre: Optional[str] = None):
        """
        Envoi un message sur le canal voulu

        Ex params :
        canal : "général" ou "état_bot" ou "prise_position"
        message : contenue du message
        titre (optionnel) : titre du message
        """
        adresse = ""

        if canal == "général":
            adresse = self.adr_webhook_general
        elif canal == "état_bot":
            adresse = self.adr_webhook_state_bot
        elif canal == "prise_position":
            adresse = self.adr_webhook_prise_position

        webhook = DiscordWebhook(
            url=adresse, username=self.nom, content=message)

        if titre is not None:
            embed = DiscordEmbed(title=titre, color="03b2f8")

            embed.add_embed_field(name="Message :", value=message)

            webhook.add_embed(embed)
            webhook.content = None

        webhook.execute()

    def message_erreur(self, error: Exception, location_error: str) -> None:
        """
        S'occupe de recevoir une erreur et de l'envoyer sur le canal discord

        Ex params :
        error : erreur python
        location_error : Message de l'utilisateur, emplacement de l'erreur dans le programme
        """
        # Récupération de l'erreur
        error = "".join(traceback.format_exception(type(error), error, error.__traceback__))

        with open("log_files/log_erreur.txt", "a") as f:
            f.write(f"{location_error} ; {error} \n")

        # On envoie l'emplacement de l'erreur, où elle s'est produite
        # Et si cela arrête le programme ou non
        self.message_canal("général", location_error)

        # Si l'erreur est trop grande, alors on la coupe en plusieurs morceaux
        if len(error) > 2000:
            while len(error) >= 2000:
                self.message_canal("général", error[:2000])
                error = error[2000:]
            if error != "":
                self.message_canal("général", error)
        else:
            self.message_canal("général", error)
