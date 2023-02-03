import paramiko
import json


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
    sftp.get('/home/Bot_crypto/Version_1/fichier_log/log_requete.txt',
             "log_requete.txt")
    sftp.get('/home/Bot_crypto/Version_1/fichier_log/log_stoploss_manuel.txt',
             "log_stoploss_manuel.txt")
    sftp.get('/home/Bot_crypto/Version_1/fichier_log/log_update_id_position.txt',
             "log_update_id_position.txt")
    sftp.get('/home/Bot_crypto/Version_1/fichier_log/log_erreur.txt',
             "log_erreur.txt")

    ssh.exec_command(
        'echo "" > /home/Bot_crypto/Version_1/fichier_log/log_requete.txt')
    ssh.exec_command(
        'echo "" > /home/Bot_crypto/Version_1/fichier_log/log_stoploss_manuel.txt')
    ssh.exec_command(
        'echo "" > /home/Bot_crypto/Version_1/fichier_log/log_update_id_position.txt')
    ssh.exec_command(
        'echo "" > /home/Bot_crypto/Version_1/fichier_log/log_erreur.txt')

    # Fermer la session SFTP
    sftp.close()

    # Déconnectez-vous du serveur SSH
    ssh.close()


def analyse_fichier(nom_fichier: str):
    """
    Fonction qui analyse le fichier et renvoie tous les problèmes
    """
    fichier = open(nom_fichier, "r").read()
    if fichier != "":
        # On sépare chaque ligne entre elles (-1 car on ne garde pas le dernier retoure a la ligne)
        contenue = fichier[1:].split("\n")[:-1]
        requete = []
        résultat = []

        # On ne garde que la requête sans la date
        for i in range(len(contenue)):
            requete.append(contenue[i].split(";")[1])

        # Puis on retransforme la requête en un objet python sans les espaces de début et fin
        for j in range(len(requete)):
            requete[j] = json.loads(requete[j][1:-1])

        # Enfin on parcours toutes les requêtes pour vérifier s'il y en a une qui n'a pas abouti
        for k in range(len(requete)):
            if requete[k]['code'] != '200000':
                résultat.append(requete[k])

        return résultat


récupération_fichier()

print(analyse_fichier("log_requete.txt"))
print(analyse_fichier("log_stoploss_manuel.txt"))
print(analyse_fichier("log_stoploss_manuel.txt"))
