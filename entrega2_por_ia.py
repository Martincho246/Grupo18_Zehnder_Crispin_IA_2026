"""
Entrega 2: Ares-1 — Diseño del campamento base
CSP formulado con SimpleAI (CspProblem + backtrack).
"""

from simpleai.search import CspProblem, backtrack


def _is_border(r, c, rows, cols):
    return r == 0 or r == rows - 1 or c == 0 or c == cols - 1


def _adjacent(r1, c1, r2, c2):
    return abs(r1 - r2) + abs(c1 - c2) == 1


def _neighbors(r, c, rows, cols):
    return [
        (r + dr, c + dc)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if 0 <= r + dr < rows and 0 <= c + dc < cols
    ]


def build_camp(camp_size, habs, generators, labs, deposits, airlocks, craters):
    rows, cols = camp_size
    craters_set = set(map(tuple, craters))

    # Caso trivial
    if habs + generators + labs + deposits + airlocks == 0:
        return []

    # ── Variables: una por módulo ────────────────────────────────────
    variables = []
    for i in range(habs):       variables.append(f"hab_{i}")
    for i in range(generators): variables.append(f"gen_{i}")
    for i in range(labs):       variables.append(f"lab_{i}")
    for i in range(deposits):   variables.append(f"dep_{i}")
    for i in range(airlocks):   variables.append(f"air_{i}")

    # ── Dominios ────────────────────────────────────────────────────
    all_free = [(r, c) for r in range(rows) for c in range(cols)
                if (r, c) not in craters_set]
    border   = [(r, c) for (r, c) in all_free if _is_border(r, c, rows, cols)]
    interior = [(r, c) for (r, c) in all_free if not _is_border(r, c, rows, cols)]

    # Poda rápida
    if airlocks > len(border):  return None
    if habs > len(interior):    return None

    domains = {}
    for v in variables:
        kind = v.split("_")[0]
        if kind == "air":
            domains[v] = list(border)
        elif kind == "hab":
            domains[v] = list(interior)
        else:
            domains[v] = list(all_free)

    # ── Restricciones ───────────────────────────────────────────────
    constraints = []

    # R1: Sin superposición — un par a la vez, sin itertools
    def no_overlap(variables, values):
        return values[0] != values[1]

    n = len(variables)
    for i in range(n):
        for j in range(i + 1, n):
            constraints.append(((variables[i], variables[j]), no_overlap))

    # R3 y R4 cubiertas por los dominios (border / interior).

    # R5: Generador no adyacente a habitacional
    def gen_not_adj_hab(variables, values):
        (gr, gc), (hr, hc) = values
        return abs(gr - hr) + abs(gc - hc) != 1

    for i in range(generators):
        for j in range(habs):
            constraints.append(((f"gen_{i}", f"hab_{j}"), gen_not_adj_hab))

    # R6: Dos generadores no adyacentes entre sí
    def gens_not_adj(variables, values):
        (r1, c1), (r2, c2) = values
        return abs(r1 - r2) + abs(c1 - c2) != 1

    for i in range(generators):
        for j in range(i + 1, generators):
            constraints.append(((f"gen_{i}", f"gen_{j}"), gens_not_adj))

    # R7: Cada laboratorio adyacente a al menos un depósito (n-aria)
    if labs > 0 and deposits > 0:
        dep_vars = tuple(f"dep_{j}" for j in range(deposits))

        def lab_adj_some_dep(variables, values):
            lr, lc = values[0]
            for dr, dc in values[1:]:
                if abs(lr - dr) + abs(lc - dc) == 1:
                    return True
            return False

        for i in range(labs):
            constraints.append(((f"lab_{i}",) + dep_vars, lab_adj_some_dep))

    # R8: Cada habitacional con al menos una celda adyacente libre (n-aria)
    if habs > 0:
        for i in range(habs):
            others = tuple(v for v in variables if v != f"hab_{i}")

            def make_evac(rows=rows, cols=cols, cs=craters_set):
                def evacuation(variables, values):
                    hr, hc = values[0]
                    occupied = set(values[1:])
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = hr + dr, hc + dc
                        if 0 <= nr < rows and 0 <= nc < cols:
                            if (nr, nc) not in occupied and (nr, nc) not in cs:
                                return True
                    return False
                return evacuation

            constraints.append(((f"hab_{i}",) + others, make_evac()))

    # ── Resolver ────────────────────────────────────────────────────
    problem = CspProblem(variables, domains, constraints)
    solution = backtrack(problem, inference=True)

    if solution is None:
        return None

    return [(var.split("_")[0], r, c) for var, (r, c) in solution.items()]