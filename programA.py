from programB import ReSearcher


def printNameA():
    print("Name is programA")
    print(__name__)


if __name__ == "__main__":
    print("Dit is de main procedure van ProgrammaA")
    printNameA()
    # programB.printNameB()

r = ReSearcher()
r()
ReSearcher.printAll(r)
print(r)
