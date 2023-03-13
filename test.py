from main import IA, insert_data_historique_bdd

# reste a faire : ETH, BNB, XRP, ADA, SOL

insert_data_historique_bdd("BTCDOWNUSDT", 50_000)

ia = IA("BTC")

ia.training_2()
