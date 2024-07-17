'''
This function generates a dictionary that organizes the data of the offets.
The json load of the restconf configuration values provided are:
admin-control-list-lenght
time-interval-value
'''
from netconf_client.connect import connect_ssh
from netconf_client.ncclient import Manager
from lxml import etree
import copy
def gates_parameter_generator(Clean_offsets):
    grouped_offsets = {}
    for frame in Clean_offsets:
        identificator=frame['Task'].split(',')
        try:
            grouped_offsets[identificator[3]][identificator[1]].append(frame['Start'])
        except:
            try:
                grouped_offsets[identificator[3]][identificator[1]] = [frame['Start']]
            except :
                grouped_offsets[identificator[3]]= {identificator[1] : [frame['Start']]}

    return grouped_offsets
       
'''This function generates the period to be used as admin cycle time'''
def full_scheduler_generator(grouped_offsets, Repetitions_Descriptor, Streams_Period):
    stream_index = 0
    for repetitions in Repetitions_Descriptor:
        for repetition in repetitions:

            for link in grouped_offsets.keys():
                if " " + str(stream_index) in grouped_offsets[link].keys():
                    if repetition != 0:
                        repetition_offsets = [x+ Streams_Period[str(stream_index)]*repetition for x in grouped_offsets[link][" " + str(stream_index)]]
                        print("looking for this", grouped_offsets[link][" " + str(stream_index)])
                        print("and its type", type(grouped_offsets[link][" " + str(stream_index)]))
                        print(f"link index {link}  stream_index  {stream_index}")
                        for new_offset in repetition_offsets:
                            grouped_offsets[link][" " + str(stream_index)].append(new_offset)
        stream_index = stream_index +  1
    return grouped_offsets


''' 
The following fucntion presents the values in the following way (example):
gate-states-values= [128, "in binary 10000000
                    128, "in binary 10000000
                    255], "in binary 11111111
time-interval-values=[1000
                    2000
                    3000]

With this values is enough to build the admin-control-list of the json payload
'''
def gates_states_values_generator(grouped_offsets, priority_mapping):
    # organize the offsets per link and time
    gates_states={}
    for link in grouped_offsets.keys():
        offsets_organizer= {}
        for stream in grouped_offsets[link].keys():
            for repetition in grouped_offsets[link][stream]:
                offsets_organizer[repetition] = stream
        offsets_organizer= {x:offsets_organizer[x] for x in sorted(offsets_organizer)}

        gates_states[link] = offsets_organizer

    
    #Change stream identificator for priority in binary
    new_gates_states = copy.deepcopy(gates_states)
    for link in gates_states.keys():
        for gate in gates_states[link].keys():
            for i in range(7):
                if gates_states[link][gate] == " "+str(i) :
                    print("link and gate", link, gate)
                    new_gates_states[link][gate] = 2**i
    
    #This will add the best effort traffics
    new_gates_states_be = copy.deepcopy(new_gates_states)
    for key, link in new_gates_states.items():
        for time_interval in link.keys():
            new_gates_states_be[key][time_interval+12] = 255 # This has a hardcoded 12 because it is the duration of the link
    
    # Final_sort
    final_sorted_offsets= {} 
    for link in new_gates_states_be.keys():
        final_sorted_offsets[link] = {x: new_gates_states_be[link][x] for x in sorted(new_gates_states_be[link])}

    print ("-----------FINAL SORTED OFFSETS-------------")
    print (final_sorted_offsets)
    return final_sorted_offsets


'''
Generates the payload defined in the 802.1 qcc schedule
'''
def payload_generator(Clean_offsets, Repetitions_Descriptor, Streams_Period,priority_mapping, hyperperiod, interface_port):

    grouped_offsets=gates_parameter_generator(Clean_offsets)
    grouped_offsets=full_scheduler_generator(grouped_offsets, Repetitions_Descriptor, Streams_Period)
    final_sorted_offsets = gates_states_values_generator(grouped_offsets, priority_mapping)

    per_link_payload = {}
    for link, streams in final_sorted_offsets.items():
        
        admin_control_list = []
        offsets_list = list(streams.keys())
        print("Looking for the offsets_list don't you?", offsets_list)
        offsets_index= 0
        #to_define = "PORT_0"

        #############################XML BUILDING
        #crear elemento config
        config = etree.Element("config")
        # Crear el elemento raíz
        root = etree.SubElement(config, "interfaces")

        # Añadir el espacio de nombres
        root.set("xmlns", "urn:ietf:params:xml:ns:yang:ietf-interfaces")

        #añadir campo interface
        interface = etree.SubElement(root, "interface")
        # Añadir el nombre de la interfaz
        name = etree.SubElement(interface, "name")
        name.text = interface_port

        # Añadir el tipo de interfaz
        nsiana = "urn:ietf:params:xml:ns:yang:iana-if-type"
        nsmapp = {'ianaift' : nsiana,}
        type = etree.SubElement(interface, "type", nsmap=nsmapp)
        type.text = "ianaift:ethernetCsmacd"
        # Añadir el puerto del puente
        bridge_port = etree.SubElement(interface, "bridge-port")
        bridge_port.set("xmlns", "urn:ieee:std:802.1Q:yang:ieee802-dot1q-bridge")

        # Añadir la tabla de parámetros de la puerta
        gate_parameter_table = etree.SubElement(bridge_port, "gate-parameter-table")
        gate_parameter_table.set("xmlns", "urn:ieee:std:802.1Q:yang:ieee802-dot1q-sched")

        # Añadir la puerta habilitada
        gate_enabled = etree.SubElement(gate_parameter_table, "gate-enabled")
        gate_enabled.text = "true"

        # Añadir los estados de la puerta de administración
        admin_gate_states = etree.SubElement(gate_parameter_table, "admin-gate-states")
        admin_gate_states.text = "255"

        # Añadir el máximo de la lista compatible
        supported_list_max = etree.SubElement(gate_parameter_table, "supported-list-max")
        supported_list_max.text = "90"

        # Añadir el ciclo máximo compatible
        supported_cycle_max = etree.SubElement(gate_parameter_table, "supported-cycle-max")

        # Añadir el numerador del ciclo máximo compatible
        numerator = etree.SubElement(supported_cycle_max, "numerator")
        numerator.text = "99999999"

        # Añadir el denominador del ciclo máximo compatible
        denominator = etree.SubElement(supported_cycle_max, "denominator")
        denominator.text = "999999999"

        # Añadir el intervalo máximo compatible
        supported_interval_max = etree.SubElement(gate_parameter_table, "supported-interval-max")
        supported_interval_max.text = "999999999"

        # ADMIN CONTROL LIST
        admin_control_list = etree.SubElement(gate_parameter_table, "admin-control-list")

        #admin cycle time
        admin_cycle_time = etree.SubElement(gate_parameter_table, "admin-cycle-time")

        # Añadir el numerador del ciclo máximo compatible
        numerator = etree.SubElement(admin_cycle_time, "numerator")
        numerator.text = "1"

        # Añadir el denominador del ciclo máximo compatible
        denominator = etree.SubElement(admin_cycle_time, "denominator")
        denominator.text = str(int(1000000/hyperperiod))

        #admin cycle time extension
        admin_cycle_time_extension = etree.SubElement(gate_parameter_table, "admin-cycle-time-extension")
        admin_cycle_time_extension.text = "0"

        #admin base time
        admin_base_time = etree.SubElement(gate_parameter_table, "admin-base-time")
        seconds = etree.SubElement(admin_base_time, "seconds")
        seconds.text = "0"
        nanoseconds = etree.SubElement(admin_base_time, "nanoseconds")
        nanoseconds.text = "0"

        #config change
        config_change = etree.SubElement(gate_parameter_table, "config-change")
        config_change.text = "true"



        for gate_state in streams.values():
            # Evaluate a offset with the next offset to get the total duration of the transmission
            # Until this moment, all offsets and period values were in microseconds
            try:
                time_interval_value = str(int(1000*(offsets_list[offsets_index +1 ] - offsets_list[offsets_index])))
            except:
                print("______________The mistake you are looking for _______________________")
                print(hyperperiod, " __ ", offsets_list[offsets_index])
                time_interval_value = str(int(1000*(hyperperiod - offsets_list[offsets_index]) + 1000))
            #sgs_params = {"gate-states-value": str(int(gate_state)),

                         # "time-interval-value" :time_interval_value # Nanoseconds
                     #   }
            #################### ADMIN CONTROL LIST
            # Añadir la entrada de control de puerta
            gate_control_entry = etree.SubElement(admin_control_list, "gate-control-entry")

            # Añadir el índice
            index = etree.SubElement(gate_control_entry, "index")
            index.text = str(offsets_index)

            # Añadir el nombre de la operación
            operation_name = etree.SubElement(gate_control_entry, "operation-name")
            operation_name.text = "set-gate-states"

            # Añadir el valor del intervalo de tiempo
            timeintervalvalue = etree.SubElement(gate_control_entry, "time-interval-value")
            timeintervalvalue.text = time_interval_value

            # Añadir el valor de los estados de la puerta
            gate_states_value = etree.SubElement(gate_control_entry, "gate-states-value")
            gate_states_value.text = str(int(gate_state))
            #admin_control_list.append(
            #    {#sched-gate-control-entry
             #       "index": str(offsets_index), #does not appear in 09-04-2021 revision
              #      "operation-name": "set-gate-states", #yang checked
                    #"sgs-params": sgs_params #does not appear in 09-04-2021 revision --> gate-states-value + time-interval-value
               #     "gate-states-value": str(int(gate_state)),
                #    "time-interval-value" :time_interval_value # Nanoseconds 
                #}
            #)
            offsets_index = offsets_index + 1
            '''
            per_link_payload[link] = {
                    "interface": {
                                "name": interface,
                                "type": "iana-if-type:ethernetCsmacd",
                                "bridge-port": {
                                    "gate-parameter-table": {
                                    "gate-enabled": "true",
                                    "admin-gate-states": "255",
                                    "supported-list-max": 90,
                                    "supported-cycle-max": {
                                        "numerator": 99999999,
                                        "denominator": 999999999
                                    },
                                    "supported-interval-max": 999999999,
                                    "admin-control-list": {
                                        "gate-control-entry": admin_control_list
                                    },
                                    "admin-cycle-time": {
                                        "numerator": "1",
                                        "denominator": str(int(1000000/(hyperperiod)))
                                    },
                                    "admin-cycle-time-extension": "0",
                                    "admin-base-time": {
                                        "seconds": "0",
                                        "nanoseconds": "0"
                                    },
                                    "config-change": "true"
                                }
                            }
                        }
                    }
        print("----------------------------PAYLOAD----------------------------")
        '''


        # Imprimir la cadena XML
        # Convertir el elemento a una cadena XML
        xml_string = etree.tostring(config, pretty_print=True, encoding="unicode")
        print(xml_string)
        per_link_payload[link] = xml_string
    return per_link_payload


# hyperperiod= 32_000 # Hyperperiod is in microseconds
# Repetitions_Descriptor = [[0, 0], [0, 1], [0, 1], [0, 1], [0, 1]]
# Clean_offsets = [{'Task': "('S', 0, 'L', 6, 'F', 0)", 'Start': 1.0}, 
#                 {'Task': "('S', 1, 'L', 0, 'F', 0)", 'Start': 124.0}, 
#                 {'Task': "('S', 1, 'L', 4, 'F', 0)", 'Start': 1.0}, 
#                 {'Task': "('S', 2, 'L', 4, 'F', 0)", 'Start': 2377.0}, 
#                 {'Task': "('S', 3, 'L', 1, 'F', 0)", 'Start': 1.0}, 
#                 {'Task': "('S', 4, 'L', 0, 'F', 0)", 'Start': 1.0}]
# Streams_Period=  {'0': 32_000, '1': 32_000, '2': 32_000, '3': 16_000, '4': 32_000} # streams_periods are in microseconds 

# # The chu
# # The priority number 7 is always for ptp traffic
# priority_mapping= {'0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '7'} 
# per_link_payload = payload_generator(Clean_offsets, Repetitions_Descriptor, Streams_Period,priority_mapping, hyperperiod)
# print(per_link_payload)