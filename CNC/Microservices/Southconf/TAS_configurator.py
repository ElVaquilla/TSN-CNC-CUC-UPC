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
        # Limpia comillas, paréntesis y espacios
        identificator = [token.strip().strip("()'") for token in frame['Task'].split(',')]
        
        try:
            link_id = int(identificator[3])     # Ej: ' 0' → 0
            stream_id = int(identificator[1])   # Ej: ' 1' → 1
        except ValueError:
            print(f"Error interpretando identificadores: {identificator}")
            continue

        try:
            grouped_offsets[link_id][stream_id].append(frame['Start'])
        except KeyError:
            try:
                grouped_offsets[link_id][stream_id] = [frame['Start']]
            except KeyError:
                grouped_offsets[link_id] = {stream_id: [frame['Start']]}
    
    print("CLEAN OFFSETS------------------------------")
    print(Clean_offsets)
    print("GROUPED OFFSETS----------------------------")
    print(grouped_offsets)

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
def payload_generator(Clean_offsets, Repetitions_Descriptor, Streams_Period, priority_mapping, hyperperiod, interface_port, Network_links):

     # 1) Construye estados por enlace
    grouped_offsets = gates_parameter_generator(Clean_offsets)
    grouped_offsets = full_scheduler_generator(grouped_offsets, Repetitions_Descriptor, Streams_Period)
    final_sorted_offsets = gates_states_values_generator(grouped_offsets, priority_mapping)

    per_link_payload = {}

    # 2) Un XML por CADA link_id (OJO: 'link' ya es ID, p.ej. 1, 12, 3)
    for link, streams in final_sorted_offsets.items():
        try:
            offsets_list = list(streams.keys())
            print("Looking for the offsets_list don't you?", offsets_list)
            offsets_index = 0

            # Normaliza el nombre de interfaz: evita None
            iface_name = interface_port if interface_port is not None else ""

            # -------- XML (igual que ya tenías) --------
            config = etree.Element("config")
            root = etree.SubElement(config, "interfaces")
            root.set("xmlns", "urn:ietf:params:xml:ns:yang:ietf-interfaces")

            interface = etree.SubElement(root, "interface")
            name = etree.SubElement(interface, "name")
            name.text = iface_name

            nsiana = "urn:ietf:params:xml:ns:yang:iana-if-type"
            nsmapp = {"ianaift": nsiana}
            if_type = etree.SubElement(interface, "type", nsmap=nsmapp)
            if_type.text = "ianaift:ethernetCsmacd"

            bridge_port = etree.SubElement(interface, "bridge-port")
            bridge_port.set("xmlns", "urn:ieee:std:802.1Q:yang:ieee802-dot1q-bridge")

            gate_parameter_table = etree.SubElement(bridge_port, "gate-parameter-table")
            gate_parameter_table.set("xmlns", "urn:ieee:std:802.1Q:yang:ieee802-dot1q-sched")

            gate_enabled = etree.SubElement(gate_parameter_table, "gate-enabled")
            gate_enabled.text = "true"

            admin_gate_states = etree.SubElement(gate_parameter_table, "admin-gate-states")
            admin_gate_states.text = "255"

            supported_list_max = etree.SubElement(gate_parameter_table, "supported-list-max")
            supported_list_max.text = "90"

            supported_cycle_max = etree.SubElement(gate_parameter_table, "supported-cycle-max")
            numerator = etree.SubElement(supported_cycle_max, "numerator")
            numerator.text = "99999999"
            denominator = etree.SubElement(supported_cycle_max, "denominator")
            denominator.text = "999999999"

            supported_interval_max = etree.SubElement(gate_parameter_table, "supported-interval-max")
            supported_interval_max.text = "999999999"

            admin_control_list = etree.SubElement(gate_parameter_table, "admin-control-list")

            admin_cycle_time = etree.SubElement(gate_parameter_table, "admin-cycle-time")
            numerator = etree.SubElement(admin_cycle_time, "numerator")
            numerator.text = "1"
            denominator = etree.SubElement(admin_cycle_time, "denominator")
            denominator.text = str(int(1000000 / hyperperiod))

            admin_cycle_time_extension = etree.SubElement(gate_parameter_table, "admin-cycle-time-extension")
            admin_cycle_time_extension.text = "0"

            admin_base_time = etree.SubElement(gate_parameter_table, "admin-base-time")
            seconds = etree.SubElement(admin_base_time, "seconds")
            seconds.text = "0"
            nanoseconds = etree.SubElement(admin_base_time, "nanoseconds")
            nanoseconds.text = "0"

            config_change = etree.SubElement(gate_parameter_table, "config-change")
            config_change.text = "true"


            # Entradas GCL (duraciones en ns, offsets en us → *1000)
            for gate_state in streams.values():
                try:
                    time_interval_value = str(int(1000 * (offsets_list[offsets_index + 1] - offsets_list[offsets_index])))
                except Exception:
                    print("______________The mistake you are looking for _______________________")
                    print(hyperperiod, " __ ", offsets_list[offsets_index])
                    time_interval_value = str(int(1000 * (hyperperiod - offsets_list[offsets_index]) + 1000))

                gce = etree.SubElement(admin_control_list, "gate-control-entry")
                idx = etree.SubElement(gce, "index")
                idx.text = str(offsets_index)
                op = etree.SubElement(gce, "operation-name")
                op.text = "set-gate-states"
                tiv = etree.SubElement(gce, "time-interval-value")
                tiv.text = time_interval_value
                gsv = etree.SubElement(gce, "gate-states-value")
                gsv.text = str(int(gate_state))

                offsets_index += 1
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


            # Convertir el elemento a una cadena XML
            xml_string = etree.tostring(config, pretty_print=True, encoding="unicode")
            per_link_payload[str(int(link))] = xml_string
            print(f" Añadido linkID {link} al payload.")

        except Exception as e:
            print(f"[payload_generator] Error construyendo payload para link {link}: {e}")

    print("Raw payload keys:", per_link_payload.keys())
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