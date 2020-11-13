# -*- coding: utf-8 -*-
# @Time    : 20-10-21
# @Author  : 边中鉴

import pyaudio
import numpy as np
from scipy import fftpack
import wave


# 录音
# 录音必须安装portaudio模块，否则会报错
# http://portaudio.com/docs/v19-doxydocs/compile_linux.html

class sound_recording:
    CHUNK = 2000  # 块大小
    FORMAT = pyaudio.paInt16  # 每次采集的位数
    CHANNELS = 1  # 声道数
    RATE = 8000  # 采样率：每秒采集数据的次数
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    def recording(self, filename, time=2, threshold=7000):
        """
        :param filename: 文件名
        :param time: 录音时间,如果指定时间，按时间来录音，默认为自动识别是否结束录音
        :param threshold: 判断录音结束的阈值
        :return:
        """
        RECORD_SECONDS = time  # 录音时间
        WAVE_OUTPUT_FILENAME = filename  # 文件存放位置
        print("* 录音中...")
        frames = []
        for i in range(0, int(self.RATE / self.CHUNK * RECORD_SECONDS)):
            data = self.stream.read(self.CHUNK)
            frames.append(data)
        stopflag = 0
        stopflag2 = 0
        while True:
            data = self.stream.read(self.CHUNK)
            rt_data = np.frombuffer(data, np.dtype('<i2'))
                # print(rt_data*10)
                # 傅里叶变换
            fft_temp_data = fftpack.fft(rt_data, rt_data.size, overwrite_x=True)
            fft_data = np.abs(fft_temp_data)[0:fft_temp_data.size // 2 + 1]

                # 测试阈值，输出值用来判断阈值
                # print(sum(fft_data) // len(fft_data))

                # 判断麦克风是否停止，判断说话是否结束，# 麦克风阈值，默认7000
            if sum(fft_data) // len(fft_data) > threshold:
                stopflag += 1
            else:
                stopflag2 += 1
            oneSecond = int(self.RATE / self.CHUNK)
            if stopflag2 + stopflag > oneSecond:
                if stopflag2 > oneSecond // 3 * 2:
                    break
                else:
                    stopflag2 = 0
                    stopflag = 0
            frames.append(data)
        print("* 录音结束")
        wf=wave.open(WAVE_OUTPUT_FILENAME,'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
    def luexit(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()


#recording('ppp.mp3', time=5)  # 按照时间来录音，录音5秒
#recording('ppp.mp3')  # 没有声音自动停止，自动停止