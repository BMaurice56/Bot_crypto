from main import *

symbol = 'BTCEUR'

data = donnée(symbol, "600 min ago UTC", "0 min ago UTC", 40)
rsi = donnée(symbol, "225 min ago UTC", "0 min ago UTC", 15)

print(prédiction_keras(data, rsi))
print(prix_temps_reel(symbol))
