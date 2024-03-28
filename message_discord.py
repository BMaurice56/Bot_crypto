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
        self.adr_webhook_general = "Adresse webhook 1"
        self.adr_webhook_state_bot = "Adresse webhook 2"
        self.adr_webhook_prise_position = "Adresse webhook 3"

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
