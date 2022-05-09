"""
import matplotlib.pyplot as plt
from datetime import datetime


symbol = 'BTCEUR'
interval = client.KLINE_INTERVAL_15MINUTE
fin = "0 min ago UTC"

data = donnée(symbol, interval, "30000 min ago UTC", fin, 2000)
#data = select_data_bdd()


close = data.close.values

for i in range(len(close)):
    close[i] = float(close[i])


minimum = float('inf')
maximum = float('-inf')

indice_min = 0
indice_max = 0

for i in range(1, len(close) - 1):
    if close[i-1] > close[i] and close[i] < close[i+1] and minimum > close[i]:
        minimum = close[i]
        indice_min = i
    elif close[i-1] < close[i] and close[i] > close[i+1] and maximum < close[i]:
        maximum = close[i]
        indice_max = i

ratio_desc = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
ratio_asc = ratio_desc.copy()
ratio_asc.reverse()

diff = maximum - minimum

ls = []
if indice_max > indice_min:
    for elt in ratio_asc:
        ls.append(minimum + (diff * elt))
else:
    for elt in ratio_desc:
        ls.append(maximum - (diff * elt))
couleurs = ["black","r","g","b","cyan","magenta","yellow", "black"]
cpt = 0
for element in ls:
    plt.hlines(element, 2, len(close), couleurs[cpt], "dashed", f"{ratio_asc[cpt] * 100}")
    cpt += 1

plt.plot(close)
plt.scatter(indice_min, minimum)
plt.scatter(indice_max, maximum)
plt.show()

from main import *

print(sys.argv[0], sys.argv[1], sys.argv[2])
"""
