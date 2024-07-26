from .Utils import Utils
from .Events import EventHandler
from .keywords import EntityKeyword

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
    def getDataField(node:dict):
        dataname = EntityKeyword.data
        if not node.keys().__contains__(dataname):
            node.setdefault(dataname, {})
        return node[dataname]

    @staticmethod
    def setTitleOverride(node:dict, overridenodeid:str, newtitle:str):
        data:dict = ImmortalEntity.getDataField(node)
        overidekey = EntityKeyword.overridetitle
        if not data.keys().__contains__(overidekey):
            data.setdefault(overidekey, {})
        overridesection:dict = data[overidekey]
        if not overridesection.keys().__contains__(overridenodeid):
            overridesection.setdefault(overridenodeid, newtitle)
        else:
            overridesection[overridenodeid] = newtitle
        return node

    @staticmethod
    def getTitleOverride(node:dict, overridenodeid)->str:
        defaultTitle = node["Title"]
        data:dict = ImmortalEntity.getDataField(node)
        if not data.keys().__contains__(EntityKeyword.overridetitle):
            return defaultTitle
        overridesection:dict = data[EntityKeyword.overridetitle]
        if not overridesection.keys().__contains__(overridenodeid):
            return defaultTitle
        return overridesection[overridenodeid]

    @staticmethod
    def searchNextNodes(entity, nodeid, context:dict)->list:
        listnode = []
        nodes = entity["Nodes"]
        for nd in nodes:
            ismatched = EventHandler.conditionMapping(nodeid, context, nd)
            # nodeids = ImmortalEntity.getPrevNode(nd)
            # if nodeids.__contains__(nodeid):
            overrideTitle = ImmortalEntity.getTitleOverride(nd, nodeid)
            if ismatched:
                listnode.append({"ID": nd["ID"], "Title":overrideTitle, "Question": nd["Question"]})
        return listnode

    @staticmethod
    def mergeNode(nodea, nodeb):
        # merge prev
        prevlista = ImmortalEntity.getPrevNode(nodea)
        prevlistb = ImmortalEntity.getPrevNode(nodeb)
        joined = set(prevlista + prevlistb)

        # merge data field
        newData = Utils.mergeDict(nodea[EntityKeyword.data], nodeb[EntityKeyword.data])

        nodec = Utils.cloneDict(nodea)
        nodec[EntityKeyword.data] = newData
        for i in joined:
            ImmortalEntity.setPrevNode(nodec, i)

        return nodec