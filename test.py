from main import *

#prédiction_keras(pandas.DataFrame(), pandas.DataFrame())

toto = curseur.execute("select harami from data").fetchall()
indice_min = 10**9
for element in toto:
    element = ast.literal_eval(str(element[0]))
    for elt in element:
        if elt != 0:
            if element.index(elt) < indice_min:
                print(element)
                indice_min = element.index(elt)

print(indice_min, len(toto[0]))
