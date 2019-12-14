# -视觉跟踪遥控小车
1.实现功能：
  -图像无线回传功能
  -人为遥控功能
  -视觉跟踪功能
  
2.实现方法
2.1图像无线回传功能
     -使用TCP
     -树莓派小车作为服务器，上位机作为客户端
     -将小车摄像头采集到的图片压缩编码后发送给上位机，上位机将图片显示出来（小车为发送方，上位机为接收方）
2.2人为遥控功能
     -使用TCP
     -树莓派小车作为服务器，上位机作为客户端
     -双方设定好运动指令，上位机发送运动指令给小车，小车按照指令进行特定的驱动电机的动作（小车作为接收方，上位机作为发送方）
2.3视觉跟踪功能
     -功能有限，设计场合为目标颜色与背景颜色区分较大且目标运动不快
     -由于硬件电机（普通直流电机）及摄像头（单目摄像头，单台易产生摇晃）限制导致，工作方式为检测目标-运动特定时间-停下-检测目标，如此循环
     -半自动的跟踪方法，需在上位机手动框选出目标形状
     -以opencv的均值漂移方法（cv2.CamShift）来寻找目标位置，以opencv的模板匹配方法（cv2.matchTemplate）来判断目标，以基于模板库的模板更新方法            （Memory_Space）来更新模板，实现对目标的跟踪
     
