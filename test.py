"""
import matplotlib.pyplot as plt
from datetime import datetime



interval = client.KLINE_INTERVAL_15MINUTE
fin = "0 min ago UTC"

data = donnée(symbol, interval, "30000 min ago UTC", fin, 2000)
#data = select_data_bdd()


from main import *
t1 = perf_counter()
insert_data_historique_bdd('BTCEUR', 10_000)
t2 = perf_counter()
print(t2 - t1)
"""
from main import *

prédiction_keras(pandas.DataFrame(), pandas.DataFrame())
