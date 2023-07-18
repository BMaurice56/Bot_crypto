from main import IA, Binance, insert_data_historique_bdd, select_data_bdd, train_test_split

bi = Binance("BTCDOWN")
ia = IA("BTC")
"""
insert_data_historique_bdd("BTCDOWN", 548)

ia.training_2()


"""
# ku = Kucoin("BTC")


rsi = bi.data("15 day ago UTC", "0 day ago UTC")
data = bi.data("40 day ago UTC", "0 day ago UTC")

print(ia.prediction_keras(data, data[25:].rename(index=lambda x: x - 25), True))
