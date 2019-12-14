#coding=utf-8
#发送方（服务器）
import socket
import threading
import cv2
import time
import struct
import numpy
import re
import RPi.GPIO as GPIO
from _XiaoRGEEK_SERVO_ import XR_Servo
from MemorySpace import Memory_Space
# from myKalmanFilter import myKalmanFilter


#定义全局变量
img_buf=numpy.uint8(numpy.ones((480,640,3)))
recv_content="0"
CLOSE=False


#tcp套接字初始化
def Server_Init(ip_address,ip_port):
    tcp_server_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_add=(ip_address,ip_port)
    tcp_server_socket.bind(server_add)
    tcp_server_socket.listen(5)
    return tcp_server_socket


def Server_Send(socket,lock):
    global img_buf,CLOSE
    frame_total = 0
    capture = cv2.VideoCapture(0)
    print("摄像头初始化完毕")
    try:
        while True:
            ret, frame = capture.read()
            lock.acquire()
            img_buf=frame
            lock.release()
            jpg_img = cv2.imencode(".jpg", frame)
            byte_img = jpg_img[1].tostring()
            head = struct.pack("I", int(len(byte_img)))
            try:
                socket.send(head + byte_img)
            except:
                pass
            frame_total += 1
            # print "成功发送第%d帧,图片大小为%d,报头大小为%d" % (frame_total, int(len(byte_img)), int(len(head)))
            if CLOSE==True:
                break
        capture.release()
        socket.close()
        print("发送线程关闭")
        CLOSE=False
    except Exception as e:
        print ("发送线程错误:"), e
        lock.release()
        capture.release()
        socket.close()
        print ("传输错误,断开链接\n")


class Movtion(threading.Thread):
    def __init__(self,socket,lock):
        super(Movtion, self).__init__()
        self.socket = socket
        self.lock = lock
        self.IN1 = 19
        self.IN2 = 16
        self.IN3 = 21
        self.IN4 = 26
        self.ENA = 13
        self.ENB = 20
        self.ECHO=4
        self.TRIG=17
        self.__aim_pic=""
        self.__Car_Init()

        self.MS = Memory_Space()
        self.track_window = (0,0,img_buf.shape[0],img_buf.shape[1])
        self.rank=0
        self.cnt=0
        print ("----运动线程初始化完成----")

    def __Car_Init(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.IN1, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.IN2, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.IN3, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.IN4, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.ENA, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.ENB, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.ECHO,GPIO.IN,pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.TRIG,GPIO.OUT,initial=GPIO.LOW)
        self.pwmA = GPIO.PWM(self.ENA, 1000)
        self.pwmB = GPIO.PWM(self.ENB, 1000)
        self.pwmA.start(0)
        self.pwmB.start(0)
        print("电机驱动初始化完毕")
        self.servo = XR_Servo()
        # self.servo.XiaoRGEEK_ReSetServo()
        try:
            self.servo.XiaoRGEEK_SetServoAngle(7, 72)
            self.servo.XiaoRGEEK_SetServoAngle(8, 70)
        except:
            print("舵机初始化失败")

    def __Back(self):
        GPIO.output(self.IN1, True)
        GPIO.output(self.IN2, False)
        GPIO.output(self.IN3, True)
        GPIO.output(self.IN4, False)
        # print("Back")

    def __Go(self):
        GPIO.output(self.IN1, False)
        GPIO.output(self.IN2, True)
        GPIO.output(self.IN3, False)
        GPIO.output(self.IN4, True)
        # print("Go")

    def __Right(self):
        GPIO.output(self.IN1, True)
        GPIO.output(self.IN2, False)
        GPIO.output(self.IN3, False)
        GPIO.output(self.IN4, True)
        # print("Right")

    def __Left(self):
        GPIO.output(self.IN1, False)
        GPIO.output(self.IN2, True)
        GPIO.output(self.IN3, True)
        GPIO.output(self.IN4, False)
        # print("Left")

    def __Stop(self):
        GPIO.output(self.IN1, False)
        GPIO.output(self.IN2, False)
        GPIO.output(self.IN3, False)
        GPIO.output(self.IN4, False)

    def __Get_Distance(self):
        time.sleep(0.05)
        # print("超声波模块工作开始")
        GPIO.output(self.TRIG,GPIO.HIGH)
        time.sleep(0.000015)
        GPIO.output(self.TRIG,GPIO.LOW)
        while not GPIO.input(self.ECHO):
            pass
        t1=time.time()
        while GPIO.input(self.ECHO):
            pass
        t2=time.time()
        time.sleep(0.1)
        # print("超声波模块工作结束")
        return (t2-t1)*340/2*100


    def run(self):
        # try:
        global CLOSE
        while True:
            try:
                recv_content = str(self.socket.recv(1))[2:-1]
            except Exception as E:
                print("等待模式接收错误：",E)
                break
            if len(recv_content)==0:
                # CLOSE=True
                break
            if recv_content=="0":
                print ("进入调节状态,等待接收目标图片")
                while True:
                    print ("等待接收目标图片")
                    recv_aim_head = self.socket.recv(16)
                    if str(recv_aim_head)[2:-1]=="c":
                        # self.MS.Remenber(img_buf[coordinate[1]:coordinate[3],coordinate[0]:coordinate[2]])
                        self.cnt=0
                        print ("返回等待状态")
                        break
                    coordinate = struct.unpack("IIII", recv_aim_head)
                    self.track_window=coordinate
                    print(coordinate)
            elif recv_content=="1":
                self.pwmA.ChangeDutyCycle(75)
                self.pwmB.ChangeDutyCycle(75)
                print("PWM信号占空比调整完毕")
                up_down=45
                right_left=72
                print("进入控制状态")
                while True:
                    try:
                        recv_content = str(self.socket.recv(1))[2:-1]
                        if recv_content=="c":
                            print ("返回等待状态")
                            break
                        elif recv_content=="s":
                            self.__Stop()
                        elif recv_content=="g":
                            self.__Go()
                        elif recv_content=="b":
                            self.__Back()
                        elif recv_content=="l":
                            self.__Left()
                        elif recv_content=="r":
                            self.__Right()
                        elif recv_content == "u":
                            up_down += 5
                            if up_down >= 160:
                                up_down = 160
                            self.servo.XiaoRGEEK_SetServoAngle(8, up_down)
                        elif recv_content == "d":
                            up_down -= 5
                            if up_down <= 25:
                                up_down = 25
                            self.servo.XiaoRGEEK_SetServoAngle(8, up_down)
                        elif recv_content == "z":
                            right_left += 5
                            if right_left >= 160:
                                right_left = 160
                            self.servo.XiaoRGEEK_SetServoAngle(7, right_left)
                        elif recv_content == "y":
                            right_left -= 5
                            if right_left <= 20:
                                right_left = 20
                            self.servo.XiaoRGEEK_SetServoAngle(7, right_left)
                    except:
                        print("舵机运动错误")
            elif recv_content=="2":
                #设定pwm占空比(设定运动速度)
                self.pwmA.ChangeDutyCycle(45)
                self.pwmB.ChangeDutyCycle(45)
                #运动相关状态初始化
                run = False
                run_coordinate = (0, 0)
                center_distance = 20

                #初始化预测坐标
                prediction=[0,0]
                #带跟踪目标处理
                self.lock.acquire()
                roi=current_img=img_buf[self.track_window[1]:self.track_window[3],self.track_window[0]:self.track_window[2]]
                self.lock.release()
                # self.MS.Remenber(img_buf[self.track_window[1]:self.track_window[3],self.track_window[0]:self.track_window[2]])
                cv2.imwrite("roi.png",roi)
                roi_hsv=cv2.cvtColor(roi,cv2.COLOR_RGB2HSV)
                mask=cv2.inRange(roi_hsv,numpy.array([70,43,46]),numpy.array([180,255,255]))
                roi_hist=cv2.calcHist([roi_hsv],[0],mask,[16],[0,180])
                roi_hist=cv2.normalize(roi_hist,roi_hist,0,255,cv2.NORM_MINMAX)
                term=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,20,1)

                kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(10,10))

                window_width=img_buf.shape[1]
                window_height=img_buf.shape[0]

                rec_lower=[0,0]
                rec_upper=[0,0]

                track_window_lower = [0,0]
                track_window_upper = [window_width,window_height]

                template=[roi,1]


                Turn=""
                #记录丢失的次数
                lose_time=0

                #增加目标边界信息
                boundary_add=3

                first_lost=(0,0)
                first_lost_get=(0,0)

                #用于记录上次运动是否转向
                which_side=''
                print("进入跟踪状态")
                while True:
                    #查看是否接收到退出指令
                    recv_content=str(self.socket.recv(1000))[2:-1]
                    ret=re.match("[c]",recv_content)
                    if ret!=None:
                        self.__aim_pic = template[0]
                        print ("返回等待状态")
                        # self.socket.send("o")
                        break
                    # time.sleep(0.1)
                    t1=cv2.getTickCount()
                    #图片预处理
                    img=img_buf
                    p1=cv2.getTickCount()
                    track_img=img[track_window_lower[1]:track_window_upper[1],track_window_lower[0]:track_window_upper[0]]
                    print("track_img.shape:",track_img.shape)
                    print("template[0].shape",template[0].shape)
                    hsv=cv2.cvtColor(track_img,cv2.COLOR_RGB2HSV)
                    black=cv2.inRange(hsv,numpy.array([0,0,0]),numpy.array([180,255,46]))
                    white=cv2.bitwise_not(black)
                    dst=cv2.calcBackProject([hsv],[0],roi_hist,[0,180],1)
                    dst=cv2.erode(dst,kernel)
                    # dst=cv2.morphologyEx(dst,cv2.MORPH_OPEN,kernel)
                    dst&=white
                    #均值漂移
                    print("self.track_window_lower:", track_window_lower)
                    print("self.track_window_upper:", track_window_upper)
                    pts,track_window=cv2.CamShift(dst,self.track_window,term)
                    p8 = cv2.getTickCount()
                    print("total:%.6f" % float((p8 - p1) / cv2.getTickFrequency()))
                    self.cnt+=1
                    #坐标处理，防止坐标越界
                    pts = numpy.int32(cv2.boxPoints(pts))
                    print(pts)
                    x_list = []
                    y_list = []
                    for num in list(pts):
                        x_list.append(num[0])
                        y_list.append(num[1])
                    if pts[0][0]!=pts[1][0]!=pts[2][0]!=pts[3][0] and pts[0][1]!=pts[1][1]!=pts[2][1]!=pts[3][1]:
                        rec_lower = [x_list[int(numpy.argmin(numpy.array(x_list)))],y_list[int(numpy.argmin(numpy.array(y_list)))]]
                        rec_upper = [x_list[int(numpy.argmax(numpy.array(x_list)))],y_list[int(numpy.argmax(numpy.array(y_list)))]]
                    else:
                        print("@@@@@@@@检测错误，本帧检测结果失效@@@@@@@@")
                    print("rec_lower:",rec_lower)
                    print("rec_upper:",rec_upper)
                    rec_lower_show = [rec_lower[0] + track_window_lower[0]-boundary_add, rec_lower[1] + track_window_lower[1]-boundary_add]
                    rec_upper_show = [rec_upper[0] + track_window_lower[0]+boundary_add, rec_upper[1] + track_window_lower[1]+boundary_add]
                    # 坐标处理，防止坐标越界
                    if rec_lower_show[0] <= 0:
                        rec_lower_show[0] = 0
                    if rec_lower_show[1] <= 0:
                        rec_lower_show[1] = 0
                    if rec_upper_show[0] >= window_width:
                        rec_upper_show[0] = window_width
                    if rec_upper_show[1] >= window_height:
                        rec_upper_show[1] = window_height
                    print("rec_lower_show:",rec_lower_show)
                    print("rec_upper_show:",rec_upper_show)
                    #当前匹配的候选目标图片
                    #尝试将boundary_add变量在rec_lower_show及rec_upper_show中添加
                    current_img=img[rec_lower_show[1]:rec_upper_show[1],rec_lower_show[0]:rec_upper_show[0]]
                    print("current_img:",current_img.shape)
                    #等待模板稳定
                    if self.cnt<=3:
                        # 1.更新当前模板
                        template[0]=current_img
                        # 2.最后一次时储存模板
                        if self.cnt==3:
                            self.MS.Remenber(template[0])
                            self.rank=0
                            # kalman=myKalmanFilter()
                        run=False
                    #开始正式运行（正常匹配）
                    else:
                        # 判断是否为跟踪目标
                        val = self.MS.matchImg(template[0], current_img)
                        #匹配结果高于或等于阈值：
                        if val>=0.35:
                            if val>=0.55:
                                # template[0]=self.MS.Update_Template(template[0],val,current_img)
                                template[0]=current_img
                                self.MS.Change(template[0],self.rank)
                            else:
                                template,self.rank=self.MS.Recall(current_img,template[0],True)
                            #目标中心点
                            run_coordinate = (rec_lower_show[0] + int((rec_upper_show[0] - rec_lower_show[0]) / 2),rec_lower_show[1] + int((rec_upper_show[1] - rec_lower_show[1]) / 2))
                            #卡尔曼滤波处理
                            # prediction = kalman.prediction()
                            # prediction = (int(prediction[0]), int(prediction[1]))
                            # kalman.correct(rec_lower_show[0],rec_lower_show[1])
                            #框出卡尔曼预测范围
                            # cv2.rectangle(img,prediction,(prediction[0]+template[0].shape[1],prediction[1]+template[0].shape[0]),(50,255,0),2)
                            #目标绘制
                            cv2.rectangle(img, tuple(rec_lower_show), tuple(rec_upper_show), (255, 0, 0), 2)
                            cv2.circle(img, run_coordinate, 2, (0, 255, 0), 2)
                            # 截取下一帧图片部分
                            # width = rec_upper[0] - rec_lower[0]
                            # height = rec_upper[1] - rec_lower[1]
                            width = template[0].shape[1]
                            height = template[0].shape[0]
                            # 计算坐标
                            track_window_lower = [rec_lower_show[0] - int(width * 1.25),rec_lower_show[1] - int(height *0.5)]
                            track_window_upper = [rec_upper_show[0] + int(width * 1.25),rec_upper_show[1] + int(height *0.5)]
                            # 防止坐标越界
                            if track_window_lower[0] <= 0:
                                track_window_lower[0] = 0
                            elif track_window_lower[0] >= window_width - width:
                                track_window_lower[0] = window_width - width
                            if track_window_lower[1] <= 0:
                                track_window_lower[1] = 0
                            elif track_window_lower[1] >= window_height - height:
                                track_window_lower[1] = window_height - height

                            if track_window_upper[0] >= window_width:
                                track_window_upper[0] = window_width
                            elif track_window_upper[0] <= width:
                                track_window_upper[0] = width
                            if track_window_upper[1] >= window_height:
                                track_window_upper[1] = window_height
                            elif track_window_upper[1] <= height:
                                track_window_upper[1] = height
                            print("self.track_window_lower:", track_window_lower)
                            print("self.track_window_upper:", track_window_upper)
                            # 框出有效图片区域
                            cv2.rectangle(img, tuple(track_window_lower), tuple(track_window_upper), (255, 255, 255), 2)
                            # 跟踪窗口定义
                            self.track_window = (0, 0, track_window_upper[0] - track_window_lower[0],track_window_upper[1] - track_window_lower[1])
                            if(lose_time!=0):
                                first_lost_get=tuple(rec_lower_show)
                            # 目标丢失次数置零
                            lose_time = 0
                            # 运动标志位
                            run = True
                        #匹配结果小于阈值
                        else:
                            print("-----目标丢失------")
                            if current_img.shape[0]!=0 and current_img.shape[1]!=0:
                                template, fake_rank = self.MS.Recall(current_img, template[0])
                                if fake_rank:
                                    self.rank=fake_rank
                            lose_time+=1
                            #框出当前目标范围
                            cv2.rectangle(img, tuple(rec_lower_show), tuple(rec_upper_show), (255, 255, 0), 2)
                            #框出卡尔曼滤波目标范围
                            # prediction = kalman.prediction()
                            # prediction = (int(prediction[0]), int(prediction[1]))
                            # cv2.rectangle(img, prediction,(prediction[0] + template[0].shape[1], prediction[1] + template[0].shape[0]),(0, 255, 50), 2)
                            # 目标丢失处理
                            if lose_time<=2:
                                width = template[0].shape[1]
                                height = template[0].shape[0]
                                #上次运动无转向
                                if which_side=="N":
                                    track_window_lower = [prediction[0] - int(width * 1.75),prediction[1] - int(height * 1)]
                                    track_window_upper = [prediction[0] + int(width * 4.5),prediction[1] + int(height * 1)]
                                    # prediction = kalman.prediction()
                                    # prediction = (int(prediction[0]), int(prediction[1]))
                                    # kalman.correct(prediction[0], prediction[1])
                                    # cv2.rectangle(img, prediction, (prediction[0] + template[0].shape[1], prediction[1] + template[0].shape[0]),(0, 255, 50), 2)
                                    # run_coordinate = (prediction[0] + int((template[0].shape[1]) / 2),prediction[1] + int(template[0].shape[0] / 2))
                                    print("上次运动无转向，启用卡尔曼滤波预测位置")
                                    run=True
                                #上次运动向左转动
                                elif which_side=="L":
                                    track_window_lower = [rec_lower_show[0] - int(width * 1),rec_lower_show[1] - int(height*1.25)]
                                    track_window_upper = [rec_upper_show[0] + int(width * 2.5),rec_upper_show[1] + int(height*1.25)]
                                    print("上次运动左转，偏右对目标进行搜索")
                                    run=False
                                elif which_side=="R":
                                    track_window_lower = [rec_lower_show[0] - int(width * 2.5),rec_lower_show[1] - int(height*1.25)]
                                    track_window_upper = [rec_upper_show[0] + int(width * 1),rec_upper_show[1] + int(height*1.25)]
                                    print("上次运动右转，偏左对目标进行搜索")
                                    run=False
                                # 防止坐标越界
                                if track_window_lower[0] <= 0:
                                    track_window_lower[0] = 0
                                elif track_window_lower[0] >= window_width - width:
                                    track_window_lower[0] = window_width - width
                                if track_window_lower[1] <= 0:
                                    track_window_lower[1] = 0
                                elif track_window_lower[1] >= window_height - height:
                                    track_window_lower[1] = window_height - height

                                if track_window_upper[0] >= window_width:
                                    track_window_upper[0] = window_width
                                elif track_window_upper[0] <= width:
                                    track_window_upper[0] = width
                                if track_window_upper[1] >= window_height:
                                    track_window_upper[1] = window_height
                                elif track_window_upper[1] <= height:
                                    track_window_upper[1] = height
                                # 跟踪窗口定义
                                self.track_window = (0, 0, track_window_upper[0] - track_window_lower[0],track_window_upper[1] - track_window_lower[1])
                            #3.全局搜索
                            else:
                                if current_img.shape[0]>=template[0].shape[0] and current_img.shape[1]>=template[0].shape[1]:
                                    result=cv2.matchTemplate(current_img,template[0],cv2.TM_CCOEFF_NORMED)
                                    _,max_val,_,max_index=cv2.minMaxLoc(result)
                                    print("丢失寻找全局搜索方案:%.2f"%float(max_val))
                                    if max_val>=0.3:
                                        print("-----丢失寻找方案成功找回-----")
                                        max_index=(max_index[0]+rec_lower_show[0],max_index[1]+rec_lower_show[1])
                                        track_window_lower = [int(max_index[0]-template[0].shape[1]*0.75),int(max_index[1]-template[0].shape[0]*0.75)]
                                        track_window_upper = [int(max_index[0]+template[0].shape[1]*1.75),int(max_index[1]+template[0].shape[0]*1.75)]
                                        self.track_window = (0, 0, track_window_upper[0] - track_window_lower[0],track_window_upper[1] - track_window_lower[1])
                                        width = template[0].shape[1]
                                        height = template[0].shape[0]
                                        # 防止坐标越界
                                        if track_window_lower[0] <= 0:
                                            track_window_lower[0] = 0
                                        elif track_window_lower[0] >= window_width - width:
                                            track_window_lower[0] = window_width - width
                                        if track_window_lower[1] <= 0:
                                            track_window_lower[1] = 0
                                        elif track_window_lower[1] >= window_height - height:
                                            track_window_lower[1] = window_height - height

                                        if track_window_upper[0] >= window_width:
                                            track_window_upper[0] = window_width
                                        elif track_window_upper[0] <= width:
                                            track_window_upper[0] = width
                                        if track_window_upper[1] >= window_height:
                                            track_window_upper[1] = window_height
                                        elif track_window_upper[1] <= height:
                                            track_window_upper[1] = height
                                    elif max_val<0.3 and lose_time<=15:
                                        print("丢失寻找方案三")
                                        track_window_lower = [0, 0]
                                        track_window_upper = [window_width, window_height]
                                        self.track_window = (0, 0, track_window_upper[0] - track_window_lower[0],track_window_upper[1] - track_window_lower[1])
                                    elif max_val<0.3 and lose_time>15:
                                        print("丢失寻找方案四")
                                        Turn="right"
                                        track_window_lower = [0, 0]
                                        track_window_upper = [window_width, window_height]
                                        self.track_window = (0, 0, track_window_upper[0] - track_window_lower[0],track_window_upper[1] - track_window_lower[1])

                                else:
                                    print("当前识别范围小于模板大小")
                                    track_window_lower = [0, 0]
                                    track_window_upper = [window_width, window_height]
                                    self.track_window = (0, 0, track_window_upper[0] - track_window_lower[0],track_window_upper[1] - track_window_lower[1])
                                run=False
                    # 框出有效图片区域
                    cv2.rectangle(img, tuple(track_window_lower), tuple(track_window_upper), (255, 255, 255), 2)

                    t2 = cv2.getTickCount()
                    fps=cv2.getTickFrequency()/(t2-t1)
                    print("t=%.6f"%float(1/fps))
                    cv2.putText(img,"FPS:"+str(fps)[:4],(10,30),cv2.FONT_HERSHEY_COMPLEX,1,(0,0,255),1)
                    if self.cnt>=4:
                        cv2.putText(img,"match_val:"+str(val)[:5],(250,30),cv2.FONT_HERSHEY_COMPLEX,1,(0,0,255),1)
                    #图片中心位置框
                    cv2.rectangle(img, (int(window_width/ 2 - center_distance), int(window_height / 2 - center_distance)),(int(window_width / 2 + center_distance),int( window_height / 2 + center_distance)),(255, 0, 0), 1)
                    # cv2.imshow("black",black)
                    print("template.shape:",template[0].shape)
                    cv2.imshow("template",template[0])
                    # cv2.imshow("current_img",current_img)
                    # cv2.imshow("track_img",track_img)
                    cv2.imshow("dst",dst)
                    cv2.imshow("Video",img)
                    cv2.waitKey(5)
                    distance=self.__Get_Distance()
                    print ("距离障碍物 %d 厘米"%distance)

                    #运动状态控制部分
                    if run==True or Turn=="right":
                        if run_coordinate[0]<img.shape[1]/2-center_distance and Turn=="":
                            which_side="L"
                            print ("左转")
                            self.__Left()
                            time.sleep(0.125)
                            self.__Stop()
                        elif run_coordinate[0]>img.shape[1]/2+center_distance or Turn=="right":
                            which_side="R"
                            print ("右转")
                            self.__Right()
                            time.sleep(0.125)
                            self.__Stop()
                        else:
                            which_side="N"
                            print ("水平方向校准完成")
                            print (run_coordinate)
                        if run_coordinate[1]<img.shape[0]/2-center_distance and distance>=55 and Turn=="":
                            print ("前进")
                            self.__Go()
                            time.sleep(0.25)
                            self.__Stop()
                        elif run_coordinate[1]>img.shape[0]/2+center_distance and distance<=55 and Turn=="":
                            print ("后退")
                            self.__Back()
                            time.sleep(0.25)
                            self.__Stop()
                        else:
                            print ("垂直方向校准完成")
                            print (run_coordinate)
                        Turn = ""
                    print ("---------------------------------------------------")
        self.socket.close()
        # self.servo.XiaoRGEEK_ReSetServo()
        cv2.destroyAllWindows()
        CLOSE = True
        print("套接字关闭,接收与运动线程退出")
        # GPIO.cleanup()
        # except Exception as e:
        #     print ("接收与运动线程错误："),e
        #     GPIO.cleanup()


if __name__ == '__main__':
    lock = threading.Lock()
    tcp_server_socket = Server_Init('192.168.1.1',8877)
    print ("----服务器初始化成功----\n")
    thread_list=[]
    while True:
        print("等待客户端接入。。。")
        client_socket, client_add = tcp_server_socket.accept()
        print (str(client_add)+"连接成功\n" )
        send = threading.Thread(target=Server_Send, args=(client_socket, lock,))
        movtion=Movtion(client_socket,lock)
        send.start()
        thread_list.append(send)
        movtion.start()
        thread_list.append(movtion)

        for t in thread_list:
            t.join()

        GPIO.cleanup()

