import json
import os.path
import sys
import requests
#
# script_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
# sys.path.append(script_path)
# sys.path.append("")
# sys.path.append(script_path)
# from Utils import Utils
from .Utils import Utils

class TTSUtils:

    regularFemale=9245

    @staticmethod
    def ChatTTS(text, to, speed=1, voiceid=9245):
        headers = {"Content-Type": "application/json"}
        text = {"text": text, "seed": voiceid, "speed": speed}
        response = requests.post("http://localhost:9880", data=json.dumps(text), headers=headers)
        data = response.content
        Utils.mkdir(to)
        with open(to, mode='wb') as f:
            f.write(data)
        return to
        pass

    @staticmethod
    def ChatTTS_with_break(text, to, speed=5, voiceid=1342):
        pieces = TTSUtils.breakdownText(text)
        print(f"tts pieces: {pieces}")
        from pydub import AudioSegment
        sound = None
        for piece in pieces:
            if type(piece) == type(""):
                # text path
                id, path = Utils.generatePathId(namespace="tts", exten="wav")
                dir = os.path.dirname(path)
                if not os.path.exists(dir):
                    os.makedirs(dir)
                TTSUtils.ChatTTS(piece, path,speed, voiceid)
                clip = AudioSegment.from_file(path, format='wav')
            else:
                clip = AudioSegment.silent(duration=piece * 1000)

            if sound is None:
                sound = clip
            else:
                sound = sound + clip
        sound.export(to,format='wav')

    @staticmethod
    def cosvoiceTTS(text, to, speakerID='dushuai'):
        headers = {"Content-Type": "application/json"}
        text = {"text": text, "speaker": speakerID, "new": 1}
        response = requests.post("http://localhost:9880", data=json.dumps(text), headers=headers)
        data = response.content
        Utils.mkdir(to)
        with open(to, mode='wb') as f:
            f.write(data)
        return to
        pass

    @staticmethod
    def breakdownText(text:str):
        muteMode = False
        result = []
        temp = ""
        for char in text:
            if char == "[":
                muteMode = True
                if len(temp) > 0:
                    result.append(temp)
                    temp = ""
                continue
            if char == "]":
                muteMode = False
                if len(temp) > 0:
                    result.append(int(temp))
                    temp = ""
                continue
            temp += char
        if len(temp) > 0:
            if muteMode:
                result.append(int(temp))
            else:
                result.append(temp)
        return result


if __name__ == "__main__":
    for i in range(0,10):
        result = TTSUtils.ChatTTS(
            "长按手柄的电源按钮:大多数PS4手柄都有一个单独的电源按钮,您可以长按几秒钟来完全关闭它。使用PS4主机:连接您的PS4手柄到PS4主机后,在主机上找到并选择“设置”选项。在设置菜单中,选择“控制器”,然后选择“断开”。这将从PS4主机中断开与手柄的连接。"
            , f"r:\\outputChartTTS{i}.wav", i)
        print(result)
