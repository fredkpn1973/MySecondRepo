class Test:
    naam =   "Jan"
    match = "The attribute does not exist"
    
    def __getattr__(self, name):
        return 'The attribute {} does not exisct'.format(str(name))
        
           
if  __name__ == '__main__':
    naam = Test()
    print(naam.naam)
    print(naam.voornaam)
    
    