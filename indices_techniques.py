import talib
import numpy
import pandas
import math


# Fonctions qui renvoient sous forme d'un entier ou décimal
# data de 15 éléments

def RSI(donnée_rsi: pandas.DataFrame) -> float:
    """
    Fonction qui prend en argument une dataframe pandas et une durée qui est un entier
    Et renvoie le rsi sous forme d'un float
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


def VWAP(donnée_vwap: pandas.DataFrame) -> float:
    """
    Fonction qui prend en argument une dataframe pandas
    Et qui renvoie le vwap sous forme d'une float
    """

    haut = [float(x) for x in donnée_vwap.high.values]
    bas = [float(x) for x in donnée_vwap.low.values]
    fermeture = [float(x) for x in donnée_vwap.close.values]
    volume = [float(x) for x in donnée_vwap.volume.values]

    somme_pr_t_x_volume = 0
    for i in range(len(haut)):
        prix_typique = (haut[i] + bas[i] + fermeture[i])/3
        somme_pr_t_x_volume += prix_typique * volume[i]

    vwap = somme_pr_t_x_volume / sum(volume)

    return vwap


def chaikin_money_flow(donnée_cmf: pandas.DataFrame) -> float:
    """
    Fonction qui prend en argument une dataframe pandas
    Et qui renvoie le cmf sous forme d'un float
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

    result = moyenne(moyenne_flow) / moyenne(moyenne_volume)

    return result


def CCI(donnée_cci) -> float:
    """
    Fonction qui calcule le CCI (tente d'interpréter les signaux d'achat 
    et de vente et peut identifier les zones de surachat et de 
    survente de l'action des prix)
    """
    data_high = [float(x) for x in donnée_cci.high.values]
    data_low = [float(x) for x in donnée_cci.low.values]
    data_close = [float(x) for x in donnée_cci.close.values]

    np_high = numpy.array(data_high)
    np_low = numpy.array(data_low)
    np_close = numpy.array(data_close)

    cci = talib.CCI(np_high, np_low, np_close, len(data_close))

    return float(cci[-1])


def MFI(donnée_mfi: pandas.DataFrame) -> float:
    """
    Fonction qui calcul le MFI (utile pour confirmer les tendances 
    des prix et avertir d'éventuels renversements de prix)
    """
    data_volume = [float(x) for x in donnée_mfi.volume.values]
    data_high = [float(x) for x in donnée_mfi.high.values]
    data_low = [float(x) for x in donnée_mfi.low.values]
    data_close = [float(x) for x in donnée_mfi.close.values]

    np_volume = numpy.array(data_volume)
    np_high = numpy.array(data_high)
    np_low = numpy.array(data_low)
    np_close = numpy.array(data_close)

    mfi = float(talib.MFI(np_high, np_low, np_close, np_volume)[-1])

    return mfi


def LinearRegression(donnée_lr: pandas.DataFrame) -> float:
    """
    Fonction qui calcule la régrésion linéraire
    """
    data_close = [float(x) for x in donnée_lr.close.values]

    np_close = numpy.array(data_close)

    line = float(talib.LINEARREG(np_close, 15)[-1])

    return line

# Fonctions qui renvoient sous forme d'une liste
# data de 40 éléments


def SMA(donnée_sma: pandas.DataFrame) -> list:
    """
    Fonction qui prend en argument une dataframe pandas et une durée qui est un entier
    Et renvoie le sma sous forme d'une liste
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
    Fonction qui prend en argument une dataframe pandas et une durée qui est un entier
    Et renvoie le ema sous forme d'une liste
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


def evening_star(donnée_es: pandas.DataFrame) -> list:
    """
    Fonction qui calcule le evening star (modèle de retournement baissier)
    Renvoie sous forme d'une liste composée de [-100, 0 ou 100]
    """
    data_open = [float(x) for x in donnée_es.open.values]
    data_high = [float(x) for x in donnée_es.high.values]
    data_low = [float(x) for x in donnée_es.low.values]
    data_close = [float(x) for x in donnée_es.close.values]

    np_open = numpy.array(data_open)
    np_high = numpy.array(data_high)
    np_low = numpy.array(data_low)
    np_close = numpy.array(data_close)

    es = talib.CDLEVENINGSTAR(np_open, np_high, np_low, np_close)

    return es


def harami(donnée_harami: pandas.DataFrame) -> list:
    """
    Fonction qui calcule le harami (modèle de renversement qui peut être haussier ou baissier)
    """
    data_open = [float(x) for x in donnée_harami.open.values]
    data_high = [float(x) for x in donnée_harami.high.values]
    data_low = [float(x) for x in donnée_harami.low.values]
    data_close = [float(x) for x in donnée_harami.close.values]

    np_open = numpy.array(data_open)
    np_high = numpy.array(data_high)
    np_low = numpy.array(data_low)
    np_close = numpy.array(data_close)

    ha = talib.CDLHARAMI(np_open, np_high, np_low, np_close)

    return ha


def doji(donnée_doji: pandas.DataFrame) -> list:
    """
    Fonction qui calcule le doji (peuvent être considérés comme un renversement possible ou comme un modèle de continuation)
    """
    data_open = [float(x) for x in donnée_doji.open.values]
    data_high = [float(x) for x in donnée_doji.high.values]
    data_low = [float(x) for x in donnée_doji.low.values]
    data_close = [float(x) for x in donnée_doji.close.values]

    np_open = numpy.array(data_open)
    np_high = numpy.array(data_high)
    np_low = numpy.array(data_low)
    np_close = numpy.array(data_close)

    doji_data = talib.CDLDOJI(np_open, np_high, np_low, np_close)

    return doji_data


def ADX(donnée_adx: pandas.DataFrame) -> list:
    """
    Fonction qui calcul le ADX (Décrit si un marché est en tendance ou non)
    """
    data_high = [float(x) for x in donnée_adx.high.values]
    data_low = [float(x) for x in donnée_adx.low.values]
    data_close = [float(x) for x in donnée_adx.close.values]

    np_high = numpy.array(data_high)
    np_low = numpy.array(data_low)
    np_close = numpy.array(data_close)

    data = talib.ADX(np_high, np_low, np_close)

    adx = [float(x) for x in data if math.isnan(x) == False]

    return adx


def KAMA(donnée_kama) -> list:
    """
    Fonction qui calcule le KAMA (devient plus sensible pendant les périodes 
    où les mouvements de prix sont stables dans une certaine direction 
    et devient moins sensible aux mouvements de prix lorsque le prix est volatile)
    """
    data_close = [float(x) for x in donnée_kama.close.values]

    np_close = numpy.array(data_close)

    kama = [float(x) for x in talib.KAMA(np_close) if math.isnan(x) == False]

    return kama

# Fonctions qui renvoient sous forme d'une liste de listes


def MACD(donnée_macd: pandas.DataFrame) -> [list, list, list]:
    """
    Fonction qui prend en argument une dataframe pandas
    Et renvoie le MACD sous forme d'une liste de trois listes
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


def stochRSI(donnée_stochrsi: pandas.DataFrame) -> [list, list]:
    """
    Fonction qui prend en argument une dataframe pandas
    Et qui renvoie le stochRSI sous forme de deux listes
    On utilise pas la fonction par défaut stochrsi de talib car
    celle-ci applique stochf à rsi et non pas stoch à rsi
    """
    # On récupère les données de la colonne close
    data = [float(x) for x in donnée_stochrsi.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    np_data = numpy.array(data)

    # On récupère le retour de la fonction rsi sur les valeurs données
    rsi = talib.RSI(np_data)

    # Et on applique stoch dessus
    stochrsi, signal = talib.STOCH(rsi, rsi, rsi)

    # Enfin, on enlève les nan
    stochrsi = [float(x) for x in stochrsi if math.isnan(x) == False]
    signal = [float(x) for x in signal if math.isnan(x) == False]

    return [stochrsi, signal]


def bandes_bollinger(donnée_bandes: pandas.DataFrame) -> [list, list, list]:
    """
    Fonction qui prend en argument une dataframe pandas
    Et qui renvoie les bandes de bollinger sous forme d'une liste de trois listes
    """

    # On récupère les données de la colonne close
    data = [float(x) for x in donnée_bandes.close.values]

    # Création d'un tableau numpy pour la fonction de talib
    np_data = numpy.array(data)

    # On récupère le retour de la fonction bbands sur les valeurs données
    up, middle, low = talib.BBANDS(np_data)

    # Et on enlève les nan
    up = [float(x) for x in up if math.isnan(x) == False]
    middle = [float(x) for x in middle if math.isnan(x) == False]
    low = [float(x) for x in low if math.isnan(x) == False]

    return [up, middle, low]
