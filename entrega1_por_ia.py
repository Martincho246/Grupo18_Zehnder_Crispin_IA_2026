from functools import lru_cache

from simpleai.search import SearchProblem, astar


MAX_BATERIA = 20
MAX_CARGA = 2

ACCION_MINUTOS = {
	"moverse": 1,
	"sobremarcha": 1,
	"equipar": 3,
	"recolectar": 2,
	"depositar": 1,
	"recargar": 4,
}

ACCION_BATERIA = {
	"moverse": 1,
	"sobremarcha": 4,
	"equipar": 1,
	"recolectar": 3,
	"depositar": 1,
	"recargar": -10,
}

MOVIMIENTOS = (
	(1, 0),
	(-1, 0),
	(0, 1),
	(0, -1),
)

SOBREMARCHAS = (
	(2, 0),
	(-2, 0),
	(0, 2),
	(0, -2),
)

TIPO_POR_MUESTRA = {
	"ignea": "termico",
	"sedimentaria": "percusion",
}


def _manhattan(a, b):
	return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _ceil_half(value):
	return (value + 1) // 2


def _bounds_from_points(points, margin=2):
	rows = [p[0] for p in points]
	cols = [p[1] for p in points]
	if not rows:
		return -margin, margin, -margin, margin
	return min(rows) - margin, max(rows) + margin, min(cols) - margin, max(cols) + margin


@lru_cache(maxsize=None)
def _mst_lower_bound(points):
	if len(points) <= 1:
		return 0

	pendientes = list(points)
	visitados = {pendientes.pop()}
	costo_total = 0

	while pendientes:
		mejor_costo = None
		mejor_indice = None

		for indice, punto in enumerate(pendientes):
			costo_punto = min(_ceil_half(_manhattan(punto, otro)) for otro in visitados)
			if mejor_costo is None or costo_punto < mejor_costo:
				mejor_costo = costo_punto
				mejor_indice = indice

		costo_total += mejor_costo
		visitados.add(pendientes.pop(mejor_indice))

	return costo_total


def _distancia_a_mas_cercana(posicion, puntos):
	if not puntos:
		return 0
	return min(_manhattan(posicion, punto) for punto in puntos)


def _tipos_pendientes(muestras_igneas, muestras_sedimentarias):
	tipos = set()
	if muestras_igneas:
		tipos.add("termico")
	if muestras_sedimentarias:
		tipos.add("percusion")
	return tipos


class RoverProblem(SearchProblem):
	def __init__(self, initial_state, zonas_sombra, limites):
		super().__init__(initial_state)
		self.zonas_sombra = frozenset(zonas_sombra)
		self.min_row, self.max_row, self.min_col, self.max_col = limites

	def _dentro_de_limites(self, posicion):
		row, col = posicion
		return self.min_row <= row <= self.max_row and self.min_col <= col <= self.max_col

	def actions(self, state):
		posicion, bateria, taladro, carga, muestras_igneas, muestras_sedimentarias = state
		restantes = len(muestras_igneas) + len(muestras_sedimentarias)
		acciones = []

		if carga and (carga == MAX_CARGA or restantes == 0):
			acciones.append(("depositar", None))

		if restantes and carga < MAX_CARGA:
			if posicion in muestras_igneas and taladro == "termico":
				acciones.append(("recolectar", "ignea"))
			if posicion in muestras_sedimentarias and taladro == "percusion":
				acciones.append(("recolectar", "sedimentaria"))

		if bateria < MAX_BATERIA and posicion not in self.zonas_sombra:
			acciones.append(("recargar", None))

		tipos_necesarios = _tipos_pendientes(muestras_igneas, muestras_sedimentarias)
		if bateria > 1:
			if "termico" in tipos_necesarios and taladro != "termico":
				acciones.append(("equipar", "termico"))
			if "percusion" in tipos_necesarios and taladro != "percusion":
				acciones.append(("equipar", "percusion"))

		if restantes and carga < MAX_CARGA:
			candidatos_movimiento = []
			for delta in MOVIMIENTOS:
				destino = (posicion[0] + delta[0], posicion[1] + delta[1])
				if bateria > 1 and self._dentro_de_limites(destino):
					candidatos_movimiento.append(("moverse", destino))

			for delta in SOBREMARCHAS:
				destino = (posicion[0] + delta[0], posicion[1] + delta[1])
				if bateria > 4 and self._dentro_de_limites(destino):
					candidatos_movimiento.append(("sobremarcha", destino))

			destinos = set(muestras_igneas) | set(muestras_sedimentarias)
			candidatos_movimiento.sort(
				key=lambda accion: (
					_distancia_a_mas_cercana(accion[1], destinos),
					0 if accion[0] == "sobremarcha" else 1,
				)
			)
			acciones.extend(candidatos_movimiento)

		return acciones

	def cost(self, state1, action, state2):
		if action[0] == "depositar":
			return ACCION_MINUTOS["depositar"] * state1[3]
		return ACCION_MINUTOS[action[0]]

	def result(self, state, action):
		posicion, bateria, taladro, carga, muestras_igneas, muestras_sedimentarias = state
		muestras_igneas = list(muestras_igneas)
		muestras_sedimentarias = list(muestras_sedimentarias)

		tipo_accion, parametro = action
		if tipo_accion == "moverse" or tipo_accion == "sobremarcha":
			posicion = parametro
			bateria -= ACCION_BATERIA[tipo_accion]
		elif tipo_accion == "equipar":
			taladro = parametro
			bateria -= ACCION_BATERIA[tipo_accion]
		elif tipo_accion == "recolectar":
			if parametro == "ignea":
				muestras_igneas.remove(posicion)
			else:
				muestras_sedimentarias.remove(posicion)
			carga += 1
			bateria -= ACCION_BATERIA[tipo_accion]
		elif tipo_accion == "depositar":
			carga = 0
			bateria -= ACCION_BATERIA[tipo_accion]
		elif tipo_accion == "recargar":
			bateria = min(MAX_BATERIA, bateria - ACCION_BATERIA[tipo_accion])

		return (
			posicion,
			bateria,
			taladro,
			carga,
			tuple(muestras_igneas),
			tuple(muestras_sedimentarias),
		)

	def is_goal(self, state):
		_, _, _, carga, muestras_igneas, muestras_sedimentarias = state
		return carga == 0 and not muestras_igneas and not muestras_sedimentarias

	def heuristic(self, state):
		posicion, bateria, taladro, carga, muestras_igneas, muestras_sedimentarias = state
		muestras_restantes = tuple(sorted(set(muestras_igneas) | set(muestras_sedimentarias)))
		cantidad_muestras = len(muestras_igneas) + len(muestras_sedimentarias)

		if cantidad_muestras == 0:
			return carga

		costo = 0

		tipos_necesarios = _tipos_pendientes(muestras_igneas, muestras_sedimentarias)
		if taladro in tipos_necesarios:
			costo += max(0, len(tipos_necesarios) - 1) * ACCION_MINUTOS["equipar"]
		else:
			costo += len(tipos_necesarios) * ACCION_MINUTOS["equipar"]

		costo += cantidad_muestras * ACCION_MINUTOS["recolectar"]
		costo += (cantidad_muestras + carga) * ACCION_MINUTOS["depositar"]

		puntos_mst = tuple(sorted({posicion, *muestras_restantes}))
		costo += _mst_lower_bound(puntos_mst)

		return costo


def planear_rover(rover_inicio, bateria_inicial, zonas_sombra, muestras_igneas, muestras_sedimentarias):
	muestras_igneas = tuple(muestras_igneas)
	muestras_sedimentarias = tuple(muestras_sedimentarias)
	zonas_sombra = tuple(zonas_sombra)

	estado_inicial = (
		rover_inicio,
		bateria_inicial,
		"ninguno",
		0,
		muestras_igneas,
		muestras_sedimentarias,
	)

	puntos_relevantes = (rover_inicio,) + zonas_sombra + muestras_igneas + muestras_sedimentarias
	limites = _bounds_from_points(puntos_relevantes, margin=2)

	problema = RoverProblem(estado_inicial, zonas_sombra, limites)
	solucion = astar(problema, graph_search=True)

	return [accion for accion, _ in solucion.path()[1:]]
