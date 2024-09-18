
'''
This microservice is in charge of sending the appropiate configuration to the two Southbound Microservices i.e., Vlan_Configurator and Opendaylight

The Opendaylight controller will receive a HTTP jetconf for each of the elements in the topology following the ieee802dot1sched.

IP address -> Table between the node number and an IP address
interface.name ->Table between the connection and the interface name 
gate-enabled -> Always on
admin-gate-states -> 255 (everything on)
admin-control-list-length -> This should vary according to the number of streams will pass through the switch
admin-control-list - > one per each stream
operation-name: set-gates-states 
sgs-params
gate-states-value -> This is a value in binary to decimal that shold represent the state of the gate for that specific traffic
time-interval-value -> Total duration of the stream
admin-cycle-time -> This is just one cause is the general of the gate, numerator and denominator for representing the total time
admin-cycle-time-extension -> same as above
admin-base-time -> seconds and fractionals
seconds
fractional-seconds
config-change -> Always true

On the other hand, VLan configurator will need the following parameters:

IP address ->
VLANS and priority coddes
Topology
Members of the same Vlan

This is the diagram that represents this microservice:

                            Export
                                 Service

                                  ▲
                                  │
        ┌─────────────────────────┼────────────────────────────┐
        │                         │                            │
        │  ┌────────────┐   ┌─────┴──────┐    ┌────────────┐   │
        │  │            │   │            │    │            │   │    ┌──────────────┐
        │  │ ilp_south  │   │ Web        │    │ Json vlans │   │    │              │
   ┌────┼──► Rabitmq    │   │  Interface │    │            │   │    │  Vlan        │
   │    │  │            │   │            │    │ contains:  ├───┼────►  Configurator│
┌──┴──┐ │  └─────┬──────┘   └────────────┘    │ -devices   │   │    │              │
│ ILP │ │        │                            │ -vlans each│   │    │              │
└─────┘ │  ┌─────▼─────────────────────────┐  │            │   │    └──────────────┘
        │  │                               │  │            │   │
        │  │ ConfGen              ┌────────┼──►            │   │
        │  │                      │        │  └────────────┘   │
        │  │  ┌───────────────────┴─────┐  │                   │
        │  │  │ Vlans_configurator      │  │  ┌────────────┐   │
        │  │  │                         │  │  │ Restconf   │   │    ┌──────────────┐
        │  │  └─────────────────────────┘  │  │            │   │    │              │
        │  │                               │  │ contains:  │   │    │  Open        │
        │  │  ┌─────────────────────────┐  │  │ -devices   ├───┼────►    Daylight  │
        │  │  │ TAS_configurator        │  │  │ -offsets   │   │    │              │
        │  │  │                         ├──┼──► -priorities│   │    │              │
        │  │  └─────────────────────────┘  │  │ -cycles    │   │    └──────────────┘
        │  │                               │  │            │   │
        │  └───────────────────────────────┘  └────────────┘   │
        │                                                      │
        └──────────────────────────────────────────────────────┘
'''


import os
import json
from Vlans_configurator import *
from TAS_configurator import *
from Rest_client import *
import time

if __name__ == "__main__":
    raw_scheduler_data = os.path.exists('/var/ilp.txt')
    if(raw_scheduler_data):
        with open('/var/ilp.txt') as raw_scheduler_data_file:
                ilp_data = json.load(raw_scheduler_data_file)
        print(ilp_data)
        """
        TAS payload generator for the Yang models
        Necessary parameters:
        
        Clean_offsets, 
        Repetitions_Descriptor, 
        Streams_Period,
        priority_mapping, 
        Hyperperiod
        It is also necessary the connection between the link id and the two devices that connects


        """
        Clean_offsets = ilp_data["Clean_offsets"]
        Repetitions_Descriptor = ilp_data["Repetitions_Descriptor"]
        Streams_Period = ilp_data["Streams_Period"]
        Hyperperiod =  ilp_data["Hyperperiod"]
        priority_mapping= {'0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '7'}
        identificator = ilp_data["identificator"]
        linksInterfaces = ilp_data["linksInterfaces"]
        networkLinks =ilp_data['Network_links']
        unusedLinks = ilp_data['unused_links']

        print("LINKS INTERFACES ------")
        print(linksInterfaces)
        print("CLEAN OFFSETS ---------")
        print(Clean_offsets)
        print("REPETITIONS DESCRIPTOR -----")
        print(Repetitions_Descriptor)
        print("STREAMS PERIOD --------")
        print(Streams_Period)
        print("HYPERPERIOD -----------")
        print(Hyperperiod)
        print("IDENTIFICATOR ---------")
        print(identificator)
        print("NETWORK LINKS ---------")
        print(networkLinks)
        print("UNUSED LINKS --------")
        print(unusedLinks)
        #interface_Matrix = ilp_data["interface_Matrix"]
        countSwitches = 0
        totalLinks = []
        switchesIDs = []
        # device_list should be created
        for index, device in identificator.items() :
            if device.startswith('192.168.2.'):
                 #request = REST_DEVICE_creation(device, "TSN_SWITCH_" + str(countSwitches))
                 #print(request)
                 switchName = "TSN_SWITCH_"+str(countSwitches)
                 switchesIDs.append([device,switchName])
                 countSwitches += 1
        time.sleep(2)
        print("SWITCHES IDs -------")
        print(switchesIDs)
            
        configurableLinks = []
        for key in linksInterfaces.keys():
             totalLinks.append(int(key))
             if int(key) not in unusedLinks:
                  configurableLinks.append(int(key))

        print("TOTAL LINKS ---------")
        print(totalLinks)
        print ("CONFIGURABLE LINKS ---------")
        print(configurableLinks)
        for key in configurableLinks: #A partir del linkID, conseguir el nombre de los switch y las interficies que forman parte del link
            linkID = int(key)
            print("LINK ID-----")
            print(linkID)
            link = networkLinks[linkID] #link para el cual se ha generado una configuración
            switchIP = 0
            switchInterfaces = []
            print(link)
            for index,interfaces in linksInterfaces.items():
                 if int(index) == linkID:
                      print(interfaces)
                      switchInterfaces = interfaces
            #print(interfaces)
            for switchID in link: #Para cada switch en el link, encontrar su nombre (ej: TSN_SWITCH_0) a partir de su ID
                for index, ip in identificator.items(): 
                     if int(index) == int(switchID):
                          switchIP = ip #Encontrar su IP primero
                          for element in switchesIDs:
                               if switchIP in element: #Encontrar nombre del switch mediante la IP
                                    switchConfName = element[1]
                                    interface = switchInterfaces[int(link.index(switchID))]
                                    per_link_payload = payload_generator(Clean_offsets, Repetitions_Descriptor, Streams_Period,priority_mapping, Hyperperiod, interface)
                                    #request= NETCONF_Device_configuration (per_link_payload[" "+str(key)], switchConfName, interface, switchIP) 
                                    request= NETCONF_Device_configuration (per_link_payload[" "+str(key)], switchIP) #El indice de per_link_payload hace referencia al ID del link al que pertenece la interficie que se configura
                                    print(switchConfName)
                                    print(interface)
                                    print("Link "+str(key))
                                    print(str(per_link_payload[" "+str(key)]))
                                    print(f"----------------RESPONSE TO REQUEST: {request}")
                                    #streams = asyncio.run

                                    
                                    

            
        
        
        #request= REST_Device_configuration (per_link_payload[" 0"], "TSN_SWITCH_1")
        #print(json.dumps(per_link_payload[" 0"]))
        
        print(identificator)
    else:
        print("There is not input data, check the previous microservices or the RabbitMQ logs")