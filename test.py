from main import IA
from database_old import insert_data_historique_bdd

insert_data_historique_bdd("BTCDOWNUSDT", 364 * 12)

ia = IA("BTC")

ia.training_2()

