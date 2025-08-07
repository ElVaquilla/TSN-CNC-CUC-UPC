
import random
import json
import math
import numpy as np

def improved_aco_scheduler(topology, flows, link_capacities, flow_bandwidths, H=0.8, max_iter=50, num_ants=10):
    # Parámetros del algoritmo
    alpha = 1.0
    beta = 2.0
    rho = 0.1
    Q = 1.0
    C = 1.0
    ph_max = 5.0
    ph_min = 0.01
    q0 = 0.8  # Umbral pseudoaleatorio

    nodes = set()
    for (a, b) in topology:
        nodes.update([a, b])
    nodes = list(nodes)

    # Inicializar feromonas con fórmula mejorada
    pheromone = {}
    heuristic = {}
    for edge in topology:
        u, v = edge
        count_UJ = sum(1 for n in nodes if (v, n) not in topology)
        pheromone[edge] = 1.0 / (C + count_UJ)
        heuristic[edge] = 1.0 / (link_capacities.get(edge, 1) + 1)

    best_solution = None
    best_cost = float("inf")

    for iteration in range(max_iter):
        solutions = []

        for _ in range(num_ants):
            solution = {}
            link_usage = {e: 0 for e in topology}
            valid = True

            for fid, (src, dst) in flows.items():
                path = [src]
                current = src
                visited = set([src])
                while current != dst:
                    neighbors = [v for (u, v) in topology if u == current and v not in visited]
                    if not neighbors:
                        valid = False
                        break

                    q = random.random()
                    if q <= q0:
                        next_node = max(
                            neighbors,
                            key=lambda n: pheromone.get((current, n), 0.01) * heuristic.get((current, n), 0.01) ** beta
                        )
                    else:
                        probs = []
                        total = 0.0
                        for n in neighbors:
                            tau = pheromone.get((current, n), 0.01)
                            eta = heuristic.get((current, n), 0.01)
                            p = (tau ** alpha) * (eta ** beta)
                            probs.append((n, p))
                            total += p
                        r = random.random() * total
                        s = 0.0
                        for n, p in probs:
                            s += p
                            if s >= r:
                                next_node = n
                                break

                    path.append(next_node)
                    visited.add(next_node)
                    current = next_node

                if not valid:
                    break

                solution[fid] = path
                for i in range(len(path) - 1):
                    edge = (path[i], path[i + 1])
                    link_usage[edge] += flow_bandwidths[fid]

            if not valid:
                continue

            # Cálculo del retardo autosimilar (modelo del paper)
            cost = 0.0
            for fid, path in solution.items():
                for i in range(len(path) - 1):
                    edge = (path[i], path[i + 1])
                    b = flow_bandwidths[fid]
                    c_ij = link_usage[edge] / link_capacities[edge]
                    if c_ij >= 1:
                        cost = float("inf")
                        break
                    delay = (c_ij ** (1 / (2 * (1 - H)))) / (b * (1 - c_ij) ** (H / (1 - H)))
                    cost += delay

            if cost < best_cost:
                best_cost = cost
                best_solution = solution

            solutions.append((solution, cost))

        # Evaporación
        for e in pheromone:
            pheromone[e] *= (1 - rho)
            pheromone[e] = max(ph_min, min(ph_max, pheromone[e]))

        # Refuerzo
        for sol, cost in solutions:
            if cost == float("inf"):
                continue
            for fid, path in sol.items():
                for i in range(len(path) - 1):
                    edge = (path[i], path[i + 1])
                    pheromone[edge] += Q / cost
                    pheromone[edge] = min(ph_max, pheromone[edge])

    # Generar planificación de ejemplo (slots estáticos)
    schedule = {}
    offset = 0
    for fid, path in best_solution.items():
        for i in range(len(path) - 1):
            sw = f"{path[i]}->{path[i+1]}"
            if sw not in schedule:
                schedule[sw] = []
            schedule[sw].append({
                "gate": "open",
                "start": offset,
                "duration": 10,
                "stream": fid
            })
        offset += 10

    result = {
        "paths": best_solution,
        "schedule": schedule
    }

    with open("/var/aco_results.json", "w") as f:
        json.dump(result, f, indent=4)
    return result
