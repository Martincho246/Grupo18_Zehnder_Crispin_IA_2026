from simpleai.search.models import SearchProblem

Max_Bateria = 20

Zona_Sombra = []

CapMax_Carga = 2

Costo_Bateria = {"moverse": 1, "sobremarcha": 4, "equipar": 1, "recolectar": 3, "depositar": 1, "recargar": 10}

Costo_Minutos = {"moverse": 1, "sobremarcha": 1, "equipar": 3, "recolectar": 2, "depositar": 1, "recargar": 4}

Max_Y = 3
Max_X = 3

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
            "percusión"
        )

        for move in posibles_movimientos:
            nueva_posicion = (posicion_rover[0] + move[0], posicion_rover[1] + move[1])

            if nueva_posicion[0] <= Max_X and nueva_posicion[1] <= Max_Y and bateria_actual - Costo_Bateria["moverse"] > 0 and nueva_posicion[0] >= 0 and nueva_posicion[1] >=0:
                acciones_validas.append(("moverse", nueva_posicion))
        
        for move in posibles_sobremarchas:
            nueva_posicion = (posicion_rover[0] + move[0], posicion_rover[1] + move[1])

            if nueva_posicion[0] <= Max_X and nueva_posicion[1] <= Max_Y and bateria_actual - Costo_Bateria["sobremarcha"] > 0 and nueva_posicion[0] >= 0 and nueva_posicion[1] >=0:
                acciones_validas.append(("sobremarcha", nueva_posicion))
        
        for equip in posibles_equipasiones:
            if taladro_activo != equip and bateria_actual - Costo_Bateria["equipar"] > 0:
                acciones_validas.append(("equipar", equip))
        
        if taladro_activo == "termico":
            if posicion_rover in muestras_igneas and carga_actual < CapMax_Carga and bateria_actual - Costo_Bateria["recolectar"] > 0:
                acciones_validas.append(("recolectar", "ignea"))
        elif taladro_activo == "percusión":
            if posicion_rover in muestras_sedimentarias and carga_actual < CapMax_Carga and bateria_actual - Costo_Bateria["recolectar"] > 0:
                acciones_validas.append(("recolectar", "sedimentaria"))
        
        if carga_actual == CapMax_Carga and bateria_actual - Costo_Bateria["recolectar"] > 0:
            acciones_validas.append(("entregar", None))

        if carga_actual == 1 and len(muestras_igneas) == 0 and len(muestras_sedimentarias) == 0:
            acciones_validas.append(("entregar", None))

        if posicion_rover not in Zona_Sombra:
            acciones_validas.append(("recargar", None))

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
        muestras_igneas = state[4]
        muestras_sedimentarias = state[5]

        if action[0] == "moverse" or action[0] == "sobremarcha":
            posicion_rover = action[1]
            bateria_actual = bateria_actual - Costo_Bateria[action[0]]
        elif action[0] == "equipar":
            taladro_activo = action[1]
            bateria_actual = bateria_actual - Costo_Bateria[action[0]]
        elif action[0] == "recolectar":
            if action[1] == "ignea":
                muestras_igneas = muestras_igneas.remove(posicion_rover)
            else:
                muestras_sedimentarias = muestras_sedimentarias.remove(posicion_rover)
        elif action[0] == "depositar":
            carga_actual = 0
            bateria_actual = bateria_actual - Costo_Bateria[action[0]]
        elif action[0] == "recargar":
            bateria_actual = bateria_actual + Costo_Bateria[action[0]]

        return tuple(posicion_rover, bateria_actual, taladro_activo, carga_actual, muestras_igneas, muestras_sedimentarias)

    def heuristic(self, state):
        #(posicionrover(X,Y), bateria int,taladroactivo string ,cargaactual int ,muestrasigneas [(X1, Y1), (X2, Y2), (Xn, Yn)], muestrassedimentarias [(X1, Y1), (X2, Y2), (Xn, Yn)])
        posicion_rover = state [0]
        #bateria_actual = state [1]
        taladro_activo = state [2]
        carga_actual = state[3]
        muestras_igneas = state[4]
        muestras_sedimentarias = state[5]
        #por cada muestra en el piso el costo de buscarla seria la distancia manhattan entre 2(la sobremarcha) + costo de cambiar el taladro si amerita.
        costo_unitario_max = 0
        for muestra in muestras_igneas:
            costo_muestra = 0
            if taladro_activo != "termico":
                costo_muestra += Costo_Minutos["equipar"]
            
            distance = abs(muestra[0] - posicion_rover[0]) + abs(muestra[1] - posicion_rover[1])
            costo_muestra += (distance/2) * Costo_Minutos["sobremarcha"] 
            
            if costo_muestra > costo_unitario_max:
                costo_unitario_max = costo_muestra
            
        for muestra in muestras_sedimentarias:
            costo_muestra = 0
            if taladro_activo != "percusión":
                costo_muestra += Costo_Minutos["equipar"]
            
            distance = abs(muestra[0] - posicion_rover[0]) + abs(muestra[1] - posicion_rover[1])
            costo_muestra += (distance/2) * Costo_Minutos["sobremarcha"] 
            
            if costo_muestra > costo_unitario_max:
                costo_unitario_max = costo_muestra
        
        #para todos (carga actual + cantida de muestras en el piso)/2 * costo de deposito. recolectar al menos una vez por cada cosa en el piso.
        cantidad_muestras = len(muestras_igneas) + len(muestras_sedimentarias)
        costo_global = ((carga_actual + cantidad_muestras)/2 ) * Costo_Minutos["depositar"] + cantidad_muestras * Costo_Minutos["recolectar"]

        return costo_global + costo_unitario_max
