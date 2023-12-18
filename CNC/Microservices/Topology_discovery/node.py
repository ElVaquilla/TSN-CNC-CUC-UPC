class node:

    def __init__(self, id, confIp, ip, interfacesNeighbors):
        self.id = id
        self.confIp = confIp
        self.ip = ip
        self.interfacesAndNeighbors = interfacesNeighbors
    
    def getInterfacesAndNeighbors (self):
        return self.interfacesAndNeighbors
        
def findIdbyIp (nodeList, ip):
    for nodetsn in nodeList:
        if (str(nodetsn.ip).rstrip('\n')==str(ip)):
            return nodetsn.id
        

