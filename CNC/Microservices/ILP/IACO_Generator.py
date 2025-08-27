# IACO_Generator.py
# Genera planificación con IACO y exporta salida ILP-compatible a /var/ilp.txt

import json
import math
import random
from typing import Dict, List, Tuple

# ------------------------------
# 1) Algoritmo IACO (ejemplo)
# ------------------------------
def improved_aco_scheduler(
    topology: Dict,
    flows: List[int],
    link_capacities: Dict[Tuple[int,int], int],
    flow_bandwidths: Dict[int, int],
    H: float = 0.8,
    max_iter: int = 50,
    num_ants: int = 10,
):
    """
    Devuelve un diccionario con:
      - "paths":    dict {stream_id: [nodo,...]}
      - "schedule": dict {"u->v": [ {"gate":"open","start":t,"duration":d,"stream":sid}, ... ]}
    (Stub de ejemplo: sustituye por tu implementación real)
    """

    # --- Topología: aceptar dict o lista ---
    if isinstance(topology, dict):
        network_links = topology.get("Network_links") or topology.get("networkLinks")
        # Si no viene, usa por defecto una cadena lineal 3-0-1-2 como en tus logs
        if not network_links:
            network_links = [[0, 3], [0, 1], [1, 2]]
    else:
        # Si te llega como lista, úsala directamente
        network_links = topology or [[0, 3], [0, 1], [1, 2]]

    # --- Flujos: aceptar dict o lista de ids ---
    if isinstance(flows, dict):
        # si te pasan un dict, extrae los ids de flujo de las claves esperables
        if "Streams_Period" in flows:
            flow_ids = sorted(int(k) for k in flows["Streams_Period"].keys())
        elif "flows" in flows and isinstance(flows["flows"], list):
            flow_ids = sorted(int(f) for f in flows["flows"])
        else:
            # fallback: intenta convertir claves numéricas
            try:
                flow_ids = sorted(int(k) for k in flows.keys())
            except Exception:
                flow_ids = []
    else:
        # si ya te pasan lista/iterable de ids
        flow_ids = sorted(int(f) for f in flows)

    # --- Demo: ruta fija y ranuras fijas, como en tus trazas ---
    # construimos una ruta 3-0-1-2 para todos
    best_paths = {sid: [3, 0, 1, 2] for sid in flow_ids}

    # Schedule simple con offsets 0,12,24,36… y duration=12
    per_link = [(3, 0), (0, 1), (1, 2)]
    sched: Dict[str, List[Dict]] = {}
    for idx_link, (u, v) in enumerate(per_link):
        key = f"{u}->{v}"
        sched[key] = []
        offset = 12 * idx_link
        for sid in flow_ids:
            sched[key].append({
                "gate": "open",
                "start": offset,
                "duration": 12,
                "stream": sid
            })
            offset += 12
    try:
        print("============= IACO RESULTS SUMMARY =============")
        print("[IACO][SUMMARY] Paths:", json.dumps(best_paths))
        pretty_sched = {k: [{"s":e["start"], "d":e["duration"], "stream":e["stream"]} for e in v]
                        for k, v in sched.items()}
        print("[IACO][SUMMARY] Schedule:", json.dumps(pretty_sched))
        print("=============== END OF SUMMARY ==============")
    except Exception as _:
        print("[IACO][SUMMARY] Paths:", best_paths)
        print("[IACO][SUMMARY] Schedule:", sched)

    # DEVOLVER COMO DICCIONARIO (para que iaco_result["paths"] funcione)
    return {
        "paths": best_paths,
        "schedule": sched,
    }

# ----------------------------------------------
# 2) Conversión a estructura ILP-compatible
# ----------------------------------------------
def build_ilp_compatible_payload(
    best_paths: Dict[int, List[int]],
    best_schedule: Dict[str, List[Dict]],
    topology: Dict,
    streams_period: Dict[str, int],
    hyperperiod: int,
    identificator: Dict[str, str],
    links_interfaces: Dict[str, List[str]],
    frames_per_stream: List[List[int]],
    num_of_frames: List[int],
    repetitions_descriptor: List[List[int]],
    deathline_stream: Dict[str, int],
) -> Dict:
    """
    Construye el dict que Southconf esperaba de ILP (según tus logs).
    """
    # Clean_offsets: lista de dicts con {'Task': "(...)", 'Start': t}
    # Derivamos de best_schedule (ordenado por enlace y por start)
    clean_offsets = []
    # Además agruparemos por enlace para luego depurar (como en tus prints)
    for link_key, entries in best_schedule.items():
        # link_key tipo "3->0"
        try:
            src_str, dst_str = link_key.split("->")
            src = int(src_str); dst = int(dst_str)
        except Exception:
            # si el formato fuera distinto, intenta parsear de otra forma
            continue

        # Para cada entrada de la lista
        for e in sorted(entries, key=lambda x: x.get("start", 0)):
            # Construimos Task con el patrón que veíamos:
            # ('S', stream, 'L', link_id, 'F', frame_idx)
            # Donde link_id = 10*src + dst (esto es lo que usan tus logs)
            link_id = 10*src + dst
            stream_id = int(e.get("stream", 0))
            # En tus logs los F eran 0/1/2…; aquí asumimos un frame por stream (0)
            # o replicamos índice por orden. Para mantenerlo sencillo:
            frame_idx = 0
            task_str = f"('S', {stream_id}, 'L', {link_id}, 'F', {frame_idx})"
            clean_offsets.append({
                "Task": task_str,
                "Start": int(e.get("start", 0))
            })

    # Streams_links_paths: del best_paths sacamos los links por stream (pares consecutivos)
    streams_links_paths: List[List[List[int]]] = []
    for sid in sorted(map(int, best_paths.keys())):
        path_nodes = best_paths[sid]
        link_list = []
        for i in range(len(path_nodes)-1):
            u = path_nodes[i]; v = path_nodes[i+1]
            link_list.append([u, v])
        streams_links_paths.append(link_list)

    # Link_order_Descriptor: orden de links por stream (0,1,2 ...)
    lod = []
    for link_list in streams_links_paths:
        lod.append(list(range(len(link_list))))

    # Network_links, unused_links del topology (o vacíos)
    network_links = topology.get("Network_links", [])
    unused_links = topology.get("unused_links", [])

    # Streams_size, Num_of_Frames: si no los tienes, puedes mantener placeholders consistentes
    # con tu pipeline real. Aquí deducimos num_of_streams y ponemos tamaños de ejemplo.
    # NOTA: ya se pasan frames/num_of_frames por parámetro.

    # Construir diccionario final
    payload = {
        # Metadatos mínimos útiles para debugging/consumo
        "type": "IACO",

        # --- compat Southconf/ILP ---
        "Clean_offsets": clean_offsets,
        "Repetitions_Descriptor": repetitions_descriptor,
        "Streams_Period": streams_period,
        "Hyperperiod": hyperperiod,

        "identificator": identificator,
        "linksInterfaces": links_interfaces,

        "Network_links": network_links,
        "unused_links": unused_links,

        # cosas que Southconf imprime y usa
        "Frames_per_Stream": frames_per_stream,
        "Num_of_Frames": num_of_frames,

        # extras que también se veían en tus trazas
        "Streams_links_paths": streams_links_paths,
        "Link_order_Descriptor": lod,

        # opcionales (si tu pipeline los usa)
        "Deathline_Stream": deathline_stream,
    }

    return payload

# ---------------------------------------------------
# 3) Punto de entrada: correr IACO y escribir /var/ilp.txt
# ---------------------------------------------------
def run_and_export():
    # ============
    # TODO: Sustituye con lo real de tu pipeline
    # ============
    # Topología mínima (según tus trazas):
    topology = {
        "Network_links": [[0,3], [0,1], [1,2]],
        "unused_links": []
    }
    # Flujos presentes (IDs 0 y 1 como en tus logs)
    flows = [0, 1]

    # Capacidad y BW (si tu IACO real lo usa)
    link_capacities = {(3,0): 1000, (0,1): 1000, (1,2): 1000}
    flow_bandwidths = {0: 256, 1: 1400}

    # Identificadores (según logs):
    identificator = {
        "0": "192.168.2.66",
        "1": "192.168.2.67",
        "2": "192.168.4.53",
        "3": "192.168.4.50",
    }

    # Interfaces por linkID (como en tus logs):
    # link_id = 10*src + dst  => 3->0 => 30 (en tus logs aparecía '3', '1', '12'
    # NOTA: en tus trazas el ID que imprimís es 3, 1, 12 (no 30, 01, 12).
    # Para mantener ese convenio, usamos los mismos strings:
    links_interfaces = {
        "3":  ["PORT_0", "PORT_1"],  # (0,3) en tus prints aparecía como 3
        "1":  ["PORT_1", "PORT_1"],  # (0,1)
        "12": ["PORT_0", "PORT_0"],  # (1,2)
    }

    # Periodos / Hyperperiod (como en tus logs):
    streams_period = {"0": 10000, "1": 5000}
    hyperperiod = 10000

    # Frames por stream y número de frames (como en logs):
    frames_per_stream = [[1], [1]]
    num_of_frames = [1, 1]

    # Repetitions descriptor (logs):
    repetitions_descriptor = [[0,0], [0,1]]

    # Deathline (logs):
    deathline_stream = {"0": 10000, "1": 10000}

    # 1) Ejecutar IACO
    best_paths, best_schedule = improved_aco_scheduler(
        topology, flows, link_capacities, flow_bandwidths
    )

    # 2) (Opcional) Guardar el resultado “corto” de IACO (compat hacia atrás)
    aco_result = {
        "paths": best_paths,
        "schedule": best_schedule,
    }
    try:
        with open("/var/aco_results.json", "w") as f:
            json.dump(aco_result, f, indent=2)
    except Exception:
        pass

    # 3) Convertir a formato ILP-compatible (lo que Southconf espera)
    payload = build_ilp_compatible_payload(
        best_paths=best_paths,
        best_schedule=best_schedule,
        topology=topology,
        streams_period=streams_period,
        hyperperiod=hyperperiod,
        identificator=identificator,
        links_interfaces=links_interfaces,
        frames_per_stream=frames_per_stream,
        num_of_frames=num_of_frames,
        repetitions_descriptor=repetitions_descriptor,
        deathline_stream=deathline_stream,
    )

    # 4) Escribir /var/ilp.txt
    with open("/var/ilp.txt", "w") as f:
        json.dump(payload, f, indent=2)

    print("[IACO] Exportado formato ILP a /var/ilp.txt")

if __name__ == "__main__":
    run_and_export()
