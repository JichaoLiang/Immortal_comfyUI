import json
import random
import shutil
import time
import os
from pathlib import Path
# from config import ImmortalConfig
from .config import ImmortalConfig


class Utils:
    @staticmethod
    def setObjectStoreKey(key, val):
        path = Utils.getPathByObjectStoreKey(key)
        exists = False
        if os.path.exists(path):
            exists = True
            os.remove(path)
        with open(path,"w", encoding='utf-8') as f:
            f.write(val)
        return exists

    @staticmethod
    def getObjectStoreKey(key):
        path = Utils.getPathByObjectStoreKey(key)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                value = f.read()
                return value
        else:
            return None
    @staticmethod
    def objectStorekeyExists(key):
        path = Utils.getPathByObjectStoreKey(key)
        return os.path.exists(path)

    @staticmethod
    def getPathByObjectStoreKey(key):
        path = os.path.join(ImmortalConfig.objectStorePath, key)
        return path

    @staticmethod
    def tryExtractPathByKey(keyMaybe):
        keypath = keyMaybe
        try:
            print(keypath)
            keypath = Utils.getPathById(id=keypath)
            print(keypath)
        except Exception as e:
            print(e)
            pass
        filepath = keypath
        return filepath

    @staticmethod
    def writetempfile(content):
        id, path = Utils.generatePathId(namespace='temp', exten='txt')
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return id, path

    @staticmethod
    def mkdir(path):
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
            os.makedirs(dir)

    @staticmethod
    def generatePathId(basepath=ImmortalConfig.basepath, namespace="Immortal", exten=None):
        fnow = time.time()
        intNow = int(fnow * 1000)
        milliSec = intNow % 1000
        now = time.localtime(fnow)
        id = f'{namespace}_{now.tm_year}_{now.tm_mon}_{now.tm_mday}_{now.tm_hour}_{now.tm_min}_{now.tm_sec}_{milliSec}'
        if exten is not None:
            id += "." + exten
        destPath = os.path.join(basepath, f'{namespace}/{now.tm_year}_{now.tm_mon}/{now.tm_mday}/{id}')
        # destDir = os.path.dirname(destPath)
        # if not Path(destPath).exists():
        #     os.makedirs(destPath)
        time.sleep(0.001)
        return id, destPath

    @staticmethod
    def getPathById(basepath=ImmortalConfig.basepath, id: str = None):
        tokens = id.split('_')
        namespace = tokens[0]
        year = tokens[1]
        mon = tokens[2]
        mday = tokens[3]
        hour = tokens[4]
        min = tokens[5]
        sec = tokens[6]
        mill = tokens[7].split('.')[0]

        destpath = os.path.join(basepath,
                                f'{namespace}/{year}_{mon}/{mday}/{id}')
        # if len(id.split('.')) > 1:
        #     exten = id.split('.')[-1]
        #     destpath += '.' + exten
        return destpath

    @staticmethod
    def generateId(namespace="immortal"):
        fnow = time.time()
        intNow = int(fnow * 1000)
        milliSec = intNow % 1000
        now = time.localtime(fnow)
        id = f'{namespace}_{now.tm_year}_{now.tm_mon}_{now.tm_mday}_{now.tm_hour}_{now.tm_min}_{now.tm_sec}_{milliSec}'
        return id
    @staticmethod
    def randomPick(length):
        rand = random.Random()
        value = rand.random()
        return int(value * length)
    pass
    @staticmethod
    def cloneDict(dict:dict):
        dumps = json.dumps(dict)
        newDict = json.loads(dumps)
        return newDict

    @staticmethod
    def removeFileByKey(key:str):
        path = Utils.getPathById(id=key)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
        pass

    @staticmethod
    def isJsonString(string):
        try:
            json.loads(string)
            return True
        except json.decoder.JSONDecodeError:
            return False
        return True
