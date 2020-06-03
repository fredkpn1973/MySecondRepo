import re
import json
import ipaddress


#Helper classe 
class ReSearcher():
    match = None

    #Methode die de uiteindelijke vergelijking voor je doet
    #Kan worden aangeroepen als functie
    def __call__(self, pattern, string):
        self.match = re.search(pattern, string)
        return self.match

    def __getattr__(self, name):
        return getattr(self.match, name)


class Vividict(dict):
    #Dit doet iets om er voor te zorgen dat er toch een key is als deze er niet is.
    #Juiste ja, type(self)() geeft de default waarde van het object
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
    
    for configfile in configfiles:

        with open('switch-1.cfg', 'r') as f:
            lines = f.readlines()

        switchinfo = Vividict()
        context = ''
        
        #Ga per regel van het bestand deze for loop in
        for line in lines:
            #Verwijder eventuele rechts spaties
            line = line.rstrip()
            
            #Als we een regel tegenkomen met daarin het word interface
            if match(r'interface (.*)', line):
                #Als dus de regel met interface begint dan hebben we het tweede
                #element nodig, de interface naam
                portindex = format(match.group(1))
                context = 'port'

            if context == 'port':
                
                #Nu gaan we onder het inerface kijken wat we tegen komen, we matchen dus de
                #ene of de andere if statment
                
                #Deze regulier expresies matched op een regel die begint met een spatie gevolgd
                #door 'switchport mode' envervolgens een string van ten minste een lang
                #word geregeld via de __call__ methode
                if match(r'^ switchport mode (\w+)' , line):
                    value = format(match.group(1))
                    switchinfo['port'][portindex]['switchport mode'] = value


                if match(r'^ description (\w+)', line):
                    value = format(match.group(1))
                    switchinfo['port'][portindex]['description'] = value
                    
                if match(r'^ ip address (\d{1,3}[.]\d{1,3}[.]\d{1,3}[.]\d{1,3}) (\d{1,3}[.]\d{1,3}[.]\d{1,3}[.]\d{1,3})', line):
                    value1 = format(match.group(1))
                    value2 = translate_netmask_cidr(format(match.group(2)))
                    value3 = value1 + value2
                    switchinfo['port'][portindex]['ip address'] = value3
    return(switchinfo)                

           
if  __name__ == '__main__':
    porten = configreader('switch-1.cfg')
    
    print(porten)
            
            

        


