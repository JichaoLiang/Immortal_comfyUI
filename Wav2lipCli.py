import os
import shutil
import sys

# script_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
# parentPath = os.path.dirname(script_path)
# sys.path.append(script_path)
# sys.path.append(parentPath)
# sys.path.append("")
# print(script_path)

from gradio_client import client,handle_file
from .Utils import Utils
import time
import hashlib
import json

musetalkpkg = __import__("ComfyUI-MuseTalk")
musetalknodes = musetalkpkg.nodes
vhspkg = __import__("ComfyUI-VideoHelperSuite")
vhsnodes = vhspkg.videohelpersuite.nodes

class Wav2lipCli:
    @staticmethod
    def videocheckpointExists(videoCheckpointID:str)->bool:
        checkpoint_basepath = r'D:\MyWork\Projects\dhlive\DH_live\video_data'
        ckptpath = os.path.join(checkpoint_basepath, videoCheckpointID)
        return os.path.exists(ckptpath)

    @staticmethod
    def dh_live(audioPath: str, faceVideoID: str, toPath: str):
        client = Client("http://127.0.0.1:7860/")
        result = client.predict(
            face=faceVideoID,
            audio=handle_file(audioPath),
            api_name="/do_cloth"
        )
        print(result)
        videopath = result["video"]
        shutil.move(videopath, toPath)
        return toPath
        pass

    @staticmethod
    def dh_live_make_checkpoint(videopath:str):
        client = Client("http://127.0.0.1:7860/")
        result = client.predict(
            face={"video": handle_file(videopath)},
            api_name="/do_make"
        )
        print(result)
        videoname = os.path.basename(videopath)
        return videoname

    @staticmethod
    def musetalk(audioPath: str, faceVideoPath: str, toPath: str, bbox_shift=6, batch_size=16):
        # Utils.mkdir(toPath)
        musetalk = musetalknodes.MuseTalkRun()
        images = musetalk.run(faceVideoPath,audioPath,bbox_shift,batch_size)[0]
        loadaudio = vhsnodes.LoadAudio()
        audio = loadaudio.load_audio(audio_file=audioPath, seek_seconds=0)[0]
        videocombine = vhsnodes.VideoCombine()
        filenames = videocombine.combine_video(images=images,audio=audio,frame_rate=30,loop_count=0,format="video/h264-mp4")
        print(filenames)
        filenames = filenames["result"]
        resultpath = filenames[0][-1][-1]
        shutil.move(resultpath,toPath)
        pass

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
    def testMuseTalk():
        audioPath = r'r:/xTTS_ll_open1.wav'
        faceVideoPath = r'D:\MyWork\data\sucai\zhangguorong\shanghai_clip_1.mp4'
        toPath = r'r:/zgr_open1.mp4'
        Wav2lipCli.musetalk(audioPath, faceVideoPath, toPath)

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
    def convert_batch(videolist, voicelist, use="musetalk"):
        resultid = []
        result = []
        for i in range(0, len(videolist)):
            video = videolist[i]
            voice = voicelist[i]

            # md5Cache
            obj = {"function": f"wav2lip_{use}", "video": video, "voice": voice }
            md5 = hashlib.md5(json.dumps(obj).encode('utf-8')).hexdigest()
            keyExists = Utils.objectStorekeyExists(md5)
            if keyExists:
                cache = json.loads(Utils.getObjectStoreKey(md5))
                toid = cache["id"]
                to = cache["path"]
            else:
                toid, to = Utils.generatePathId(namespace="wav2lip", exten="mp4")
                todir = os.path.dirname(to)
                if not os.path.exists(todir):
                    os.mkdir(todir)
                if use=="musetalk":
                    Wav2lipCli.musetalk(voice, video, to)
                elif use=="wav2lip":
                    Wav2lipCli.wav2lip(voice, video, to)
                else:
                    Wav2lipCli.wav2lip(voice, video, to)
                Utils.setObjectStoreKey(md5, json.dumps({"id":toid, "path":to}))
            resultid.append(toid)
            result.append(to)
        return resultid, result
        pass



if __name__ == '__main__':
    # import Utils
    # Wav2lipCli.testVC()
    # Wav2lipCli.test()
    # Wav2lipCli.batchTest2()
    Wav2lipCli.testMuseTalk()
