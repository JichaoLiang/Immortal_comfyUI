import os.path
import sys
from . import Utils
# import Utils

class ImmortalConfig:
    base = r"d:\immortaldata"
    basepath = os.path.join(base, "Immortal")
    sucaipath = os.path.join(basepath, r"sucai")
    packpath = os.path.join(basepath, r'package')
    objectStorePath = os.path.join(basepath, "objectstore")

    @staticmethod
    def decisionToPackPath(key):
        fileExists = False
        filepath = key
        try:
            keypath = Utils.getPathById(key)
            fileExists = os.path.exists(keypath)
        except Exception as e:
            fileExists = False
        if fileExists:
            filepath = keypath
        if not os.path.exists(filepath) and not fileExists or os.path.isdir(key):
            return None
        if filepath.__contains__("."):
            extenName = filepath.split(".")[-1].lower()
            imagewhitelist = ["jpg", "png"]
            videowhitelist = ["mp4"]
            audiowhitelist = ["mp3", "wav"]
            if imagewhitelist.__contains__(extenName):
                return "images"
            if videowhitelist.__contains__(extenName):
                return "videos"
            if audiowhitelist.__contains__(extenName):
                return "audios"
        return None
        pass
    pass