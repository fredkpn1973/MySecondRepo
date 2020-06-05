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
    
    #Hier tellen we simpel weg alle 0en die in het masker voorkomen
    #dit doen we per octet, vandaar de split, en webginnen achteraan, 
    #vandaar de reversed.
    for octet in reversed(netmask_octets):
        #Zet de decimale octet om naar een binary van acht lang
        binary = format(int(octet), '08b')
        #Zodra we een een tegen kunnen we stoppen met de for loop
        #als we een nul zien dan verhogen we de teller met een
        for char in reversed(binary):
            if char == '1':
                break
            negative_offset += 1
    #Het masker is nu dus het totaal aantal bits in een adres min het aantal 0en
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
    geeft_terug = []
    for configfile in configfiles:
        with open(configfile, 'r') as f:
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

            
            elif match(r'vlan (\d+)', line):
                vlanindex = format(match.group(1))
                context = 'vlans'

            if context == 'port':
                
                #Nu gaan we onder het inerface kijken wat we tegen komen, we matchen dus de
                #ene of de andere if statment
                
                #Deze regulier expresies matched op een regel die begint met een spatie gevolgd
                #door 'switchport mode' envervolgens een string van ten minste een lang
                #word geregeld via de __call__ methode
                if match(r'^ switchport mode (\w+)' , line):
                    value = format(match.group(1))
                    switchinfo['port'][portindex]['switchport mode'] = value
                    
                elif match(r'^ ip vrf forwarding (\w+)' , line):
                    value = format(match.group(1))
                    switchinfo['port'][portindex]['ip vrf forwarding'] = value

                elif match(r'^ description (\w+)', line):
                    value = format(match.group(1))
                    switchinfo['port'][portindex]['description'] = value
                    
                elif match(r'^ ip address (\d{1,3}[.]\d{1,3}[.]\d{1,3}[.]\d{1,3}) (\d{1,3}[.]\d{1,3}[.]\d{1,3}[.]\d{1,3})', line):
                    value = format(match.group(1)) + translate_netmask_cidr(format(match.group(2)))
                    switchinfo['port'][portindex]['ip address'] = value

            elif context == 'vlans':
                
                if match(r'^ name (\w+)', line):
                    value = format(match.group(1))
                    switchinfo['vlans'][vlanindex]['name'] = value

            if line == "!":
                context = ''

        geeft_terug.append(switchinfo)

            


    return(geeft_terug)                

           
if  __name__ == '__main__':
    porten = configreader(['TestSwitch-cfg.txt','switch-1.cfg'])
    
    print(json.dumps(porten, indent = 4))
 
            
            

        


