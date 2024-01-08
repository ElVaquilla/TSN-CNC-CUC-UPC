import json
class node:

    def __init__(self, id, confIp, ip, neighbors):
        self.id = id
        self.confIp = confIp
        self.ip = ip
        self.neighbors = neighbors #neighbors structure : [neighbor ID, neighbor Interface, self interface]
    
    def getNeighbors (self):
        return self.neighbors
        
def findIdbyIp (nodeList, ip):
    for nodetsn in nodeList:
        if ((str(nodetsn.ip).rstrip('\n')==str(ip)) or (str(nodetsn.confIp).rstrip('\n')==str(ip))):
            return nodetsn.id
        
def find_values(id, json_repr):
    results = []

    def _decode_dict(a_dict):
        try:
            results.append(a_dict[id])
        except KeyError:
            pass
        return a_dict

    json.loads(json_repr, object_hook=_decode_dict) # Return value ignored.
    return results
