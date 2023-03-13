from main import IA, insert_data_historique_bdd, model_from_json

# reste a faire : BTC, ETH, BNB, XRP, ADA, SOL

insert_data_historique_bdd("BTCUSDT", 50_000)

ia = IA("BTC")

ia.training_2()
