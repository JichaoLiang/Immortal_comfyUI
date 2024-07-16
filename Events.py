from . import keywords
from . import ImmortalEntity

class EventBehavior:
    @staticmethod
    def set(field:dict, key:str, value):
        field.setdefault(key, value)
        pass
    @staticmethod
    def increase(field:dict, key:str, value):
        if not field.keys().__contains__(key):
            field.setdefault(key, 0)
        val = field[key]
        field[key] = val + value
        pass

    @staticmethod
    def append(field:dict, key:str, value):
        if not field.keys().__contains__(key):
            field.setdefault(key, [])
        field[key].append(value)
        pass

    @staticmethod
    def remove(field:dict, key:str, value):
        if not field.keys().__contains__(key):
            field.setdefault(key, [])
        val = field[key]
        if val.__contains__(value):
            val.remove(value)
        pass

    @staticmethod
    def gt(field:dict, key:str, value)->bool:
        if not field.keys().__contains__(key):
            return False
        val = field[key]
        return val > value
        pass

    @staticmethod
    def lt(field:dict, key:str, value)->bool:
        if not field.keys().__contains__(key):
            return False
        val = field[key]
        return val < value
        pass
    @staticmethod
    def equal(field:dict, key:str, value)->bool:
        if not field.keys().__contains__(key):
            return False
        val = field[key]
        return val == value
        pass

    @staticmethod
    def contains(field:dict, key:str, value)->bool:
        if not field.keys().__contains__(key):
            return False
        val = field[key]
        return val.__contains__(value)
        pass


class EventHandler:
    Eventsdict = {
        "Set": EventBehavior.set,
        "increase": EventBehavior.increase,
        "append": EventBehavior.append,
        "remove": EventBehavior.remove,
    }

    Conditiondict = {
        "gt": EventBehavior.gt,
        "lt": EventBehavior.lt,
        "equal": EventBehavior.equal,
        "contains": EventBehavior.contains,
    }

    @staticmethod
    def handleEvent(context:dict, nodeevent:list)->dict:
        for item in nodeevent:
            k = item.keys().__iter__().__next__()
            val = item[k]
            var1 = val[0]
            var2 = val[1]
            if EventHandler.Eventsdict.keys().__contains__(k):
                func = EventHandler.Eventsdict[k]
                context = func(context, var1, var2)
        return context
        pass

    @staticmethod
    def conditionMapping(nodeid:str, context:dict, node:dict)->bool:
        mapping:list = node["Mapping"]
        previdlist = ImmortalEntity.ImmortalEntity.getPrevNode(node)
        if previdlist is not None and len(previdlist) > 0:
            if not previdlist.__contains__(nodeid):
                return False
        for item in mapping:
            k = item.keys().__iter__().__next__()
            val = item[k]
            if k == "Parent":
                continue

            var1 = val[0]
            var2 = val[1]
            if EventHandler.Conditiondict.keys().__contains__(k):
                func = EventHandler.Conditiondict[k]
                result = func(context, var1, var2)
                if not result:
                    return False
        return True
        pass