#coding=utf-8
#接收方（客户端）
import socket
import threading
import cv2
import numpy
import struct
import time
import pygame


#定义全局变量
img_buf=numpy.uint8(numpy.ones((480,640,3)))
status=""
target_area=()
CLOSE=False
ip=""
port=""

def Client_Init():
    global ip,port
    tcp_client_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    # server_ip=raw_input("输入服务器IP地址：")
    # server_port=int(raw_input("输入服务器端口号:"))
    server_ip = str(ip)
    server_port = int(str(port))
    server_address=(server_ip,server_port)
    tcp_client_socket.connect(server_address)
    print "成功链接服务器\n"
    return tcp_client_socket


class Client_Recv_(threading.Thread):
    def __init__(self,socket,lock):
        super(Client_Recv_, self).__init__()
        self.socket=socket
        self.lock=lock
        self.__frame_total=0


    def run(self):
        global img_buf
        while True:
            recv_content=self.socket.recv(4)
            head=struct.unpack("I",recv_content)[0]
            self.__img_size =head
            self.__img=''
            # if head<200000:
            while True:
                self.__img+=self.socket.recv(head)
                # print "第%d帧图片大小为%d,现在接收到的大小为%d" % (self.__frame_total + 1, self.__img_size, len(self.__img))
                if len(self.__img)<self.__img_size:
                    head=self.__img_size-len(self.__img)
                elif len(self.__img)==self.__img_size:
                    array_img=numpy.fromstring(self.__img,numpy.uint8)
                    img_buf=cv2.imdecode(array_img,1)
                    self.__frame_total+=1
                    # print "完成第%d帧的解释"%self.__frame_total
                    break
            if CLOSE==True:
                self.socket.close()
                break


def on_mouse(event, x, y, flags, param):
    global p1,p2,cut_img,target_area
    img=img_buf.copy()
    if event==cv2.EVENT_LBUTTONDOWN and status=="0":
        print "左键点击"
        p1=(x,y)
        cv2.imshow("Video",img)
    elif event==cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON) and status=="0":
        print "拖动"
        cv2.rectangle(img,p1,(x,y),(0,0,255),2)
        cv2.imshow("Video",img)
    elif event==cv2.EVENT_LBUTTONUP and status=="0":
        print "左键松开"
        p2=(x,y)
        # cv2.rectangle(img,p1,p2,(0,0,255),2)
        cv2.imshow("Video",img)
        min_x = min(p1[0], p2[0])
        min_y = min(p1[1], p2[1])
        width = abs(p1[0] - p2[0])
        height = abs(p1[1] - p2[1])
        cut_img = img[min_y:min_y + height, min_x:min_x + width]
        cv2.imwrite('upload.png', cut_img)
        target_area=p1+p2
        print target_area
        print "完成截取"

def Show_Mode(img,mode):
    cv2.putText(img,str(mode), (10, 30), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 1)
    return img

def Client_Show_Send(socket):
    global img_buf,status,CLOSE
    cut_img = numpy.uint8(numpy.ones((100, 100, 3)))
    while True:
        # t1=cv2.getTickCount()
        # t2=cv2.getTickCount()
        # t=(t2-t1)/cv2.getTickFrequency()
        # print "图片处理耗时:%.2f"%t
        if status=="":
            img=Show_Mode(img_buf,"waiting")
        elif status=="0":
            img=Show_Mode(img_buf,"adjusting")
        elif status=="1":
            img=Show_Mode(img_buf,"controling")
        elif status=="2":
            img=Show_Mode(img_buf,"tracking")
        else:
            img=img_buf
        cv2.imshow("Video",img)
        key=cv2.waitKey(40)

        if status=="" and key==96:
            socket.send("0")
            status="0"
            print "调节状态"
        elif status == "" and key == 49:
            socket.send("1")
            status = "1"
            print "控制状态"
        elif status == "" and key == 50:
            socket.send("2")
            status = "2"
            print "跟随状态"
        elif status=="" and key==27:
            CLOSE=True
            break
        elif status=="":
            socket.send("c")


        elif status == "0" and key == 99:
            socket.send("c")
            status = ""
            print "等待状态"
        elif status == "1" and key == 99:
            socket.send("c")
            status = ""
            print "等待状态"
        elif status == "2" and key == 99:
            socket.send("c")
            time.sleep(1)
            status = ""
            print "等待状态"


        elif status=="0" and key==113:
            cv2.imwrite(str(time.time()) + ".png", img_buf)
            print "照片储存成功"
        elif status=="0" and key==13:
            # aim_pic=cv2.imread("upload.png")
            # jpg_img = cv2.imencode(".jpg", aim_pic)
            # byte_img = jpg_img[1].tostring()
            # head = struct.pack("I", int(len(byte_img)))
            # socket.send(head + byte_img)
            # cut_img=aim_pic
            # print "确认传输"
            coordinate=struct.pack("IIII",target_area[0],target_area[1],target_area[2],target_area[3])
            socket.send(coordinate)
            print "确认传输"
            send=True
        elif status == "0":
            cv2.setMouseCallback("Video", on_mouse)


        elif status == "1" and key == (-1):
            socket.send("s")
        elif status == "1" and key == 119:
            socket.send("g")
        elif status == "1" and key == 115:
            socket.send("b")
        elif status == "1" and key == 97:
            socket.send("l")
        elif status == "1" and key == 100:
            socket.send("r")
        elif status == "1" and key == 105:
            socket.send("u")
        elif status == "1" and key == 107:
            socket.send("d")
        elif status == "1" and key == 106:
            socket.send("z")
        elif status == "1" and key == 108:
            socket.send("y")
        elif status =="1" and key==113:
            cv2.imwrite(str(time.time())+".png",img_buf)
            print "照片储存成功"

        elif status=="2" and key==113:
            cv2.imwrite(str(time.time()) + ".png", img_buf)
            print "照片储存成功"
        elif status=="2":
            socket.send("a")


class TextBox:
    def __init__(self, w, h, x, y, font=None, callback=None):
        """
        :param w:文本框宽度
        :param h:文本框高度
        :param x:文本框坐标
        :param y:文本框坐标
        :param font:文本框中使用的字体
        :param callback:在文本框按下回车键之后的回调函数
        """
        self.width = w
        self.height = h
        self.x = x
        self.y = y
        self.text = ""  # 文本框内容
        self.callback = callback
        # 创建
        self.__surface = pygame.Surface((w, h))
        # 如果font为None,那么效果可能不太好，建议传入font，更好调节
        if font is None:
            self.font = pygame.font.SysFont("arial", 35)  # 使用pygame自带字体
        else:
            self.font = font

    def draw(self, dest_surf):
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        dest_surf.blit(self.__surface, (self.x, self.y))
        dest_surf.blit(text_surf, (self.x, self.y + (self.height - text_surf.get_height())),
                       (0, 0, self.width, self.height))

    def key_down(self, event):
        unicode = event.unicode
        key = event.key

        # 退位键
        if key == 8:
            self.text = self.text[:-1]
            return

        # 切换大小写键
        if key == 301:
            return

        # 回车键
        if key == 13:
            if self.callback is not None:
                self.callback()
            return

        if unicode != "":
            char = unicode
        else:
            char = chr(key)

        self.text += char
        return self.text


def gui():
    # 英文文本框demo
    pygame.init()
    window = pygame.display.set_mode((640, 480))
    pygame.display.set_caption("Visual tracking and remote control car--upper cmputer                   by:JunHao Li")
    # 创建文本框
    text_box_ip = TextBox(200, 40, 200, 120)
    text_box_port = TextBox(200, 40, 200, 220)
    #用于设置ip，port的标题字体
    text_tag=pygame.font.SysFont("arial",35,True)
    text_ip=text_tag.render("ip address",1,(255,255,255))
    text_port=text_tag.render("port",1,(255,255,255))
    #用于设置按钮的字体
    text_button=pygame.font.SysFont("arial", 40,True)
    text_connect=text_button.render("connect",1,(255,255,255))
    text_exit=text_button.render("exit",1,(255,255,255))

    EXIT=False
    CLICK="0"
    connect_click=False
    exit_click=False
    global ip,port
    # 游戏主循环
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.pos[0]>=200 and event.pos[0]<=400:
                    if event.pos[1]>=120 and event.pos[1]<=155:
                        CLICK="IP"
                    elif event.pos[1]>=220 and event.pos[1]<=255:
                        CLICK="PORT"
                elif event.pos[1]>=345 and event.pos[1]<=385:
                    if event.pos[0]>=115 and event.pos[0]<265:
                        connect_click=True
                    elif event.pos[0]>=415 and event.pos[0]<=495:
                        exit_click=True
            elif event.type==pygame.MOUSEBUTTONUP:
                if event.pos[1]>=345 and event.pos[1]<=385:
                    if event.pos[0]>=115 and event.pos[0]<265:
                        connect_click = False
                    elif event.pos[0]>=415 and event.pos[0]<=495:
                        exit_click = False
            elif event.type == pygame.KEYDOWN:
                if CLICK=="IP":
                    ip=text_box_ip.key_down(event)
                elif CLICK=="PORT":
                    port=text_box_port.key_down(event)
                elif CLICK=="0":
                    pass
        if EXIT==True:
            pygame.quit()
            break
        pygame.time.delay(20)
        window.fill((0, 50, 0))
        #按钮显示
        if connect_click==False:
            pygame.draw.rect(window,(0,0,150),(115,345,150,40))
        #按下connect
        elif connect_click==True and len(ip)==11 and len(port)==4:
            pygame.draw.rect(window, (100, 0, 150), (115, 345, 150, 40))
            window.blit(text_connect, (120, 340))
            EXIT=True
        if exit_click==False:
            pygame.draw.rect(window, (0, 0, 150), (415, 345, 80, 40))
        #按下exit
        elif exit_click==True:
            pygame.draw.rect(window, (100, 0, 150), (415, 345, 80, 40))
            window.blit(text_exit, (420, 340))
            pygame.display.flip()
            exit()
        window.blit(text_connect, (120, 340))
        window.blit(text_exit, (420, 340))
        #文本框显示
        window.blit(text_ip,(50,120))
        window.blit(text_port,(135,220))
        #文本框内容显示
        text_box_ip.draw(window)
        text_box_port.draw(window)
        pygame.display.flip()


if __name__ == '__main__':
    gui()
    lock = threading.Lock()
    tcp_client_socket = Client_Init()
    recv = Client_Recv_(tcp_client_socket, lock)
    send=threading.Thread(target=Client_Show_Send,args=(tcp_client_socket,))
    recv.start()
    send.start()
