from main import IA, insert_data_historique_bdd

# reste a faire : XRP, ADA, SOL

insert_data_historique_bdd("XRPUSDT", 50_000)

ia = IA("XRP")

ia.training_2()
