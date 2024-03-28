import paramiko

# Créer une instance de la classe Paramiko SSHClient
ssh = paramiko.SSHClient()

# Autorise les connexions SSH à des hôtes non connus
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Connection au serveur SSH
ssh.connect('adresse ip', username='root', password='mdp')

# Démarre la session SFTP
sftp = ssh.open_sftp()

# Télécharge les fichiers depuis le serveur SSH
sftp.get('/home/Bot_crypto/log_files/log_erreur.txt',
         "log_erreur.txt")

sftp.get('/home/Bot_crypto/log_files/log_recap.txt',
         "log_recap.txt")

ssh.exec_command(
    'echo > /home/Bot_crypto/log_files/log_erreur.txt')
ssh.exec_command(
    'echo > /home/Bot_crypto/log_files/log_recap.txt')

# Ferme la session SFTP
sftp.close()

# Déconnexion du serveur SSH
ssh.close()
