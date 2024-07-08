import requests
import json
from netconf_client.connect import connect_ssh
from netconf_client.ncclient import Manager
from lxml import etree
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
    session = connect_ssh(host=ip, port=830, username="root", password="root")
    mgr = Manager(session, timeout=120)
    mgr.edit_config(config=str(payload))
    return mgr
