from ILP_Generator import *
from IACO_Generator import * # Importamos el algoritmo IACO
from Solutions_Visualizer import *
from time import time
import os
import json
import sys
import traceback
from typing import Dict, List, Tuple
from Rabbitmq_queues import *


'''
this is the list of input elements:


'Number_of_Streams',
'Network_links', 
'Link_order_Descriptor', 
'Streams_Period', 
'Hyperperiod', 
'Frames_per_Stream', 
'Max_frames', 
'Num_of_Frames', 
'Model_Descriptor', 
'Model_Descriptor_vector', 
'Deathline_Stream', 
'Repetitions', 
'Repetitions_Descriptor', 
'Frame_Duration', 
'unused_links'
'''

# === Dependencias internas del proyecto ===
# Asegúrate de que este import coincide con tu estructura real


PREPROC_PATH = "/var/preprocessing.txt"
OUT_DEBUG_JSON = "/var/ilp_payload.json"


def _keys_to_int(d):
    """Convierte las claves de un dict a int cuando es posible (robustez frente a JSON)."""
    if isinstance(d, dict):
        out = {}
        for k, v in d.items():
            try:
                out[int(k)] = v
            except (ValueError, TypeError):
                out[k] = v
        return out
    return d


def _pair_is_ip(p):
    """Devuelve True si p es una pareja [src, dst] de strings con pinta de IP."""
    try:
        a, b = p
        return isinstance(a, str) and isinstance(b, str) and "." in a and "." in b
    except Exception:
        return False


def _to_bidirected_edges(base_edges: List[List[int]]) -> List[Tuple[int, int]]:
    """Dada una lista de aristas [u,v] (no necesariamente dirigidas), crea ambas direcciones."""
    topology = []
    seen = set()
    for (u, v) in base_edges:
        u, v = int(u), int(v)
        for a, b in ((u, v), (v, u)):
            if (a, b) not in seen:
                topology.append((a, b))
                seen.add((a, b))
    return topology


def _flows_from_sources(pre: dict) -> Dict[int, Tuple[int, int]]:
    """
    Construye {sid: (src, dst)} a partir de Stream_Source_Destination.
    Admite que vengan como IPs o ya como índices de nodo.
    """
    ssd = pre["Stream_Source_Destination"]  # puede venir [[ip,ip], ...] o [[idx,idx], ...]
    ident = pre.get("identificator", {})    # {'0': '192.168.2.66', ...}
    # Mapa inverso IP -> idx si es posible
    ip_to_idx = None
    if ident:
        try:
            idx_to_ip = {int(k): v for k, v in ident.items()}
            ip_to_idx = {v: k for k, v in idx_to_ip.items()}
        except Exception:
            ip_to_idx = None

    flows = {}
    for sid, pair in enumerate(ssd):
        if _pair_is_ip(pair) and ip_to_idx:
            src = ip_to_idx[pair[0]]
            dst = ip_to_idx[pair[1]]
        else:
            # Asumimos que ya vienen como índices
            src = int(pair[0])
            dst = int(pair[1])
        flows[sid] = (src, dst)
    return flows


def main():
    try:
        # ================== CARGA DE PREPROCESADO ==================
        with open(PREPROC_PATH, "r") as f:
            Preprocessed_data = json.load(f)

        # ------------- Normalización robusta de claves por sid -------------
        Streams_Period = _keys_to_int(Preprocessed_data["Streams_Period"])
        Deathline_Stream = _keys_to_int(Preprocessed_data["Deathline_Stream"])

        Streams_size = Preprocessed_data["Streams_size"]
        if isinstance(Streams_size, dict):
            Streams_size = _keys_to_int(Streams_size)

        N = int(Preprocessed_data["Number_of_Streams"])
        assert len(Streams_size) == N, "Streams_size no coincide con Number_of_Streams"

        # ------------- Bandwidth por flujo (b_k) -------------
        flow_bandwidths = {
            sid: float(Streams_size[sid]) / float(Streams_Period[sid])
            for sid in range(N)
        }

        # ------------- Topología dirigida en ambos sentidos -------------
        base_edges = [tuple(e) for e in Preprocessed_data["Network_links"]]
        topology = _to_bidirected_edges(base_edges)

        # ------------- Capacidades por enlace y sentido -------------
        # Ajusta CAP_DEFAULT a lo que uses (Mb/s, frames/slot, etc.)
        CAP_DEFAULT = 1.0
        link_capacities = {e: CAP_DEFAULT for e in topology}

        # ------------- Flujos (src,dst) en índices de nodo -------------
        flows = _flows_from_sources(Preprocessed_data)

        # ------------- slot_duration desde Frame_Duration (si existe) -------------
        slot_duration = 10
        FD = Preprocessed_data.get("Frame_Duration", {})
        if isinstance(FD, dict) and FD:
            try:
                # si hay varias entradas, tomamos la primera como tamaño de slot
                slot_duration = int(next(iter(FD.values())))
            except Exception:
                pass

        print("Running IACO...")

        # ================== EJECUCIÓN DEL IACO ==================
        iaco_result = improved_aco_scheduler(
            topology=topology,
            flows=flows,
            link_capacities=link_capacities,
            flow_bandwidths=flow_bandwidths,
            H=0.8,
            max_iter=50,
            num_ants=10,
        )

        # ================== CONSTRUIR Clean_offsets (formato LEGACY para southconf) ==================
        # Mapeo (u,v) -> link_id conservando el orden de Network_links y linksInterfaces
        edge_list = [tuple(e) for e in Preprocessed_data["Network_links"]]  # p.ej. [(0,3),(0,1),(1,2)]
        link_ids_ordered = list(Preprocessed_data["linksInterfaces"].keys())  # p.ej. ['3','1','12'] en MISMO orden

        edge_to_linkid = {}
        for idx, (u, v) in enumerate(edge_list):
            if idx < len(link_ids_ordered):
                lid = int(link_ids_ordered[idx])
                # asigna el id al enlace en ambos sentidos:
                edge_to_linkid[(u, v)] = lid
                edge_to_linkid[(v, u)] = lid

        # Si tus 'start' del scheduler están en "slots" y 1 slot = slot_duration (µs),
        # puedes escalar así. Si ya están en µs, deja start_scale = 1.
        start_scale = 1  # o: start_scale = slot_duration

        Clean_offsets_legacy = []
        for fid in range(N):
            path = iaco_result["paths"][fid]
            for hop in range(len(path) - 1):
                u, v = path[hop], path[hop + 1]
                key = f"{u}->{v}"
                # busca el slot asignado a este flujo en ese enlace
                start_slot = next(
                    ev["start"] for ev in iaco_result["schedule"][key] if ev["stream"] == fid
                )
                link_id = edge_to_linkid.get((u, v))  # ahora NUNCA será None (tenemos (u,v) y (v,u))
                if link_id is None:
                    # blindaje extra por si faltase algo raro
                    raise RuntimeError(f"No link_id mapping for edge {(u, v)}")

                # Formato EXACTO para TAS_configurator:
                # "('S', <sid>, 'L', <link_id>, 'F', <frame_idx>)" y clave 'Start'
                Clean_offsets_legacy.append({
                    "Task": f"('S', {fid}, 'L', {link_id}, 'F', {hop})",
                    "Start": int(start_scale * start_slot)
                })

        # ordena para estabilidad (opcional)
        Clean_offsets_legacy.sort(key=lambda x: (x["Task"], x["Start"]))

        # ================== Repetitions_Descriptor (dummy si no existe) ==================
        Repetitions_Descriptor = Preprocessed_data.get("Repetitions_Descriptor")
        if Repetitions_Descriptor is None:
            # Dummy mínimo viable: para cada flujo, una única repetición [sid, 0]
            Repetitions_Descriptor = [[sid, 0] for sid in range(N)]

        # ================== PAYLOAD PARA SOUTHCONF ==================
        ilp_payload = {
            "Paths": iaco_result["paths"],
            "Schedule": iaco_result["schedule"],  # útil para depuración/visualización
            "Clean_offsets": Clean_offsets_legacy,
            "Repetitions_Descriptor": Repetitions_Descriptor,
            "Streams_Period": Streams_Period,
            "Hyperperiod": Preprocessed_data["Hyperperiod"],
            "identificator": Preprocessed_data.get("identificator", {}),
            "linksInterfaces": Preprocessed_data.get("linksInterfaces", {}),
            "Network_links": Preprocessed_data.get("Network_links", []),
            "unused_links": Preprocessed_data.get("unused_links", []),
            "Frames_per_Stream": Preprocessed_data.get("Frames_per_Stream"),
            "Num_of_Frames": Preprocessed_data.get("Num_of_Frames"),
        }


        # (opcional) persistimos para depuración local
        try:
            with open(OUT_DEBUG_JSON, "w") as f:
                json.dump(ilp_payload, f, indent=2)
        except Exception:
            pass

        # ================== ENVÍO A RABBITMQ (southconf) ==================
        json_ilp_payload = json.dumps(ilp_payload, indent=4)
        send_message(json_ilp_payload, "ilp-south")
        print("Message sent to RabbitMQ (queue: ilp-south)")

    except Exception as e:
        print("ERROR in ILP/__init__.py:", e)
        traceback.print_exc()
        # Señal de error a tu pipeline, si procede:
        print("There is not input data, check the previous microservices or the RabbitMQ logs")
        sys.exit(1)


if __name__ == "__main__":
    main()
