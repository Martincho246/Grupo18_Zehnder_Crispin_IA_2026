from simpleai.search import (
    CspProblem,
    backtrack
)
ADYACENCIAS = (
    (0,1),
    (0,-1),
    (1,0),
    (-1,0)
)










def build_camp(camp_size, habs, generators, labs, deposits, airlocks, craters):

    constraints = []
    variables = []
    for i in range (habs):
        variables.append("hab" + str(i + 1))
    for i in range (generators):
        variables.append("gen" + str(i + 1))
    for i in range (labs):
        variables.append("lab" + str(i + 1))
    for i in range (deposits):
        variables.append("dep" + str(i + 1))
    for i in range (airlocks):
        variables.append("air" + str(i + 1))

    filas = camp_size[0]
    columnas = camp_size[1]
    posibles_celdas = [(x, y) for x in range(filas) for y in range(columnas) if (x, y) not in craters]

    domains = {}
    for var in variables:
        domains[var] = posibles_celdas

    def DosModulosSinSuperposicion(var, values):
        return values[0] != values[1]

    def EsclusasBordes(var, values):
        posicion_esclusa = values[0]
        if posicion_esclusa[0] == 0 or posicion_esclusa[0] == filas - 1:
            return True
        if posicion_esclusa[1] == 0 or posicion_esclusa[1] == columnas - 1:
            return True
        return False
    
    def HabitacionInterior(var, values):
        posicion_habitacion = values[0]
        if posicion_habitacion[0] == 0 or posicion_habitacion[0] == filas - 1:
            return False
        if posicion_habitacion[1] == 0 or posicion_habitacion[1] == columnas - 1:
            return False
        return True
    
    def SeguridadEnergeticaYAislamientoGenerador(var, values):
        #el primer valor representa la habitacion y el segundo el generador
        posicion_habitacion = values[0]
        posicion_generador = values[1]
        for adyasencia in ADYACENCIAS:
            celda_adyacente = (posicion_habitacion[0] + adyasencia[0], posicion_habitacion[1] + adyasencia[1]) 
            if posicion_generador == celda_adyacente:
                return False
        return True
    
    def CadenaSuministro(var, values):
        # el primer valor representa al laboratorio, el resto a los depositos
        posicion_lab = values[0]
        posiciones_depositos = values[1:]
        # por cada celda ayacente al laboratorio, pregunta si hay algun deposito ahí, retornando true si hay al menos uno
        for adyasencia in ADYACENCIAS:
            celda_adyacente = (posicion_lab[0] + adyasencia[0], posicion_lab[1] + adyasencia[1]) 
            if celda_adyacente in posiciones_depositos:
                return True
        return False
    
    def RutaEvacuacion(var, values):
        posicion_habitacion = values[0]
        demas_posiciones = set(values[1:])
        for adyacencia in ADYACENCIAS:
            celda_adyacente = (posicion_habitacion[0] + adyacencia[0], posicion_habitacion[1] + adyacencia[1])
            if celda_adyacente not in demas_posiciones and celda_adyacente not in craters:
                return True
        return False

    for i in range(len(variables)):
        if "hab" in variables[i]:
            # Regla 4
            constraints.append(((variables[i], ), HabitacionInterior))
            # Se quitan los generadores debido a que por la regla 5, no pueden estar adyacentes a un modulo habitacional
            variables_sin_generadores = [var for var in variables if var != variables[i] and "gen" not in var]
            # Regla 8
            constraints.append(((variables[i], *(var for var in variables_sin_generadores)),RutaEvacuacion))
            for j in range(len(variables)):
                if i == j:
                    continue
                if "gen" in variables[j]:
                    # Regla 5
                    constraints.append(((variables[i], variables[j]), SeguridadEnergeticaYAislamientoGenerador))
        if "gen" in variables[i]:
            # Se evita la duplicación de reglas, comenzando en el siguiente elemento del que se está actualmente
            # Generando solo las reglas (gen1, gen2), (gen1, gen3) y (gen2, gen3)
            for j in range(i+1, len(variables), 1):
                if "gen" in variables[j]:
                    # Regla 6
                    constraints.append(((variables[i], variables[j]), SeguridadEnergeticaYAislamientoGenerador))
        if "air" in variables[i]:
            # Regla 3
            constraints.append(((variables[i], ), EsclusasBordes))

        if "lab" in variables[i]:
            depositos = [var for var in variables if "dep" in var]
            tupla_variables = (variables[i], *depositos)
            # Regla 7
            constraints.append((tupla_variables,CadenaSuministro))
            
    for i in range(len(variables)):
        # Se evita que se coloque la misma variable en la regla, y se evita la duplicación de contraints por considerar A,B y B,A
        for j in range(i+1, len(variables), 1):
            # Regla 1
            constraints.append(((variables[i], variables[j]), DosModulosSinSuperposicion))
    
    
    problem = CspProblem(variables, domains,constraints)
    solution = backtrack(problem)
    if solution is None:
        return None
    resultado = []
    for var, pos in solution.items():
        tipo = var[:3]
        resultado.append((tipo, pos[0], pos[1]))
    return resultado