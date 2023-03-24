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


# liste #######################################


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


def calcul_indice_15_donnees(data_server_15: pandas.DataFrame) -> list:
    """
    Calcul les indices techniques qui nécessite 15 données
    """
    ls = [rsi(data_server_15), chaikin_money_flow(
        data_server_15), roc(data_server_15), obv(data_server_15)]

    return ls


def calcul_indice_40_donnees(data_server_40: pandas.DataFrame) -> list:
    """
    Calcul les indices techniques qui nécessite 40 données
    """
    ls = [sma(data_server_40), ema(
        data_server_40), macd(data_server_40)]

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
