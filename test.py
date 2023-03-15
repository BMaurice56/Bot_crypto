from main import IA, insert_data_historique_bdd, select_donnée_bdd, train_test_split, r2_score
from sklearn.metrics import mean_absolute_error, mean_squared_error

# reste a faire : XRP, ADA, SOL

# insert_data_historique_bdd("BTCUSDT", 50_000)

ia = IA("BTC")

ia.training_2()

"""
X, y = select_donnée_bdd("numpy")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42)

ia = IA("BTC")

modele, modele_up, modele_down = ia.chargement_modele()

y_pred = modele.predict(X_test)

mse = mean_squared_error(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("Mean Squared Error (MSE): {:.2f}".format(mse))
print("Mean Absolute Error (MAE): {:.2f}".format(mae))
print("Coefficient de détermination R²: {:.2f}".format(r2))

# calculer les écarts résiduels
residuals = y_test - y_pred

print(residuals)
"""
