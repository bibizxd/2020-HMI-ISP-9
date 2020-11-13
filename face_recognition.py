# pylint: disable=no-member
# author:           边中鉴&朱旭东&任锦涛
# pc_type           dell
# create_time:      2020/10/1 19:25
import wx
import wx.grid
from wx.lib.pubsub import pub
import time
import sqlite3
from time import localtime, strftime
import os
from skimage import io as iio
import io
import zlib
import dlib  # 人脸识别的库dlib
import numpy as np  # 数据处理的库numpy
import cv2  # 图像处理的库OpenCv
import _thread
import threading
from wav import WWAV#音频播放
from translation import Translation
from playsound import playsound#音频播放
from Thread_sre import Thread_sre

ID_NEW_REGISTER = 160
ID_FINISH_REGISTER = 161

ID_START_PUNCHCARD = 190
ID_END_PUNCARD = 191

ID_OPEN_LOGCAT = 283
ID_CLOSE_LOGCAT = 284

ID_VOICE_WORD = 130
ID_VOICE_WORD_1 = 131
ID_WORD_VOICE = 132
ID_DELETE_MESSAGE = 133

ID_WORKER_UNAVIABLE = -1

PATH_FACE = "data/face_img_database/"
# face recognition model, the object maps human faces into 128D vectors
facerec = dlib.face_recognition_model_v1(
    "model/dlib_face_recognition_resnet_model_v1.dat")
# Dlib 预测器
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('model/shape_predictor_68_face_landmarks.dat')

user_now = -1
note2person = ""
wxexit = 1
notelist = ""

def return_euclidean_distance(feature_1, feature_2):
    feature_1 = np.array(feature_1)
    feature_2 = np.array(feature_2)
    dist = np.sqrt(np.sum(np.square(feature_1 - feature_2)))
    # print("欧式距离: ", dist)
    if dist > 0.4:
        return "diff"
    else:
        return "same"


w = WWAV()
x = Translation()

#下拉列表子窗口
class ComboxFrameDemo1(wx.Frame):
    def __init__(self, p, t,list):
        wx.Frame.__init__(self,
                        id=wx.NewId(),
                        parent=p,
                        size=(300, 150),
                        title=t)
        panel = wx.Panel(self, -1,style=wx.SUNKEN_BORDER)
        self.picture = wx.StaticBitmap(panel)
        panel.SetBackgroundColour(wx.WHITE)
        #加入两个按键
        wx.Button(panel, 1, '取 消', (130, 70))
        wx.Button(panel, 2, '确 定', (50, 70))
        self.label1 = wx.StaticText(parent=panel,
                                    id=-1,
                                    size=(100, 18),
                                    label=u"请选择需留言用户:",
                                    pos=(10, 10))
        candidates = list
        self.combo1 = wx.ComboBox(parent=panel,
                                id=-1,
                                size=wx.DefaultSize,
                                pos=(160, 10),
                                value="",
                                choices=candidates,
                                name=u"家庭成员名单")
        
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=1)
        self.Bind(wx.EVT_BUTTON, self.OK, id=2)
        #panel.Bind(wx.EVT_COMBOBOX,  self.__OnComboBoxSelected, self.combo1)

    def OnClose(self, event):
        self.Close()

    def OK(self, event):
        global note2person
        currentProvinceIndex = self.combo1.GetSelection()
        if wx.NOT_FOUND == currentProvinceIndex: return
        note2person = self.combo1.GetItems()[currentProvinceIndex]
        #print(note2person)
        self.Close()



class WAS(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None, title="家庭智能门禁", size=(920, 560))

        self.initMenu()
        self.initInfoText()
        self.initGallery()
        self.initDatabase()
        self.initData()
        # create a pubsub receiver
        pub.subscribe(self.updateDisplay,"update") 
        Thread_sre()

    def initData(self):
        self.name = ""
        self.id = ID_WORKER_UNAVIABLE
        self.face_feature = ""
        self.message = ""
        self.pic_num = 0
        self.flag_registed = False
        self.puncard_time = "21:00:00"
        self.loadDataBase(1)

    def initMenu(self):

        menuBar = wx.MenuBar()  # 生成菜单栏
        menu_Font = wx.Font()  # Font(faceName="consolas",pointsize=20)
        menu_Font.SetPointSize(14)
        menu_Font.SetWeight(wx.BOLD)

        registerMenu = wx.Menu()  # 生成菜单
        self.new_register = wx.MenuItem(registerMenu, ID_NEW_REGISTER, "新建录入")
        self.new_register.SetBitmap(wx.Bitmap("drawable/new_register.png"))
        self.new_register.SetTextColour("SLATE BLUE")
        self.new_register.SetFont(menu_Font)
        registerMenu.Append(self.new_register)

        self.finish_register = wx.MenuItem(
            registerMenu, ID_FINISH_REGISTER, "完成录入")
        self.finish_register.SetBitmap(
            wx.Bitmap("drawable/finish_register.png"))
        self.finish_register.SetTextColour("SLATE BLUE")
        self.finish_register.SetFont(menu_Font)
        self.finish_register.Enable(False)
        registerMenu.Append(self.finish_register)

        puncardMenu = wx.Menu()
        self.start_punchcard = wx.MenuItem(
            puncardMenu, ID_START_PUNCHCARD, "识别开门")
        self.start_punchcard.SetBitmap(
            wx.Bitmap("drawable/start_punchcard.png"))
        self.start_punchcard.SetTextColour("SLATE BLUE")
        self.start_punchcard.SetFont(menu_Font)
        puncardMenu.Append(self.start_punchcard)

        self.end_puncard = wx.MenuItem(puncardMenu, ID_END_PUNCARD, "取消识别")
        self.end_puncard.SetBitmap(wx.Bitmap("drawable/end_puncard.png"))
        self.end_puncard.SetTextColour("SLATE BLUE")
        self.end_puncard.SetFont(menu_Font)
        self.end_puncard.Enable(False)
        puncardMenu.Append(self.end_puncard)

        logcatMenu = wx.Menu()
        self.open_logcat = wx.MenuItem(logcatMenu, ID_OPEN_LOGCAT, "打开日志")
        self.open_logcat.SetBitmap(wx.Bitmap("drawable/open_logcat.png"))
        self.open_logcat.SetFont(menu_Font)
        self.open_logcat.SetTextColour("SLATE BLUE")
        logcatMenu.Append(self.open_logcat)

        self.close_logcat = wx.MenuItem(logcatMenu, ID_CLOSE_LOGCAT, "关闭日志")
        self.close_logcat.SetBitmap(wx.Bitmap("drawable/close_logcat.png"))
        self.close_logcat.SetFont(menu_Font)
        self.close_logcat.SetTextColour("SLATE BLUE")
        logcatMenu.Append(self.close_logcat)

        voiceMessage = wx.Menu()
        self.voice_word = wx.MenuItem(voiceMessage, ID_VOICE_WORD, "选择留言对象")
        self.voice_word.SetBitmap(wx.Bitmap("drawable/open_logcat.png"))
        self.voice_word.SetFont(menu_Font)
        self.voice_word.SetTextColour("SLATE BLUE")
        voiceMessage.Append(self.voice_word)

        self.voice_word_1 = wx.MenuItem(voiceMessage, ID_VOICE_WORD_1, "语音留言")
        self.voice_word_1.SetBitmap(wx.Bitmap("drawable/open_logcat.png"))
        self.voice_word_1.SetFont(menu_Font)
        self.voice_word_1.SetTextColour("SLATE BLUE")
        voiceMessage.Append(self.voice_word_1)

        self.word_voice = wx.MenuItem(voiceMessage, ID_WORD_VOICE, "留言读取")
        self.word_voice.SetBitmap(wx.Bitmap("drawable/close_logcat.png"))
        self.word_voice.SetFont(menu_Font)
        self.word_voice.SetTextColour("SLATE BLUE")
        voiceMessage.Append(self.word_voice)

        self.delete_message = wx.MenuItem(voiceMessage, ID_DELETE_MESSAGE, "留言清除")
        self.delete_message.SetBitmap(wx.Bitmap("drawable/close_logcat.png"))
        self.delete_message.SetFont(menu_Font)
        self.delete_message.SetTextColour("SLATE BLUE")
        voiceMessage.Append(self.delete_message)

        menuBar.Append(registerMenu, "&人脸录入")
        menuBar.Append(puncardMenu, "&刷脸识别")
        menuBar.Append(logcatMenu, "&门禁日志")
        menuBar.Append(voiceMessage, "&留言功能")
        self.SetMenuBar(menuBar)
        #绑定事件函数
        self.Bind(wx.EVT_MENU, self.OnNewRegisterClicked, id=ID_NEW_REGISTER)
        self.Bind(wx.EVT_MENU, self.OnFinishRegisterClicked,
                  id=ID_FINISH_REGISTER)
        self.Bind(wx.EVT_MENU, self.OnStartPunchCardClicked,
                  id=ID_START_PUNCHCARD)
        self.Bind(wx.EVT_MENU, self.OnEndPunchCardClicked, id=ID_END_PUNCARD)
        self.Bind(wx.EVT_MENU, self.OnOpenLogcatClicked, id=ID_OPEN_LOGCAT)
        self.Bind(wx.EVT_MENU, self.OnCloseLogcatClicked, id=ID_CLOSE_LOGCAT)
        self.Bind(wx.EVT_MENU, self.Voice2word, id=ID_VOICE_WORD)
        self.Bind(wx.EVT_MENU, self.Voice2word_1, id=ID_VOICE_WORD_1)
        self.Bind(wx.EVT_MENU, self.Word2voice, id=ID_WORD_VOICE)
        self.Bind(wx.EVT_MENU, self.Deletemessage, id=ID_DELETE_MESSAGE)
        self.Bind(wx.EVT_CLOSE,self.OnExit)
        #self.OnOpenLogcatClicked(ID_OPEN_LOGCAT)


    def OnOpenLogcatClicked(self, event):
        if user_now == ID_WORKER_UNAVIABLE:
            wx.MessageBox(message="未检测到用户,请进行识别", caption="警告")
        else:
            self.loadDataBase(2)
            # 必须要变宽才能显示 scroll
            self.SetSize(980, 560)
            grid = wx.grid.Grid(self, pos=(320, 0), size=(640, 500))
            grid.CreateGrid(100, 4)
            for i in range(100):
                for j in range(4):
                    grid.SetCellAlignment(i, j, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
            grid.SetColLabelValue(0, "序号")  # 第一列标签
            grid.SetColLabelValue(1, "姓名")
            grid.SetColLabelValue(2, "识别时间")
            grid.SetColLabelValue(3, "操作")

            grid.SetColSize(0, 120)
            grid.SetColSize(1, 120)
            grid.SetColSize(2, 150)
            grid.SetColSize(3, 150)

            grid.SetCellTextColour(1, 1, 'red')
            for i, id in enumerate(self.logcat_id):
                grid.SetCellValue(i, 0, str(id))
                grid.SetCellValue(i, 1, self.logcat_name[i])
                grid.SetCellValue(i, 2, self.logcat_datetime[i])
                grid.SetCellValue(i, 3, self.logcat_late[i])

            pass

    def OnCloseLogcatClicked(self, event):
        self.SetSize(920, 560)

        self.initGallery()
        pass

    def register_cap(self, event):
        # 创建 cv2 摄像头对象
        self.cap = cv2.VideoCapture(0)
        # cap.set(propId, value)
        # 设置视频参数，propId设置的视频参数，value设置的参数值
        # self.cap.set(3, 600)
        # self.cap.set(4,600)
        # cap是否初始化成功
        while self.cap.isOpened():
            # cap.read()
            # 返回两个值：
            #    一个布尔值true/false，用来判断读取视频是否成功/是否到视频末尾
            #    图像对象，图像的三维矩阵
            flag, im_rd = self.cap.read()
            # 每帧数据延时1ms，延时为0读取的是静态帧
            kk = cv2.waitKey(1)
            # 人脸数 dets
            dets = detector(im_rd, 1)
            # 检测到人脸
            if len(dets) != 0:
                biggest_face = dets[0]
                # 取占比最大的脸
                maxArea = 0
                for det in dets:
                    w = det.right() - det.left()
                    h = det.top()-det.bottom()
                    if w*h > maxArea:
                        biggest_face = det
                        maxArea = w*h
                        # 绘制矩形框
                cv2.rectangle(im_rd, tuple([biggest_face.left(), biggest_face.top()]),
                              tuple([biggest_face.right(),
                                     biggest_face.bottom()]),
                              (255, 0, 0), 2)
                img_height, img_width = im_rd.shape[:2]
                image1 = cv2.cvtColor(im_rd, cv2.COLOR_BGR2RGB)
                pic = wx.Bitmap.FromBuffer(img_width, img_height, image1)
                # 显示图片在panel上
                self.bmp.SetBitmap(pic)
                # 获取当前捕获到的图像的所有人脸的特征，存储到 features_cap_arr
                shape = predictor(im_rd, biggest_face)
                features_cap = facerec.compute_face_descriptor(im_rd, shape)
                # 对于某张人脸，遍历所有存储的人脸特征
                for i, knew_face_feature in enumerate(self.knew_face_feature):
                    # 将某张人脸与存储的所有人脸数据进行比对
                    compare = return_euclidean_distance(
                        features_cap, knew_face_feature)
                    if compare == "same":  # 找到了相似脸
                        self.infoText.AppendText(self.getDateAndTime()+"工号:"+str(self.knew_id[i])
                                                 + " 姓名:"+self.knew_name[i]+" 的人脸数据已存在\r\n" + '\n')
                        self.flag_registed = True
                        self.OnFinishRegister()
                        _thread.exit()
                        # print(features_known_arr[i][-1])
                face_height = biggest_face.bottom()-biggest_face.top()
                face_width = biggest_face.right() - biggest_face.left()
                im_blank = np.zeros((face_height, face_width, 3), np.uint8)
                try:
                    for ii in range(face_height):
                        for jj in range(face_width):
                            im_blank[ii][jj] = im_rd[biggest_face.top(
                            ) + ii][biggest_face.left() + jj]
                    # cv2.imwrite(path_make_dir+self.name + "/img_face_" + str(self.sc_number) + ".jpg", im_blank)
                    # cap = cv2.VideoCapture("***.mp4")
                    # cap.set(cv2.CAP_PROP_POS_FRAMES, 2)
                    # ret, frame = cap.read()
                    # cv2.imwrite("我//h.jpg", frame)  # 该方法不成功
                    # 解决python3下使用cv2.imwrite存储带有中文路径图片
                    if len(self.name) > 0:
                        cv2.imencode('.jpg', im_blank)[1].tofile(
                            PATH_FACE + self.name + "/img_face_" + str(self.pic_num) + ".jpg")  # 正确方法
                        self.pic_num += 1
                        print("写入本地：", str(PATH_FACE + self.name) +
                              "/img_face_" + str(self.pic_num) + ".jpg")
                        self.infoText.AppendText(self.getDateAndTime(
                        )+"图片:"+str(PATH_FACE + self.name) + "/img_face_" + str(self.pic_num) + ".jpg保存成功\r\n" + '\n')
                except:
                    print("保存照片异常,请对准摄像头")

                if self.new_register.IsEnabled():
                    _thread.exit()
                if self.pic_num == 10:
                    self.OnFinishRegister()
                    _thread.exit()

    def OnNewRegisterClicked(self, event):
        self.new_register.Enable(False)
        self.finish_register.Enable(True)
        self.loadDataBase(1)
        flag_1 = 0
        flag_2 = 0
        while self.id == ID_WORKER_UNAVIABLE:
            self.id = wx.GetNumberFromUser(message="请输入您的序号(-1不可用)",
                                           prompt="序号", caption="温馨提示",
                                           value=ID_WORKER_UNAVIABLE,
                                           parent=self.bmp, max=100000000, min=ID_WORKER_UNAVIABLE)
            for knew_id in self.knew_id:
                if knew_id == self.id:
                    self.id = ID_WORKER_UNAVIABLE
                    wx.MessageBox(message="序号已存在，请重新输入", caption="警告")
            print(self.id)
            if self.id == ID_WORKER_UNAVIABLE:
                flag_1 = 1
                break
        while self.name == '' and flag_1 == 0:
            self.name = wx.GetTextFromUser(message="请输入您的的姓名,用于创建姓名文件夹",
                                           caption="温馨提示",
                                           default_value="", parent=self.bmp)

            # 监测是否重名
            for exsit_name in (os.listdir(PATH_FACE)):
                if self.name == exsit_name:
                    wx.MessageBox(message="姓名文件夹已存在，请重新输入", caption="警告")
                    self.name = ''
                    break
            if self.name == '':
                flag_2 = 1
                break
        if flag_2 == 0 and flag_1 == 0:
            os.makedirs(PATH_FACE+self.name)
            _thread.start_new_thread(self.register_cap, (event,))
        else:
            self.id = ID_WORKER_UNAVIABLE
            self.name = ''
        pass

    def OnFinishRegister(self):

        self.new_register.Enable(True)
        self.finish_register.Enable(False)
        self.cap.release()

        self.bmp.SetBitmap(wx.Bitmap(self.pic_index))
        if self.flag_registed == True:
            dir = PATH_FACE + self.name
            for file in os.listdir(dir):
                os.remove(dir+"/"+file)
                print("已删除已录入人脸的图片", dir+"/"+file)
            os.rmdir(PATH_FACE + self.name)
            print("已删除已录入人脸的姓名文件夹", dir)
            self.initData()
            return
        if self.pic_num > 0:
            pics = os.listdir(PATH_FACE + self.name)
            feature_list = []
            feature_average = []
            for i in range(len(pics)):
                pic_path = PATH_FACE + self.name + "/" + pics[i]
                print("正在读的人脸图像：", pic_path)
                img = iio.imread(pic_path)
                img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                dets = detector(img_gray, 1)
                if len(dets) != 0:
                    shape = predictor(img_gray, dets[0])
                    face_descriptor = facerec.compute_face_descriptor(
                        img_gray, shape)
                    feature_list.append(face_descriptor)
                else:
                    face_descriptor = 0
                    print("未在照片中识别到人脸")
            if len(feature_list) > 0:
                for j in range(128):
                    # 防止越界
                    feature_average.append(0)
                    for i in range(len(feature_list)):
                        feature_average[j] += feature_list[i][j]
                    feature_average[j] = (
                        feature_average[j]) / len(feature_list)
                self.insertARow([self.id, self.name, feature_average], 1)
                self.infoText.AppendText(self.getDateAndTime()+"序号:"+str(self.id)
                                         + " 姓名:"+self.name+" 的人脸数据已成功存入\r\n" + '\n')
            pass

        else:
            os.rmdir(PATH_FACE + self.name)
            print("已删除空文件夹", PATH_FACE + self.name)
        self.initData()

    def OnFinishRegisterClicked(self, event):
        self.OnFinishRegister()
        pass

    def punchcard_cap(self, event):
        self.cap = cv2.VideoCapture(0)
        known_face = 0
        # cap.set(propId, value)
        # 设置视频参数，propId设置的视频参数，value设置的参数值
        # self.cap.set(3, 600)
        # self.cap.set(4,600)
        # cap是否初始化成功
        # while self.cap.isOpened():
        # 读取20帧图片
        for i in range(20):
            # cap.read()
            # 返回两个值：
            #    一个布尔值true/false，用来判断读取视频是否成功/是否到视频末尾
            #    图像对象，图像的三维矩阵
            flag, im_rd = self.cap.read()
            # 每帧数据延时1ms，延时为0读取的是静态帧
            kk = cv2.waitKey(1)
            # 人脸数 dets
            dets = detector(im_rd, 1)
            global user_now

            # 检测到人脸
            if len(dets) != 0:
                biggest_face = dets[0]
                # 取占比最大的脸
                maxArea = 0
                for det in dets:
                    w = det.right() - det.left()
                    h = det.top() - det.bottom()
                    if w * h > maxArea:
                        biggest_face = det
                        maxArea = w * h
                        # 绘制矩形框

                cv2.rectangle(im_rd, tuple([biggest_face.left(), biggest_face.top()]),
                              tuple([biggest_face.right(),
                                     biggest_face.bottom()]),
                              (255, 0, 255), 2)
                img_height, img_width = im_rd.shape[:2]
                image1 = cv2.cvtColor(im_rd, cv2.COLOR_BGR2RGB)
                pic = wx.Bitmap.FromBuffer(img_width, img_height, image1)
                # 显示图片在panel上
                self.bmp.SetBitmap(pic)

                # 获取当前捕获到的图像的所有人脸的特征，存储到 features_cap_arr
                shape = predictor(im_rd, biggest_face)
                features_cap = facerec.compute_face_descriptor(im_rd, shape)

                # 对于某张人脸，遍历所有存储的人脸特征
                for i, knew_face_feature in enumerate(self.knew_face_feature):
                    # 将某张人脸与存储的所有人脸数据进行比对
                    compare = return_euclidean_distance(
                        features_cap, knew_face_feature)
                    if compare == "same":  # 找到了相似脸
                        print("same")
                        known_face = 1
                        user_now = i
                        nowdt = self.getDateAndTime()

                        wx.MessageBox(message="门已打开，欢迎" +
                                      self.knew_name[i]+"回家", caption="警告")
                        self.insertARow(
                                [self.knew_id[i], self.knew_name[i], nowdt, "开门"], 2)
                        self.infoText.AppendText(nowdt+"当前使用者：" + self.knew_name[i] + '\n')
                        self.loadDataBase(2)
                        break
            if self.start_punchcard.IsEnabled() or known_face == 1:
                self.cap.release()
                self.bmp.SetBitmap(wx.Bitmap(self.pic_index))
                self.infoText.AppendText("即将播放留言" + '\n')
                data = self.message[user_now]
                if data == "":
                    wx.MessageBox(message="暂无留言", caption="警告")
                else:
                    x.wordToFile(data,1,"audio.mp3")
                    playsound('audio.mp3')
                    self.infoText.AppendText("留言播放结束" + '\n')
                _thread.exit()
        wx.MessageBox(message="未识别到家庭成员", caption="警告")
        self.cap.release()
        self.bmp.SetBitmap(wx.Bitmap(self.pic_index))
        _thread.exit()

    def OnStartPunchCardClicked(self, event):
        # cur_hour = datetime.datetime.now().hour
        # print(cur_hour)
        # if cur_hour>=8 or cur_hour<6:
        #     return
        self.start_punchcard.Enable(False)
        self.end_puncard.Enable(True)
        self.loadDataBase(2)
        threading.Thread(target=self.punchcard_cap, args=(event,)).start()
        # _thread.start_new_thread(self.punchcard_cap,(event,))
        pass

    def OnEndPunchCardClicked(self, event):
        global user_now,note2person
        self.start_punchcard.Enable(True)
        self.end_puncard.Enable(False)
        self.infoText.Clear()
        self.infoText.AppendText("当前无使用者"  + '\n')
        user_now = -1
        note2person = ""
        pass

    def initInfoText(self):
        # 少了这两句infoText背景颜色设置失败，莫名奇怪
        resultText = wx.StaticText(parent=self, pos=(10, 20), size=(90, 60))
        resultText.SetBackgroundColour('red')

        self.info = "\r\n"+self.getDateAndTime()+"程序初始化成功\r\n"
        # 第二个参数水平混动条
        self.infoText = wx.TextCtrl(parent=self, size=(320, 500),
                                    style=(wx.TE_MULTILINE | wx.HSCROLL | wx.TE_READONLY))
        # 前景色，也就是字体颜色
        self.infoText.SetForegroundColour("ORANGE")
        self.infoText.SetLabel(self.info)
        # API:https://www.cnblogs.com/wangjian8888/p/6028777.html
        # 没有这样的重载函数造成"par is not a key word",只好Set
        font = wx.Font()
        font.SetPointSize(12)
        font.SetWeight(wx.BOLD)
        font.SetUnderlined(True)

        self.infoText.SetFont(font)
        self.infoText.SetBackgroundColour('TURQUOISE')
        self.infoText.AppendText("当前无使用者" + '\n')
        pass

    def initGallery(self):
        self.pic_index = wx.Image(
            "drawable/index.png", wx.BITMAP_TYPE_ANY).Scale(600, 500)
        self.bmp = wx.StaticBitmap(parent=self, pos=(
            320, 0), bitmap=wx.Bitmap(self.pic_index))
        pass

    def getDateAndTime(self):
        dateandtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
        return "["+dateandtime+"]"

    def Voice2word(self, event):
        global note2person
        if user_now == ID_WORKER_UNAVIABLE:
            wx.MessageBox(message="未检测到用户,请进行识别", caption="警告")
        else:
            frame = ComboxFrameDemo1(None, "选择留言用户",self.knew_name)
            frame.Show(True)
            
    def Voice2word_1(self,event):
        global note2person,notelist
        if note2person != "":
            if notelist == "":
                self.infoText.AppendText("语音识别中" + '\n')
                w.my_record()
                condition, word = x.get_word("01.wav")  # 得到转换后的信息
                if condition == 1:
                    self.infoText.AppendText("转换内容为：" + word + '\n')
                    word = self.message[self.knew_name.index(note2person)]+"来自"+str(self.knew_name[user_now])+"的留言:"+word
                    self.addNote(word,note2person)
                else:
                    self.infoText.AppendText("等待语音录入"  + '\n')
            else:
                word = self.message[self.knew_name.index(note2person)]+"来自"+str(self.knew_name[user_now])+"的留言:"+notelist
                self.addNote(word,note2person)
            nowdt = self.getDateAndTime()
            self.insertARow(
                                [self.knew_id[user_now], self.knew_name[user_now], nowdt, "留言"], 2)
            self.loadDataBase(2)
            self.loadDataBase(1)
            note2person = ""
            notelist = ""
        else:
            wx.MessageBox(message="请选择留言对象", caption="警告")
        
    def Word2voice(self, event):
        self.loadDataBase(1)
        #(user_now)
        if user_now == ID_WORKER_UNAVIABLE:
            wx.MessageBox(message="未检测到用户,请进行识别", caption="警告")
        else:
            data = self.message[user_now]
            if data == "":
                wx.MessageBox(message="暂无留言", caption="警告")
            else:
                x.wordToFile(data,1,"audio.mp3")
                playsound('audio.mp3')

    def Deletemessage(self,event):
        if user_now == ID_WORKER_UNAVIABLE:
            wx.MessageBox(message="未检测到用户,请进行识别", caption="警告")
        else:
            self.deleteData(self.knew_id[user_now])

    def updateDisplay(self, msg):       
        #Receives data from thread and updates the display     
        t = msg
        if t == "开门":
            self.OnStartPunchCardClicked(ID_START_PUNCHCARD)
        elif t == "关门":
            self.OnEndPunchCardClicked(ID_END_PUNCARD)
        else:
            if user_now == ID_WORKER_UNAVIABLE:
                wx.MessageBox(message="未检测到用户,请进行识别", caption="警告")
            else:
                global note2person,notelist
                note2person = t[t.find("给")+1:t.find("留言")]
                notelist = t[t.find("留言")+2:]
                print(note2person+'/n')
                print(notelist+'/n')
                self.Voice2word_1(ID_VOICE_WORD_1)
        #----------------------------------------------------------------------
        # Run the program
    def OnExit(self, event):
        global wxexit
        self.Destroy()
        wxexit = 0
        wx.Exit()
    # 数据库部分
    # 初始化数据库

    def initDatabase(self):
        conn = sqlite3.connect("inspurer.db")  # 建立数据库连接
        cur = conn.cursor()  # 得到游标对象
        cur.execute('''create table if not exists worker_info
        (name text not null,
        id int not null primary key,
        face_feature array not null)''')
        cur.execute('''create table if not exists logcat
         (datetime text not null,
         id int not null,
         name text not null,
         late text not null)''')
        cur.close()
        conn.commit()
        conn.close()

    def adapt_array(self, arr):
        out = io.BytesIO()
        np.save(out, arr)
        out.seek(0)

        dataa = out.read()
        # 压缩数据流
        return sqlite3.Binary(zlib.compress(dataa, zlib.Z_BEST_COMPRESSION))

    def convert_array(self, text):
        out = io.BytesIO(text)
        out.seek(0)

        dataa = out.read()
        # 解压缩数据流
        out = io.BytesIO(zlib.decompress(dataa))
        return np.load(out)

    def insertARow(self, Row, type):
        conn = sqlite3.connect("inspurer.db")  # 建立数据库连接
        cur = conn.cursor()  # 得到游标对象
        if type == 1:
            cur.execute("insert into worker_info (id,name,face_feature,message) values(?,?,?,?)",
                        (Row[0], Row[1], self.adapt_array(Row[2]),""))
            print("写人脸数据成功")
        if type == 2:
            cur.execute("insert into logcat (id,name,datetime,late) values(?,?,?,?)",
                        (Row[0], Row[1], Row[2], Row[3]))
            print("写日志成功")
            pass
        cur.close()
        conn.commit()
        conn.close()
        pass
    def deleteData(self,id):
        conn = sqlite3.connect("inspurer.db")  # 建立数据库连接
        cur = conn.cursor()  # 得到游标对象
        cur.execute("update worker_info set message=? where id=?",("",id))
        print("清除留言成功")
        cur.close()
        conn.commit()
        conn.close()
        pass
    def addNote(self,word,name):
        conn = sqlite3.connect("inspurer.db")  # 建立数据库连接
        cur = conn.cursor()  # 得到游标对象
        cur.execute("update worker_info set message=? where name=?",(word,name))
        print("留言成功！")
        cur.close()
        conn.commit()
        conn.close()
        pass

    def loadDataBase(self, type):

        conn = sqlite3.connect("inspurer.db")  # 建立数据库连接
        cur = conn.cursor()  # 得到游标对象

        if type == 1:
            self.knew_id = []
            self.knew_name = []
            self.knew_face_feature = []
            self.message = []
            cur.execute('select id,name,face_feature,message from worker_info')
            origin = cur.fetchall()
            for row in origin:
                #print(row[0])
                self.knew_id.append(row[0])
                #print(row[1])
                self.knew_name.append(row[1])
                #print(self.convert_array(row[2]))
                self.knew_face_feature.append(self.convert_array(row[2]))
                #print(row[3])
                self.message.append(row[3])
        if type == 2:
            self.logcat_id = []
            self.logcat_name = []
            self.logcat_datetime = []
            self.logcat_late = []
            cur.execute('select id,name,datetime,late from logcat')
            origin = cur.fetchall()
            for row in origin:
                #print(row[0])
                self.logcat_id.append(row[0])
                #print(row[1])
                self.logcat_name.append(row[1])
                #print(row[2])
                self.logcat_datetime.append(row[2])
                #print(row[3])
                self.logcat_late.append(row[3])
        pass
