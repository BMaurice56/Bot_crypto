from main import IA, insert_data_historique_bdd

# reste a faire : BNB, XRP, ADA, SOL

insert_data_historique_bdd("BNBUSDT", 50_000)

ia = IA("BNB")

ia.training_2()
