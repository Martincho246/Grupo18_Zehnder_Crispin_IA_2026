ADYASENCIA = (
    (0,1),
    (0,-1),
    (1,0),
    (-1,0)
)

VARIABLES = []









def build_camp(camp_size, habs, generators, labs, deposits, airlocks, craters):
    global VARIABLES

    constraints = []

    for i in range (habs):
        VARIABLES.append("hab" + str(i + 1))
    for i in range (generators):
        VARIABLES.append("gen" + str(i + 1))
    for i in range (labs):
        VARIABLES.append("lab" + str(i + 1))
    for i in range (deposits):
        VARIABLES.append("dep" + str(i + 1))
    for i in range (airlocks):
        VARIABLES.append("air" + str(i + 1))

    filas = camp_size[0]
    columnas = camp_size[1]
    posibles_celdas = ((x, y) for x in range(filas) for y in range(columnas) 
                       if (x, y) not in craters)

    domains = {}
    for var in VARIABLES:
        domains[var] = posibles_celdas

    def DosModulosSinSuperposicion(var, values):
        return values[0] != values[1]

    def EsclusasBordes(var, values):
        if values[0] == 0 or values[0] == filas:
            if values[1] == 0 or values[1] == columnas:
                return True
        return False
    
    def HabitacionInterior(var, values):
        if values[0] == 0 or values[0] == filas:
            return False
        if values[1] == 0 or values[1] == columnas:
            return False
        return True
    
    def SeguridadEnergeticaYAislamientoGenerador(var, values):
        #el primer conjunjto de valor representa la habitacion y el segundo el generador
        for adyasencia in ADYASENCIA:
            nueva_posicion = (values[0] + adyasencia[0], values[1] + adyasencia[1]) 
            if values[1] == nueva_posicion:
                return False
        return True
    
    def CadenaSuministro(var, values):
        for adyasencia in ADYASENCIA:
            nueva_posicion = (values[0] + adyasencia[0], values[1] + adyasencia[1]) 
            if values[1] == nueva_posicion:
                return True
        return False
    
    for i in range(len(VARIABLES)):
        if "hab" in VARIABLES[i]:
            constraints.append((VARIABLES[i], ), HabitacionInterior)
            for j in range(len(VARIABLES)):
                if i == j:
                    continue
                if "gen" in VARIABLES[j]:
                    constraints.append((VARIABLES[i], VARIABLES[j]), SeguridadEnergeticaYAislamientoGenerador)
        if "gen" in VARIABLES[i]:
            for j in range(len(VARIABLES)):
                if i == j:
                    continue
                if "gen" in VARIABLES[j]:
                    constraints.append((VARIABLES[i], VARIABLES[j]), SeguridadEnergeticaYAislamientoGenerador)
        if "air" in VARIABLES[i]:
            constraints.append((VARIABLES[i], ), EsclusasBordes)

        if "lab" in VARIABLES[i]:
            return False

    for i in range(len(VARIABLES)):
        for j in range(len(VARIABLES)):
            if i == j:
                continue
            constraints.append((VARIABLES[i], VARIABLES[j]), DosModulosSinSuperposicion)