

class ReSearcher(object):
    """
    Helper  to enable evaluation
    and regex formatting in a single line
    """
    match = None

    # Met __call__ kan dus vanuit een ander klasse een directe functie aanroep
    # worden gedaan.
    def __call__(self):
        print("Dit is een call")

    def __getattr__(self, name):
        return getattr(self.match, name)

    def __str__(self):
        return "Hallo hier ben ik de __str__"

    def printAll(self):
        print('printAll')


def printNameB():
    print("Name is programB")


if __name__ == "__main__":
    print("Dit is de main procedure van ProgrammaB")
    printNameB()
    programA.printNameA()
