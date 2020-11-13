# pylint: disable=no-member
import time
import wx
import threading
from wx.lib.pubsub import pub
from sound_recording import sound_recording
from translation import Translation
import face_recognition
########################################################################
x = Translation()
y = sound_recording()

class Thread_sre(threading.Thread):
#----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):             
        """Init Worker Thread Class."""      
        super(Thread_sre, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()     # 用于暂停线程的标识
        self.__flag.set()       # 设置为True
        self.__running = threading.Event()      # 用于停止线程的标识
        self.__running.set()      # 将running设置为True       
        self.start()   
        # start the thread      
        #----------------------------------------------------------------------
    
    def run(self):       
        """Run Worker Thread."""       
        # This is the code executing in the new thread.  
        while face_recognition.wxexit:
            y.recording('ppp.wav')  # 没有声音自动停止，自动停止   
            condition, word = x.get_word("ppp.wav")  # 得到转换后的信息
            print(word)
            if word.find("开门") >= 0:
                wx.CallAfter(pub.sendMessage,"update",msg="开门")
                time.sleep(3)
            elif word.find("关门") >= 0:
                wx.CallAfter(pub.sendMessage,"update",msg="关门")
            elif word.find("给") >= 0 and word.find("留言") >=0:
                wx.CallAfter(pub.sendMessage,"update",msg=word)

            
        '''
        for i in range(6):          
            time.sleep(10)        
            wx.CallAfter(self.postTime, i)  
            time.sleep(5)
        '''
        #----------------------------------------------------------------------    
    def pause(self):
        self.__flag.clear()     # 设置为False, 让线程阻塞

    def resume(self):
        self.__flag.set()    # 设置为True, 让线程停止阻塞

    def stop(self):
        self.__flag.set()       # 将线程从暂停状态恢复, 如何已经暂停的话
        self.__running.clear()        # 设置为False  

    def postTime(self , amt):              
        """       
        Send time to GUI
        """         
        amtOfTime = (amt + 1) * 10    
        pub.sendMessage("update" , msg=amtOfTime)
        ########################################################################
