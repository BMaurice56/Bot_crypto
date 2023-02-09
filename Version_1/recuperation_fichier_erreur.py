import paramiko


def récupération_fichier():
    """
    Fonction qui récupère les fichiers logs sur le serveur
    """

    # Créer une instance de la classe Paramiko SSHClient
    ssh = paramiko.SSHClient()

    # Autoriser les connexions SSH à des hôtes non connus
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Connectez-vous au serveur SSH
    ssh.connect('212.227.209.205', username='root', password='I50ja%1ItV')

    # Exécuter la commande SFTP pour démarrer la session SFTP
    sftp = ssh.open_sftp()

    # Télécharger un fichier depuis le serveur SSH
    sftp.get('/home/Bot_crypto/Version_1/fichier_log/log_erreur.txt',
             "log_erreur.txt")

    sftp.get('/home/Bot_crypto/Version_1/fichier_log/log_recap.txt',
             "log_recap.txt")

    ssh.exec_command(
        'echo "" > /home/Bot_crypto/Version_1/fichier_log/log_requete.txt')
    ssh.exec_command(
        'echo "" > /home/Bot_crypto/Version_1/fichier_log/log_recap.txt')

    # Fermer la session SFTP
    sftp.close()

    # Déconnectez-vous du serveur SSH
    ssh.close()


récupération_fichier()
