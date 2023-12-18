import requests
import json
from pprint import pprint

device = {
   "ip": "172.19.0.2",
   "username": "admin",
   "password": "admin",
   "port": "8181",
}

headers = {
      #"Accept" : "application/yang-data+json",
      "Accept" : "*/*",
      "Content-Type" : "application/json",
   }

module = "ietf-interfaces:interfaces"

# Remember to add the name of the interface when you discover what is the issue with the put method
url = f"http://{device['ip']}:{device['port']}/restconf/config/network-topology:network-topology/topology/topology-netconf/node/TSN-switch2/yang-ext:mount/{module}/interface/PORT_0"
url2 = f"http://{device['ip']}:{device['port']}/restconf/config/network-topology:network-topology/topology/topology-netconf"

payload2 = {
    "node": [
        {
            "node-id": "TSN_SWITCH_0",
            "netconf-node-topology:port": "830",
            "netconf-node-topology:reconnect-on-changed-schema": "false",
            "netconf-node-topology:connection-timeout-millis": "20000",
            "netconf-node-topology:tcp-only": "false",
            "netconf-node-topology:max-connection-attempts": "0",
            "netconf-node-topology:username": "soc-e",
            "netconf-node-topology:password": "soc-e",
            "netconf-node-topology:sleep-factor": "1.5",
            "netconf-node-topology:host": "192.168.2.64",
            "netconf-node-topology:between-attempts-timeout-millis": "2000",
            "netconf-node-topology:keepalive-delay": "120"
        }
    ]
}

payload = {
    "interface": [
        {
            "name": "PORT_0",
            "ieee802-dot1q-bridge:bridge-port": {},
            "type": "iana-if-type:ethernetCsmacd",
            "ieee802-dot1q-sched:gate-parameters": {
                "admin-gate-states": "255",
                "gate-enabled": "false",
                "admin-control-list-length": "0",
                "config-change": "false",
                "admin-cycle-time": {
                    "numerator": "1",
                    "denominator": "1000"
                },
                "admin-base-time": {
                    "seconds": "0",
                    "fractional-seconds": "0"
                },
                "admin-cycle-time-extension": "0"
            }
        }
    ]
}
requests.packages.urllib3.disable_warnings()
response = requests.post(url2, headers=headers, json=payload2, auth=(device['username'], device['password']), verify=False)
#response2 = requests.put(url2, headers=headers, json=payload2, auth=(device['username'], device['password']), verify=False)
print(response)
if (response.status_code == 204):
   print("Successfully updated interface")
else:
   print("Issue with updating interface")
