import requests
import json
from netconf_client.connect import connect_ssh
from netconf_client.ncclient import Manager
from lxml import etree
from xml.etree import ElementTree as ET
from netconf_client import error as nc_error
import os
from typing import Iterable, Tuple, Optional
from contextlib import contextmanager

#import httpx
#import asyncio
'''
This function is for allocating the device as a resource for opendaylight
This is a required previous step for the configuration of any device using netconf restconf

                                                            2.- Allocate
                                                                Device
                             RESTCONF                         ┌─────────┐
┌─────────────────────┐                       ┌───────────────┤-Device  │
│                     │                       │               │Allocated│
│ Southconf           ├───────────────────────►               │ Module  │
│       Microservice  │  1.- RestDevice       │  Opendaylight └────┬────┘
│                     │      _creation        │                    │
│                     │  4.- RestDevice       │                    │
└─────────────────────┘      _Configuration   └───────────┬────────┘
                                                          │ 3.- Check
                                                          │     Yang modules
                                                      ┌───▼───┐
                                                      │Device │
                                                      └───────┘

'''
'''
def REST_DEVICE_creation(IP_address, device_name):
    device = {
        "ip": "opendaylight",
        "username": "admin",
        "password": "admin",
        "port": "8181",
    }
    headers= {
        "Accept" : "*/*",
        "Content-Type" : "application/json",
    }
    payload= {
        "node": [
            {
                "node-id": device_name,
                "netconf-node-topology:port": 830,
                "netconf-node-topology:reconnect-on-changed-schema": "false",
                "netconf-node-topology:connection-timeout-millis": 20000,
                "netconf-node-topology:tcp-only": "false",
                "netconf-node-topology:max-connection-attempts": 0,
                "netconf-node-topology:username": "root",
                "netconf-node-topology:password": "root",
                "netconf-node-topology:sleep-factor": 1.5,
                "netconf-node-topology:host": IP_address,
                "netconf-node-topology:between-attempts-timeout-millis": 2000,
                "netconf-node-topology:keepalive-delay": 120
            }
        ]
    }
    url = f"http://{device['ip']}:{device['port']}/restconf/config/network-topology:network-topology/topology/topology-netconf" 
    #url2 = f"http://172.19.0.2:8181/restconf/config/network-topology:network-topology/topology/topology-netconf/node/new-netconf-device"
    #http://172.19.0.2:8181/restconf/config/network-topology:network-topology/topology/topology-netconf
    requests.packages.urllib3.disable_warnings()
    response = requests.post(url, headers=headers, data=json.dumps(payload), auth=(device['username'], device['password']), verify=False)    
    return response
'''
'''
url = "http://127.0.0.1:8443/restconf/data/ieee802-dot1q-tsn-types-upc-version:tsn-uni"
headers = {'X-SSL-Client-CN' : 'marc'}

async def getStreamConfig():
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(url, headers=headers)
        print(response.json())
        return response.json()
 '''   


NC_NS = "urn:ietf:params:xml:ns:netconf:base:1.0"
IF_NS = "urn:ietf:params:xml:ns:yang:ietf-interfaces"
NETCONF_USER = os.getenv("NETCONF_USER", "admin")
NETCONF_PASS = os.getenv("NETCONF_PASS", "admin")
NETCONF_PORT = int(os.getenv("NETCONF_PORT", "830"))

# ---------- Conexión NETCONF (context manager) ----------
DEFAULT_CREDS: Iterable[Tuple[str, str]] = (
    ("root", "root"),
    ("sys-admin", "sys-admin"),
    ("admin", "admin"),
)

@contextmanager
def netconf_connect(ip, username=None, password=None, port=830, timeout=120):
    creds = [
        (username, password) if username and password else ("root", "root"),
        ("sys-admin", "sys-admin"),
        ("admin", "admin"),
    ]
    last_exc = None
    for user, pwd in creds:
        try:
            session = connect_ssh(host=ip, port=port, username=user, password=pwd)
            return Manager(session, timeout=timeout)
        except Exception as e:
            last_exc = e
    raise RuntimeError(f"Conexión NETCONF falló: {last_exc}")


def NETCONF_Get_config(ip: str, filter_xml: Optional[str] = None, source: str = "running"):
    """
    Lanza get-config. Si pasas filter_xml (subtree), lo aplica.
    """
    try:
        with netconf_connect(ip) as mgr:
            # CUIDADO con el nombre de variable: siempre 'mgr'
            r = mgr.get_config(source=source, filter=("subtree", subtree_filter_xml))
            return getattr(r, "xml", str(r))
    except Exception as e:
        return f"[GET-CONFIG][ERROR] Conexión NETCONF falló: {e}"

def NETCONF_Get(ip: str, filter_xml: Optional[str] = None):
    """
    Lanza get (estado/operacional). Si pasas filter_xml (subtree), lo aplica.
    """
    try:
        with netconf_connect(ip) as mgr:
            r = mgr.get(("subtree", subtree_filter_xml))
            return getattr(r, "xml", str(r))
    except Exception as e:
        return f"[GET][ERROR] Conexión NETCONF falló: {e}"

def make_tas_filter(interface_name: str) -> str:
    """
    Subtree-filter apuntando a la tabla TAS (ieee802-dot1q-sched) de una interfaz.
    """
    return f"""
<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
  <interface>
    <name>{interface_name}</name>
    <bridge-port xmlns="urn:ieee:std:802.1Q:yang:ieee802-dot1q-bridge">
      <gate-parameter-table xmlns="urn:ieee:std:802.1Q:yang:ieee802-dot1q-sched"/>
    </bridge-port>
  </interface>
</interfaces>
""".strip()

def netconf_get_interfaces(mgr):
    """
    Devuelve la lista de nombres de interfaces (según ietf-interfaces) usando <get-config>.
    """
    # Filtro para solo interfaces
    filter_xml = f"""
    <filter xmlns="{NC_NS}">
      <interfaces xmlns="{IF_NS}">
        <interface>
          <name/>
        </interface>
      </interfaces>
    </filter>
    """.strip()

    reply = mgr.get_config(source="running", filter=filter_xml)
    # 'reply' es una cadena XML (con netconf_client); parseamos
    try:
        root = ET.fromstring(reply)
    except Exception:
        # si la librería ya da un objeto con .data, adapta aquí
        return []

    # Busca todos los <name> bajo ietf-interfaces
    ns = {"if": IF_NS}
    names = [el.text for el in root.findall(".//if:interfaces/if:interface/if:name", ns) if el.text]
    return names

def netconf_preflight_has_interface(ip, username="root", password="root"):
    """
    Abre sesión NETCONF, lista interfaces y devuelve ese listado.
    Maneja errores de conexión limpiamente.
    """
    try:
        mgr = connect_ssh(host=ip, port=830, username=username, password=password)
    except Exception as e:
        return False, [], f"Conexión NETCONF falló: {e}"

    try:
        names = netconf_get_interfaces(mgr)
        mgr.close()
        return True, names, None
    except Exception as e:
        try:
            mgr.close()
        except Exception:
            pass
        return False, [], f"Fallo en get-config: {e}"

def NETCONF_Device_configuration (payload, ip):
    '''
    device = {
        "ip": "opendaylight",
        "username": "admin",
        "password": "admin",
        "port": "8181",
    }
    headers= {
        "Accept" : "*/*",
        "Content-Type" : "application/json",
    }
    module = "ietf-interfaces:interfaces"
    url = f"http://{device['ip']}:{device['port']}/restconf/config/network-topology:network-topology/topology/topology-netconf/node/{device_name}/yang-ext:mount/{module}/interface/"+device_interface
    requests.packages.urllib3.disable_warnings()
    print("_________________This is the url_________________", url)
    # Sending the message
    response = requests.put(url, headers=headers, data=json.dumps(payload), auth=(device['username'], device['password']), verify=False)
    '''
    try:
        session = connect_ssh(host=ip, port=830, username="root", password="root")
        mgr = Manager(session, timeout=120)
        mgr.edit_config(config=str(payload))
        #session.close()
        return mgr
    except:
        session = connect_ssh(host=ip, port=830, username="sys-admin", password="sys-admin")
        mgr = Manager(session, timeout=120)
        mgr.edit_config(config=str(payload))
        #session.close()
        return mgr

