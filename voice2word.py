# -*- coding: utf-8 -*-
 
 
### 语音识别 百度API ###
# Home:https://ai.baidu.com/tech/speech/asr
# API: https://ai.baidu.com/docs#/ASR-Online-Python-SDK/top
# Q&A: https://ai.baidu.com/docs#/FAQ/a53b4698
# 在线文本转语音：https://developer.baidu.com/vcast
from aip import AipSpeech
import json
 
""" 你的 APPID AK SK （测试用，会过期的）"""
APP_ID = '22767576'
API_KEY = 'GP6G3nUYsLDGYHd5p3v2fFIG'
SECRET_KEY = 'bF0oyWZbc2dCqVsCs8I4Y1MjqCl8GtiY'
 
# AipSpeech是语音识别的Python SDK客户端
client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)  # 访问百度API，内置访问http的函数，并写死了URL路径
# 如果需要代理
'''
proxies = {
            "http": "代理地址1",
            "https": "代理地址2",
        }
client.setProxies(proxies)
'''
# client.setConnectionTimeoutInMillis( 10000 )  # 建立连接的超时时间（毫秒），默认不需要设置
# client.setSocketTimeoutInMillis(300000)  # 通过打开的连接传输数据的超时时间（毫秒）
 
 
# 语音识别：读取本地文件
def get_file_content(filePath):
    with open(filePath, 'rb') as fp:
        return fp.read()
 
# 上传 本地音频文件（SpeechToText.wav）
# 支持的格式：原始 PCM 的录音参数必须符合 16k 采样率、16bit 位深、单声道，支持的格式有：pcm（不压缩）、wav（不压缩，pcm编码）、amr（压缩格式）。
# 有长度限制（测试时尽量短一点）
response = client.asr(get_file_content('audio.wav'), 'wav', 16000, {
    # 1536：普通话(支持简单的英文识别)
    # 默认1537：普通话(纯中文识别)
    # 1737：英语
    # 1637：粤语
    'dev_pid': 1537,
})
 
# {'corpus_no': '6714166347641437907', 'err_msg': 'success.', 'err_no': 0, 'result': ['识别后的内容'], 'sn': '602626830571563263672'}
print( str(response) )
 
'''
语音原文 
tts = 'Hello everyone, I want to get a wife.'
识别结果：
'result': ['hello everyone I want to get a wife']
'''
