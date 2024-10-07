import os
import random
import shutil
from pathlib import Path

import librosa
import moviepy
from moviepy.editor import *
from moviepy.editor import CompositeVideoClip
from moviepy.editor import CompositeAudioClip
import soundfile as sf

# from moviepy.video.compositing import *
from moviepy.video.VideoClip import TextClip
#
# import Config.Config
# from MovieMaker.TTSAgent import TTSAgent
# from Utils.DataStorageUtils import DataStorageUtils
import wave
# from .. import Utils


class MovieMakerUtils:
    @staticmethod
    def enlargeFullScreen(clip: VideoClip, fullscreensize, inseconds: int):
        wdivh = clip.size[0] / clip.size[1]

        return MovieMakerUtils.animationTo(clip, (0, 0), fullscreensize, inseconds)
        pass

    @staticmethod
    def getTickStampsByInsecondsArray(inseconsArray):
        result = []
        tempTimestamp = 0
        for i in range(0, len(inseconsArray)):
            time = inseconsArray[i]
            tempTimestamp += time
            result.append(tempTimestamp)
        return result
        pass

    @staticmethod
    def normalizeWH(w, h, w_h_div):
        whdiv = w/h
        if whdiv > w_h_div:
            return h * w_h_div, h
        else:
            return w, w / w_h_div
        pass

    @staticmethod
    def animationsTo(clip: VideoClip|ImageClip, offsetArray, sizeArray, inseconsArray) -> VideoClip:
        posfuncArray = []
        sizefuncArray = []
        w_h_div = clip.size[0] / clip.size[1]
        targetDivOriginWidth = sizeArray[-1][0] / clip.size[0]
        for i in range(0, len(offsetArray)):
            def posFunc(t: int, iter = i):
                targetOffset = offsetArray[iter]
                inseconds = inseconsArray[iter]
                if iter == 0:
                    l, tp = clip.pos(0)
                else:
                    l, tp = offsetArray[iter - 1]

                movSpeed = (targetOffset[0] - l) / inseconds
                movSpeed2 = (targetOffset[1] - tp) / inseconds

                left = l + movSpeed * t
                # if left <= 0:
                #     left = 0
                top = tp + movSpeed2 * t
                # if top <= 0:
                #     top = 0
                if movSpeed > 0 and left > targetOffset[0] \
                        or movSpeed < 0 and left < targetOffset[0]:
                    left = targetOffset[0]
                if movSpeed2 > 0 and top > targetOffset[1] \
                        or movSpeed2 < 0 and top < targetOffset[1]:
                    top = targetOffset[1]
                # print(f'{left},{top},{t}')
                return (left, top)
                pass

            def sizeFunc(t: int, iter = i):
                inseconds = inseconsArray[iter]
                targetSize = sizeArray[iter]
                if iter == 0:
                    w, h = clip.size
                else:
                    w, h = sizeArray[iter -1]
                w, h = MovieMakerUtils.normalizeWH(w, h, w_h_div)

                nw = targetSize[0]
                nh = targetSize[1]

                speed = (nw - w) / w / inseconds

                neww = w + w * speed * t
                newh = h + h * speed * t

                # print(f'{neww},{newh}')
                if speed > 0:
                    if neww > targetSize[0]:
                        return (neww, newh)
                if speed < 0:
                    if neww < targetSize[0]:
                        return (neww, newh)
                return (neww, newh)
                pass

            posfuncArray.append(posFunc)
            sizefuncArray.append(sizeFunc)
        tickStamp = MovieMakerUtils.getTickStampsByInsecondsArray(inseconsArray)

        def posf(t):
            ts = 0
            for i in range(0, len(tickStamp)):
                if t < tickStamp[i]:
                    return posfuncArray[i](t - ts)
                ts = tickStamp[i]
            return posfuncArray[-1](t - ts)
            pass

        def sizef(t):
            ts = 0
            for i in range(0, len(tickStamp)):
                # print(tickStamp[i])
                if t < tickStamp[i]:
                    return sizefuncArray[i](t - ts)
                ts = tickStamp[i]
            return targetDivOriginWidth
            pass

        result = clip.set_position(lambda t: posf(t)).resize(lambda t: (sizef(t)))
        return result
        pass

    @staticmethod
    def animationTo(clip: VideoClip|ImageClip, targetOffset, targetSize, inseconds):
        w, h = clip.size
        wdivh = w / h
        nw = targetSize[0]
        nh = targetSize[1]
        targetwdivh = nw / nh
        if wdivh > targetwdivh:
            nh = nw / wdivh
        else:
            nw = nh * wdivh
        speed = (nw - w) / w / inseconds
        l, tp = clip.pos(0)
        movSpeed = (targetOffset[0] - l) / inseconds
        movSpeed2 = (targetOffset[1] - tp) / inseconds

        def posFunc(t: int):
            left = l + movSpeed * t
            if left <= 0:
                left = 0
            top = tp + movSpeed2 * t
            if top <= 0:
                top = 0

            # print(f'{left},{top},{t}')
            return (left, top)
            pass

        def sizeFunc(t: int):
            neww = w + w * speed * t
            newh = h + h * speed * t

            # print(f'{nw},{nh}')
            if speed > 0:
                if neww > targetSize[0]:
                    return (nw, nh)
            if speed < 0:
                if neww < targetSize[0]:
                    return (nw, nh)
            return (neww, newh)
            pass

        result = clip.set_position(lambda t: posFunc(t)).resize(lambda t: (sizeFunc(t)))
        return result
        pass

    @staticmethod
    def concatevideo():
        vpath = 'D:/BaiduNetdiskDownload/clip.mp4'
        vpath2 = 'D:/BaiduNetdiskDownload/clip2.mp4'
        toPath = 'D:/BaiduNetdiskDownload/clip3.mp4'
        video1 = VideoFileClip(vpath).subclip(0, 10)

        video2 = VideoFileClip(vpath2).subclip(0, 10)
        resized = video2.resize(0.3).set_position((50, 50)).set_start(2)
        moving = resized.set_position(lambda t: (50 + 10 * t, 50 + 10 * t)).resize(lambda t: 1 + 0.1 * t)
        # txtClip = TextClip('Cool effect', color='white', font="Amiri-Bold",
        #                    kerning=5, fontsize=100)
        # video1.fx(vfx.mirror_y)
        composited = CompositeVideoClip([video1, moving])
        # concatenated = concatenate_videoclips([video1,video2],method='chain') # method: chain compose
        if Path(toPath).exists():
            os.remove(toPath)
        composited.write_videofile(toPath)
        pass

    @staticmethod
    def setBGM(video:VideoClip, audio:AudioClip, vol=0.8):
        audio1 = video.audio
        looped = afx.audio_loop(audio.volumex(vol), duration=video.duration)

        print(f"audio1:{audio1}")
        print(f"audio2:{looped}")

        if audio1 is None:
            mixed = looped
        else:
            mixed = CompositeAudioClip([audio1, looped])
        return video.set_audio(mixed)
        pass

    def extendRotateDurationAudio(clip: AudioClip, durationSec, muteExtended = False):
        duration = clip.duration
        concatelist = [clip]
        while durationSec - duration > clip.duration:
            copy = clip.copy()
            if muteExtended:
                copy = copy.without_audio()
            concatelist.append(copy)
            duration += clip.duration
        if durationSec > duration:
            lastSec = clip.subclip(0, durationSec - duration)
            if muteExtended:
                lastSec = lastSec.without_audio()
            concatelist.append(lastSec)
        return concatenate_audioclips(concatelist)
        pass

    @staticmethod
    def extendRotateDuration(clip: VideoClip, durationSec, muteExtended = False):
        duration = 0
        concatelist = []
        while durationSec - duration > clip.duration:
            copy = clip.copy()
            if len(concatelist) > 0 and muteExtended:
                copy = copy.without_audio()
            concatelist.append(copy)
            duration += clip.duration
        if durationSec > duration:
            lastSec = clip.subclip(0, durationSec - duration)
            if len(concatelist) > 0 and muteExtended:
                lastSec = lastSec.without_audio()
            concatelist.append(lastSec)
        return concatenate_videoclips(concatelist)
        pass


    @staticmethod
    def seperatetextbynewline(question, sizewidth=1920, fontsize=80, charcount=20):
        result = ''
        for i in range(0, len(question)):
            result += question[i]
            if i > 0 and i % charcount == 0:
                result += '\n'
        return result
        pass
    # @staticmethod
    # def captionTextToVideoClip(clip:VideoClip, captionText: str):
    #     enlarged = clip.resize((1920, 1080))
    #     pieces = TTSAgent.splitText(captionText)
    #     offsetduration = 0
    #     textsubtitlecliplist = []
    #     for piece in pieces:
    #         rows = len(piece) / 20
    #         question = MovieMakerUtils.seperatetextbynewline(piece,1920,80)
    #         if rows > 4:
    #             question = MovieMakerUtils.seperatetextbynewline(piece, 1920, 28)
    #             rows = len(piece) / 28
    #         duration = clip.duration * len(piece) / len(captionText)
    #         fontsize = 65
    #         if rows > 3: # 三行以上,太高了
    #             fontsize = 48
    #         titleClip: TextClip = TextClip(question, font=Config.Config.Config.subtitlefont, color='white',
    #                                        align='center', stroke_color='black', fontsize=fontsize, bg_color='black', size=(1920, 290 - 54))
    #         if titleClip.size[0] > 1920 * 0.9:
    #             titleClip = titleClip.resize(1920 * 0.9 / titleClip.size[0]).set_position((96, 54 + 790))
    #
    #         titleClip = titleClip.set_duration(duration).set_start(offsetduration)
    #
    #         offsetduration += duration
    #         textsubtitlecliplist.append(titleClip)
    #     textsubtitlecliplist.insert(0,enlarged)
    #     composited = CompositeVideoClip(textsubtitlecliplist).resize(clip.size)
    #     return composited

    @staticmethod
    def getCaptureFile(videoPath, to, momentSec=1):
        clip = VideoFileClip(videoPath)
        clip.save_frame(to, t=momentSec)
        return to
        pass

    @staticmethod
    def imageToVideo(imgPath, duration, to, resize=(920, 1480)):
        clip = ImageClip(imgPath, duration=duration)
        if resize is not None:
            clip = clip.resize(resize)

        bg = ColorClip((resize[0] - 200, resize[1]-200), color=(255,255,255))
        bg = bg.set_duration(duration)

        piecelength = 8
        pieces = []
        temp = duration
        while temp > piecelength:
            pieces.append(piecelength)
            temp -= piecelength
        if temp > 0:
            pieces.append(temp)

        randPick = MovieMakerUtils.randomPick(2)

        if randPick == 0:
            clip = clip.set_position((-200, 0))
            clip = MovieMakerUtils.animationsTo(clip, [(0, 0)], [resize], [pieces[0]])
        if randPick == 1:
            enlarged = (resize[0] * 1.2, resize[1] * 1.2)
            clip = clip.resize(enlarged).set_position((-100 * 1.2, 0))
            clip = MovieMakerUtils.animationsTo(clip, [(-100, 0)], [resize], [pieces[0]])
        sequence = [bg, clip]
        composited = CompositeVideoClip(sequence)

        dir = os.path.dirname(to)
        if not os.path.exists(dir):
            os.makedirs(dir)
        composited.write_videofile(to,fps=24)
        return to

    @staticmethod
    def get_wav_duration(file_path):
        with wave.open(file_path, 'r') as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            duration = frames / float(rate)
            return duration

    @staticmethod
    def resamplewav(path, resamplerate=22050):
        temp = path + '.temp.wav'
        MovieMakerUtils.resample4wavs(path, temp, resamplerate)
        os.remove(path)
        shutil.move(temp, path)

    @staticmethod
    def resample4wavs(frompath, topath, resamplerate=22050):
        y, sr = librosa.load(frompath)
        to_y = librosa.resample(y, orig_sr=sr, target_sr=resamplerate)
        # librosa.output.write_wav(tofile, to_y, resamplerate)过时代码, 需要换成下面的代码
        sf.write(topath, to_y, resamplerate)

    @staticmethod
    def randomPick(length):
        rand = random.Random()
        value = rand.random()
        return int(value * length)

    @staticmethod
    def test():
        imgPath = r"D:\ComfyUI_windows_portable_nightly_pytorch\ComfyUI\output\ComfyUI_01709_.png"
        duration = 12
        to = imgPath + ".mp4"
        MovieMakerUtils.imageToVideo(imgPath, duration, to)
        # vpath = 'D:/BaiduNetdiskDownload/clip.mp4'
        # vpath2 = 'D:/BaiduNetdiskDownload/clip2.mp4'
        # toPath = 'D:/BaiduNetdiskDownload/clip3.mp4'
        # video1 = VideoFileClip(vpath).subclip(0, 13)
        # video2 = VideoFileClip(vpath2).subclip(0, 10)
        # resized = video2.resize(0.5).set_position((50, 50)).set_start(2)
        # fullscreensize = video1.size
        # animation = MovieMakerUtils.animationsTo(resized, [(100, 50), (400, 100)], [(100, 100), (200, 200)], [1, 2])
        # # enlarged = enlargeFullScreen(resized, fullscreensize, 1)
        # composited = CompositeVideoClip([video1, animation])
        #
        # if Path(toPath).exists():
        #     os.remove(toPath)
        # composited.write_videofile(toPath)
        # print(resized.size)
        pass

if __name__ == '__main__':
    # concatevideo()
    # text = TextClip("克拉戴假发恋爱记", font="C:\\Users\\Administrator\\AppData\\Local\\Microsoft\\Windows\\Fonts\\hanyialitifan.ttf",bg_color='black', color='white', align='center', stroke_color='black', fontsize=80, size=(1920, 1080))
    # text = text.set_fps(5).set_duration(5)
    # text.write_videofile('r:/fonttest.mp4')
    # print(TextClip.list('font'))
    MovieMakerUtils.test()

