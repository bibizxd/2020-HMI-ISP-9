# -*- coding: utf-8 -*-
# author:           边中鉴&朱旭东&任锦涛
# pc_type           dell
# create_time:      2020/10/1 19:25

from aip import AipSpeech
class Translation:
    __APP_ID = '22767576' # 百度语音API
    __API_KEY = 'GP6G3nUYsLDGYHd5p3v2fFIG'
    __SECRET_KEY = 'bF0oyWZbc2dCqVsCs8I4Y1MjqCl8GtiY'
    
    __client = AipSpeech(__APP_ID, __API_KEY, __SECRET_KEY)
    
    def __get_file_content(self,filePath):
        with open(filePath, 'rb') as fp:
            return fp.read()
    
    def get_word(self,filePath):
        '''音频转文字，参数filePath为wav音频地址，返回双值：状态(1为转换成功)及转换后文本或错误信息'''
        word = self.__client.asr(self.__get_file_content(filePath),'wav',8000,{
            'lan': 'zh'
            }) # 参数：语音对象，文件格式，采样率，语种类型
    
        if word['err_no'] == 0: # 错误值为0（即正确）
            return 1,word['result'][0] # 返回 1 与 文本信息
        else:
            return 0,word['err_no'] # 否则返回 0 与 错误内容
        
    def __init__(self):
        pass

    def wordToFile(self,data,per,filepath,spd=5,pit=5,vol=5):
        result  = self.__client.synthesis(data, 'zh', 1, {
            'vol': vol,
            'spd':spd,
            'pit':pit,
            'per':per
        })
        # 识别正确返回语音二进制 错误则返回dict 参照下面错误码
        if not isinstance(result, dict):
            with open(filepath, 'wb') as f:
                f.write(result)
