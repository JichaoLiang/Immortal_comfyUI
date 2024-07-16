import os
import sys

from .Utils import Utils
import time
import hashlib
import json

class Wav2lipCli:
    @staticmethod
    def wav2lip(audioPath: str, faceVideoPath: str, toPath: str):
        Utils.mkdir(toPath)
        script_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
        cmdPath = os.path.join(script_path, 'sh/wav2lipsh.bat')
        print(f'{cmdPath} {faceVideoPath} {audioPath} {toPath}')
        os.system(f'{cmdPath} {faceVideoPath} {audioPath} {toPath}')
        # completedproc = subprocess.run([cmdPath, faceVideoPath, audioPath, toPath])
        # print(f'process finished. code: {completedproc.returncode}')
        pass

    @staticmethod
    def xtts_vc(sourcelist:list, speakerlist:list)->list:
        if len(sourcelist) != len(speakerlist):
            raise Exception("source list length not equals speaker list length")
        # book tsv
        tsvcontent = ""
        resultPath = []
        for i in range(0, len(sourcelist)):
            source = sourcelist[i]
            speaker = speakerlist[i]
            _, topath = Utils.generatePathId(namespace="temp", exten="wav")
            tsvcontent += f'{source}\t{speaker}\t{topath}'
            resultPath.append(topath)
            tsvcontent += '\n'
            time.sleep(0.001)
        id, path = Utils.writetempfile(tsvcontent)
        script_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
        shpath = os.path.join(script_path, 'sh/voiceConvertion.cmd')
        cmdinstance = f"{shpath} {path}"
        print(cmdinstance)
        os.system(cmdinstance)
        return resultPath
    pass

    @staticmethod
    def test():
        audio = 'r:/xTTS_ll_open1.wav'
        video = r'D:\MyWork\data\sucai\zhangguorong\shanghai_clip_1.mp4'
        to = 'r:/zgr_open1.mp4'
        Wav2lipCli.wav2lip(audio, video, to)

    @staticmethod
    def batchTest():
        i = 0
        inputTemp = r'd:\{0}.wav.converted.wav'
        video = r'D:\MyWork\data\sucai\zhangguorong\shanghai_clip_1.mp4'
        toTemplate = r"D:\wav2liped\{0}.mp4"
        while True:
            audio = inputTemp.replace('{0}', str(i))
            if not os.path.exists(audio):
                break
            to = toTemplate.replace('{0}', str(i))
            Wav2lipCli.wav2lip(audio, video, to)
            i += 1

    @staticmethod
    def batchTest2():
        i = 0
        # inputTemp = r'd:\{0}.wav.converted.wav'
        inputTemp = r'D:\aianswerzgr\{0}.wav'
        video = r'D:\MyWork\data\sucai\zhangguorong\shanghai_clip_1.mp4'
        toTemplate = r"D:\wav2liped\freetalk\{0}.mp4"
        while True:
            audio = inputTemp.replace('{0}', str(i))
            if not os.path.exists(audio):
                break
            to = toTemplate.replace('{0}', str(i))
            Wav2lipCli.wav2lip(audio, video, to)
            i += 1
    @staticmethod
    def testVC():
        sourcepath = [r"r:\xTTS_zgr_open.wav",r"r:\xTTS_zgr_open.wav",]
        speakerpath = [r"r:\xTTS_ll_open1.wav",r"r:\zzx_clip.mp3"]
        converted = Wav2lipCli.xtts_vc(sourcepath,speakerpath)
        for c in converted:
            print(c)

    @staticmethod
    def wav2lip_batch(videolist, voicelist):
        resultid = []
        result = []
        for i in range(0, len(videolist)):
            video = videolist[i]
            voice = voicelist[i]

            # md5Cache
            obj = {"function": "wav2liputils", "video": video, "voice": voice }
            md5 = hashlib.md5(json.dumps(obj).encode('utf-8')).hexdigest()
            keyExists = Utils.objectStorekeyExists(md5)
            if keyExists:
                cache = json.loads(Utils.getObjectStoreKey(md5))
                toid = cache["id"]
                to = cache["path"]
            else:
                toid, to = Utils.generatePathId(namespace="wav2lip", exten="mp4")
                Wav2lipCli.wav2lip(voice, video, to)
                Utils.setObjectStoreKey(md5, json.dumps({"id":toid, "path":to}))
            resultid.append(toid)
            result.append(to)
        return resultid, result
        pass


if __name__ == '__main__':
    script_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    sys.path.append(script_path)
    sys.path.append("")
    sys.path.append(script_path)
    print(script_path)
    import Utils
    # Wav2lipCli.testVC()
    Wav2lipCli.test()
    # Wav2lipCli.batchTest2()
