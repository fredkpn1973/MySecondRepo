import re
import json
#Comment in featureA


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

    for configfile in configfiles:

        with open('switch-1.cfg', 'r') as f:
            lines = f.readlines()

        switchinfo = Vividict()
        context = ''

        for line in lines:
            line = line.rstrip()

            if match(r'interface (.*)', line):
                portindex = format(match.group(1))
                context = 'port'

            if context == 'port':

                if match(r'^ switchport mode (\w+)', line):
                    value = format(match.group(1))
                    switchinfo['port'][portindex]['switchport mode'] = value

                if match(r'^ description (\w+)', line):
                    value = format(match.group(1))
                    switchinfo['port'][portindex]['description'] = value
        print(json.dumps(switchinfo))


if __name__ == '__main__':
    configreader("switch-1.cfg")
