from ncclient import manager
import xmltodict
import xml.dom.minidom
from pprint import pprint

router = {"host": "ios-xe-mgmt-latest.cisco.com", "port": "10000",
          "username": "developer", "password": "C1sco12345"}

just_a_filter = """
    <filter>
        <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
          <interface>
            <name>GigabitEthernet1</name>
          </interface>
        </interfaces>
        
    </filter>
"""

with manager.connect(host=router["host"], port=router["port"], username=router["username"], password=router["password"], hostkey_verify=False) as m:

    interface_netconf = m.get(just_a_filter)
    xmlDom = xml.dom.minidom.parseString(str(interface_netconf))
    print(xmlDom.toprettyxml(indent=" "))
    interface_python = xmltodict.parse(interface_netconf.xml)[
        "rpc-reply"]["data"]
    pprint(interface_python)
    print(interface_python['interfaces']['interface']['name']['#text'])
