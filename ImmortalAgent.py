# import sys
#
# sys.path.append('/Entity/')
# sys.path.append('/Moviemaker/')
from moviepy.editor import *
# from Entity import ImmortalEntity
from .MovieMakerUtils import MovieMakerUtils
from . import Utils


class ImmortalAgent:
    @staticmethod
    def toTalkman(video, audio):
        id, path = Utils.Utils.generatePathId(namespace="talkman", exten='mp4')
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        videoClip = VideoFileClip(video)
        audioClip = AudioFileClip(audio)
        clip = MovieMakerUtils.setBGM(videoClip, audioClip, 1.0)
        clip.write_videofile(path)
        return id, path
        pass

    @staticmethod
    def replaceAudio(video, audio):
        id, path = Utils.Utils.generatePathId(namespace="replaceaudio", exten='mp4')
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        videoClip = VideoFileClip(video)
        audioClip = AudioFileClip(audio)
        print(f"video clip duration:{videoClip.duration} , audio duration: {audioClip.duration}")
        videoClip = videoClip.set_duration(audioClip.duration)
        print(f"after process: video duration: {videoClip.duration}")
        clip = videoClip.set_audio(audioClip)
        # clip = MovieMakerUtils.setBGM(videoClip, audioClip, 1.0)
        clip.write_videofile(path)
        return id, path
        pass

    @staticmethod
    def xTTS_VC_batch(source2speakerList:list)->list:
        id, path = Utils.Utils.generatePathId(namespace='xttsjob', exten="tsv")
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        result = []
        with open(path, 'w', encoding='utf-8') as f:
            for item in source2speakerList:
                voicepath = item[0]
                speakerpath = item[1]
                topath = voicepath + ".output.wav"
                f.write(f"{voicepath}\t{speakerpath}\t{topath}")
                result.append(topath)
        cmdpath = r'R:\workspace\xTTS\voiceConvertion.cmd'
        command = f'{cmdpath} {path}'
        os.system(command)
        return result
    pass


if __name__ == "__main__":
    video = r""
    audio = r""
    referencePose = r""
    id, path = ImmortalAgent.toTalkman(video, audio)
    print(path)

