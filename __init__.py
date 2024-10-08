# import sys
#
# sys.path.append('/Entity/')
# sys.path.append('/Moviemaker/')
import hashlib
import traceback
import numpy as np
import PIL
from PIL import Image
# from PIL.Image import Image
from PIL.PngImagePlugin import PngInfo
from moviepy.video.io import VideoFileClip

import folder_paths
from . import ImmortalAgent
import json
import os.path
import shutil

from .Utils import Utils
from .config import ImmortalConfig
from .ImmortalEntity import ImmortalEntity, NodeType
from .Wav2lipCli import Wav2lipCli
from .OllamaCli import OllamaCli
from .Events import EventHandler

from . import MovieMakerUtils
from . import TTSUtils
from .keywords import ContextKeyword, EntityKeyword


class ImmortalNodes:
    """
    A example node

    Class methods
    -------------
    INPUT_TYPES (dict):
        Tell the main program input parameters of nodes.
    IS_CHANGED:
        optional method to control when the node is re executed.

    Attributes
    ----------
    RETURN_TYPES (`tuple`):
        The type of each element in the output tulple.
    RETURN_NAMES (`tuple`):
        Optional: The name of each output in the output tulple.
    FUNCTION (`str`):
        The name of the entry-point method. For example, if `FUNCTION = "execute"` then it will run Example().execute()
    OUTPUT_NODE ([`bool`]):
        If this node is an output node that outputs a result/image from the graph. The SaveImage node is an example.
        The backend iterates on these output nodes and tries to execute all their parents if their parent graph is properly connected.
        Assumed to be False if not present.
    CATEGORY (`str`):
        The category the node should appear in the UI.
    execute(s) -> tuple || None:
        The entry point method. The name of this method must be the same as the value of property `FUNCTION`.
        For example, if `FUNCTION = "execute"` then this method's name must be `execute`, if `FUNCTION = "foo"` then it must be `foo`.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        """
            Return a dictionary which contains config for all input fields.
            Some types (string): "MODEL", "VAE", "CLIP", "CONDITIONING", "LATENT", "IMAGE", "INT", "STRING", "FLOAT".
            Input types "INT", "STRING" or "FLOAT" are special values for fields on the node.
            The type can be a list for selection.

            Returns: `dict`:
                - Key input_fields_group (`string`): Can be either required, hidden or optional. A node class must have property `required`
                - Value input_fields (`dict`): Contains input fields config:
                    * Key field_name (`string`): Name of a entry-point method's argument
                    * Value field_config (`tuple`):
                        + First value is a string indicate the type of field or a list for selection.
                        + Secound value is a config for type "INT", "STRING" or "FLOAT".
        """
        return {
            "required": {
                "image": ("IMAGE",),
                "int_field": ("INT", {
                    "default": 0,
                    "min": 0,  # Minimum value
                    "max": 4096,  # Maximum value
                    "step": 64,  # Slider's step
                    "display": "number"  # Cosmetic only: display as "number" or "slider"
                }),
                "float_field": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.01,
                    "round": 0.001,
                    # The value represeting the precision to round to, will be set to the step value by default. Can be set to False to disable rounding.
                    "display": "number"}),
                "print_to_screen": (["enable", "disable"],),
                "string_field": ("STRING", {
                    "multiline": False,  # True if you want the field to look like the one on the ClipTextEncode node
                    "default": "Hello World!"
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    # RETURN_NAMES = ("image_output_name",)

    FUNCTION = "test"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def test(self, image, string_field, int_field, float_field, print_to_screen):
        if print_to_screen == "enable":
            print(f"""Your input contains:
                string_field aka input text: {string_field}
                int_field: {int_field}
                float_field: {float_field}
            """)
        # do some processing on the image, in this example I just invert it
        image = 1.0 - image
        return (image,)

    """
        The node will always be re executed if any of the inputs change but
        this method can be used to force the node to execute again even when the inputs don't change.
        You can make this node return a number or a string. This value will be compared to the one returned the last time the node was
        executed, if it is different the node will be executed again.
        This method is used in the core repo for the LoadImage node where they return the image hash as a string, if the image hash
        changes between executions the LoadImage node is executed again.
    """
    # @classmethod
    # def IS_CHANGED(s, image, string_field, int_field, float_field, print_to_screen):
    #    return ""


# Set the web directory, any .js file in that directory will be loaded by the frontend as a frontend extension
# WEB_DIRECTORY = "./somejs"

# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique

class ApplyVoiceConversion:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "sceneEntity": ("IMMORTALENTITY",)
            }
        }
        pass

    RETURN_TYPES = ("IMMORTALENTITY",)
    # RETURN_NAMES = ("image_output_name",)

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def applyVC(self, node: dict):
        if node.keys().__contains__("Temporary"):
            temporay: dict = node["Temporary"]
            if temporay.keys().__contains__("VCTask") and len(temporay["VCTask"].keys()) > 0:
                inputvideokey = temporay["VCTask"]["inputvideokey"]
                voicePath = temporay["VCTask"]["voicepath"]

                print(f"vc: videokey: {inputvideokey}")
                _, sourceaudio = Utils.generatePathId(namespace="temp", exten="wav")
                clip = VideoFileClip.VideoFileClip(Utils.getPathById(id=inputvideokey))
                audio = clip.audio
                if audio is None:
                    return None, None
                audio.write_audiofile(sourceaudio)
                return sourceaudio, voicePath
        return None, None

    def process(self, sceneEntity):
        nodes = sceneEntity["Nodes"]
        idlist = []
        sourcelist = []
        speakerlist = []
        for node in nodes:
            source, dest = self.applyVC(node)
            if source is None:
                continue
            idlist.append(node['ID'])
            sourcelist.append(source)
            speakerlist.append(dest)
        resultlist = Wav2lipCli.xtts_vc(sourcelist, speakerlist)
        for i in range(0, len(idlist)):
            node = ImmortalEntity.getNodeById(sceneEntity, idlist[i])
            videopath = Utils.getPathById(id=node["VideoDataKey"])
            source: str = sourcelist[i]
            dest = resultlist[i]
            fid, fpath = ImmortalAgent.ImmortalAgent.replaceAudio(videopath, dest)

            # erase task
            node["Temporary"].pop("VCTask")
            # if os.path.exists(source):
            #     os.remove(source)
            node["VideoDataKey"] = fid
        newEntity = Utils.cloneDict(sceneEntity)
        return (newEntity,)
        pass


class ImDumpNode:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "sceneEntity": ("IMMORTALENTITY",),
                "pointer": ("NODE",)
            }
        }
        pass

    RETURN_TYPES = ("STRING",)
    # RETURN_NAMES = ("image_output_name",)

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, sceneEntity, pointer):
        node = ImmortalEntity.getNodeById(sceneEntity, pointer)
        jsstr = json.dumps(node)
        return (jsstr,)
        pass


class ImDumpEntity:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "sceneEntity": ("IMMORTALENTITY",)
            }
        }
        pass

    RETURN_TYPES = ("STRING",)
    # RETURN_NAMES = ("image_output_name",)

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, sceneEntity):
        jsstr = json.dumps(sceneEntity)
        return (jsstr,)
        pass


class ImApplyWav2lip:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "sceneEntity": ("IMMORTALENTITY",),
                "use": (["musetalk", "wav2lip"], {"default": "musetalk"}),
            }
        }
        pass

    RETURN_TYPES = ("IMMORTALENTITY",)
    # RETURN_NAMES = ("image_output_name",)

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def applyVA(self, node: dict):
        if node.keys().__contains__("Temporary"):
            temporay: dict = node["Temporary"]
            if temporay.keys().__contains__("wav2lip") and len(temporay["wav2lip"].keys()) > 0:
                inputvideokey = temporay["wav2lip"]["inputvideokey"]
                voicePath = temporay["wav2lip"]["voicepath"]
                videopath = Utils.getPathById(id=inputvideokey)
                return videopath, voicePath
        return None, None

    def process(self, sceneEntity, use="musetalk"):
        nodes = sceneEntity["Nodes"]
        idlist = []
        videolist = []
        voicelist = []
        for node in nodes:
            source, dest = self.applyVA(node)
            if source is None:
                continue
            idlist.append(node['ID'])
            videolist.append(source)
            voicelist.append(dest)
        resultidlist, resultPathlist = Wav2lipCli.convert_batch(videolist, voicelist, use)
        for i in range(0, len(idlist)):
            node = ImmortalEntity.getNodeById(sceneEntity, idlist[i])
            videopath = Utils.getPathById(id=node["VideoDataKey"])
            source: str = videolist[i]
            fid = resultidlist[i]

            # erase task
            node["Temporary"].pop("wav2lip")
            # if os.path.exists(source):
            #     os.remove(source)
            node["VideoDataKey"] = fid
        newEntity = Utils.cloneDict(sceneEntity)
        return (newEntity,)
        pass


class ImAppendVideoNode:
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = []
        for f in os.listdir(input_dir):
            if os.path.isfile(os.path.join(input_dir, f)):
                file_parts = f.split('.')
                if len(file_parts) > 1 and (file_parts[-1] in ['webm', 'mp4', 'mkv', 'gif']):
                    files.append(f)

        result = {"required": {
            "video": ("PATH",),
            "entity": ("IMMORTALENTITY",),
            "text": ("STRING", {"default": "", 'multiline': True}),
            "title": ("STRING", {"default": ""}),
            "question": ("STRING", {"default": ""}),
            "autoRoot": (["YES", "NO"], {"default": "YES"}),
            "enableTTS": (["YES", "NO"], {"default": "YES"}),
            "disabled": (["YES", "NO"], {"default": "NO"}),
        },
            "optional": {
                "nodepointer": ("NODE",),
                "extraNodes": ("NODES", {"default": []}),
                "ttsvoicepath": ("STRING", {"default": ""}),
                "wav2lip": (["YES", "NO"], {"default": "YES"}),
                "generatedid": ("STRING", {"default": ""}),
                "settings": ("STRING", {"default": "{ \"voiceid\": \"xujiang\" }"})
            },
        }
        return result

    CATEGORY = "Immortal"

    RETURN_TYPES = ("IMMORTALENTITY", "NODE")
    RETURN_NAMES = ("entity", "pointer")

    FUNCTION = "process"

    def process(self, video, entity, text, title, question, autoRoot, enableTTS, nodepointer=None, extraNodes=[],
                ttsvoicepath=None, wav2lip="NO", generatedid="", settings="", disabled="NO"):
        settings = json.loads(settings)
        node = ImmortalEntity.getNode()
        generatedid = node["ID"]
        if nodepointer is None or len(nodepointer) == 0:
            if autoRoot == "YES":
                entity["Properties"]["root"] = node["ID"]
        else:
            ImmortalEntity.setPrevNode(node, nodepointer)
            if extraNodes is not None and len(extraNodes) > 0:
                for nd in [ImmortalEntity.getNodeById(entity, n) for n in extraNodes]:
                    ImmortalEntity.setPrevNode(node, nd["ID"])

        # set video
        id, path = Utils.generatePathId(namespace="temp", exten='mp4')
        Utils.mkdir(path)
        shutil.copyfile(video, path)

        if enableTTS == "YES":
            ttsid, ttsPath = Utils.generatePathId(namespace="temp", exten='wav')
            ttsdir = os.path.dirname(ttsPath)
            if not os.path.exists(ttsdir):
                os.makedirs(ttsdir)
            # TTSUtils.TTSUtils.ChatTTS_with_break(text, ttsPath)

            # if settings.keys().__contains__(EntityKeyword.ttsspeakerid):
            #     speaker = settings[EntityKeyword.ttsspeakerid]
            #     TTSUtils.TTSUtils.cosvoiceTTS(text, ttsPath, speaker)
            # else:
            #     TTSUtils.TTSUtils.cosvoiceTTS(text, ttsPath)
            TTSUtils.TTSUtils.cosvoiceTTS_buildin_speaker(text, ttsPath)
            MovieMakerUtils.MovieMakerUtils.resamplewav(ttsPath, 22050)

            duration = MovieMakerUtils.MovieMakerUtils.get_wav_duration(ttsPath)
            id, path = ImmortalAgent.ImmortalAgent.replaceAudio(path, ttsPath)

        nodetemp = node["Temporary"]
        # book tasks
        if ttsvoicepath is not None and len(ttsvoicepath) > 0:
            nodetemp.setdefault("VCTask", {"inputvideokey": id, "voicepath": ttsvoicepath})

        if wav2lip == "YES":
            _, voicepath = Utils.generatePathId(namespace="temp", exten="wav")
            clip = VideoFileClip.VideoFileClip(path)
            audio = clip.audio
            audio.write_audiofile(voicepath)
            nodetemp.setdefault("wav2lip", {"inputvideokey": id, "voicepath": voicepath})

        node["VideoDataKey"] = id
        node["Title"] = title  # .encode('utf-8')
        node["Question"] = question  # .encode('utf-8')
        node["Text"] = text  # .encode('utf-8')

        entity['Nodes'].append(node)

        nodeid = node['ID']
        if disabled == 'YES':
            entity = ImmortalEntity.SetContext(entity, ImmortalEntity.getDisableKey(nodeid), 1)
        newEntity = Utils.cloneDict(entity)

        # return (newEntity,)
        return newEntity, nodeid
        pass


class CombineVideos:
    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
            "video0": ("PATH",),
        },
            "optional": {
                "video1": ("PATH",),
                "video2": ("PATH",),
                "video3": ("PATH",),
                "video4": ("PATH",),
                "video5": ("PATH",),
            }
        }

    CATEGORY = "Immortal"

    RETURN_TYPES = ("VIDEOS",)
    RETURN_NAMES = ("videos",)

    FUNCTION = "process"

    def process(self, video0, video1=None, video2=None, video3=None, video4=None, video5=None):
        list = [video0, video1, video2, video3, video4, video5]
        print(list)
        return ([l for l in list if l is not None],)
        pass


class ImAppendFreeChatAction:
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = []
        for f in os.listdir(input_dir):
            if os.path.isfile(os.path.join(input_dir, f)):
                file_parts = f.split('.')
                if len(file_parts) > 1 and (file_parts[-1] in ['webm', 'mp4', 'mkv', 'gif']):
                    files.append(f)
        return {"required": {
            "video": ("PATH",),
            "entity": ("IMMORTALENTITY",),
            "text": ("STRING", {"default": ""}),
            "title": ("STRING", {"default": ""}),
            "question": ("STRING", {"default": ""}),
            "action": (["DefaultFreeChat"], {"default": "DefaultFreeChat"}),
            "prompt": ("STRING", {
                "default": "[{\"role\":\"system\",\"content\":\"请扮演一个角色，以这个角色的口吻，和我聊天，千万不要出戏，只回复角色应该说的话本身: 背景介绍：你是我失散已久的妹妹。\"}]"}),
            "videotemplatelist": ("VIDEOS", {"default": []}),
            "autoRoot": (["YES", "NO"], {"default": "YES"}),
            "enableTTS": (["YES", "NO"], {"default": "YES"}),
        },
            "optional": {
                "nodepointer": ("NODE",),
                "extraNodes": ("NODES", {"default": []}),
                "ttsvoicepath": ("STRING", {"default": ""}),
                "wav2lip": (["YES", "NO"], {"default": "YES"}),
                "generatedid": ("STRING", {"default": ""}),
                "settings": ("STRING", {"default": "{ \"voiceid\": \"xujiang\" }"})
            },
        }

    CATEGORY = "Immortal"

    RETURN_TYPES = ("IMMORTALENTITY", "NODE")
    RETURN_NAMES = ("entity", "pointer")

    FUNCTION = "process"

    def process(self, video, entity, text, title, question, action, prompt, videotemplatelist, autoRoot, enableTTS,
                nodepointer=None, extraNodes=[], ttsvoicepath=None, wav2lip="NO", generatedid="", settings=""):
        print(f'videotemplatelist: {videotemplatelist}')
        settings = json.loads(settings)
        node = ImmortalEntity.getNode()
        generatedid = node["ID"]
        if nodepointer is None or len(nodepointer) == 0:
            if autoRoot == "YES":
                entity["Properties"]["root"] = node["ID"]
        else:
            ImmortalEntity.setPrevNode(node, nodepointer)
            if extraNodes is not None and len(extraNodes) > 0:
                for nd in [ImmortalEntity.getNodeById(entity, n) for n in extraNodes]:
                    ImmortalEntity.setPrevNode(node, nd["ID"])

        # set video
        id, path = Utils.generatePathId(namespace="temp", exten='mp4')
        Utils.mkdir(path)
        shutil.copyfile(video, path)

        if enableTTS == "YES":
            ttsid, ttsPath = Utils.generatePathId(namespace="temp", exten='wav')
            ttsdir = os.path.dirname(ttsPath)
            if not os.path.exists(ttsdir):
                os.makedirs(ttsdir)
            # TTSUtils.TTSUtils.ChatTTS_with_break(text, ttsPath)

            # if settings.keys().__contains__(EntityKeyword.ttsspeakerid):
            #     speaker = settings[EntityKeyword.ttsspeakerid]
            #     TTSUtils.TTSUtils.cosvoiceTTS(text, ttsPath, speaker)
            # else:
            #     TTSUtils.TTSUtils.cosvoiceTTS(text, ttsPath)
            TTSUtils.TTSUtils.cosvoiceTTS_buildin_speaker(text, ttsPath)
            MovieMakerUtils.MovieMakerUtils.resamplewav(ttsPath, 22050)

            duration = MovieMakerUtils.MovieMakerUtils.get_wav_duration(ttsPath)
            id, path = ImmortalAgent.ImmortalAgent.replaceAudio(path, ttsPath)

        nodetemp = node["Temporary"]
        # book tasks
        if ttsvoicepath is not None and len(ttsvoicepath) > 0:
            nodetemp.setdefault("VCTask", {"inputvideokey": id, "voicepath": ttsvoicepath})

        if wav2lip == "YES":
            _, voicepath = Utils.generatePathId(namespace="temp", exten="wav")
            clip = VideoFileClip.VideoFileClip(path)
            audio = clip.audio
            audio.write_audiofile(voicepath)
            nodetemp.setdefault("wav2lip", {"inputvideokey": id, "voicepath": voicepath})

        node["VideoDataKey"] = id
        node["Title"] = title  # .encode('utf-8')
        node["Question"] = question  # .encode('utf-8')
        node["Text"] = text  # .encode('utf-8')
        node["Action"] = action
        data: dict = ImmortalEntity.getDataField(node)
        data[EntityKeyword.voiceId] = settings
        data.setdefault("Prompt", prompt)
        if len(videotemplatelist) == 0:
            raise Exception("at least one video template required.")
        data.setdefault("VideoTemplateList", videotemplatelist)

        entity['Nodes'].append(node)

        newEntity = Utils.cloneDict(entity)
        # return (newEntity,)
        return newEntity, node['ID']
        pass


class ImAppendQuickbackVideoNode:
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = []
        for f in os.listdir(input_dir):
            if os.path.isfile(os.path.join(input_dir, f)):
                file_parts = f.split('.')
                if len(file_parts) > 1 and (file_parts[-1] in ['webm', 'mp4', 'mkv', 'gif']):
                    files.append(f)
        return {"required": {
            "video": ("PATH",),
            "entity": ("IMMORTALENTITY",),
            "text": ("STRING", {"default": ""}),
            "title": ("STRING", {"default": ""}),
            "question": ("STRING", {"default": ""}),
            "autoRoot": (["YES", "NO"], {"default": "YES"}),
            "enableTTS": (["YES", "NO"], {"default": "YES"}),
            "disabled": (["YES", "NO"], {"default": "NO"}),
        },
            "optional": {
                "nodepointer": ("NODE",),
                "extraNodes": ("NODES", {"default": []}),
                "ttsvoicepath": ("STRING", {"default": ""}),
                "wav2lip": (["YES", "NO"], {"default": "YES"}),
                "overrideBackTitle": ("STRING", {"default": ""}),
                "generatedid": ("STRING", {"default": ""}),
                "settings": ("STRING", {"default": "{ \"voiceid\": \"xujiang\" }"})
            },
        }

    CATEGORY = "Immortal"

    RETURN_TYPES = ("IMMORTALENTITY", "NODE", "NODE")
    RETURN_NAMES = ("entity", "childpointer", "parentpointer")

    FUNCTION = "process"

    def process(self, video, entity, text, title, question, autoRoot, enableTTS, nodepointer=None, extraNodes=[],
                ttsvoicepath=None, wav2lip="NO", overrideBackTitle=None, generatedid="", settings="", disabled="NO"):
        videonode = ImAppendVideoNode()
        ett, childpointer = videonode.process(video, entity, text, title, question, autoRoot, enableTTS, nodepointer,
                                              extraNodes, ttsvoicepath, wav2lip, generatedid, settings, disabled)

        redirectnode = redirectToNode()
        ett, parentpointer = redirectnode.process(ett, childpointer, nodepointer)
        for extranode in extraNodes:
            ett, _ = redirectnode.process(ett, childpointer, extranode)
        if overrideBackTitle is not None and len(overrideBackTitle) > 0:
            overridenode = ImNodeTitleOverride()
            ett, parentpointer = overridenode.process(ett, childpointer, parentpointer, overrideBackTitle)
            for extranode in extraNodes:
                ett, _ = overridenode.process(ett, extranode, childpointer, overrideBackTitle)
        # return (newEntity,)
        return ett, childpointer, parentpointer
        pass


class ImAppendNode:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        # input_dir = config.ImmortalConfig.sucaipath
        input_dir = folder_paths.get_input_directory()
        files = [item.replace(input_dir + '\\', '').replace('\\', '/') for item in
                 Utils.listAllFilesInSubFolder(input_dir)]
        # files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {
                "entity": ("IMMORTALENTITY",),
                "image": (sorted(files), {"image_upload": True}),
                "text": ("STRING", {"default": "", 'multiline': True}),
                "title": ("STRING", {"default": ""}),
                "question": ("STRING", {"default": ""}),
                "ttsvoicepath": ("STRING", {"default": ""}),
                "autoRoot": (["YES", "NO"], {"default": "YES"}),
                "skipTalk": (["YES", "NO"], {"default": "NO"}),
                "enableCache": (["YES", "NO"], {"default": "YES"}),
                "disabled": (["YES", "NO"], {"default": "NO"}),
            },
            "optional": {
                "nodepointer": ("NODE",),
                "extraNodes": ("NODES", {"default": []}),
                "settings": ("STRING", {"default": "{ \"voiceid\": \"xujiang\" }"})
            }
        }
        pass

    RETURN_TYPES = ("IMMORTALENTITY", "NODE")
    RETURN_NAMES = ("entity", "pointer")

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, entity, image, text, title, question, ttsvoicepath, autoRoot, skipTalk, enableCache,
                nodepointer=None, extraNodes=[], settings=None, disabled="NO"):
        settings = json.loads(settings)
        node = ImmortalEntity.getNode()
        if nodepointer is None or len(nodepointer) == 0:
            if autoRoot == "YES":
                entity["Properties"]["root"] = node["ID"]
        else:
            ImmortalEntity.setPrevNode(node, nodepointer)
            if extraNodes is not None and len(extraNodes) > 0:
                for nd in [ImmortalEntity.getNodeById(entity, n) for n in extraNodes]:
                    ImmortalEntity.setPrevNode(node, nd["ID"])
        # md5Cache
        obj = {"node": "ImAppendNode", "image": image, "text": text, "title": title, "question": question,
               "autoRoot": autoRoot, "skipTalk": skipTalk}
        md5 = hashlib.md5(json.dumps(obj).encode('utf-8')).hexdigest()
        keyExists = Utils.objectStorekeyExists(md5)
        if keyExists and enableCache == "YES":
            id = Utils.getObjectStoreKey(md5)
        else:
            ttsid, ttsPath = Utils.generatePathId(namespace="temp", exten='wav')
            ttsdir = os.path.dirname(ttsPath)
            if not os.path.exists(ttsdir):
                os.makedirs(ttsdir)
            properties = entity["Properties"]
            # if properties.keys().__contains__(EntityKeyword.ttsvoiceseed):
            #     voiceseed = properties[EntityKeyword.ttsvoiceseed]
            #     TTSUtils.TTSUtils.ChatTTS_with_break(text, ttsPath, voiceid=int(voiceseed))
            # TTSUtils.TTSUtils.ChatTTS_with_break(text, ttsPath)

            # if settings.keys().__contains__(EntityKeyword.ttsspeakerid):
            #     speaker = settings[EntityKeyword.ttsspeakerid]
            #     TTSUtils.TTSUtils.cosvoiceTTS(text, ttsPath, speaker)
            # else:
            #     TTSUtils.TTSUtils.cosvoiceTTS(text, ttsPath)
            TTSUtils.TTSUtils.cosvoiceTTS_buildin_speaker(text, ttsPath)
            MovieMakerUtils.MovieMakerUtils.resamplewav(ttsPath, 22050)

            duration = MovieMakerUtils.MovieMakerUtils.get_wav_duration(ttsPath)

            imagePath = os.path.join(folder_paths.get_input_directory(), image)
            id, path = Utils.generatePathId(namespace="temp", exten='mp4')
            print(type(image))
            print(f"image: {image}")
            MovieMakerUtils.MovieMakerUtils.imageToVideo(imagePath, duration=duration, to=path)
            if skipTalk == "NO":
                # replace with no skip mode
                id, generatedPath = ImmortalAgent.ImmortalAgent.replaceAudio(path, ttsPath)
            else:
                id, generatedPath = ImmortalAgent.ImmortalAgent.replaceAudio(path, ttsPath)
            Utils.setObjectStoreKey(md5, id)

        node["VideoDataKey"] = id
        node["Title"] = title  # .encode('utf-8')
        node["Question"] = question  # .encode('utf-8')
        node["Text"] = text  # .encode('utf-8')
        data = ImmortalEntity.getDataField(node)
        data[EntityKeyword.voiceId] = settings
        entity['Nodes'].append(node)

        nodeid = node['ID']
        if disabled == 'YES':
            entity = ImmortalEntity.SetContext(entity, ImmortalEntity.getDisableKey(nodeid), 1)

        nodetemp = node["Temporary"]
        # book tasks
        if ttsvoicepath is not None and len(ttsvoicepath) > 0:
            nodetemp.setdefault("VCTask", {"inputvideokey": id, "voicepath": ttsvoicepath})

        newEntity = Utils.cloneDict(entity)
        # return (newEntity,)
        return newEntity, nodeid
        pass


class ImAppendImageActionNode:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        # input_dir = config.ImmortalConfig.sucaipath
        input_dir = folder_paths.get_input_directory()
        files = [item.replace(input_dir + '\\', '').replace('\\', '/') for item in
                 Utils.listAllFilesInSubFolder(input_dir)]
        # files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {
                "entity": ("IMMORTALENTITY",),
                "image": (sorted(files), {"image_upload": True}),
                "text": ("STRING", {"default": "", 'multiline': True}),
                "title": ("STRING", {"default": ""}),
                "question": ("STRING", {"default": ""}),
                "action": (["DefaultImageFreeChat"], {"default": "DefaultImageFreeChat"}),
                "prompt": ("STRING", {
                    "default": "[{\"role\":\"system\",\"content\":\"请扮演一个角色，以这个角色的口吻，和我聊天，千万不要出戏，只回复角色应该说的话本身: 背景介绍：你是我失散已久的妹妹。\"}]"}),
                "extraimagetemplatelist": ("IMAGE",),
                "ttsvoicepath": ("STRING", {"default": ""}),
                "autoRoot": (["YES", "NO"], {"default": "YES"}),
                "skipTalk": (["YES", "NO"], {"default": "NO"}),
                "enableCache": (["YES", "NO"], {"default": "YES"}),
                "disabled": (["YES", "NO"], {"default": "NO"}),
            },
            "optional": {
                "nodepointer": ("NODE",),
                "extraNodes": ("NODES", {"default": []}),
                "settings": ("STRING", {"default": "{ \"voiceid\": \"xujiang\" }"})
            }
        }
        pass

    RETURN_TYPES = ("IMMORTALENTITY", "NODE")
    RETURN_NAMES = ("entity", "pointer")

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, entity, image, text, title, question, action, prompt, extraimagetemplatelist, ttsvoicepath,
                autoRoot, skipTalk, enableCache,
                nodepointer=None, extraNodes=[], settings=None, disabled="NO"):
        settings = json.loads(settings)
        node = ImmortalEntity.getNode()
        if nodepointer is None or len(nodepointer) == 0:
            if autoRoot == "YES":
                entity["Properties"]["root"] = node["ID"]
        else:
            ImmortalEntity.setPrevNode(node, nodepointer)
            if extraNodes is not None and len(extraNodes) > 0:
                for nd in [ImmortalEntity.getNodeById(entity, n) for n in extraNodes]:
                    ImmortalEntity.setPrevNode(node, nd["ID"])
        # md5Cache
        obj = {"node": "ImAppendNode", "image": image, "text": text, "title": title, "question": question,
               "autoRoot": autoRoot, "skipTalk": skipTalk}
        md5 = hashlib.md5(json.dumps(obj).encode('utf-8')).hexdigest()
        keyExists = Utils.objectStorekeyExists(md5)
        if keyExists and enableCache == "YES":
            id = Utils.getObjectStoreKey(md5)
        else:
            ttsid, ttsPath = Utils.generatePathId(namespace="temp", exten='wav')
            ttsdir = os.path.dirname(ttsPath)
            if not os.path.exists(ttsdir):
                os.makedirs(ttsdir)
            properties = entity["Properties"]
            # if properties.keys().__contains__(EntityKeyword.ttsvoiceseed):
            #     voiceseed = properties[EntityKeyword.ttsvoiceseed]
            #     TTSUtils.TTSUtils.ChatTTS_with_break(text, ttsPath, voiceid=int(voiceseed))
            # TTSUtils.TTSUtils.ChatTTS_with_break(text, ttsPath)

            # if settings.keys().__contains__(EntityKeyword.ttsspeakerid):
            #     speaker = settings[EntityKeyword.ttsspeakerid]
            #     TTSUtils.TTSUtils.cosvoiceTTS(text, ttsPath, speaker)
            # else:
            #     TTSUtils.TTSUtils.cosvoiceTTS(text, ttsPath)
            TTSUtils.TTSUtils.cosvoiceTTS_buildin_speaker(text, ttsPath)
            MovieMakerUtils.MovieMakerUtils.resamplewav(ttsPath, 22050)

            duration = MovieMakerUtils.MovieMakerUtils.get_wav_duration(ttsPath)

            imagePath = os.path.join(folder_paths.get_input_directory(), image)
            id, path = Utils.generatePathId(namespace="temp", exten='mp4')
            print(type(image))
            print(f"image: {image}")
            MovieMakerUtils.MovieMakerUtils.imageToVideo(imagePath, duration=duration, to=path)
            if skipTalk == "NO":
                # replace with no skip mode
                id, generatedPath = ImmortalAgent.ImmortalAgent.replaceAudio(path, ttsPath)
            else:
                id, generatedPath = ImmortalAgent.ImmortalAgent.replaceAudio(path, ttsPath)
            Utils.setObjectStoreKey(md5, id)

        node["VideoDataKey"] = id
        node["Title"] = title  # .encode('utf-8')
        node["Question"] = question  # .encode('utf-8')
        node["Text"] = text  # .encode('utf-8')
        node["Action"] = action

        data = ImmortalEntity.getDataField(node)
        data[EntityKeyword.voiceId] = settings
        data.setdefault("Prompt", prompt)
        if len(extraimagetemplatelist) == 0:
            raise Exception("at least one video template required.")

        imglist = []
        for (batch_number, image) in enumerate(extraimagetemplatelist):
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            imgid, imgpath = Utils.generatePathId(namespace="temp", exten='png')
            img.save(imgpath, pnginfo=None, compress_level=4)
            imglist.append(imgpath)
        data.setdefault("ImageTemplateList", imglist)

        entity['Nodes'].append(node)

        nodeid = node['ID']
        if disabled == 'YES':
            entity = ImmortalEntity.SetContext(entity, ImmortalEntity.getDisableKey(nodeid), 1)

        nodetemp = node["Temporary"]
        # book tasks
        if ttsvoicepath is not None and len(ttsvoicepath) > 0:
            nodetemp.setdefault("VCTask", {"inputvideokey": id, "voicepath": ttsvoicepath})

        newEntity = Utils.cloneDict(entity)
        # return (newEntity,)
        return newEntity, nodeid
        pass


class ImSetActionKeywordMapping:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "entity": ("IMMORTALENTITY",),
                "nodepointer": ("NODE",),
                "keyword_1": ("STRING", {"default": "[choice_1]"}),
                "mappingnode_1": ("NODE",),
            },
            "optional": {
                "keyword_2": ("STRING", {"default": "[choice_2]"}),
                "mappingnode_2": ("NODE",),
                "keyword_3": ("STRING", {"default": "[choice_3]"}),
                "mappingnode_3": ("NODE",)
            }
        }

        pass

    RETURN_TYPES = ("IMMORTALENTITY", "NODE", "NODE", "NODE", "NODE")
    RETURN_NAMES = ("entity", "actionpointer", "choice1pointer", "choice2pointer", "choice3pointer")

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, entity, nodepointer, keyword_1, mappingnode_1, keyword_2=None, mappingnode_2=None, keyword_3=None,
                mappingnode_3=None):
        node = ImmortalEntity.getNodeById(entity, nodepointer)

        # not action node
        if ImmortalEntity.getNodeType(node) != NodeType.Action:
            raise f"for action node only, current {node}"

        data = ImmortalEntity.getDataField(node)
        mappingfield = EntityKeyword.ActionKeywordMapping
        mappings = []
        if mappingnode_1 is not None:
            mappings.append({"key": keyword_1, "value": mappingnode_1})
        if mappingnode_2 is not None:
            mappings.append({"key": keyword_2, "value": mappingnode_2})
        if mappingnode_3 is not None:
            mappings.append({"key": keyword_3, "value": mappingnode_3})

        if data.keys().__contains__(mappingfield):
            data[mappingfield] = data[mappingfield] + mappings
        else:
            data.setdefault(mappingfield, mappings)

        newentity = Utils.cloneDict(entity)
        return newentity, nodepointer, mappingnode_1, mappingnode_2, mappingnode_3
        pass


class ImAppendQuickbackNode:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        tracebackinfo = traceback.format_stack()
        print(f"========trace back: {''.join(tracebackinfo)}")
        # input_dir = config.ImmortalConfig.sucaipath
        input_dir = folder_paths.get_input_directory()
        files = [item.replace(input_dir + '\\', '').replace('\\', '/') for item in
                 Utils.listAllFilesInSubFolder(input_dir)]
        # files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {
                "entity": ("IMMORTALENTITY",),
                "image": (sorted(files), {"image_upload": True}),
                "text": ("STRING", {"default": ""}),
                "title": ("STRING", {"default": ""}),
                "question": ("STRING", {"default": ""}),
                "ttsvoicepath": ("STRING", {"default": ""}),
                "autoRoot": (["YES", "NO"], {"default": "YES"}),
                "skipTalk": (["YES", "NO"], {"default": "NO"}),
                "enableCache": (["YES", "NO"], {"default": "YES"}),
                "disabled": (["YES", "NO"], {"default": "NO"}),
            },
            "optional": {
                "nodepointer": ("NODE",),
                "extraNodes": ("NODES", {"default": []}),
                "overrideBackTitle": ("STRING", {"default": ""}),
                "settings": ("STRING", {"default": "{ \"voiceid\": \"xujiang\" }"})
            }
        }
        pass

    RETURN_TYPES = ("IMMORTALENTITY", "NODE", "NODE")
    RETURN_NAMES = ("entity", "childpointer", "parentpointer")

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, entity, image, text, title, question, ttsvoicepath, autoRoot, skipTalk, enableCache,
                nodepointer=None, extraNodes=[], overrideBackTitle=None, settings=None, disabled="NO"):
        videonode = ImAppendNode()
        ett, childpointer = videonode.process(entity, image, text, title, question, ttsvoicepath, autoRoot, skipTalk,
                                              enableCache, nodepointer, extraNodes, settings, disabled)

        redirectnode = redirectToNode()
        ett, parentpointer = redirectnode.process(ett, childpointer, nodepointer)
        for extranode in extraNodes:
            ett, _ = redirectnode.process(ett, childpointer, extranode)
        if overrideBackTitle is not None and len(overrideBackTitle) > 0:
            overridenode = ImNodeTitleOverride()
            ett, parentpointer = overridenode.process(ett, childpointer, parentpointer, overrideBackTitle)
            for extranode in extraNodes:
                ett, _ = overridenode.process(ett, extranode, childpointer, overrideBackTitle)
        return ett, childpointer, parentpointer

        pass


class mergeEntityAndPointer:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "entity1": ("IMMORTALENTITY",),
                "entity2": ("IMMORTALENTITY",),
                "extraPrev1": ("NODE", {"default": None}),
                "extraPrev2": ("NODE", {"default": None})
            },
            "optional": {
                "entity3": ("IMMORTALENTITY",),
                "entity4": ("IMMORTALENTITY",),
                "entity5": ("IMMORTALENTITY",),
                "extraPrev3": ("NODE", {"default": None}),
                "extraPrev4": ("NODE", {"default": None}),
                "extraPrev5": ("NODE", {"default": None})
            }
        }
        pass

    RETURN_TYPES = ("IMMORTALENTITY", "NODE", "NODES")
    RETURN_NAMES = ("entity", "pointer", "others")

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, entity1, entity2, extraPrev1, extraPrev2, entity3=None, entity4=None, entity5=None,
                extraPrev3=None, extraPrev4=None, extraPrev5=None):
        Node_merge = ImMergeNode()
        mergedEntity = Node_merge.process(entity1, entity2, entity3, entity4, entity5)[0]
        Node_batchnode = batchNodes()
        batched = Node_batchnode.process(extraPrev2, extraPrev3, extraPrev4, extraPrev5)[0]
        print(f"merged entity: {mergedEntity}")
        print(f"batched:{batched}")
        return mergedEntity, extraPrev1, batched
        pass


class batchNodes:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "extraPrev1": ("NODE", {"default": None})
            },
            "optional": {
                "extraPrev2": ("NODE", {"default": None}),
                "extraPrev3": ("NODE", {"default": None}),
                "extraPrev4": ("NODE", {"default": None}),
                "extraPrev5": ("NODE", {"default": None}),
                "extraPrev6": ("NODE", {"default": None}),
                "extraPrev7": ("NODE", {"default": None}),
                "extraPrev8": ("NODE", {"default": None}),
                "extraPrev9": ("NODE", {"default": None}),
                "extraPrev10": ("NODE", {"default": None})
            }
        }
        pass

    RETURN_TYPES = ("NODES",)
    RETURN_NAMES = ("nodes",)

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, extraPrev1, extraPrev2=None, extraPrev3=None, extraPrev4=None, extraPrev5=None, extraPrev6=None,
                extraPrev7=None, extraPrev8=None, extraPrev9=None, extraPrev10=None):

        extraPrevs = [extraPrev1, extraPrev2, extraPrev3, extraPrev4, extraPrev5, extraPrev6, extraPrev7, extraPrev8,
                      extraPrev9, extraPrev10]
        prevs = []
        for i in range(0, len(extraPrevs)):
            current = extraPrevs[i]
            if current is not None:
                prevs.append(current)
        return (prevs,)
        pass


class redirectToNode:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "entity": ("IMMORTALENTITY",),
                "From": ("NODE", {"default": None}),
                "To": ("NODE", {"default": None})
            },
            "optional": {
                "overrideTargetTitle": ("STRING", {"default": "NULL"}),
            }
        }
        pass

    RETURN_TYPES = ("IMMORTALENTITY", "NODE", "NODE")
    RETURN_NAMES = ("entity", "from", "to")

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, entity, From, To, overrideTargetTitle="NULL"):
        # print(f"entity : {entity}")
        toNode = ImmortalEntity.getNodeById(entity, To)
        # print(f"to node: {toNode}")
        ImmortalEntity.setPrevNode(toNode, From)

        newEntity = Utils.cloneDict(entity)
        if overrideTargetTitle != "NULL":
            overrideNode = ImNodeTitleOverride()
            newEntity, _ = overrideNode.process(newEntity, To, From, overrideTargetTitle)

        return newEntity, From, toNode["ID"]
        pass


class ImNewNode:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
            },
            "optional": {
                "DUMMYCODE": ("STRING", {"default": ""}),
            }
        }
        pass

    RETURN_TYPES = ("IMMORTALENTITY", "NODE")
    RETURN_NAMES = ("entity", "pointer")

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, DUMMYCODE):
        entity = ImmortalEntity.getEntity()
        newEntity = Utils.cloneDict(entity)
        return newEntity, None
        pass


class ImMergeNode:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "entity1": ("IMMORTALENTITY",),
                "entity2": ("IMMORTALENTITY",)
            },
            "optional": {
                "entity3": ("IMMORTALENTITY",),
                "entity4": ("IMMORTALENTITY",),
                "entity5": ("IMMORTALENTITY",),
                "entity6": ("IMMORTALENTITY",),
                "entity7": ("IMMORTALENTITY",),
                "entity8": ("IMMORTALENTITY",),
                "entity9": ("IMMORTALENTITY",),
                "entity10": ("IMMORTALENTITY",)
            }
        }
        pass

    RETURN_TYPES = ("IMMORTALENTITY",)
    # RETURN_NAMES = ("image_output_name",)

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, entity1, entity2, entity3=None, entity4=None, entity5=None, entity6=None, entity7=None,
                entity8=None, entity9=None, entity10=None):
        entities = [entity1, entity2, entity3, entity4, entity5, entity6, entity7, entity8, entity9, entity10]

        current = None
        for ett in entities:
            if current is None:
                current = ett
            else:
                if ett is not None and current != ett:
                    current = ImmortalEntity.mergeContext(current, ett)
                    nodeIDs = [c["ID"] for c in current["Nodes"]]
                    cNodes = set(nodeIDs)
                    eNodes = ett["Nodes"]
                    for n in eNodes:
                        nodeid = n["ID"]
                        if not cNodes.__contains__(nodeid):
                            current["Nodes"].append(n)
                        else:
                            cnode = ImmortalEntity.getNodeById(current, nodeid)
                            newNode = ImmortalEntity.mergeNode(cnode, n)
                            cnodelist: list = current["Nodes"]
                            current["Nodes"].remove(cnode)
                            cnodelist.append(newNode)

        return (current,)
        pass


class ImNodeTitleOverride:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "sceneEntity": ("IMMORTALENTITY",),
                "node": ("NODE",),
                "fromNode": ("NODE",),
                "overrideTitle": ("STRING", {"default": r""}),
            }
        }
        pass

    RETURN_TYPES = ("IMMORTALENTITY", "NODE")
    RETURN_NAMES = ("entity", "to_node")

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, sceneEntity, node, fromNode, overrideTitle):
        currentnode = ImmortalEntity.getNodeById(sceneEntity, node)
        ImmortalEntity.setTitleOverride(currentnode, fromNode, overrideTitle)
        newEntity = Utils.cloneDict(sceneEntity)
        return newEntity, node
        pass


class SetNodeMapping:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        from .Events import EventHandler
        return {
            "required": {
                "sceneEntity": ("IMMORTALENTITY",),
                "node": ("NODE",),
                "func": (list(EventHandler.Conditiondict.keys()), {"default": r"equal"}),
                "key": ("STRING", {"default": r""}),
                "value": ("STRING", {"default": r""}),
            }
        }
        pass

    RETURN_TYPES = ("IMMORTALENTITY", "NODE")
    # RETURN_NAMES = ("image_output_name",)

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, sceneEntity, node, func, key, value):
        currentnode = ImmortalEntity.getNodeById(sceneEntity, node)
        if Utils.isJsonString(key):
            key = json.loads(key)
        if Utils.isJsonString(value):
            value = json.loads(value)
        if not isinstance(value, int):
            if value.isdigit() or value.replace('-', '').isdigit():
                value = int(value)
        mapping: list = currentnode["Mapping"]
        mapping.append({func: [key, value]})
        newEntity = Utils.cloneDict(sceneEntity)
        print(f"after set mapping:  {newEntity}")
        return newEntity, node
        pass


class SetProperties:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "sceneEntity": ("IMMORTALENTITY",),
                "keys": ("STRING", {"default": r""}),
                "values": ("STRING", {"default": r""})
            }
        }
        pass

    RETURN_TYPES = ("IMMORTALENTITY",)
    # RETURN_NAMES = ("image_output_name",)

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, sceneEntity, keys, values):
        prop = sceneEntity["Properties"]
        keyArray = keys.split(',')
        valArray = values.split('.')
        for i in range(0, len(keyArray)):
            k = keyArray[i]
            v = valArray[i]
            prop[k] = v
        newEntity = Utils.cloneDict(sceneEntity)
        return (newEntity,)
        pass


class TurnOnOffNodeOnEnter:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        input_dir = ImmortalConfig.sucaipath
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {
                "sceneEntity": ("IMMORTALENTITY",),
                "enterNode": ("NODE",),
                "disableNode": ("NODE",),
                "turn": (["on", "off"], {"default": "off"}),
            }
        }
        pass

    RETURN_TYPES = ("IMMORTALENTITY", "NODE", "NODE")
    RETURN_NAMES = ("entity", "enternode", "disablenode")

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, sceneEntity, enterNode, disableNode, turn):
        if turn == 'on':
            onoff = '0'
        else:
            onoff = '1'
        eventnode = SetEvent()
        entity, node = eventnode.process(sceneEntity, enterNode, "OnEnter", "Set",
                                         ImmortalEntity.getDisableKey(disableNode), onoff)
        return entity, enterNode, disableNode
        pass


class SetEvent:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        input_dir = ImmortalConfig.sucaipath
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {
                "sceneEntity": ("IMMORTALENTITY",),
                "node": ("NODE", {"default": None}),
                "eventid": (["OnEnter", "OnLeave"], {"default": r"OnEnter"}),
                "func": (["Set", "increase", "append", "remove"], {"default": r"Set"}),
                "key": ("STRING", {"default": r"BGMusicKey"}),
                "value": ("STRING", {"default": r""})
            }
        }
        pass

    RETURN_TYPES = ("IMMORTALENTITY", "NODE")
    RETURN_NAMES = ("entity", "pointer")

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, sceneEntity, node, eventid, func, key, value):
        currentnode = ImmortalEntity.getNodeById(sceneEntity, node)
        if not currentnode["Events"].keys().__contains__(eventid):
            currentnode["Events"].setdefault(eventid, [])
        keys = key
        values = value
        keyArray = keys.split(',')
        valArray = values.split(',')
        for i in range(0, len(keyArray)):
            k = keyArray[i]
            v = valArray[i]
            if v.isdigit() or v.replace('-', '').isdigit():
                v = int(v)
            tar = currentnode["Events"][eventid]
            print(f'set {tar} for function {func} with key {k} and val {v}')
            currentnode["Events"][eventid].append({func: [k, v]})
        newEntity = Utils.cloneDict(sceneEntity)
        return newEntity, node
        pass


class ImLoadPackage:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "packagedir": ("STRING",),
                "entityfilename": ("STRING", {"default": "entity.json"}),
                "nodepointerid": ("STRING", {"default": "ROOT"})
            }
        }
        pass

    RETURN_TYPES = ("IMMORTALENTITY", "NODE")
    RETURN_NAMES = ("entity", "pointer")

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def allToPackPath(self, dictPointer, packagedir, strategyFunc=ImmortalConfig.grepFullpath):
        for k in dictPointer.keys():
            v = dictPointer[k]
            # print(f"k:{k}")
            # print(f"v type:{type(v)}")
            # print(f"dict type: {type(dict)}")
            # print(f"dict instance type:{type({})}")
            if type(v) == type(""):
                print(f'handle:{v}')
                targetSubPath = strategyFunc(v, packagedir)
                print(f'path decision: {targetSubPath}')
                if targetSubPath is not None:
                    dictPointer[k] = targetSubPath
            elif type(v) == type({}):
                dictPointer[k] = self.allToPackPath(v, packagedir, strategyFunc)
            elif type(v) == type([]):
                for i in range(0, len(v)):
                    vi = v[i]
                    if type(vi) == type(''):
                        targetSubPath = strategyFunc(vi, packagedir)
                        if targetSubPath is not None:
                            dictPointer[k][i] = targetSubPath
                    elif type(vi) == type({}):
                        dictPointer[k][i] = self.allToPackPath(v[i], packagedir, strategyFunc)
        return Utils.cloneDict(dictPointer)

    def mapKey2AbsPath(self, entity, packagedir):
        nodes = entity["Nodes"]
        for i in range(0, len(nodes)):
            node = nodes[i]
            node[i] = self.allToPackPath(node, packagedir)
        return entity
        pass

    def process(self, packagedir, entityfilename, nodepointerid):
        file = os.path.join(packagedir, entityfilename)
        with open(file, "r", encoding='utf-8') as f:
            datastr = f.read()
        entity = json.loads(datastr)
        entity = self.mapKey2AbsPath(entity, packagedir)
        if nodepointerid == 'ROOT':
            pointer = entity["Properties"]["root"]
        else:
            pointer = nodepointerid
        # print(entity)
        return entity, pointer


class grepNodeByText:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "sceneEntity": ("IMMORTALENTITY",),
                "text": ("STRING",)
            }
        }
        pass

    RETURN_TYPES = ("NODE",)
    RETURN_NAMES = ("nodepointer",)

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, sceneEntity, text):
        nodelist = sceneEntity["Nodes"]

        result = []
        for nd in nodelist:
            txt = nd["Text"]
            if txt is not None and txt == text:
                result.append(nd["ID"])

        if sceneEntity.keys().__contains__("Actions"):
            actionlist = sceneEntity["Actions"]
            for nd in actionlist:
                txt = nd["Text"]
                if txt is not None and txt == text:
                    result.append(nd["ID"])
        if len(result) > 0:
            return (result[0],)
        else:
            return (None,)
        pass


class String2Node:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "nodeidStr": ("STRING",)
            }
        }
        pass

    RETURN_TYPES = ("NODE",)
    RETURN_NAMES = ("nodepointer",)

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, nodeidStr):
        return (nodeidStr,)
        pass


class OllamaChat:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": ("STRING", {"default": "我会给出一段描述的话，作为生成图片的提示词， 帮我把它翻译成英文。要求1.只回复翻译的内容本身，2.可以适当加一些细节描述。",
                                      'multiline': True}),
                "input": ("STRING", {"default": "一个女孩", 'multiline': True})
            }
        }
        pass

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, prompt, input):
        history = [
            {'role': 'user', 'content': prompt},
            {'role': 'assistant', 'content': '好的，咱们开始吧！'},
        ]
        response, _ = OllamaCli.chatOnce(input, history, model='qwen2')
        return (response,)
        pass


class Node2String:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "nodeidStr": ("NODE",)
            }
        }
        pass

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("nodeid",)

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, nodeidStr):
        return (nodeidStr,)
        pass


class SaveToDirectory:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "sceneEntity": ("IMMORTALENTITY",),
                "to": ("STRING", {"default": r"D:\immortaldata\Immortal\package"})
            }
        }
        pass

    RETURN_TYPES = ("STRING",)
    # RETURN_NAMES = ("image_output_name",)

    FUNCTION = "process"

    # OUTPUT_NODE = False

    CATEGORY = "Immortal"

    def process(self, sceneEntity, to):
        toPath = ImmortalConfig.packpath
        if len(to) > 0:
            toPath = to
        id, targetDir = Utils.generatePathId(toPath)
        self.preprocess(sceneEntity, id, toPath)
        js = json.dumps(sceneEntity)
        destPath = os.path.join(targetDir, "entity.json")
        with open(destPath, 'w') as f:
            f.write(js)
            f.flush()
        return (targetDir,)
        pass

    def preprocess(self, sceneEntity, id, to=ImmortalConfig.packpath):
        entity = self.mappingToPackPath(sceneEntity, id, to)
        return entity
        pass

    def toPackPath(self, id, basepath):
        videoPath = Utils.tryExtractPathByKey(id)
        extendName = videoPath.split('.')[-1]
        id = Utils.generateId()
        filename = f"{id}.{extendName}"
        if not os.path.exists(basepath):
            os.makedirs(basepath)
        destPath = os.path.join(basepath, filename)
        shutil.copyfile(videoPath, destPath)
        return id

    def allToPackPath(self, dictPointer, targetPackPath, strategyFunc=config.ImmortalConfig.decisionToPackPath):
        for k in dictPointer.keys():
            v = dictPointer[k]
            print(f"k:{k}")
            print(f"v type:{type(v)}")
            print(f"dict type: {type(dict)}")
            print(f"dict instance type:{type({})}")
            if type(v) == type(""):
                print(f'handle:{v}')
                targetSubPath = strategyFunc(v)
                print(f'path decision: {targetSubPath}')
                if targetSubPath is not None:
                    targetbasepath = os.path.join(targetPackPath, targetSubPath)
                    dictPointer[k] = self.toPackPath(v, targetbasepath)
            elif type(v) == type({}):
                dictPointer[k] = self.allToPackPath(v, targetPackPath, strategyFunc)
            elif type(v) == type([]):
                for i in range(0, len(v)):
                    vi = v[i]
                    if isinstance(vi, type('')):
                        targetSubPath = strategyFunc(vi)
                        print(f'====converting: {vi}')
                        print(f'====targetsubpath: {targetSubPath}')
                        if targetSubPath is not None:
                            targetbasepath = os.path.join(targetPackPath, targetSubPath)
                            dictPointer[k][i] = self.toPackPath(vi, targetbasepath)
                    elif type(vi) == type({}):
                        dictPointer[k][i] = self.allToPackPath(v[i], targetPackPath, strategyFunc)
        return dictPointer

    def mappingToPackPath(self, sceneEntity, id, to=ImmortalConfig.packpath):
        targetPath = Utils.getPathById(to, id)
        videoBasePath = os.path.join(targetPath, "videos")
        imageBasePath = os.path.join(targetPath, "images")
        if not os.path.exists(videoBasePath):
            os.makedirs(videoBasePath)
        nodes = sceneEntity["Nodes"]
        for node in nodes:
            node["VideoDataKey"] = self.toPackPath(node["VideoDataKey"], videoBasePath)
            events = node["Events"]
            node["Events"] = self.allToPackPath(events, targetPath)
            datafield: dict = ImmortalEntity.getDataField(node)
            if datafield.keys().__contains__("VideoTemplateList"):
                VideoTemplateList = datafield["VideoTemplateList"]
                for i in range(0, len(VideoTemplateList)):
                    VideoTemplateList[i] = self.toPackPath(VideoTemplateList[i], videoBasePath)
            if datafield.keys().__contains__("ImageTemplateList"):
                ImageTemplateList = datafield["ImageTemplateList"]
                for i in range(0, len(ImageTemplateList)):
                    ImageTemplateList[i] = self.toPackPath(ImageTemplateList[i], imageBasePath)
        pass


class SaveImagePath:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(s):
        return {"required":
                    {"images": ("IMAGE",),
                     "filename_prefix": ("STRING", {"default": "ComfyUI"})},
                "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
                }

    RETURN_TYPES = ("IMAGE_PATH",)
    FUNCTION = "save_images"

    OUTPUT_NODE = True

    CATEGORY = "image"

    def save_images(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
        from comfy.cli_args import args
        from PIL import Image, ImageOps, ImageSequence, ImageFile
        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])
        results = list()
        for (batch_number, image) in enumerate(images):
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            metadata = None
            if not args.disable_metadata:
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{counter:05}_.png"
            img.save(os.path.join(full_output_folder, file), pnginfo=metadata, compress_level=self.compress_level)
            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })
            counter += 1

        return (os.path.join(full_output_folder, results[0]["filename"]),)


NODE_CLASS_MAPPINGS = {
    "NewNode": ImNewNode,
    "AppendNode": ImAppendNode,
    "MergeNode": ImMergeNode,
    "SetProperties": SetProperties,
    "SaveToDirectory": SaveToDirectory,
    "batchNodes": batchNodes,
    "redirectToNode": redirectToNode,
    "SetEvent": SetEvent,
    "SaveImagePath": SaveImagePath,
    "ImAppendVideoNode": ImAppendVideoNode,
    "ApplyVoiceConversion": ApplyVoiceConversion,
    "ImApplyWav2lip": ImApplyWav2lip,
    "ImDumpEntity": ImDumpEntity,
    "ImDumpNode": ImDumpNode,
    "ImLoadPackage": ImLoadPackage,
    "SetNodeMapping": SetNodeMapping,
    "ImNodeTitleOverride": ImNodeTitleOverride,
    "mergeEntityAndPointer": mergeEntityAndPointer,
    "ImAppendQuickbackVideoNode": ImAppendQuickbackVideoNode,
    "ImAppendQuickbackNode": ImAppendQuickbackNode,
    "String2Node": String2Node,
    "grepNodeByText": grepNodeByText,
    "CombineVideos": CombineVideos,
    "ImAppendFreeChatAction": ImAppendFreeChatAction,
    "ImAppendImageActionNode": ImAppendImageActionNode,
    "ImSetActionKeywordMapping": ImSetActionKeywordMapping,
    "Node2String": Node2String,
    "OllamaChat": OllamaChat,
    "TurnOnOffNodeOnEnter": TurnOnOffNodeOnEnter,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "NewNode": "ImNewNode",
    "AppendNode": "ImAppendNode",
    "MergeNode": "MergeNode",
    "SetProperties": "SetProperties",
    "SaveToDirectory": "SaveToDirectory",
    "batchNodes": "batchNodes",
    "redirectToNode": "redirectToNode",
    "SetEvent": "SetEvent",
    "SaveImagePath": "[helper]:SaveImagePath",
    "ImAppendVideoNode": "ImAppendVideoNode",
    "ApplyVoiceConversion": "ApplyVoiceConversion",
    "ImApplyWav2lip": "ImApplyWav2lip",
    "ImDumpEntity": "ImDumpEntity",
    "ImDumpNode": "ImDumpNode",
    "ImLoadPackage": "ImLoadPackage",
    "SetNodeMapping": "SetNodeMapping",
    "ImNodeTitleOverride": "ImNodeTitleOverride",
    "mergeEntityAndPointer": "mergeEntityAndPointer",
    "ImAppendQuickbackVideoNode": "ImAppendQuickbackVideoNode",
    "ImAppendQuickbackNode": "ImAppendQuickbackNode",
    "String2Node": "String2Node",
    "grepNodeByText": "grepNodeByText",
    "CombineVideos": "CombineVideos",
    "ImAppendFreeChatAction": "ImAppendFreeChatAction",
    "ImAppendImageActionNode": "ImAppendImageActionNode",
    "ImSetActionKeywordMapping": "ImSetActionKeywordMapping",
    "Node2String": "Node2String",
    "OllamaChat": "OllamaChat",
    "TurnOnOffNodeOnEnter": "TurnOnOffNodeOnEnter"
}
