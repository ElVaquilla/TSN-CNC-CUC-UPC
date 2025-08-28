# IACO_Generator.py
# Genera planificación con IACO y exporta salida ILP-compatible a /var/ilp.txt
# IACO_Generator.py — Implementación realista de IACO para TSN
#
# Este módulo implementa un planificador conjunto de routing + scheduling
# basado en Improved Ant Colony Optimization (IACO) conforme al paper
# "A time-sensitive network scheduling algorithm based on improved ACO"
# (Wang et al., Alexandria Engineering Journal, 2020).
#
# Entradas principales de `improved_aco_scheduler`:
#   - topology: lista de aristas dirigidas [(u,v), ...] o dict con "Network_links"
#   - flows: dict {sid: (src, dst)} (índices de nodos)
#   - link_capacities: dict {(u,v): C_ij} (misma dirección que topology)
#   - flow_bandwidths: dict {sid: b_k}
#   - H: parámetro del modelo de tráfico autosimilar (0 < H < 1)
#   - max_iter: iteraciones IACO
#   - num_ants: hormigas por iteración
#
# Salidas de `improved_aco_scheduler`:
#   - dict con "paths": {sid: [n0, n1, ..., ndst]}
#   - dict "schedule": {"u->v": [ {"gate":"open","start":t,"duration":d,"stream":sid}, ... ]}
#     * Scheduling generado con una ranura global por flujo (mismo offset
#       en todos los enlaces de su ruta) evitando colisiones por enlace/ranura.
#
# Además se proporciona `build_ilp_compatible_payload(...)` y un `main` opcional
# que lee /var/preprocessing.txt y escribe /var/ilp.txt con el payload
# esperado por Southconf (Clean_offsets, Repetitions_Descriptor, Streams_Period,
# Hyperperiod, identificator, linksInterfaces, Network_links, unused_links, etc.).
#
# NOTAS DE COMPATIBILIDAD:
# - El Southconf reconstruye linkID = 10*src + dst por cada enlace (src,dst).
# - Clean_offsets debe contener items {"Task":"('S', sid, 'L', link_id, 'F', frame_idx)", "Start":offset}.
# - Repetitions_Descriptor se rellena con un valor por defecto si no existe.

from __future__ import annotations

import json
import math
import random
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Tuple, Iterable, Optional

# -------------------------------
# Utilidades internas
# -------------------------------

Edge = Tuple[int, int]
Path = List[int]


def _normalize_topology(topology) -> List[Edge]:
    """Acepta lista de aristas o dict con "Network_links" y devuelve lista de aristas dirigidas.
    Si llegan aristas no dirigidas, las duplicamos en ambos sentidos.
    """
    edges: List[Edge] = []
    if isinstance(topology, dict):
        base = topology.get("Network_links") or topology.get("networkLinks") or []
    else:
        base = topology or []

    seen = set()
    for e in base:
        u, v = int(e[0]), int(e[1])
        for a, b in ((u, v), (v, u)):
            if (a, b) not in seen:
                edges.append((a, b))
                seen.add((a, b))
    return edges


def _adjacency(edges: Iterable[Edge]) -> Dict[int, List[int]]:
    adj: Dict[int, List[int]] = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)
    return adj


def _all_nodes(edges: Iterable[Edge]) -> List[int]:
    s = set()
    for u, v in edges:
        s.add(u); s.add(v)
    return sorted(s)


def _shortest_hops_heuristic(adj: Dict[int, List[int]], nodes: List[int]) -> Dict[Tuple[int, int], int]:
    """Distancia mínima en saltos entre cualquier par (u,d). Útil para sesgar la heurística."""
    dist: Dict[Tuple[int, int], int] = {}
    for d in nodes:
        # BFS desde d (para obtener distancias a d)
        q: deque = deque([d])
        local = {d: 0}
        rev_adj = defaultdict(list)
        for x, nbrs in adj.items():
            for y in nbrs:
                rev_adj[y].append(x)
        while q:
            x = q.popleft()
            for p in rev_adj.get(x, []):
                if p not in local:
                    local[p] = local[x] + 1
                    q.append(p)
        for u, hops in local.items():
            dist[(u, d)] = hops
    return dist


# -------------------------------
# Núcleo IACO
# -------------------------------

@dataclass
class IACOParams:
    alpha: float = 1.0          # influencia de feromona
    beta: float = 2.0           # influencia de heurística
    rho: float = 0.25           # evaporación global
    q0: float = 0.90            # umbral de explotación (pseudo-random rule)
    tau0: float = 0.1           # feromona inicial por arista
    tau_min: float = 1e-4       # límites min/max para Min-Max ACO
    tau_max: float = 10.0
    C_boost: float = 0.5        # C de (14)(15) para boost/dampen
    base_slot: int = 12         # tamaño de ranura (us) para generar offsets
    max_search_slots: int = 4096
    seed: Optional[int] = None


@dataclass
class IACOSolution:
    paths: Dict[int, Path]
    schedule: Dict[str, List[Dict]]  # clave "u->v"
    cost: float


def _edge_delay_estimate(edge: Edge, b_k: float, load_wo_k: float, C_ij: float, H: float) -> float:
    """Estimación de retraso medio en el enlace (i,j) para el flujo k usando (10):
        φ_ij = c_ij^{1/(2(1-H))} * b_k * (1 - c_ij)^{H/(1-H)}
      con c_ij = (load + b_k)/C_ij acotado en (0,1).
    """
    if C_ij <= 0:
        return float('inf')
    c_ij = (max(0.0, load_wo_k) + max(0.0, b_k)) / float(C_ij)
    # Evitar extremos 0/1 exactos para mantener derivadas finitas
    c_ij = min(0.999999, max(1e-6, c_ij))
    try:
        term1 = c_ij ** (1.0 / (2.0 * (1.0 - H)))
        term2 = (1.0 - c_ij) ** (H / (1.0 - H))
        return term1 * b_k * term2
    except Exception:
        return float('inf')


def _construct_path_for_flow(
    sid: int,
    src: int,
    dst: int,
    adj: Dict[int, List[int]],
    tau: Dict[Edge, float],
    eta_base: Dict[Edge, float],
    dist_hops: Dict[Tuple[int, int], int],
    current_edge_load: Dict[Edge, float],
    b_k: float,
    caps: Dict[Edge, float],
    params: IACOParams,
) -> Optional[Path]:
    """Construcción de ruta para un flujo usando regla pseudo-aleatoria adaptativa (13)."""
    rng = random.random
    tabu = set([src])
    path = [src]
    u = src
    hop_limit = 2 * len(adj) if adj else 64

    for _ in range(hop_limit):
        nbrs = [v for v in adj.get(u, []) if v not in tabu]
        if not nbrs:
            # ataúd: reinicia en origen (IACO paso 6)
            return None
        # Probabilidades / explotación
        scores: List[Tuple[int, float]] = []
        best_v = None
        best_score = -1.0
        for v in nbrs:
            e = (u, v)
            # Heurística combinada: eta_base(e) / (1 + edge_delay_est)
            delay_est = _edge_delay_estimate(e, b_k, current_edge_load.get(e, 0.0), caps.get(e, 1.0), H=eta_base['H'])
            eta = 1.0 / (1e-9 + delay_est)
            # Sesgo por proximidad a destino en saltos
            hops = dist_hops.get((v, dst), 1_000_000)
            eta *= 1.0 / (1.0 + hops)
            score = (tau.get(e, params.tau0) ** params.alpha) * (eta ** params.beta)
            scores.append((v, score))
            if score > best_score:
                best_score = score; best_v = v
        q = rng()
        if q <= params.q0:
            nxt = best_v
        else:
            total = sum(s for _, s in scores) or 1.0
            r = rng() * total
            acc = 0.0
            nxt = scores[-1][0]
            for v, s in scores:
                acc += s
                if acc >= r:
                    nxt = v
                    break
        # Avanza
        path.append(nxt)
        tabu.add(nxt)
        # Si alcanzamos destino, ruta completa
        if nxt == dst:
            return path
        u = nxt
    return None


def _evaluate_cost(paths: Dict[int, Path], bws: Dict[int, float], caps: Dict[Edge, float], H: float) -> float:
    """Costo objetivo (11): suma de retrasos promedio por flujo y enlace con cargas finales."""
    # Cargas por enlace
    load: Dict[Edge, float] = defaultdict(float)
    for sid, p in paths.items():
        bk = bws[sid]
        for i in range(len(p) - 1):
            e = (p[i], p[i+1])
            load[e] += bk
    # Suma de retrasos
    total = 0.0
    for sid, p in paths.items():
        bk = bws[sid]
        for i in range(len(p) - 1):
            e = (p[i], p[i+1])
            Cij = caps.get(e, 1.0)
            total += _edge_delay_estimate(e, bk, load[e] - bk, Cij, H)
    return total


def _assign_global_offsets(paths: Dict[int, Path], base_slot: int, max_search_slots: int) -> Dict[int, int]:
    """Asigna un offset global (en µs) a cada flujo evitando colisiones por enlace/ranura.
    Greedy: para cada flujo, el primer offset libre en TODOS los enlaces de su ruta.
    """
    # Mapa por enlace -> offsets ocupados
    used: Dict[Edge, set] = defaultdict(set)
    # Orden determinista por id de flujo
    sids = sorted(paths.keys())
    offsets: Dict[int, int] = {}
    for sid in sids:
        path = paths[sid]
        # Enumerar candidatos 0, base, 2*base, ...
        placed = False
        for slot_idx in range(max_search_slots):
            t = slot_idx * base_slot
            # ¿libre en todos los enlaces?
            ok = True
            for i in range(len(path) - 1):
                e = (path[i], path[i+1])
                if t in used[e]:
                    ok = False
                    break
            if ok:
                offsets[sid] = t
                for i in range(len(path) - 1):
                    e = (path[i], path[i+1])
                    used[e].add(t)
                placed = True
                break
        if not placed:
            # Como salvaguarda, asigna al final (permitiría colisión si se diera el caso)
            t = len(used) * base_slot
            offsets[sid] = t
            for i in range(len(path) - 1):
                e = (path[i], path[i+1])
                used[e].add(t)
    return offsets


def improved_aco_scheduler(
    topology,
    flows: Dict[int, Tuple[int, int]],
    link_capacities: Dict[Edge, float],
    flow_bandwidths: Dict[int, float],
    H: float = 0.8,
    max_iter: int = 50,
    num_ants: int = 10,
    *,
    params: Optional[IACOParams] = None,
) -> Dict:
    """IACO sobre la topología y los flujos (routing + asignación de ranura global por flujo).

    Devuelve {"paths": {sid: [ruta]}, "schedule": {"u->v": [ entries ]}}
    """
    params = params or IACOParams()
    if params.seed is not None:
        random.seed(params.seed)

    edges = _normalize_topology(topology)
    adj = _adjacency(edges)
    nodes = _all_nodes(edges)

    # Capacidades por defecto
    caps: Dict[Edge, float] = {e: float(link_capacities.get(e, 1.0)) for e in edges}

    # Feromonas iniciales (mejoradas por impasables: vecinos sin capacidad)
    tau: Dict[Edge, float] = {}
    for e in edges:
        u, v = e
        impassables = 0
        for w in adj.get(u, []):
            if caps.get((u, w), 0.0) <= 0.0:
                impassables += 1
        tau[e] = max(params.tau_min, min(params.tau_max, 1.0 / (params.C_boost + impassables)))

    # Heurística base fija + H para cálculo de delay
    eta_base: Dict[Edge, float] = {e: 1.0 for e in edges}
    eta_base['H'] = H  # truco para pasar H a _construct_path_for_flow sin firmar más

    dist_hops = _shortest_hops_heuristic(adj, nodes)

    # Inicialización con Dijkstra aproximado (por si IACO no encuentra)
    def _dijkstra(src: int, dst: int) -> Optional[Path]:
        import heapq
        # cost(e) ~ 1/capacidad para empezar
        cost_e = {e: 1.0 / max(1e-9, caps.get(e, 1.0)) for e in edges}
        pq = [(0.0, src, None)]
        prev = {}
        seen_cost = {src: 0.0}
        while pq:
            c, u, p = heapq.heappop(pq)
            if u in prev:
                continue
            prev[u] = p
            if u == dst:
                break
            for v in adj.get(u, []):
                nc = c + cost_e.get((u, v), 1.0)
                if v not in seen_cost or nc < seen_cost[v]:
                    seen_cost[v] = nc
                    heapq.heappush(pq, (nc, v, u))
        if dst not in prev:
            return None
        # reconstruir
        rev = []
        x = dst
        while x is not None:
            rev.append(x)
            x = prev[x]
        return list(reversed(rev))

    # Mejor solución conocida
    best_paths: Dict[int, Path] = {}
    # arranque con Dijkstra por flujo
    for sid, (s, d) in flows.items():
        p = _dijkstra(s, d)
        if not p:
            # como mínimo, si src=dst
            p = [s, d] if s != d else [s]
        best_paths[sid] = p
    best_cost = _evaluate_cost(best_paths, flow_bandwidths, caps, H)

    # Bucle principal IACO
    for _gen in range(max_iter):
        iter_best_paths = None
        iter_best_cost = float('inf')

        for _ant in range(num_ants):
            # construcción secuencial de rutas, actualizando cargas locales
            current_paths: Dict[int, Path] = {}
            current_load: Dict[Edge, float] = defaultdict(float)
            # orden aleatorio de flujos ayuda a diversificar
            for sid in random.sample(list(flows.keys()), len(flows)):
                src, dst = flows[sid]
                bk = flow_bandwidths[sid]
                p = _construct_path_for_flow(
                    sid, src, dst, adj, tau, eta_base, dist_hops, current_load, bk, caps, params
                )
                if p is None:
                    # fallback a Dijkstra si la hormiga se estanca
                    p = _dijkstra(src, dst)
                    if p is None:
                        # no se puede rutear; penaliza con coste infinito
                        current_paths = {}
                        break
                current_paths[sid] = p
                for i in range(len(p) - 1):
                    current_load[(p[i], p[i+1])] += bk

            if not current_paths:
                continue

            c = _evaluate_cost(current_paths, flow_bandwidths, caps, H)
            if c < iter_best_cost:
                iter_best_cost = c
                iter_best_paths = current_paths

        if iter_best_paths is None:
            # nada válido en esta iteración
            continue

        # Evaporación global
        for e in tau:
            tau[e] = max(params.tau_min, (1.0 - params.rho) * tau[e])

        # Reforzamiento Min–Max (14)(15) en aristas de la mejor solución de la iteración
        # Usamos un delta inverso al coste
        delta = 1.0 / max(1e-9, iter_best_cost)
        m_edges = max(1, len(edges))
        for sid, p in iter_best_paths.items():
            for i in range(len(p) - 1):
                e = (p[i], p[i+1])
                # Boost/dampen según el nivel actual
                if tau[e] > params.tau_max * 0.8:
                    factor = math.sqrt((m_edges + params.C_boost) / m_edges)
                else:
                    factor = math.sqrt((m_edges - params.C_boost) / m_edges) if m_edges > params.C_boost else 1.0
                tau[e] = max(params.tau_min, min(params.tau_max, factor * tau[e] + delta))

        # Actualiza mejor global
        if iter_best_cost < best_cost:
            best_cost = iter_best_cost
            best_paths = iter_best_paths

    # Asignación de una ranura global por flujo evitando colisiones por enlace
    offsets = _assign_global_offsets(best_paths, params.base_slot, params.max_search_slots)

    # Generar schedule por enlace
    schedule: Dict[str, List[Dict]] = defaultdict(list)
    for sid, p in best_paths.items():
        off = int(offsets[sid])
        for i in range(len(p) - 1):
            u, v = p[i], p[i+1]
            key = f"{u}->{v}"
            schedule[key].append({
                "gate": "open",
                "start": off,
                "duration": params.base_slot,  # duración homogénea
                "stream": sid,
            })

    # Ordenar por inicio para estabilidad
    for key in schedule:
        schedule[key].sort(key=lambda e: (e["start"], e["stream"]))

    return {"paths": best_paths, "schedule": schedule}


# ----------------------------------------------
# Construcción del payload compatible con Southconf
# ----------------------------------------------

def build_ilp_compatible_payload(
    best_paths: Dict[int, Path],
    best_schedule: Dict[str, List[Dict]],
    topology,
    streams_period: Dict[str, int],
    hyperperiod: int,
    identificator: Dict[str, str],
    links_interfaces: Dict[str, List[str]],
    frames_per_stream: List[List[int]],
    num_of_frames: List[int],
    repetitions_descriptor: Optional[List[List[int]]],
    deathline_stream: Dict[str, int],
) -> Dict:
    # Clean_offsets a partir del schedule. LinkID = 10*src + dst (compatibilidad Southconf)
    clean_offsets = []
    for link_key, entries in best_schedule.items():
        try:
            src_str, dst_str = link_key.split("->")
            src = int(src_str); dst = int(dst_str)
        except Exception:
            continue
        link_id = 10 * src + dst
        for idx, e in enumerate(entries):
            sid = int(e.get("stream", 0))
            task_str = f"('S', {sid}, 'L', {link_id}, 'F', {idx})"
            clean_offsets.append({"Task": task_str, "Start": int(e.get("start", 0))})

    # Streams_links_paths: pares [u,v] por flujo
    streams_links_paths: List[List[List[int]]] = []
    for sid in sorted(best_paths.keys()):
        nodes = best_paths[sid]
        links = [[nodes[i], nodes[i+1]] for i in range(len(nodes)-1)]
        streams_links_paths.append(links)

    # Orden de links por flujo (0..n-1)
    lod = [list(range(len(links))) for links in streams_links_paths]

    # Topología base
    if isinstance(topology, dict):
        network_links = topology.get("Network_links", [])
        unused_links = topology.get("unused_links", [])
    else:
        network_links = _normalize_topology(topology)
        # colapsa a no dirigidos para compatibilidad si fuera necesario
        uniq = set()
        und = []
        for u, v in network_links:
            a, b = min(u, v), max(u, v)
            if (a, b) not in uniq:
                uniq.add((a, b)); und.append([a, b])
        network_links = und
        unused_links = []

    # Repetitions_Descriptor dummy si no existe
    if not repetitions_descriptor:
        # Por compatibilidad simple: una sola repetición (0) por flujo
        repetitions_descriptor = [[0] for _ in streams_links_paths]

    payload = {
        "type": "IACO",
        "Clean_offsets": clean_offsets,
        "Repetitions_Descriptor": repetitions_descriptor,
        "Streams_Period": streams_period,
        "Hyperperiod": hyperperiod,
        "identificator": identificator,
        "linksInterfaces": links_interfaces,
        "Network_links": network_links,
        "unused_links": unused_links,
        "Frames_per_Stream": frames_per_stream,
        "Num_of_Frames": num_of_frames,
        "Streams_links_paths": streams_links_paths,
        "Link_order_Descriptor": lod,
        "Deathline_Stream": deathline_stream,
    }
    return payload


# ----------------------------------------------
# Ejecutable: lee /var/preprocessing.txt y escribe /var/ilp.txt
# ----------------------------------------------

PREPROC_PATH = "/var/preprocessing.txt"
ILP_OUT_PATH = "/var/ilp.txt"


def _keys_to_int(d):
    if isinstance(d, dict):
        out = {}
        for k, v in d.items():
            try:
                out[int(k)] = v
            except Exception:
                out[k] = v
        return out
    return d


def run_and_export_from_preprocessing():
    with open(PREPROC_PATH, "r") as f:
        pre = json.load(f)

    # -------- Entradas mínimas --------
    streams_period = _keys_to_int(pre.get("Streams_Period", {}))
    hyperperiod = int(pre.get("Hyperperiod", 1000))

    # BW por flujo: tamaño/periodo si está disponible
    sizes = pre.get("Streams_size") or pre.get("Streams_Size") or {}
    sizes = _keys_to_int(sizes)
    flow_bandwidths = {sid: float(sizes.get(sid, 1.0)) / max(1.0, float(streams_period.get(sid, 1))) for sid in sizes}

    # Topología dirigida
    base_edges = [tuple(e) for e in pre.get("Network_links", [])]
    topology = {"Network_links": base_edges, "unused_links": pre.get("unused_links", [])}

    # Capacidades por enlace (si no llegan, 1.0)
    CAP_DEF = 1.0
    link_capacities = {}
    for u, v in _normalize_topology(topology):
        link_capacities[(u, v)] = float(pre.get("link_capacities", {}).get(f"{u}->{v}", CAP_DEF)) if isinstance(pre.get("link_capacities"), dict) else CAP_DEF

    # Flujos (src,dst)
    flows: Dict[int, Tuple[int, int]] = {}
    ssd = pre.get("Stream_Source_Destination") or []
    ident = pre.get("identificator", {})
    ip2idx = {ip: int(idx) for idx, ip in ident.items()} if ident else {}
    for sid, pair in enumerate(ssd):
        try:
            a, b = pair
            if isinstance(a, str) and a.count('.') and a in ip2idx:
                src, dst = ip2idx[a], ip2idx[b]
            else:
                src, dst = int(a), int(b)
        except Exception:
            continue
        flows[int(sid)] = (src, dst)

    # Valores necesarios para payload final
    identificator = pre.get("identificator", {})
    links_interfaces = pre.get("linksInterfaces", {})
    frames_per_stream = pre.get("Frames_per_Stream", [])
    num_of_frames = pre.get("Num_of_Frames", [])
    repetitions_descriptor = pre.get("Repetitions_Descriptor")
    deathline_stream = pre.get("Deathline_Stream", {})

    # -------- Ejecutar IACO --------
    iaco = improved_aco_scheduler(
        topology=topology,
        flows=flows,
        link_capacities=link_capacities,
        flow_bandwidths=flow_bandwidths,
        H=float(pre.get("H", 0.8)),
        max_iter=int(pre.get("max_iter", 50)),
        num_ants=int(pre.get("num_ants", 10)),
    )

    payload = build_ilp_compatible_payload(
        best_paths=iaco["paths"],
        best_schedule=iaco["schedule"],
        topology=topology,
        streams_period={str(k): int(v) for k, v in streams_period.items()},
        hyperperiod=int(hyperperiod),
        identificator=identificator,
        links_interfaces=links_interfaces,
        frames_per_stream=frames_per_stream,
        num_of_frames=num_of_frames,
        repetitions_descriptor=repetitions_descriptor,
        deathline_stream=deathline_stream,
    )

    with open(ILP_OUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    return payload


if __name__ == "__main__":
    try:
        out = run_and_export_from_preprocessing()
        print("[IACO] Payload exportado en", ILP_OUT_PATH)
        print(json.dumps({k: out[k] for k in ["type", "Hyperperiod", "Clean_offsets"]}, indent=2)[:2000])
    except Exception as e:
        print("[IACO][ERROR]", e)
