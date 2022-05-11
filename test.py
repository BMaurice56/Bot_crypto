"""
import matplotlib.pyplot as plt
from datetime import datetime



interval = client.KLINE_INTERVAL_15MINUTE
fin = "0 min ago UTC"

data = donnée(symbol, interval, "30000 min ago UTC", fin, 2000)
#data = select_data_bdd()

"""

from main import *

symbol = 'BTCEUR'


for i in range(3000, 40*15, -15):

    data = donnée(symbol, f"{i} min ago UTC",
                      f"{i - 15*15} min ago UTC", 15)
    
    d = toto(data)
    print(d)
    break
    

