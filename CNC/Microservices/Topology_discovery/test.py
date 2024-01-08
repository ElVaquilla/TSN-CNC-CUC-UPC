import os
import json
from node import *
import socket
'''
os.system('lldpcli show neighbors -f json > nodes.json')
n = open("nodes.json")
jsonNodes = json.load(n)
jsonStringNodes = json.dumps(jsonNodes)
networkNodes = find_values('mgmt-ip',jsonStringNodes)

with open('sw_addresses.conf', 'a') as t:
    t.truncate(0)
    for networkNode in networkNodes:
        t.write(str(networkNode) + '\n')
        '''
os.system('ip --json address show > ip.json')
ifconfig = open('ip.json')
jsonIfconfig = json.load(ifconfig)
jsonStringIfconfig = json.dumps(jsonIfconfig)
myIps = find_values('local', jsonStringIfconfig)
with open('Topology_discovery/myIps.txt', 'a') as f:
    f.truncate(0)
    for ip in myIps:
        f.write(str(ip)+'\n')
print(myIps)