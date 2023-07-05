from main import IA, Binance, Kucoin, Process, sleep

# bi = Binance("BTC")
# ia = IA("BTC")

# ku = Kucoin("BTC")

p = Process()

print(p.is_alive())
p.start()
print(p.is_alive())
p.kill()
print(p.is_alive())

sleep(3)
print(p.is_alive())

"""
datas = bi.all_data()

data = datas[0]
data_up = datas[1]
data_down = datas[2]

rsi_vwap_cmf = datas[3]
rsi_vwap_cmf_up = datas[4]
rsi_vwap_cmf_down = datas[5]

prediction = ia.prediction_keras(data, rsi_vwap_cmf, True)
prediction_up = ia.prediction_keras(
    data_up, rsi_vwap_cmf_up, False)
prediction_down = ia.prediction_keras(
    data_down, rsi_vwap_cmf_down, None)

prix = float(data['close'][39])
prix_up = float(data_up['close'][39])
prix_down = float(data_down['close'][39])

print(f"prix crypto down : {prix_down}, prix de la prédiction : {prediction_down}")
"""