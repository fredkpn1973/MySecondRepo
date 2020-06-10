import re
import json
import ipaddress
from openpyxl.utils import get_column_letter
from openpyxl import Workbook


class ReSearcher():
    match = None

    def __call__(self, pattern, string):
        self.match = re.search(pattern, string)
        return self.match

    def __getattr__(self, name):
        return getattr(self.match, name)


class Vividict(dict):
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value


def translate_netmask_cidr(netmask):
    """
    Translate IP netmask to CIDR notation.
    :param netmask:
    :return: CIDR netmask as string
    """
    netmask_octets = netmask.split('.')
    negative_offset = 0

    for octet in reversed(netmask_octets):
        binary = format(int(octet), '08b')
        for char in reversed(binary):
            if char == '1':
                break
            negative_offset += 1
    return '/{0}'.format(32-negative_offset)


def splitrange(raw_range):
    """
    ex. splitrange('105-107') will return ['105','106','107']
    """

    m = re.search(r'^(\d+)\-(\d+)$', raw_range)
    if m:
        first = int(format(match.group(1)))
        last = int(format(match.group(2)))
        return [str(i) for i in range(first, last+1)]


def configreader(configfiles):

    match = ReSearcher()
    geeft_terug = {}
    for configfile in configfiles:
        with open(configfile, 'r') as f:
            lines = f.readlines()

        switchinfo = Vividict()
        context = ''

        for line in lines:

            line = line.rstrip()

            if match(r'interface (.*)', line):
                portindex = format(match.group(1))
                context = 'port'

            elif match(r'vlan (\d+)', line):
                vlanindex = format(match.group(1))
                context = 'vlans'

            if context == 'port':

                if match(r'^ switchport mode (\w+)', line):
                    value = format(match.group(1))
                    switchinfo[configfile]['port'][portindex]['switchport mode'] = value

                elif match(r'^ ip vrf forwarding (\w+)', line):
                    value = format(match.group(1))
                    switchinfo[configfile]['port'][portindex]['ip vrf forwarding'] = value

                elif match(r'^ description ([a-zA-Z0-9_-|\s]+)', line):
                    value = format(match.group(1))
                    switchinfo[configfile]['port'][portindex]['description'] = value

                elif match(r'^ ip address (\d{1,3}[.]\d{1,3}[.]\d{1,3}[.]\d{1,3}) (\d{1,3}[.]\d{1,3}[.]\d{1,3}[.]\d{1,3})', line):
                    value = format(match.group(1)) + \
                        translate_netmask_cidr(format(match.group(2)))
                    switchinfo[configfile]['port'][portindex]['ip address'] = value

            elif context == 'vlans':

                if match(r'^ name (\w+)', line):
                    value = format(match.group(1))
                    switchinfo[configfile]['vlans'][vlanindex]['name'] = value

            if line == "!":
                context = ''

        geeft_terug.update(switchinfo)

    return(geeft_terug)


if __name__ == '__main__':

    # Tja, wat gebeurd hier nu? Wel we geven aan configreader een lijst van configuraties. Configreader geeft vervolgens dat deel terug wat wij willen weten
    porten = configreader(['TestSwitch-cfg.txt', 'switch-1.cfg'])

    x = 0
    # Ook nu wordt het interessant. We hebben nu dus een lijst met twee elemenet. TestSwitch en switch-1. De bevatten op hun beurt weer een dictionary.
    with open('json.json', 'r') as f:
        lines = f.readlines()
        file_dict = json.dumps(f)
        print(file_dict)
