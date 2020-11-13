# pylint: disable=no-member
# -*- coding: utf-8 -*-
# author:           边中鉴&朱旭东&任锦涛
# pc_type           dell
# create_time:      2020/10/1 19:25
# github            https://github.com/inspurer

from face_recognition import WAS #导入主体功能类
from aip import AipSpeech#百度AI
import requests
import re
import os
import time
import wx
import wx.grid

app = wx.App()
frame = WAS()
frame.Show()
app.MainLoop()#主线程循环

