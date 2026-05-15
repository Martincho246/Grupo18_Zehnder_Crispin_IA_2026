from simpleai.search.models import SearchProblem
from simpleai.search import SearchProblem, astar

Max_Bateria = 20

Zona_Sombra = []

CapMax_Carga = 2

Costo_Bateria = {"moverse": 1, "sobremarcha": 4, "equipar": 1, "recolectar": 3, "depositar": 1, "recargar": -10}

Costo_Minutos = {"moverse": 1, "sobremarcha": 1, "equipar": 3, "recolectar": 2, "depositar": 1, "recargar": 4}


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

        acciones_validas = []

        posibles_movimientos = (
            (0,1),
            (0,-1),
            (1,0),
            (-1,0)
        )
        posibles_sobremarchas = (
            (0,2),
            (0,-2),
            (2,0),
            (-2,0)
        )
        posibles_equipasiones = (
            "termico",
            "percusion"
        )

        if bateria_actual - Costo_Bateria["moverse"] > 0:
            for move in posibles_movimientos:
                nueva_posicion = (posicion_rover[0] + move[0], posicion_rover[1] + move[1])
                acciones_validas.append(("moverse", nueva_posicion))
        
        if bateria_actual - Costo_Bateria["sobremarcha"] > 0:
            for move in posibles_sobremarchas:
                nueva_posicion = (posicion_rover[0] + move[0], posicion_rover[1] + move[1])
                acciones_validas.append(("sobremarcha", nueva_posicion))
        
        for equip in posibles_equipasiones:
            if taladro_activo != equip and bateria_actual - Costo_Bateria["equipar"] > 0:
                acciones_validas.append(("equipar", equip))
        
        if taladro_activo == "termico":
            if posicion_rover in muestras_igneas and carga_actual < CapMax_Carga and bateria_actual - Costo_Bateria["recolectar"] > 0:
                acciones_validas.append(("recolectar", "ignea"))
        elif taladro_activo == "percusion":
            if posicion_rover in muestras_sedimentarias and carga_actual < CapMax_Carga and bateria_actual - Costo_Bateria["recolectar"] > 0:
                acciones_validas.append(("recolectar", "sedimentaria"))
        
        if carga_actual == CapMax_Carga and bateria_actual - Costo_Bateria["depositar"] > 0:
            acciones_validas.append(("depositar", None))

        if carga_actual == 1 and len(muestras_igneas) == 0 and len(muestras_sedimentarias) == 0 and bateria_actual - Costo_Bateria["depositar"] > 0:
            acciones_validas.append(("depositar", None))

        if posicion_rover not in Zona_Sombra:
            acciones_validas.append(("recargar", None))

        return acciones_validas

    def cost(self, state1, action, state2):
        #costos_minutos
        if action[0] == "depositar":
            carga_actual = state1[3]
            return Costo_Minutos[action[0]] * carga_actual

        return Costo_Minutos[action[0]]
    
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

        bateria_actual = bateria_actual - Costo_Bateria[action[0]]

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
            if bateria_actual > Max_Bateria:
                bateria_actual = Max_Bateria

        return (posicion_rover, bateria_actual, taladro_activo, carga_actual, tuple(muestras_igneas), tuple(muestras_sedimentarias))

    def heuristic(self, state):
        #(posicionrover(X,Y), bateria int,taladroactivo string ,cargaactual int ,muestrasigneas [(X1, Y1), (X2, Y2), (Xn, Yn)], muestrassedimentarias [(X1, Y1), (X2, Y2), (Xn, Yn)])
        posicion_rover = state [0]
        bateria_actual = state [1]
        taladro_activo = state [2]
        carga_actual = state[3]
        muestras_igneas = state[4]
        muestras_sedimentarias = state[5]
        #por cada muestra en el piso el costo de buscarla seria la distancia manhattan entre 2(la sobremarcha) + costo de cambiar el taladro si amerita.
        costo_unitario_max = 0
        costo_bateria_local = 0

        for muestra in muestras_igneas:
            costo_muestra = 0
            costo_bateria_muestra = 0
            if taladro_activo != "termico":
                costo_muestra += Costo_Minutos["equipar"]
                costo_bateria_muestra += Costo_Bateria["equipar"]
            
            distance = abs(muestra[0] - posicion_rover[0]) + abs(muestra[1] - posicion_rover[1])
            costo_muestra += (distance/2) * Costo_Minutos["sobremarcha"]
            costo_bateria_muestra += (distance) * Costo_Bateria["moverse"]
            
            if costo_muestra > costo_unitario_max:
                costo_bateria_local = costo_bateria_muestra
                costo_unitario_max = costo_muestra
            
        for muestra in muestras_sedimentarias:
            costo_muestra = 0
            costo_bateria_muestra = 0
            if taladro_activo != "percusion":
                costo_muestra += Costo_Minutos["equipar"]
                costo_bateria_muestra += Costo_Bateria["equipar"]
            
            distance = abs(muestra[0] - posicion_rover[0]) + abs(muestra[1] - posicion_rover[1])
            costo_muestra += (distance/2) * Costo_Minutos["sobremarcha"]
            costo_bateria_muestra += (distance) * Costo_Bateria["moverse"]
            
            if costo_muestra > costo_unitario_max:
                costo_bateria_local = costo_bateria_muestra
                costo_unitario_max = costo_muestra
        
        #para todos (carga actual + cantida de muestras en el piso)/2 * costo de deposito. recolectar al menos una vez por cada cosa en el piso.
        cantidad_muestras = len(muestras_igneas) + len(muestras_sedimentarias)
        costo_bateria = cantidad_muestras * Costo_Bateria["recolectar"] + ((carga_actual + cantidad_muestras)/2 ) * Costo_Bateria["depositar"]
        costo_global = (carga_actual + cantidad_muestras ) * Costo_Minutos["depositar"] + cantidad_muestras * Costo_Minutos["recolectar"]
        bateria_actual = bateria_actual - costo_bateria - costo_bateria_local

        while bateria_actual < 0:
            bateria_actual = bateria_actual - Costo_Bateria["recargar"]
            costo_global += Costo_Minutos["recargar"]
        
        return costo_global + costo_unitario_max

def planear_rover(rover_inicio, bateria_inicial, zonas_sombra, muestras_igneas, muestras_sedimentarias):
    EstadoInicial = (rover_inicio, bateria_inicial, "ninguno", 0, tuple(muestras_igneas), tuple(muestras_sedimentarias))
    
    global Zona_Sombra
    Zona_Sombra = zonas_sombra

    Problema = RoverProblem(EstadoInicial)
    Resultado = astar(Problema)
    return [accion for accion, estado in Resultado.path()[1:]]
