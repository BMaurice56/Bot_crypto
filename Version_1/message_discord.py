from discord_webhook import DiscordWebhook, DiscordEmbed


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

    def message_prise_position(self, message: str, prise_position: bool) -> None:
        """
        Fonction qui envoie un message au serveur discord au travers d'un webhook sur le canal de prise de position
        Envoie la prise ou vente de position, les gains, etc...
        Ex param :
        message : "vente d'une position etc...
        prise_position : True pour un achat et False pour une vente
        """
        webhook = DiscordWebhook(
            url=self.adr_webhook_prise_position, username=self.nom)

        if prise_position == True:
            embed = DiscordEmbed(title='Prise de position', color="03b2f8")
        else:
            embed = DiscordEmbed(title='Vente de position', color="03b2f8")

        embed.add_embed_field(name="Message :", value=message)
        webhook.add_embed(embed)
        webhook.execute()

    def message_état_bot(self, message: str) -> None:
        """
        Fonction qui envoie un message au serveur discord au travers d'un webhook sur le canal éta bot
        Envoie l'état en cours du bot
        Ex param :
        message : "Bot toujours en cours d'execution ..."
        """
        webhook = DiscordWebhook(
            url=self.adr_webhook_état_bot, username=self.nom)

        embed = DiscordEmbed(title='Etat du bot !', color="03b2f8")
        embed.add_embed_field(name="Message :", value=message)
        webhook.add_embed(embed)
        webhook.execute()

    def message_status_général(self, message: str) -> None:
        """
        Fonction qui envoie un message au serveur discord au travers d'un webhook sur le canal général
        Ex param :
        message : "Bot crypto est lancé"
        """
        webhook = DiscordWebhook(
            url=self.adr_webhook_général, username=self.nom, content=message)

        webhook.execute()

    def message_erreur(self, erreur: str, emplacement_erreur: str) -> None:
        """
        Fonction qui gère de recevoir une erreur et de l'envoyer sur le canal discord
        """
        fichier = open("fichier_log/log_erreur.txt", "a")

        fichier.write(f"{emplacement_erreur} ; {erreur} \n")

        # On envoie l'emplacement de l'erreur, où elle s'est produite
        # Et si cela arrête le programme ou non
        self.message_status_général(emplacement_erreur)

        # Si l'erreur est trop grande, alors on la coupe en plusieurs morceaux
        if len(erreur) > 2000:
            while len(erreur) >= 2000:
                self.message_status_général(erreur[:2000])
                erreur = erreur[2000:]
            if erreur != "":
                self.message_status_général(erreur)
        else:
            self.message_status_général(erreur)

    def message_vente_ordre(self, montant: str) -> None:
        """
        Fonction qui envoie un message au serveur discord au travers d'un webhook sur le canal de prise de position
        Envoi un message pour annoncer la vente de l'ordre
        """
        webhook = DiscordWebhook(
            url=self.adr_webhook_prise_position, username=self.nom)

        embed = DiscordEmbed(title="Vente de l'ordre limite", color="03b2f8")

        embed.add_embed_field(
            name="Message :", value=f"Vente de l'ordre limite, il reste {montant} USDT !")
        webhook.add_embed(embed)
        webhook.execute()

    def message_changement_ordre(self, gain) -> None:
        """
        Fonction qui prévient d'un changement / d'une baisse de l'ordre limite
        """
        webhook = DiscordWebhook(
            url=self.adr_webhook_prise_position, username=self.nom)

        embed = DiscordEmbed(
            title="Modification de l'ordre limite", color="03b2f8")

        msg = "Baisse de l'ordre limite, l'estimation du prix de revente risque d'être fausse !\n" + \
            f"Nouveau gain : {gain}"

        embed.add_embed_field(
            name="Message :", value=msg)
        webhook.add_embed(embed)
        webhook.execute()

    def message_vente_stoploss(self) -> None:
        """
        Fonction qui envoit un message sur le canal prise_position
        Averti que le stoploss vend la position
        """
        webhook = DiscordWebhook(
            url=self.adr_webhook_prise_position, username=self.nom)

        embed = DiscordEmbed(
            title="Exécution du stoploss", color="03b2f8")

        embed.add_embed_field(
            name="Message :", value="Vente des cryptos via le stoploss")
        webhook.add_embed(embed)
        webhook.execute()
