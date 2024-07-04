from netconf_client.connect import connect_ssh
from netconf_client.ncclient import Manager
from lxml import etree
import sys


#session = connect_ssh(host="192.168.2.68", port=830, username="root", password="root")
#mgr = Manager(session, timeout=120)
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
# Crear el elemento raíz
root = etree.Element("interface")

# Añadir el espacio de nombres
root.set("xmlns", "urn:ietf:params:xml:ns:yang:ietf-interfaces")

# Añadir el nombre de la interfaz
name = etree.SubElement(root, "name")
name.text = "PORT_1"

# Añadir el tipo de interfaz
nsiana = "urn:ietf:params:xml:ns:yang:iana-if-type"
nsmapp = {'ianaift' : nsiana,}
type = etree.SubElement(root, "type", nsmap=nsmapp)
type.text = "ianaift:ethernetCsmacd"
# Añadir el puerto del puente
bridge_port = etree.SubElement(root, "bridge-port")
bridge_port.set("xmlns", "urn:ieee:std:802.10:yang:ieee802-dotiq-bridge")

# Añadir la tabla de parámetros de la puerta
gate_parameter_table = etree.SubElement(bridge_port, "gate-parameter-table")
gate_parameter_table.set("xmlns", "urn:ieee:std:802.10:yang:ieee802-dot1q-sched")

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

# Añadir el nombre de la operación
operation_name = etree.SubElement(gate_control_entry, "operation-name")
operation_name.text = "set-gate-states"

# Añadir el índice
index = etree.SubElement(gate_control_entry, "index")
index.text = "0"

# Añadir el valor del intervalo de tiempo
time_interval_value = etree.SubElement(gate_control_entry, "time-interval-value")
time_interval_value.text = "500000"

# Añadir el valor de los estados de la puerta
gate_states_value = etree.SubElement(gate_control_entry, "gate-states-value")
gate_states_value.text = "255"

# Añadir el valor del ciclo
cycle_value = etree.SubElement(gate_control_entry, "cycle-value")
cycle_value.text = "0"

# Añadir el valor del intervalo
interval_value = etree.SubElement(gate_control_entry, "interval-value")
interval_value.text = "0"

# Convertir el elemento a una cadena XML
xml_string = etree.tostring(root, pretty_print=True, encoding="utf-8")

# Imprimir la cadena XML
print(xml_string)
with open('netconftest.xml', 'a') as f:
    f.write(str(xml_string))
#print(mgr.get(filter="""<filter> ... </filter>""").data_xml)