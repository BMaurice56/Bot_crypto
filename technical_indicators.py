from typing import Union, Optional
import pandas
import talib
import numpy
import math
import ast


# Autres fonctions


def moyenne(liste: list or dict) -> float:
    """
    Calcule la moyenne des éléments d'une liste d'entier ou de décimaux
    Obliger de faire la deuxième liste en deux étapes, car parfois, les nombres décimaux
    sont sous forme d'une chaine de caractère, et donc il faut d'abord les re-transformer en décimaux
    """
    liste2 = [float(x) for x in liste]
    liste2 = [float(x) for x in liste2 if math.isnan(x) is False]
    if len(liste2) == 0:
        liste2.append(5)

    return sum(liste2) / len(liste2)


# Fonctions qui renvoient sous forme d'un entier ou décimal ou d'une liste
# data de 15 éléments


# Fonctions qui renvoient sous forme d'un entier ou décimal ou d'une liste
# data de 15 éléments


def rsi(data_rsi: pandas.DataFrame) -> float:
    """
    Prend en argument une dataframe pandas et une durée qui est un entier
    Renvoie le rsi sous forme d'un float
    """
    # On récupère les données de la colonne close
    data = [float(x) for x in data_rsi.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    np_data = numpy.array(data)

    # On récupère le temps (nombre de données) et on fait -1, car sinon cela ne marche pas (renvoie que des nan)
    # Et on garde le dernier élément que renvoie la fonction (parce que les autres sont que des nan)
    # Et on le transforme en float

    return float(talib.RSI(np_data, len(np_data) - 1)[-1])


def vwap(data_vwap: pandas.DataFrame) -> float:
    """
    Fonction qui prend en argument une dataframe pandas
    Et qui renvoie le vwap sous forme d'une float
    """

    haut = [float(x) for x in data_vwap.high.values]
    bas = [float(x) for x in data_vwap.low.values]
    fermeture = [float(x) for x in data_vwap.close.values]
    volume = [float(x) for x in data_vwap.volume.values]

    somme_pr_t_x_volume = 0
    for i in range(len(haut)):
        prix_typique = (haut[i] + bas[i] + fermeture[i]) / 3
        somme_pr_t_x_volume += prix_typique * volume[i]

    somme_volume = sum(volume)

    if somme_volume == 0:
        somme_volume = 1

    return somme_pr_t_x_volume / somme_volume


def chaikin_money_flow(data_cmf: pandas.DataFrame) -> float:
    """
    Prend en argument une dataframe pandas
    Renvoie le cmf sous forme d'un float
    Daily Money Flow = [((Close – Low) – (High – Close)) / (High – Low)] * Volume
    Chaikin Money Flow = 21-Day Average of Daily Money Flow / 21-Day Average of Volume
    """
    moyenne_flow = []
    moyenne_volume = []
    for i in range(len(data_cmf)):
        close = float(data_cmf.close.values[i])
        low = float(data_cmf.low.values[i])
        high = float(data_cmf.high.values[i])
        volume = float(data_cmf.volume.values[i])
        numerator = (close - low) - (high - close)
        denominator = (high - low)
        if denominator == 0:
            denominator = 1
        flow = (numerator / denominator) * volume
        moyenne_flow.append(flow)
        moyenne_volume.append(volume)

    my_volume = moyenne(moyenne_volume)

    if my_volume == 0:
        my_volume = 1

    result = moyenne(moyenne_flow) / my_volume

    return result


def cci(data_cci: pandas.DataFrame) -> float:
    """
    Fonction qui calcule le CCI (tente d'interpréter les signaux d'achat
    et de vente et peut identifier les zones de sur-achat et de
    survente de l'action des prix)
    """
    data_high = [float(x) for x in data_cci.high.values]
    data_low = [float(x) for x in data_cci.low.values]
    data_close = [float(x) for x in data_cci.close.values]

    np_high = numpy.array(data_high)
    np_low = numpy.array(data_low)
    np_close = numpy.array(data_close)

    return float(talib.CCI(np_high, np_low, np_close, len(data_close))[-1])


def mfi(data_mfi: pandas.DataFrame) -> float:
    """
    Fonction qui calcul le MFI (utile pour confirmer les tendances
    des prix et avertir d'éventuels renversements de prix)
    """
    data_volume = [float(x) for x in data_mfi.volume.values]
    data_high = [float(x) for x in data_mfi.high.values]
    data_low = [float(x) for x in data_mfi.low.values]
    data_close = [float(x) for x in data_mfi.close.values]

    np_volume = numpy.array(data_volume)
    np_high = numpy.array(data_high)
    np_low = numpy.array(data_low)
    np_close = numpy.array(data_close)

    return float(talib.MFI(np_high, np_low, np_close, np_volume)[-1])


def linearregression(data_lr: pandas.DataFrame) -> float:
    """
    Fonction qui calcule la regression linéaire
    """
    data_close = [float(x) for x in data_lr.close.values]

    np_close = numpy.array(data_close)

    return float(talib.LINEARREG(np_close, 15)[-1])


def tsf(data_tsf: pandas.DataFrame) -> float:
    """
    Fonction qui renvoie le TSF (calcule une ligne de meilleure adéquation sur une période donnée
    pour tenter de prédire les tendances futures)
    """
    data_close = [float(x) for x in data_tsf.close.values]

    np_close = numpy.array(data_close)

    return float(talib.TSF(np_close, 15)[-1])


def aroon_oscilator(data_ao: pandas.DataFrame) -> float:
    """
    Fonction qui calcule le AO (aide les traders à savoir quand un marché à une tendance à la hausse,
    à la baisse, où se trouve dans une zone de fluctuation ou un marché sans tendance)
    """
    data_high = [float(x) for x in data_ao.high.values]
    data_low = [float(x) for x in data_ao.low.values]

    np_high = numpy.array(data_high)
    np_low = numpy.array(data_low)

    return float(talib.AROONOSC(np_high, np_low)[-1])


def williams_r(data_wr: pandas.DataFrame) -> float:
    """
    Fonction qui calcule le williams R (indicateur technique de sur-achat
    et de survente qui peut offrir des signaux potentiels d'achat et de vente)
    """

    data_high = [float(x) for x in data_wr.high.values]
    data_low = [float(x) for x in data_wr.low.values]
    data_close = [float(x) for x in data_wr.close.values]

    np_high = numpy.array(data_high)
    np_low = numpy.array(data_low)
    np_close = numpy.array(data_close)

    return float(talib.WILLR(np_high, np_low, np_close, 15)[-1])


# ###################liste####################


def roc(data_roc: pandas.DataFrame) -> list:
    """
    Calcule le ROC (compare le prix actuel à un prix antérieur
    et est utilisé pour confirmer les mouvements de prix ou détecter les divergences)
    """
    data = [float(x) for x in data_roc.close.values]

    np_data = numpy.array(data)

    return [float(x) for x in talib.ROC(np_data) if math.isnan(x) is False]


def obv(data_obv: pandas.DataFrame) -> list:
    """
    Calcule le OBV (combine le prix et le volume afin de déterminer
    si les mouvements de prix sont forts ou faibles)
    """
    data_volume = [float(x) for x in data_obv.low.values]
    data_close = [float(x) for x in data_obv.close.values]

    np_volume = numpy.array(data_volume)
    np_close = numpy.array(data_close)

    ls = []

    for elt in talib.OBV(np_close, np_volume):
        ls.append(elt)

    return ls


def mom(data_mom: pandas.DataFrame) -> list:
    """
    Fonction qui calcule le MOM (compare le prix actuel par rapport au prix antérieur)
    """
    data = [float(x) for x in data_mom.close.values]

    np_data = numpy.array(data)

    return [float(x) for x in talib.MOM(np_data) if math.isnan(x) is False]


###################################################################

# Fonctions qui renvoient sous forme d'une liste
# data de 40 éléments


def sma(data_sma: pandas.DataFrame) -> list:
    """
    Prend en argument une dataframe pandas et une durée qui est un entier
    Renvoie le sma sous forme d'une liste
    """
    # On récupère les données de la colonne close
    data = [float(x) for x in data_sma.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    np_data = numpy.array(data)

    return [float(x) for x in talib.SMA(np_data) if math.isnan(x) is False]


def ema(data_ema: pandas.DataFrame) -> list:
    """
    Prend en argument une dataframe pandas et une durée qui est un entier
    Renvoie l'ema sous forme d'une liste
    """

    # On récupère les données de la colonne close
    data = [float(x) for x in data_ema.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    np_data = numpy.array(data)

    return [float(x) for x in talib.EMA(np_data) if math.isnan(x) is False]


def adx(data_adx: pandas.DataFrame) -> list:
    """
    Fonction qui calcul le ADX (Décrit si un marché est en tendance ou non)
    """
    data_high = [float(x) for x in data_adx.high.values]
    data_low = [float(x) for x in data_adx.low.values]
    data_close = [float(x) for x in data_adx.close.values]

    np_high = numpy.array(data_high)
    np_low = numpy.array(data_low)
    np_close = numpy.array(data_close)

    data = talib.ADX(np_high, np_low, np_close)

    return [float(x) for x in data if math.isnan(x) is False]


def kama(data_kama: pandas.DataFrame) -> list:
    """
    Fonction qui calcule le KAMA (devient plus sensible pendant les périodes
    où les mouvements de prix sont stables dans une certaine direction
    et devient moins sensible aux mouvements de prix lorsque le prix est volatile)
    """
    data_close = [float(x) for x in data_kama.close.values]

    np_close = numpy.array(data_close)

    return [float(x) for x in talib.KAMA(np_close) if math.isnan(x) is False]


def t3(data_t3: pandas.DataFrame) -> list:
    """
    Fonction qui calcule le triple moving average exponential (peut donner des signaux potentiels d'achat
    et de vente et tente de filtrer le bruit à court terme.)
    """
    data_close = [float(x) for x in data_t3.close.values]

    np_close = numpy.array(data_close)

    return [float(x) for x in talib.T3(np_close) if math.isnan(x) is False]


def trima(data_trima: pandas.DataFrame) -> list:
    """
    Fonction qui calcule le TRIMA (Moyenne mobile simple qui a été moyennée une nouvelle fois,
    créant ainsi une ligne très lisse)
    """
    data_close = [float(x) for x in data_trima.close.values]

    np_close = numpy.array(data_close)

    return [float(x) for x in talib.TRIMA(np_close) if math.isnan(x) is False]


def ppo(data_ppo: pandas.DataFrame) -> list:
    """
    Fonction qui calcule le PPO (calcule la différence entre les deux moyennes mobiles)
    """
    data = [float(x) for x in data_ppo.close.values]

    np_data = numpy.array(data)

    return [float(x) for x in talib.PPO(np_data) if math.isnan(x) is False]


def ultimate_oscilator(data_uo: pandas.DataFrame) -> list:
    """
    Fonction qui calcule ultimate oscilator (combine l'action des prix à court terme,
    à moyen terme et à long terme en un seul oscillateur)
    """
    data_high = [float(x) for x in data_uo.high.values]
    data_low = [float(x) for x in data_uo.low.values]
    data_close = [float(x) for x in data_uo.close.values]

    np_high = numpy.array(data_high)
    np_low = numpy.array(data_low)
    np_close = numpy.array(data_close)

    return [float(x) for x in talib.ULTOSC(
        np_high, np_low, np_close) if math.isnan(x) is False]


# Fonctions qui renvoient sous forme d'une liste de listes


def macd(data_macd: pandas.DataFrame) -> Union[list, list, list]:
    """
    Prend en argument une dataframe pandas
    Renvoie le MACD sous forme d'une liste de trois listes
    """

    # On récupère les données de la colonne close
    data = [float(x) for x in data_macd.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    np_data = numpy.array(data)

    # On récupère le retour de la fonction macd sur les valeurs données
    ma, signal, hist = talib.MACD(np_data)

    # Et on enlève les nan
    ma = [float(x) for x in ma if math.isnan(x) is False]
    signal = [float(x) for x in signal if math.isnan(x) is False]
    hist = [float(x) for x in hist if math.isnan(x) is False]

    return [ma, signal, hist]


def stochrsi(data_stochrsi: pandas.DataFrame) -> Union[list, list]:
    """
    Fonction qui prend en argument une dataframe pandas
    Et qui renvoie le stochRSI sous forme de deux listes
    On n'utilise pas la fonction par défaut stochrsi de talib car
    celle-ci applique stochf à rsi et non pas stoch à rsi
    """
    # On récupère les données de la colonne close
    data = [float(x) for x in data_stochrsi.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    np_data = numpy.array(data)

    # On récupère le retour de la fonction rsi sur les valeurs données
    valeur_rsi = talib.RSI(np_data)

    # Et on applique stoch dessus
    stoch_rsi, signal = talib.STOCH(valeur_rsi, valeur_rsi, valeur_rsi)

    # Enfin, on enlève les nan
    stoch_rsi = [float(x) for x in stoch_rsi if math.isnan(x) is False]
    signal = [float(x) for x in signal if math.isnan(x) is False]

    return [stoch_rsi, signal]


def bandes_bollinger(data_bandes: pandas.DataFrame) -> Union[list, list, list]:
    """
    Fonction qui prend en argument une dataframe pandas
    Et qui renvoie les bandes de bollinger sous forme d'une liste de trois listes
    """

    # On récupère les données de la colonne close
    data = [float(x) for x in data_bandes.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    np_data = numpy.array(data)

    # On récupère le retour de la fonction bbands sur les valeurs données
    up, middle, low = talib.BBANDS(np_data)

    # Et on enlève les nan
    up = [float(x) for x in up if math.isnan(x) is False]
    middle = [float(x) for x in middle if math.isnan(x) is False]
    low = [float(x) for x in low if math.isnan(x) is False]

    return [up, middle, low]


def calcul_indice_15_donnees_small(data_server_15: pandas.DataFrame) -> list:
    """
    Calcul les indices techniques qui nécessite 15 données
    """
    ls = [rsi(data_server_15), chaikin_money_flow(
        data_server_15), roc(data_server_15), obv(data_server_15)]

    return ls


def calcul_indice_40_donnees_small(data_server_40: pandas.DataFrame) -> list:
    """
    Calcul les indices techniques qui nécessite 40 données
    """
    ls = [sma(data_server_40), ema(
        data_server_40), macd(data_server_40)]

    return ls


def one_liste_small(donnee: list or tuple, bdd: Optional[bool] = None) -> list:
    """
    Prend en argument la liste avec toutes les données brutes
    Renvoi une seule et même liste avec toutes les données (pas de sous liste)
    """
    result = []

    cpt = 1
    for element in donnee:
        elt = element
        if cpt <= 2 or cpt >= 6:
            if bdd is not None:
                elt = ast.literal_eval(str(elt))

            for nb in elt:
                result.append(nb)
        elif cpt <= 3:
            if bdd is not None:
                elt = ast.literal_eval(str(elt))

            for liste in elt:
                for nb in liste:
                    result.append(nb)
        elif cpt <= 5:
            if bdd is not None:
                elt = float(elt)

            result.append(elt)

        cpt += 1

    return result


def calcul_indice_15_donnees(data_server_15: pandas.DataFrame) -> list:
    """
    Calcul les indices techniques qui nécessite 15 données
    """
    ls = [rsi(data_server_15), vwap(data_server_15), chaikin_money_flow(
        data_server_15), cci(data_server_15), mfi(data_server_15), linearregression(
        data_server_15), tsf(data_server_15), aroon_oscilator(data_server_15), williams_r(
        data_server_15), roc(data_server_15), obv(data_server_15), mom(data_server_15)]

    return ls


def calcul_indice_40_donnees(data_server_40: pandas.DataFrame) -> list:
    """
    Calcul les indices techniques qui nécessite 40 données
    """

    ls = [sma(data_server_40), ema(data_server_40), adx(data_server_40),
          kama(data_server_40), t3(data_server_40), trima(data_server_40),
          ppo(data_server_40), ultimate_oscilator(data_server_40),
          macd(data_server_40), stochrsi(data_server_40), bandes_bollinger(data_server_40)]

    return ls


def one_liste(donnee: list or tuple, bdd: Optional[bool] = None) -> list:
    """
    Prend en argument la liste avec toutes les données brutes
    Renvoi une seule et même liste avec toutes les données (pas de sous liste)
    """
    result = []

    cpt = 1
    for element in donnee:
        elt = element
        if cpt <= 8 or cpt >= 21:
            if bdd is not None:
                elt = ast.literal_eval(str(elt))

            for nb in elt:
                result.append(nb)
        elif cpt <= 11:
            if bdd is not None:
                elt = ast.literal_eval(str(elt))

            for liste in elt:
                for nb in liste:
                    result.append(nb)
        elif cpt <= 20:
            if bdd is not None:
                elt = float(elt)

            result.append(elt)

        cpt += 1

    return result
