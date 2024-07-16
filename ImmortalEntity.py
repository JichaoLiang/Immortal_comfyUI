from .Utils import Utils
from .Events import EventHandler

class ImmortalEntity:
    @staticmethod
    def getEntity():
        entity = {
                      "Properties": {

                      },
                      "Nodes": []
                    }
        return entity

    @staticmethod
    def getNode():
        node = {
                  "ID": "",
                  "Mapping": [],
                  "VideoDataKey": "",
                  "Title": "",
                  "Question": "",
                  "Events": {
                    "OnEnter": [
                    ],
                    "OnLeave": {
                    }
                  },
                  "Data":{
                  },
                  "Temporary":{

                  }
              }
        id = Utils.generateId()
        node["ID"] = id
        return node

    @staticmethod
    def getPrevNode(node)->list:
        print(f"getNode:{node}")
        mapping = node["Mapping"]
        prevKey = ''
        foundparent = False
        for item in mapping:
            if item.keys().__contains__("Parent"):
                prevKey = item["Parent"]
                foundparent = True
        if not foundparent:
            mapping.append({"Parent": ""})
        # if not mapping.keys().__contains__("Parent"):
        #     mapping.setdefault("Parent", [])
        # prevKey = mapping["Parent"]
        if prevKey is None or len(prevKey) == 0:
            return []
        return prevKey.split(',')

    @staticmethod
    def setPrevNode(node, key):
        prevNodes = ImmortalEntity.getPrevNode(node)
        if not prevNodes.__contains__(key):
            prevNodes.append(key)
        mapping = node["Mapping"]
        for item in mapping:
            print(f"item {item}")
            print(f"type of item {type(item)}")
            if item.keys().__contains__("Parent"):
                item["Parent"] = ",".join(prevNodes)
        pass

    @staticmethod
    def getNodeById(entity, nodeid):
        print(f"node:{entity}")
        nodes = entity["Nodes"]
        for nd in nodes:
            if nd["ID"] == nodeid:
                return nd
        return None

    @staticmethod
    def searchNextNodes(entity, nodeid, context:dict)->list:
        listnode = []
        nodes = entity["Nodes"]
        for nd in nodes:
            ismatched = EventHandler.conditionMapping(nodeid, context, nd)
            # nodeids = ImmortalEntity.getPrevNode(nd)
            # if nodeids.__contains__(nodeid):
            if ismatched:
                listnode.append({"ID":nd["ID"],"Title":nd["Title"], "Question":nd["Question"]})
        return listnode

    @staticmethod
    def mergeNode(nodea, nodeb):
        prevlista = ImmortalEntity.getPrevNode(nodea)
        prevlistb = ImmortalEntity.getPrevNode(nodeb)
        joined = set(prevlista + prevlistb)
        nodec = Utils.cloneDict(nodea)
        for i in joined:
            ImmortalEntity.setPrevNode(nodec, i)

        return nodec