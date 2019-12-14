import cv2
import numpy

class myKalmanFilter(object):
    def __init__(self):
        self.kalman=cv2.KalmanFilter(4,2,0)
        #观测矩阵
        self.kalman.measurementMatrix=1.*numpy.eye(2,4)
        #转移矩阵
        self.kalman.transitionMatrix=numpy.array([[1.,0.,.1,0.],
                                                  [0.,1.,0.,.1],
                                                  [0.,0.,1.,0.],
                                                  [0.,0.,0.,1.]])
        #过程噪声协方差矩阵
        self.kalman.processNoiseCov=1e-5*numpy.eye(4,4)
        #测量噪声协方差矩阵
        self.kalman.measurementNoiseCov=1e-3*numpy.eye(2,2)
        #状态误差协方差矩阵
        self.kalman.errorCovPost=1e-1*numpy.eye(4,4)

        self.kalman.statePost=numpy.array([0,0,0,0],dtype='float64')


    def correct(self,x,y):
        current_measurment = (numpy.dot(self.kalman.measurementNoiseCov, numpy.random.randn(2, 1))).reshape(-1)
        current_measurment = numpy.dot(self.kalman.measurementMatrix, numpy.array([x, y, 0, 0])) + current_measurment
        self.kalman.correct(current_measurment)

    def prediction(self):
        return self.kalman.predict()



