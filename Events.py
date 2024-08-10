from . import keywords
from . import ImmortalEntity

class EventBehavior:
    @staticmethod
    def set(field:dict, var:list):
        key = var[0]
        value = var[1]
        if not field.keys().__contains__(key):
            field.setdefault(key, value)
        # print(f"set: field{field}, with key : {key}, val: {value}")
        else:
            field[key] = value
        # print(f"after set: {field}")
        return field
        pass
    @staticmethod
    def increase(field:dict, var):
        key = var[0]
        value = var[1]
        if not field.keys().__contains__(key):
            field.setdefault(key, 0)
        val = field[key]
        field[key] = val + value
        return field
        pass

    @staticmethod
    def append(field:dict, var):
        key = var[0]
        value = var[1]
        if not field.keys().__contains__(key):
            field.setdefault(key, [])
        field[key].append(value)
        return field
        pass

    @staticmethod
    def remove(field:dict, var):
        key = var[0]
        value = var[1]
        if not field.keys().__contains__(key):
            field.setdefault(key, [])
        val = field[key]
        if val.__contains__(value):
            val.remove(value)
        return field
        pass

    @staticmethod
    def gt(field:dict, var)->bool:
        key = var[0]
        value = var[1]
        if not field.keys().__contains__(key):
            field.setdefault(key, 0)
        val = field[key]
        return val > value
        pass

    @staticmethod
    def lt(field:dict, var)->bool:
        key = var[0]
        value = var[1]
        print(f"lt: field: {field}; key: {key}; value: {value}")
        if not field.keys().__contains__(key):
            field.setdefault(key, 0)
        val = field[key]
        return val < value
        pass
    @staticmethod
    def equal(field:dict, var)->bool:
        key = var[0]
        value = var[1]
        if not field.keys().__contains__(key):
            field.setdefault(key, 0)
        val = field[key]
        return val == value
        pass

    @staticmethod
    def notEqual(field:dict, var)->bool:
        key = var[0]
        value = var[1]
        if not field.keys().__contains__(key):
            field.setdefault(key, 0)
        val = field[key]
        return val != value
        pass

    @staticmethod
    def contains(field:dict, var)->bool:
        key = var[0]
        value = var[1]
        if not field.keys().__contains__(key):
            field.setdefault(key, [])
        val = field[key]
        return val.__contains__(value)
        pass

    @staticmethod
    def notContains(field:dict, var)->bool:
        key = var[0]
        value = var[1]
        if not field.keys().__contains__(key):
            field.setdefault(key, [])
        val = field[key]
        return not val.__contains__(value)
        pass

    @staticmethod
    def And(field:dict, var)->bool:
        key = var[0]
        value = var[1]
        result1:bool = EventHandler.handleCondition(field, key)
        result2:bool = EventHandler.handleCondition(field, value)

        return result1 and result2
        pass


    @staticmethod
    def Or(field:dict, var)->bool:
        key = var[0]
        value = var[1]
        result1:bool = EventHandler.handleCondition(field, key)
        result2:bool = EventHandler.handleCondition(field, value)

        return result1 or result2
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
        "not_equal": EventBehavior.notEqual,
        "contains": EventBehavior.contains,
        "not_contains": EventBehavior.notContains,
        "and": EventBehavior.And,
        "or": EventBehavior.Or
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
                print(f'var1:{var1} var2: {var2}')
                if var1.__eq__(keywords.ContextKeyword.allcustomvalue):
                    keycount = len(context.keys())
                    keys = list(context.keys())
                    for i in range(0, keycount):
                        contextkey = keys[i]
                        if contextkey not in keywords.ContextKeyword.notCustomKeys:
                            context = func(context, [var1, var2])
                else:
                    context = func(context, [var1, var2])
                print(f"after handle: {context}")
        return context
        pass

    @staticmethod
    def handleCondition(context, expression):
        k = expression.keys().__iter__().__next__()
        val = expression[k]
        if k == "Parent":
            return False

        var1 = val[0]
        var2 = val[1]
        if EventHandler.Conditiondict.keys().__contains__(k):
            func = EventHandler.Conditiondict[k]
            result = func(context, val)
            return result
        return False

    @staticmethod
    def conditionMapping(nodeid:str, context:dict, node:dict)->bool:
        mapping:list = node["Mapping"]
        previdlist = ImmortalEntity.ImmortalEntity.getPrevNode(node)
        if previdlist is not None and len(previdlist) > 0:
            if not previdlist.__contains__(nodeid):
                return False
        else:
            # empty mapping, which means root node
            if len(mapping) == 1 and mapping[0].keys().__iter__().__next__() == 'Parent':
                return False
        for item in mapping:
            k = item.keys().__iter__().__next__()
            val = item[k]
            if k == "Parent":
                continue
            result = EventHandler.handleCondition(context,item)
            if not result:
                return False
            # var1 = val[0]
            # var2 = val[1]
            # if EventHandler.Conditiondict.keys().__contains__(k):
            #     func = EventHandler.Conditiondict[k]
            #     result = func(context, val)
            #     if not result:
            #         return False
        return True
        pass