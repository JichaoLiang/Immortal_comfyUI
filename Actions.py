import json
import os.path

from .keywords import ContextKeyword
from .keywords import EntityKeyword
from .ImmortalEntity import ImmortalEntity
from .Utils import Utils
from .OllamaCli import OllamaCli
from .TTSUtils import TTSUtils
from .Wav2lipCli import Wav2lipCli

# 默认实时回话场景
class DefaultChatAction:

    def handleRequest(self, packageEntity, actionNode:dict, nextList:list, context:dict):
        history = []
        historykey_context = f"{ContextKeyword.DefaultChatAction_history}_{actionNode['ID']}"
        if context.keys().__contains__(historykey_context):
            history = context[historykey_context]
        datafield = ImmortalEntity.getDataField(actionNode)
        prompt = datafield["Prompt"]
        promptHistory = json.loads(prompt)
        wholehistory = promptHistory + history
        videotemplate = datafield["VideoTemplateList"]
        defaultvideo = actionNode["VideoDataKey"]

        datafield = ImmortalEntity.getDataField(actionNode)
        settings = datafield[EntityKeyword.settings]
        voiceid = settings[EntityKeyword.voiceId]
        question = None
        if context.keys().__contains__(ContextKeyword.Question):
            question = context[ContextKeyword.Question]
            context[ContextKeyword.Question] = ""
        if question is None or len(question) == 0:
            videoFileID = defaultvideo
            datafield["playvideo"] = videoFileID
        else:
            # random pick video template
            picked = Utils.randomPick(len(videotemplate))
            videoFile = videotemplate[picked]
            videoFileID = os.path.basename(videoFile)

            # get response text
            response, newHistory = OllamaCli.chatOnce(question,wholehistory)
            context[historykey_context] = newHistory[len(promptHistory):]

            # TTS
            toid, topath = Utils.generatePathId(namespace="temp", exten="wav")
            TTSUtils.cosvoiceTTS(response, topath, voiceid)

            # generate dhlive
            if not Wav2lipCli.videocheckpointExists(videoFileID):
                print(f'no checkpoint for {videoFileID}, generate one.')
                Wav2lipCli.dh_live_make_checkpoint(videoFile)
            toid, topath = Utils.generatePathId(namespace="videogen", exten="mp4")
            Wav2lipCli.dh_live(topath,videoFileID,topath)

            #pack entity
            datafield["playvideo"] = toid
        return actionNode,nextList,context

ActionMapping = {
    "DefaultFreeChat": DefaultChatAction
}