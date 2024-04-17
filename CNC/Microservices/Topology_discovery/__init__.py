import paramiko, time
from Rabbitmq_queues import *
from node import *
import os,sys
import json

txt_files = []
nodeList = []
i = 0
j = 0
try:
    os.mkdir('devices')
except:
    print("already_created")
''''
os.system('sudo lldpcli show neighbors -f json > nodes.json')
n = open("nodes.json")
jsonNodes = json.load(n)
jsonStringNodes = json.dumps(jsonNodes)
networkNodes = find_values('mgmt-ip',jsonStringNodes)

with open('sw_addresses.conf', 'a') as t:
    t.truncate(0)
    for networkNode in networkNodes:
        t.write(str(networkNode) + '\n')

with open('myIps.txt', 'r') as myIps:
    myIps=myIps.read().split('\n') 
 
print('The host IP addresses are '+str(myIps))
'''
with open('sw_addresses.conf', 'r') as address_file:
    addresses = address_file.read().split('\n')
    #addresses.remove("")
    print(addresses, type(addresses))

for mgmtIp in addresses:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(mgmtIp, username='sys-admin', password='sys-admin')
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
        #if i == 0:
            #nodeTSN.ip = "192.168.4.64"
        #elif i == 1:
            #nodeTSN.ip = "192.168.4.65"
        nodeList.append(nodeTSN) #Adds node to node list
        i += 1
        print("The node's data plane IP address is "+str(nodeTSN.ip))
        print("The node's id is "+str(nodeTSN.id))
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('sudo lldpcli show neighbors -f json',get_pty=True)
    ssh_stdin.write('sys-admin\n')
    ssh_stdin.flush()
    data = ssh_stdout.readlines()
    #print("DATA----------")
    #print(data)
    with open('devices/topology_'+ mgmtIp + '.json', 'a') as f:
        f.truncate(0)
        del data[0:2]
        #data = data[:-5]
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
            finalNeighbors = []
            neighbors = find_values('mgmt-ip',jsonstring) #neighbors of given node
            for neighbor in neighbors:
                finalNeighbors.append(neighbor[0])
            print ("FOUND NEIGHBORS ------------------------")
            print (finalNeighbors)
            finalNeighborsset = set(finalNeighbors)
            neighborPorts = find_values('port', jsonstring) #Ports belonging to neighbors of the given node
            jsonPortNames = json.dumps(neighborPorts)
            portNames = find_values('descr', jsonPortNames) #name of the neighbors' interface (port) directly connected to the given node
            print("FOUND NEIGHBOR INTERFACES ----------------------")
            print(portNames)
            myInterfaces = []
            interfaces = find_values('interface', jsonstring)
            if (len(interfaces[0]) == 1):
                myInterface = jsondata["lldp"]["interface"].keys()
                for key in myInterface:
                    if key.startswith('PORT.'):
                        modKey = key.replace('.','_')
                    myInterfaces.append(modKey)
            else:
                for t in range(len(interfaces[0])):
                # myInterfaces.append(interfaces)
                    myInterface = jsondata["lldp"]["interface"][t].keys()
                    for key in myInterface:
                        if key.startswith('PORT.'):
                            modKey = key.replace('.','_')
                        myInterfaces.append(key)
            print("SELF INTERFACES ----- ")
            print(myInterfaces)
           # interfacesData = json.dumps(interfaces)
            print(interfaces)
            for tsndevice in nodeList:
                j = 0
                if (tsndevice.confIp == device):
                    for neighbor in finalNeighborsset:
                        neighborId = findIdbyIp(nodeList, neighbor)
                        if neighborId is None:  #You just found an end device or CNC
                            #if neighbor in myIps: #CNC is being reported as neighbor
                                #next(neighbors, None)
                                #continue
                            print("End device found with IP address: "+ str(neighbor) +". ID assigned: "+str(i))
                            endDevice = node(i,neighbor, 0,[] )
                            endDevice.neighbors.append([tsndevice.id,myInterfaces[j],portNames[j]]) #neighbors structure : [neighbor ID, neighbor Interface, self interface]
                            tsndevice.neighbors.append([i,portNames[j], myInterfaces[j]])
                            nodeList.append(endDevice)
                            j += 1
                            i += 1
                        else:
                            tsndevice.neighbors.append([neighborId,portNames[j],myInterfaces[j]]) 
                            j += 1

                              
        except Exception as e: 
                print(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
            
            #print(device+ " does not have any neighbor")

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
y = 0
for nodes in nodeList:
    y = 0
    print ("node with ID = "+str(nodes.id))
    for neighbor in nodes.neighbors:
        print("neighbor with ID: "+ str(nodes.neighbors[y][0]) + " and interface: "+str(nodes.neighbors[y][1]))
        y += 1

#retrieving network_nodes, network_links, adjacency_matrix

Topology = {}
networkNodes = []
networkLinks = []
adjacencyMatrix = []
identificator = {}
interfaceMatrix = []
linksInterfaces = {}

countNodes = len(nodeList)
x=0
for tsndevice in nodeList:

    #create list with network nodes
    networkNodes.append(tsndevice.id)
    
    #create list with network links
    for element in tsndevice.neighbors:

        link = []
        link.append(tsndevice.id)
        neighborId = element [0]
        link.append(neighborId)
        inverseLink = [link[1], link[0]]
        if (networkLinks.count(inverseLink) == 0):
            networkLinks.append(link)
            linkInterf = []
            linkInterf.append(element [2])
            linkInterf.append(element [1])
            linksInterfaces [x] = linkInterf
            x+=1

    
    

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
        nodeLinks[neighbor [0]]=1

    adjacencyMatrix.append(nodeLinks)

#Build final topology json

Topology["Network_nodes"] = networkNodes
Topology["Network_links"] = networkLinks
Topology["Adjacency_Matrix"] = adjacencyMatrix
Topology["identificator"] = identificator
Topology["interface_Matrix"] = interfaceMatrix
Topology["Sources"] = sources
Topology["Destinations"] = destinations
Topology["linksInterfaces"] = linksInterfaces
print(Topology)
json_Topology = json.dumps(Topology, indent = 4)


#print(networkNodes)
#print(networkLinks)
#print(adjacencyMatrix)
#print(identificator)

# Sending the messages to the RabbitMQ server

send_message(json_Topology, 'top-pre')
