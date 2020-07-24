from ncclient import manager
import xml.dom.minidom
import xmltodict
from pprint import pprint

router = {"host": "10.23.62.38", "port": "830",
          "username": "vosko", "password": "Vosko123"}

netconf_filter = """
<filter>
    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
     
    </interfaces>
</filter>


"""

with manager.connect(host=router['host'], port=router['port'], username=router['username'], password=router['password'], hostkey_verify=False) as m:
    interfaces = m.get(netconf_filter)
    #xml_output = xml.dom.minidom.parseString(str(interfaces))
    xml_dict = xmltodict.parse(interfaces.xml)["rpc-reply"]["data"]
    pprint(xml_dict)
