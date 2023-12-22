import paramiko, time
from Rabbitmq_queues import *
from node import *
import os
import json

txt_files = []
nodeList = []
i = 0
try:
    os.mkdir('devices')
except:
    print("already_created")
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
myIps = find_values('local', jsonStringIfconfig) #Finds my IPs to not be added as a neighbor when receiving the report from switches

with open('sw_addresses.conf', 'r') as address_file:
    addresses=address_file.read().split('\n')
    print(addresses, type(addresses))

for mgmtIp in addresses:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(mgmtIp, username='soc-e', password='soc-e')
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('ip -f inet addr show eth0 | sed -En -e \'s/.*inet ([0-9.]+).*/\\1/p\'') #Ask for the data plane ip address
    time.sleep(1)
    data = ssh_stdout.readlines()
    with open('devices/relatedIPs_'+ mgmtIp + '.txt', 'a') as f: #Creates file with related IPs (management IP address and data plane IP address)
        f.truncate(0)
        f.write(mgmtIp+'\n')
        nodeTSN = node (i,mgmtIp,0,[]) #Creates node instance
        for line in data:
            f.write(str(line) + '\n')
            nodeTSN.ip = line
            nodeList.append(nodeTSN) #Adds node to node list
            i += 1
            print("The node's data plane IP address is "+nodeTSN.ip)
            print("The node's id is "+str(nodeTSN.id))
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('sudo lldpcli show neighbors -f json')
    time.sleep(1)
    data = ssh_stdout.readlines()
    with open('devices/topology_'+ mgmtIp + '.json', 'a') as f:
        f.truncate(0)
        for line in data:
            f.write(str(line) + '\n')

# Parse the created json files to find neighbors

for file in os.listdir("./devices"):
    if file.startswith("topology_"):
        filename = os.path.splitext(os.path.basename(file))[0]
        device = filename.split("_")[1] #Gets the node's management IP address
        #print("The device id is "+str(nodeList[1].id))
        f = open("./devices/"+file)
        jsondata = json.load(f)
        jsonstring = json.dumps(jsondata)
        print(find_values('mgmt-ip',jsonstring))

        try:
            neighbors = find_values('mgmt-ip',jsonstring) #neighbors of each node
            for tsndevice in nodeList:
                if (tsndevice.confIp == device):
                    for neighbor in neighbors:
                        neighborId = findIdbyIp(nodeList, neighbor)
                        if neighborId is None:  #You just found an end device or CNC
                            if neighbor in myIps: #CNC is being reported as neighbor
                                next(neighbors, None)
                                continue
                            print("End device found with IP address: "+ str(neighbor) +". ID assigned: "+str(i))
                            endDevice = node(i,neighbor, 0,[] )
                            endDevice.neighbors.append(tsndevice.id)
                            tsndevice.neighbors.append(i)
                            nodeList.append(endDevice)
                            i += 1
                        else:
                            tsndevice.neighbors.append(neighborId)  
                              
        except:
            print(device+ " does not have any neighbor")
'''
        try:
            neighbor = jsondata['lldp']['interface']['PORT.0']['chassis']['SOCE_MTSN_KIT']['mgmt-ip']
            neighborId = findIdbyIp(nodeList, neighbor)
            print("Neighbor found. Node with id: "+str(neighborId))
            for tsndevice in nodeList:
                if (tsndevice.confIp == device):
                    intfNeighbor = ['PORT.0', neighborId]
                    tsndevice.interfacesAndNeighbors.append(intfNeighbor)
                    #print("The node mgmt IP is "+tsndevice.confIp+", the data plane ip is "+tsndevice.ip+", one used interface is "+tsndevice.interfacesAndNeighbors[0][0]+", and the neighbor is "+tsndevice.interfacesAndNeighbors[0][1])

        except:
            print("Port 0 from "+device+ " does not have any neighbor")

        try:
            neighbor = jsondata['lldp']['interface']['PORT.1']['chassis']['SOCE_MTSN_KIT']['mgmt-ip']
            neighborId = findIdbyIp(nodeList, neighbor)
            print("Neighbor found. Node with id: "+str(neighborId))
            for tsndevice in nodeList:
                if (tsndevice.confIp == device):
                    intfNeighbor = ['PORT.1', neighborId]
                    tsndevice.interfacesAndNeighbors.append(intfNeighbor)
        except:
            print("Port 1 from "+device+ " does not have any neighbor")
        try:
            neighbor = jsondata['lldp']['interface']['PORT.2']['chassis']['SOCE_MTSN_KIT']['mgmt-ip']
            neighborId = findIdbyIp(nodeList, neighbor)
            print("Neighbor found. Node with id: "+str(neighborId))
            for tsndevice in nodeList:
                if (tsndevice.confIp == device):
                    intfNeighbor = ['PORT.2', neighborId]
                    tsndevice.interfacesAndNeighbors.append(intfNeighbor)
        except:
            print("Port 2 from "+device+ " does not have any neighbor")
        try:
            neighbor = jsondata['lldp']['interface']['PORT.3']['chassis']['SOCE_MTSN_KIT']['mgmt-ip']
            print("The neighbor found has ip address: "+str(neighbor))
            neighborId = findIdbyIp(nodeList, neighbor)
            print("Neighbor found. Node with id: "+str(neighborId))
            for tsndevice in nodeList:
                if (tsndevice.confIp == device):
                    intfNeighbor = ['PORT.3', neighborId]
                    tsndevice.interfacesAndNeighbors.append(intfNeighbor)
        except:
            print("Port 3 from "+device+ " does not have any neighbor")

'''
#retrieving network_nodes, network_links, adjacency_matrix

Topology = {}
networkNodes = []
networkLinks = []
adjacencyMatrix = []
identificator = {}
interfaceMatrix = []

countNodes = len(nodeList)
for tsndevice in nodeList:

    #create list with network nodes
    networkNodes.append(tsndevice.id)

    #create list with network links
    for element in tsndevice.neighbors:
        link = []
        link.append(tsndevice.id)
        neighborId = element
        link.append(neighborId)
        inverseLink = [link[1], link[0]]
        if (networkLinks.count(inverseLink) == 0):
            networkLinks.append(link)

#Build link sources and destinations
sources = [link[0] for link in networkLinks]
destinations = [link[1] for link in networkLinks]

#build adjacency matrix and identificators
for tsndevice in nodeList:
    nodeLinks = []
    identificator[tsndevice.id] = str(tsndevice.confIp) #identificators
    for nodes in nodeList:
        nodeLinks.append(0)

    for neighbor in tsndevice.neighbors:
        nodeLinks[neighbor]=1

    adjacencyMatrix.append(nodeLinks)

#Build final topology json

Topology["Network_nodes"] = networkNodes
Topology["Network_links"] = networkLinks
Topology["Adjacency_Matrix"] = adjacencyMatrix
Topology["identificator"] = identificator
Topology["interface_Matrix"] = interfaceMatrix
Topology["Sources"] = sources
Topology["Destinations"] = destinations
print(Topology)
json_Topology = json.dumps(Topology, indent = 4)


#print(networkNodes)
#print(networkLinks)
#print(adjacencyMatrix)
#print(identificator)

# Sending the messages to the RabbitMQ server

send_message(json_Topology, 'top-pre')
