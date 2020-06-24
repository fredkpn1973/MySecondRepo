import re
import json
# Comment in featureA
# This text is added in featureZ


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
        return values


def splitrange(raw_range):
    """
    ex. splitrange('105-107') will return ['105','106','107']
    """

    m = re.search(r'^(\d+)\-(\d+)$', raw_range)
    if m:
        first = int(format(m.group(1)))
        last = int(format(m.group(2)))
        return [str(i) for i in range(first, last+1)]


def configreader(configfiles):


<< << << < HEAD
    net_info = []  # list of switchinfo objects

== == == =
>>>>>> > featureA
    match = ReSearcher()

    for configfile in configfiles:

        with open(configfile, 'r') as f:
            lines = f.readlines()

        switchinfo = Vividict()
        context = ''

        for line in lines:
            line = line.rstrip()

            if match(r'interface (.*)', line):
                portindex = format(match.group(1))
                vlan_list = []
                context = 'port'

            elif match(r'hostname (.*)', line):
                hostname = format(match.group(1))
                switchinfo['hostname'] = hostname

            if context == 'port':

                if match(r'^ switchport mode (\w+)', line):
                    value = format(match.group(1))
                    switchinfo['port'][portindex]['switchport mode'] = value

                elif match(r'^ description (\w+)', line):
                    value = format(match.group(1))
                    switchinfo['port'][portindex]['description'] = value

<< << << < HEAD
                elif match(r'^ switchport access vlan (\d+)', line):
                    value = format(match.group(1))
                    portitems = switchinfo['port'][portindex]
                    portitems['switchport access vlan'] = value

                elif match(r'^ switchport trunk allow vlan.* ([0-9,-]+)', line):
                    value = format(match.group(1))
                    for raw_vlans in value.split(','):
                        if '-' in raw_vlans:
                            for vlan_id in splitrange(raw_vlans):
                                vlan_list.append(vlan_id)
                        else:
                            vlan_list.append(raw_vlans)
                    switchinfo['port'][portindex]['vlan_list'] = vlan_list

                elif match(r'!', line):
                    context = ''

        net_info.append(switchinfo)

    return net_info


def main():

    configfiles = ['switch-1.cfg', 'TestSwitch-cfg.txt']

    net_info = configreader(configfiles)

    with open('net_info.json', 'w') as f:
        json.dump(net_info, f, indent=4)


if __name__ == '__main__':
    main()
=======

if __name__ == '__main__':
    configreader("switch-1.cfg")
>>>>>>> featureA
