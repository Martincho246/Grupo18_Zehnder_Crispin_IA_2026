from simpleai.search.models import SearchProblem
from simpleai.search import SearchProblem, astar

MAX_BATERIA = 20

CAP_MAX_CARGA = 2

COSTO_BATERIA = {"moverse": 1, "sobremarcha": 4, "equipar": 1, "recolectar": 3, "depositar": 1, "recargar": -10}

COSTO_MINUTOS = {"moverse": 1, "sobremarcha": 1, "equipar": 3, "recolectar": 2, "depositar": 1, "recargar": 4}

POSIBLES_MOVIMIENTOS = (
    (0,1),
    (0,-1),
    (1,0),
    (-1,0)
)
POSIBLES_SOBREMARCHAS = (
    (0,2),
    (0,-2),
    (2,0),
    (-2,0)
)
POSIBLES_EQUIPACIONES = (
    "termico",
    "percusion"
)

def CombinacionTaladroValida(taladro,muestras_igneas,muestras_sedimentarias):
    if taladro == "termico" and len(muestras_igneas) > 0:
        return True
    if taladro == "percusion" and len(muestras_sedimentarias) > 0:
        return True
    return False

def DistanciaARecorrerPorEje(posicion_rover,lista_muestras):
    lista_resultado = []
    # [0] diferencia más grande en el ancho (eje x) de los puntos de interes
    # [1] distancia del rover al borde mas cercano en el eje x
    # [2] diferencia más grande en el alto (eje y) de los puntos de interes 
    # [3] distancia del rover al borde mas cercano en el eje y
    for i in range(2):
        minima_coordenada_eje = posicion_rover[i]
        maxima_coordenada_eje = posicion_rover[i]
        for muestra in lista_muestras:
            if muestra[i] > maxima_coordenada_eje:
                maxima_coordenada_eje = muestra[i]
            if muestra[i] < minima_coordenada_eje:
                minima_coordenada_eje = muestra[i]
        lista_resultado.append(abs(maxima_coordenada_eje - minima_coordenada_eje))
        diferencia_rover_izquierda = abs(posicion_rover[i] - minima_coordenada_eje)
        diferencia_rover_derecha = abs(posicion_rover[i] - maxima_coordenada_eje)
        if diferencia_rover_izquierda <= diferencia_rover_derecha:
            lista_resultado.append(diferencia_rover_izquierda)
        else:
            lista_resultado.append(diferencia_rover_derecha)
    return lista_resultado

def MinimosMaximosPorEje(lista_objetos):
    min_x, max_x, min_y, max_y = 0,0,0,0
    primero = True
    for elemento in lista_objetos:
        if primero:
            min_x = elemento[0]
            max_x = elemento[0]
            min_y = elemento[1]
            max_y = elemento[1]
            primero = False
            continue
        if elemento[0] > max_x:
            max_x = elemento[0]
        if elemento[0] < min_x:
            min_x = elemento[0]
        if elemento[1] > max_y:
            max_y = elemento[1]
        if elemento[1] < min_y:
            min_y = elemento[1]

    return min_x,max_x,min_y,max_y

class RoverProblem(SearchProblem):
    #pensar estado.
    #(posicionrover(X,Y), bateria int,taladroactivo string ,cargaactual int ,muestrasigneas [(X1, Y1), (X2, Y2), (Xn, Yn)], muestrassedimentarias [(X1, Y1), (X2, Y2), (Xn, Yn)])

    def actions(self, state):
        posicion_rover = state [0]
        bateria_actual = state [1]
        taladro_activo = state [2]
        carga_actual = state[3]
        muestras_igneas = state[4]
        muestras_sedimentarias = state[5]
        lista_muestras = list(muestras_igneas) + list(muestras_sedimentarias)
        acciones_validas = []

        # Solo se puede mover si tiene batería y no lleva toda su carga, o si tiene batería y está en una zona sombra, aplica igual para sobremarcha.
        if bateria_actual - COSTO_BATERIA["moverse"] > 0 and (carga_actual < CAP_MAX_CARGA or posicion_rover in ZONA_SOMBRA):
            for move in POSIBLES_MOVIMIENTOS:
                nueva_posicion = (posicion_rover[0] + move[0], posicion_rover[1] + move[1])
                if MIN_X <= nueva_posicion[0] <= MAX_X and MIN_Y <= nueva_posicion[1] <= MAX_Y:
                    acciones_validas.append(("moverse", nueva_posicion))
        
        if bateria_actual - COSTO_BATERIA["sobremarcha"] > 0 and (carga_actual < CAP_MAX_CARGA or posicion_rover in ZONA_SOMBRA):
            for move in POSIBLES_SOBREMARCHAS:
                nueva_posicion = (posicion_rover[0] + move[0], posicion_rover[1] + move[1])
                if MIN_X <= nueva_posicion[0] <= MAX_X and MIN_Y <= nueva_posicion[1] <= MAX_Y:
                    acciones_validas.append(("sobremarcha", nueva_posicion))
        
        presencia_muestra_en_zona_sombra = False
        for muestra in lista_muestras:
            if muestra in ZONA_SOMBRA:
                presencia_muestra_en_zona_sombra = True
                break
        
        # Si tengo batería y estoy en una muestra o tengo batería y hay una muestra en una zona sombra, entonces puedo equipar
        if bateria_actual - COSTO_BATERIA["equipar"] > 0 and (posicion_rover in lista_muestras or presencia_muestra_en_zona_sombra):
            for equip in POSIBLES_EQUIPACIONES:
                # Solo equipar si no es el activo y hay muestras del tipo que saca el taladro
                if taladro_activo != equip and CombinacionTaladroValida(equip, muestras_igneas, muestras_sedimentarias):
                    acciones_validas.append(("equipar", equip))
        

        if bateria_actual - COSTO_BATERIA["recolectar"] > 0 and carga_actual < CAP_MAX_CARGA:
            if taladro_activo == "termico" and posicion_rover in muestras_igneas:
                acciones_validas.append(("recolectar", "ignea"))
            elif taladro_activo == "percusion" and posicion_rover in muestras_sedimentarias:
                acciones_validas.append(("recolectar", "sedimentaria"))
        
        if bateria_actual - COSTO_BATERIA["depositar"] > 0:
            if carga_actual == CAP_MAX_CARGA:
                acciones_validas.append(("depositar", None))

            if carga_actual == 1 and len(muestras_igneas) == 0 and len(muestras_sedimentarias) == 0:
                acciones_validas.append(("depositar", None))

        if bateria_actual < MAX_BATERIA and posicion_rover not in ZONA_SOMBRA:
            acciones_validas.append(("recargar", None))

        return acciones_validas

    def cost(self, state1, action, state2):
        #costos_minutos
        if action[0] == "depositar":
            carga_actual = state1[3]
            return COSTO_MINUTOS[action[0]] * carga_actual

        return COSTO_MINUTOS[action[0]]
    
    def is_goal(self, state):
        carga_actual = state[3]
        muestras_igneas = state[4]
        muestras_sedimentarias = state[5]
        return carga_actual == 0 and len(muestras_igneas) == 0 and len(muestras_sedimentarias) == 0
    

    def result(self, state, action):
        #(posicionrover(X,Y), bateria int,taladroactivo string ,cargaactual int ,muestrasigneas [(X1, Y1), (X2, Y2), (Xn, Yn)], muestrassedimentarias [(X1, Y1), (X2, Y2), (Xn, Yn)])
        posicion_rover = state [0]
        bateria_actual = state [1]
        taladro_activo = state [2]
        carga_actual = state[3]
        muestras_igneas = list(state[4])
        muestras_sedimentarias = list(state[5])

        bateria_actual = bateria_actual - COSTO_BATERIA[action[0]]

        if action[0] == "moverse" or action[0] == "sobremarcha":
            posicion_rover = action[1]
        elif action[0] == "equipar":
            taladro_activo = action[1]
        elif action[0] == "recolectar":
            if action[1] == "ignea":
                muestras_igneas.remove(posicion_rover)
            else:
                muestras_sedimentarias.remove(posicion_rover)
            carga_actual +=1
        elif action[0] == "depositar":
            carga_actual = 0
        elif action[0] == "recargar":
            if bateria_actual > MAX_BATERIA:
                bateria_actual = MAX_BATERIA

        return (posicion_rover, bateria_actual, taladro_activo, carga_actual, tuple(muestras_igneas), tuple(muestras_sedimentarias))

    def heuristic(self, state):
        #(posicionrover(X,Y), bateria int,taladroactivo string ,cargaactual int ,muestrasigneas [(X1, Y1), (X2, Y2), (Xn, Yn)], muestrassedimentarias [(X1, Y1), (X2, Y2), (Xn, Yn)])
        posicion_rover = state [0]
        bateria_actual = state [1]
        taladro_activo = state [2]
        carga_actual = state[3]
        muestras_igneas = list(state[4])
        muestras_sedimentarias = list(state[5])
        #por cada muestra en el piso el costo de buscarla seria la distancia manhattan entre 2(la sobremarcha) + costo de cambiar el taladro si amerita.
        
        costo = 0
        costo_bateria = 0

        # Por equipaciones
        for equip in POSIBLES_EQUIPACIONES:
            if equip != taladro_activo and CombinacionTaladroValida(equip,muestras_igneas,muestras_sedimentarias):
                costo += COSTO_MINUTOS["equipar"]
                costo_bateria += COSTO_BATERIA["equipar"]

        # Por moverse, considerando el movimiento más rápido (2 casillas por minuto), de la manera más barata (1 unidad de energia por casilla)
        lista_muestras = muestras_igneas+muestras_sedimentarias
        lista_resultado_movimiento = DistanciaARecorrerPorEje(posicion_rover,lista_muestras)
        
        distancia = 0
        cantidad_distancias_impares = 0
        for distance in lista_resultado_movimiento:
            distancia += distance
            if distance % 2 != 0:
                cantidad_distancias_impares += 1
        
        # Se suman los impares porque es como si tuviera que hacer un movimiento completo más en vez de solo la mitad al dividir entre dos
        # No se suma los impares en el costo bateria porque no se "recorren"
        costo += (distancia + cantidad_distancias_impares) / 2 * COSTO_MINUTOS["sobremarcha"]
        costo_bateria += distancia * COSTO_BATERIA["moverse"]

        # Por recolectar
        cantidad_muestras = len(muestras_igneas) + len(muestras_sedimentarias)
        costo += cantidad_muestras * COSTO_MINUTOS["recolectar"]
        costo_bateria += cantidad_muestras * COSTO_BATERIA["recolectar"]

        # Por depositar en el suelo. Tarda 1 minuto por muestra y gasta 1 de energia por cada vez que deposita (deposita con 2 muestras o cuando tiene una y no quedan en el suelo)
        cantidad_a_depositar = cantidad_muestras + carga_actual
        costo += cantidad_a_depositar * COSTO_MINUTOS["depositar"]
        costo_bateria += (cantidad_a_depositar +1) // 2 * COSTO_BATERIA["depositar"]

        bateria_resultante = bateria_actual - costo_bateria
        while(bateria_resultante < 0):
            costo += COSTO_MINUTOS["recargar"]
            bateria_resultante -= COSTO_BATERIA["recargar"]
        
        return costo

def planear_rover(rover_inicio, bateria_inicial, zonas_sombra, muestras_igneas, muestras_sedimentarias):
    estadoInicial = (rover_inicio, bateria_inicial, "ninguno", 0, tuple(muestras_igneas), tuple(muestras_sedimentarias))
    
    global ZONA_SOMBRA, MIN_X, MAX_X, MIN_Y, MAX_Y
    ZONA_SOMBRA = set(zonas_sombra)
    lista_objetos = [rover_inicio] + list(zonas_sombra) + list(muestras_igneas) + list(muestras_sedimentarias)
    min_x, max_x,min_y,max_y = MinimosMaximosPorEje(lista_objetos)
    if(len(zonas_sombra) > 0):
        min_x -= 1
        min_y -= 1
        max_x += 1
        max_y += 1
    MIN_X = min_x
    MAX_X = max_x
    MIN_Y = min_y
    MAX_Y = max_y
    problema = RoverProblem(estadoInicial)
    resultado = astar(problema)
    return [accion for accion, estado in resultado.path()[1:]]
