from netconf_client.connect import connect_ssh
from netconf_client.ncclient import Manager
from lxml import etree
#import hashlib

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
name.text = "PORT_1"

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

# Añadir la lista de control de administración
admin_control_list = etree.SubElement(gate_parameter_table, "admin-control-list")

# Añadir la entrada de control de puerta
gate_control_entry = etree.SubElement(admin_control_list, "gate-control-entry")

# Añadir el índice
index = etree.SubElement(gate_control_entry, "index")
index.text = "0"

# Añadir el nombre de la operación
operation_name = etree.SubElement(gate_control_entry, "operation-name")
operation_name.text = "set-gate-states"

# Añadir el valor del intervalo de tiempo
time_interval_value = etree.SubElement(gate_control_entry, "time-interval-value")
time_interval_value.text = "500000"

# Añadir el valor de los estados de la puerta
gate_states_value = etree.SubElement(gate_control_entry, "gate-states-value")
gate_states_value.text = "255"

###############################
# Añadir la entrada de control de puerta
gate_control_entry = etree.SubElement(admin_control_list, "gate-control-entry")

# Añadir el índice
index = etree.SubElement(gate_control_entry, "index")
index.text = "1"

# Añadir el nombre de la operación
operation_name = etree.SubElement(gate_control_entry, "operation-name")
operation_name.text = "set-gate-states"

# Añadir el valor del intervalo de tiempo
time_interval_value = etree.SubElement(gate_control_entry, "time-interval-value")
time_interval_value.text = "500000"

# Añadir el valor de los estados de la puerta
gate_states_value = etree.SubElement(gate_control_entry, "gate-states-value")
gate_states_value.text = "188"
############################

#admin cycle time
admin_cycle_time = etree.SubElement(gate_parameter_table, "admin-cycle-time")

# Añadir el numerador del ciclo máximo compatible
numerator = etree.SubElement(admin_cycle_time, "numerator")
numerator.text = "1000000"

# Añadir el denominador del ciclo máximo compatible
denominator = etree.SubElement(admin_cycle_time, "denominator")
denominator.text = "1000000000"

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

# Convertir el elemento a una cadena XML
xml_string = etree.tostring(config, pretty_print=True, encoding="unicode")

# Imprimir la cadena XML
print(xml_string)

session = connect_ssh(host="192.168.2.67", port=830, username="sys-admin", password="sys-admin")
mgr = Manager(session, timeout=120)
mgr.edit_config(config=str(xml_string))
'''
mgr.edit_config(config="""<config><interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
  <interface>
    <name>PORT_1</name>
    <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
    <bridge-port xmlns="urn:ieee:std:802.1Q:yang:ieee802-dot1q-bridge">
      <gate-parameter-table xmlns="urn:ieee:std:802.1Q:yang:ieee802-dot1q-sched">
        <gate-enabled>true</gate-enabled>
        <admin-gate-states>255</admin-gate-states>
        <supported-list-max>90</supported-list-max>
        <supported-cycle-max>
          <numerator>99999999</numerator>
          <denominator>999999999</denominator>
        </supported-cycle-max>
        <supported-interval-max>999999999</supported-interval-max>
        <admin-control-list>
          <gate-control-entry>
            <index>0</index>
            <operation-name>set-gate-states</operation-name>
            <time-interval-value>500000</time-interval-value>
            <gate-states-value>255</gate-states-value>
          </gate-control-entry>
          <gate-control-entry>
            <index>1</index>
            <operation-name>set-gate-states</operation-name>
            <time-interval-value>500000</time-interval-value>
            <gate-states-value>188</gate-states-value>
          </gate-control-entry>
        </admin-control-list>
        <admin-cycle-time>
          <numerator>1000000</numerator>
          <denominator>1000000000</denominator>
        </admin-cycle-time>
        <admin-cycle-time-extension>8</admin-cycle-time-extension>
        <admin-base-time>
          <seconds>0</seconds>
          <nanoseconds>0</nanoseconds>
        </admin-base-time>
        <config-change>true</config-change>
      </gate-parameter-table>
    </bridge-port>
  </interface>
</interfaces></config>""",default_operation='replace')
'''


#with open('netconftest.xml', 'a') as f:
   # f.write(str(xml_string))
#print(mgr.get(filter="""<filter> ... </filter>""").data_xml)