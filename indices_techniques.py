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
    Obliger de faire la deuxième liste en deux étape car parfois, les nombres décimaux
    sont sous forme d'une chaine de caractère, et donc faut d'abord les re-transformer en décimaux
    """
    liste2 = [float(x) for x in liste]
    liste2 = [float(x) for x in liste2 if math.isnan(x) == False]
    if len(liste2) == 0:
        liste2.append(5)

    return sum(liste2) / len(liste2)

# Fonctions qui renvoient sous forme d'un entier ou décimal ou d'une liste
# data de 15 éléments


def RSI(donnée_rsi: pandas.DataFrame) -> float:
    """
    Prend en argument une dataframe pandas et une durée qui est un entier
    Renvoie le rsi sous forme d'un float
    """
    # On récupère les données de la colonne close
    data = [float(x) for x in donnée_rsi.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    np_data = numpy.array(data)

    # On récupère le temps (nombre de données) et on fait -1 car sinon cela ne marche pas (renvoie que des nan)
    # Et on garde le dernier élément que renvoie la fonction (car les autres sont que des nan)
    # Et on le transforme en float

    rsi = float(talib.RSI(np_data, len(np_data) - 1)[-1])

    return rsi


def chaikin_money_flow(donnée_cmf: pandas.DataFrame) -> float:
    """
    Prend en argument une dataframe pandas
    Renvoie le cmf sous forme d'un float
    Daily Money Flow = [((Close – Low) – (High – Close)) / (High – Low)] * Volume
    Chaikin Money Flow = 21-Day Average of Daily Money Flow / 21-Day Average of Volume
    """
    moyenne_flow = []
    moyenne_volume = []
    for i in range(len(donnée_cmf)):
        close = float(donnée_cmf.close.values[i])
        low = float(donnée_cmf.low.values[i])
        high = float(donnée_cmf.high.values[i])
        volumme = float(donnée_cmf.volume.values[i])
        numérateur = (close - low) - (high - close)
        dénominateur = (high - low)
        if dénominateur == 0:
            dénominateur = 1
        flow = (numérateur / dénominateur) * volumme
        moyenne_flow.append(flow)
        moyenne_volume.append(volumme)

    my_volume = moyenne(moyenne_volume)

    if my_volume == 0:
        my_volume = 1

    result = moyenne(moyenne_flow) / my_volume

    return result


#################### liste####################


def ROC(donnée_roc: pandas.DataFrame) -> list:
    """
    Calcule le ROC (compare le prix actuel à un prix antérieur 
    et est utilisé pour confirmer les mouvements de prix ou détecter les divergences)
    """
    data = [float(x) for x in donnée_roc.close.values]

    np_data = numpy.array(data)

    roc = [float(x) for x in talib.ROC(np_data) if math.isnan(x) == False]

    return roc


def OBV(donnée_obv: pandas.DataFrame) -> list:
    """
    Calcule le OBV (combine le prix et le volume afin de déterminer 
    si les mouvements de prix sont forts ou faibles)
    """
    data_volume = [float(x) for x in donnée_obv.low.values]
    data_close = [float(x) for x in donnée_obv.close.values]

    np_volume = numpy.array(data_volume)
    np_close = numpy.array(data_close)

    obv = talib.OBV(np_close, np_volume)

    ls = []

    for elt in obv:
        ls.append(elt)

    return ls

###################################################################

# Fonctions qui renvoient sous forme d'une liste
# data de 40 éléments


def SMA(donnée_sma: pandas.DataFrame) -> list:
    """
    Prend en argument une dataframe pandas et une durée qui est un entier
    Renvoie le sma sous forme d'une liste
    """
    # On récupère les données de la colonne close
    data = [float(x) for x in donnée_sma.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    np_data = numpy.array(data)

    # On récupère le retour de la fonction sma sur les valeurs données
    sma = talib.SMA(np_data)

    # Et on enlève les nan
    sma = [float(x) for x in sma if math.isnan(x) == False]

    return sma


def EMA(donnée_ema: pandas.DataFrame) -> list:
    """
    Prend en argument une dataframe pandas et une durée qui est un entier
    Renvoie le ema sous forme d'une liste
    """

    # On récupère les données de la colonne close
    data = [float(x) for x in donnée_ema.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    np_data = numpy.array(data)

    # On récupère le retour de la fonction ema sur les valeurs données
    ema = talib.EMA(np_data)

    # Et on enlève les nan
    ema = [float(x) for x in ema if math.isnan(x) == False]

    return ema


# Fonctions qui renvoient sous forme d'une liste de listes


def MACD(donnée_macd: pandas.DataFrame) -> Union[list, list, list]:
    """
    Prend en argument une dataframe pandas
    Renvoie le MACD sous forme d'une liste de trois listes
    """

    # On récupère les données de la colonne close
    data = [float(x) for x in donnée_macd.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    np_data = numpy.array(data)

    # On récupère le retour de la fonction macd sur les valeurs données
    macd, signal, hist = talib.MACD(np_data)

    # Et on enlève les nan
    macd = [float(x) for x in macd if math.isnan(x) == False]
    signal = [float(x) for x in signal if math.isnan(x) == False]
    hist = [float(x) for x in hist if math.isnan(x) == False]

    return [macd, signal, hist]


def calcul_indice_15_donnees(donnée_serveur_rsi: pandas.DataFrame) -> list:
    """
    Calcul les indices techniques qui nécessite 15 données
    """
    ls = [RSI(donnée_serveur_rsi), chaikin_money_flow(
        donnée_serveur_rsi), ROC(donnée_serveur_rsi), OBV(donnée_serveur_rsi)]

    return ls


def calcul_indice_40_donnees(donnée_serveur_data: pandas.DataFrame) -> list:
    """
    Calcul les indices techniques qui nécessite 40 données
    """
    ls = [SMA(donnée_serveur_data), EMA(
        donnée_serveur_data), MACD(donnée_serveur_data)]

    return ls


def one_liste(donnee: list or tuple, bdd: Optional[bool] = None) -> list:
    """
    Prend en argument la liste avec toutes les données brutes
    Renvoi une seule et même liste avec toutes les données (pas de sous liste)
    """
    resultat = []

    cpt = 1
    for element in donnee:
        elt = element
        if cpt <= 2 or cpt >= 6:
            if bdd != None:
                elt = ast.literal_eval(str(elt))

            for nb in elt:
                resultat.append(nb)
        elif cpt <= 3:
            if bdd != None:
                elt = ast.literal_eval(str(elt))

            for liste in elt:
                for nb in liste:
                    resultat.append(nb)
        elif cpt <= 5:
            if bdd != None:
                elt = float(elt)

            resultat.append(elt)

        cpt += 1

    return resultat
