import time
import traceback

import functools
from PyQt5.QtWidgets import QFileDialog,QMainWindow,QApplication,QMessageBox,QErrorMessage, QTableWidgetItem
from PyQt5.QtMultimedia import *
from PyQt5.QtGui import QPainter, QPixmap, QPen, QImage
from PyQt5.QtCore import QPoint, QThread, pyqtSignal
import cv2
import numpy as np
from PyQt5 import QtGui, QtCore
from mainUI import  Ui_QtWidgetsApplication1Class
# import tilt_flame_model_v2 as tfm
# import upright_flame_model_v3 as ufm
# import matplotlib.pyplot as plt
import plotdrawProcess
import multiprocessing

def alert(Qwidget, message):
    reply = QMessageBox.information(Qwidget, '提示', message, QMessageBox.Ok | QMessageBox.Close,
                                    QMessageBox.Close)


videoName = ""

closed = False
def close_handle(evt):
    global  closed
    time.sleep(2)
    closed = True
    print("close")


class MainPage(Ui_QtWidgetsApplication1Class, QMainWindow):
    def __init__(self):
        super(MainPage,self).__init__()
        self.setupUi(self)

        ## connect 函数
        self.action.triggered.connect(self.OpenVideo)
        self.actiond.triggered.connect(self.restartProcess)
        self.pushButton.clicked.connect(self.MarkSize)
        self.label_6.doubleClicked.connect(self.DoubleClick)
        self.pushButton_6.clicked.connect(self.CalculateRate)
        self.pushButton_7.clicked.connect(self.addThresholdValue_Color)
        self.pushButton_8.clicked.connect(self.addFireSize)
        self.pushButton_9.clicked.connect(self.setAutoAnalysisFireInfo)

        self.pushButton_3.clicked.connect(self.draw_rad_heat_flux_curve_FH1)
        self.pushButton_2.clicked.connect(self.draw_rad_heat_flux_curve_FV2)
        self.pushButton_4.clicked.connect(self.plot_abc)
        self.pushButton_10.clicked.connect(self.tilt_flame_hazardous_radius_xa)
        self.pushButton_11.clicked.connect(self.tilt_flame_hazardous_radius_xb)
        self.pushButton_12.clicked.connect(self.tilt_flame_hazardous_radius_xc)

        self.pushButton_5.clicked.connect(self.draw_rad_heat_flux_curve_Fh)
        self.pushButton_14.clicked.connect(self.flame_hazardous_radius_xa)
        self.pushButton_15.clicked.connect(self.draw_rad_heat_flux_vertical_view)
        self.pushButton_16.clicked.connect(self.draw_rad_heat_flux_curve_Fv)
        self.pushButton_13.clicked.connect(self.addHeatFluxParam)

        self.pushButton_17.clicked.connect(self.addRDistanceMax)
        self.pushButton_18.clicked.connect(self.addk)
        self.pushButton_19.clicked.connect(self.addT)
        self.pushButton_20.clicked.connect(self.addRadioThresholds)

        ## 内部用属性
        self.rateInX = 1
        self.rateInY = 1

        self.X1inPixel = 0
        self.X2inPixel = 0
        self.Y1inPixel = 0
        self.Y2inPixel = 0


        self.minBar = 0
        self.maxBar = 0


        self.fireHeight = 0
        self.fireWidget = 0
        self.fireAngel = 0
        self.fireHeatFluxparam = 0
        self.fireLayerDiameter =[]
        self.fireLayerHeight =[]
        self.R_distance_max = 50
        self.k = 1
        self.T = 100
        self.RadioThreshold = [1.6,4.0,12.5,25.0,37.5]

        self.paused = False
        self.moveMouse = False
        self.tableWidgetIndex = 1

        self.th = Thread(self)
        self.queue = multiprocessing.Queue()
        self.plotProcess = plotdrawProcess.PlotProcess(self.queue)
        self.plotProcess.run()

        self.algorithmMap = {"draw_rad_heat_flux_curve_FH1":False,
                            "draw_rad_heat_flux_curve_FV2" :False,
                            "plot_abc" : False,
                            "tilt_flame_hazardous_radius_xa":False,
                            "tilt_flame_hazardous_radius_xb":False,
                             "tilt_flame_hazardous_radius_xc":False,
                             "draw_rad_heat_flux_curve_Fh":False,
                             "draw_rad_heat_flux_curve_Fv":False,
                             "draw_rad_heat_flux_vertical_view":False,
                             "flame_hazardous_radius_xa":False
                             }

    def OpenVideo(self):

        try:

            global videoName
            videoName = QFileDialog.getOpenFileName(self,"选择视频文件")[0]
            #TODO: 判断视频文件后缀

            if(self.th.isRunning()):
                #TODO: 实现在视频播放时切换视频的功能
                self.th.CloseVideo()
                #self.th.closeSignal = False
            self.th.changePixmap.connect(self.setImage)
            self.th.changeSegmentPic.connect(self.setSegmentedPic)
            self.th.changeFireinfo.connect(self.fireInfo)
            self.th.changeFireLayerInfo.connect(self.fireLayerInfo)
            self.th.writeRequestandMsgToQueueSignal.connect(self.writeRequestandMsgToQueue)
            self.th.start()

        except Exception as e :
            alert(self,"请选择视频文件")
            traceback.print_exc()


    def restartProcess(self):
        self.queue = multiprocessing.Queue()
        self.plotProcess = plotdrawProcess.PlotProcess(self.queue)
        self.plotProcess.run()

    def DoubleClick(self):   #双击事件，视频暂停
        print("double Click")
        self.th.PauseVideo()


    def MarkSize(self):
        self.th.PauseVideo()
        self.moveMouse = True



    def mousePressEvent(self, event):
        if(self.moveMouse):
            print("mouse press")
            s = event.windowPos()
            #self.setMouseTracking(True)
            self.label_8.setText(str(s.x()))
            self.label_11.setText(str(s.y()))

            self.X1inPixel = int(s.x())
            self.Y1inPixel = int(s.y())

            self.lastPoint = (int(s.x()),int(s.y()))


    def mouseReleaseEvent(self, event):
        if(self.moveMouse):
            print("mouse release")
            s = event.windowPos()
            # self.setMouseTracking(True)
            self.label_5.setText(str(s.x()))
            self.label_12.setText(str(s.y()))

            self.X2inPixel = int(s.x())
            self.Y2inPixel = int(s.y())

            self.moveMouse = False
            self.endPoint = (int(s.x()),int(s.y()))

            # self.th.DrawRect(self.lastPoint, self.endPoint)



    def setImage(self, image):
        try:
            self.label_6.setPixmap(QPixmap.fromImage(image))
        except Exception as e:
            print(e)

    def setSegmentedPic(self, image):
        try:
            self.label_15.setPixmap(QPixmap.fromImage(image))
        except Exception as e:
            print(e)

    def CalculateRate(self):

        try:
            if(self.lineEdit.text() == "" or self.lineEdit_2.text()==""):
                alert(self, "请输入距离")
                return
            Xdistance,Ydistance = self.lineEdit.text(), self.lineEdit_2.text()

            XdisInPix = abs(self.X1inPixel-self.X2inPixel)
            YdisInPix = abs(self.Y1inPixel-self.Y2inPixel)

            self.rateInX = XdisInPix/float(Xdistance)
            self.rateInY = YdisInPix/float(Ydistance)
            self.label_7.setText("1:"+str(self.rateInX))
            self.label_13.setText("1:"+str(self.rateInY))


            #alert(self, "添加成功，正在计算比例")

        except Exception as e:
            print(e)

    def addThresholdValue_Grey(self):
        if(self.lineEdit_3.text()==""or self.lineEdit_4.text()==""):
            alert(self,"请输入阈值")
            return


        self.minBar = int(self.lineEdit_3.text())
        self.maxBar = int(self.lineEdit_4.text())



        self.th.setThresholdValue(self.minBar, self.maxBar)

          #print(self.minThresholdValueR,self.maxThresholdValueB)

        return


    def addThresholdValue_Color(self):
        if(self.lineEdit_3.text()==""or self.lineEdit_4.text()==""):
            alert(self,"请输入阈值")
            return


        minbar = self.lineEdit_3.text().split(",")
        maxbar = self.lineEdit_4.text().split(",")

        for i in range(3):
            minbar[i] = int(minbar[i])
            maxbar[i] = int(maxbar[i])

        self.minBar = minbar
        self.maxBar = maxbar

        self.th.setThresholdValue(self.minBar, self.maxBar)

          #print(self.minThresholdValueR,self.maxThresholdValueB)

        return


    def addFireSize(self):

        try:
            if(self.lineEdit_5.text()=="" or self.lineEdit_6.text()==""):
                alert(self,"请输入数据")
                return
            if ((not self.lineEdit_5.text().isnumeric()) or (not self.lineEdit_6.text().isnumeric())):
                alert(self,"请输入数据")
                return
            self.fireHeight = float(self.lineEdit_5.text())
            self.fireWidget = float(self.lineEdit_6.text())


        except Exception as e:
            print(e)

    def autoAnalysisFireSize(self):
        while(1):
            if(self.th.closeSignal):
                return
            if(self.th.paused):
                time.sleep(1)
                continue


    def fireInfo(self,height,width,angle):
        self.lineEdit_5.setText(str("{:.2f}".format(height / self.rateInY)))
        self.lineEdit_6.setText(str("{:.2f}".format(width / self.rateInX)))
        self.fireHeight = float("{:.2f}".format(height / self.rateInY))
        self.fireWidget = float("{:.2f}".format(width / self.rateInX))
        self.fireAngel =  angle
        self.label_19.setText(str(angle))
        self.algorithmMap["fireHeight"] = self.fireHeight
        self.algorithmMap["fireWidget"] = self.fireWidget
        self.algorithmMap["angle"] = self.fireAngel
        self.algorithmMap['R_distance_max'] = self.R_distance_max
        self.algorithmMap['k'] = self.k
        self.algorithmMap['RadioThreshold'] = self.RadioThreshold
        self.algorithmMap['layer_thickness'] = 10/self.rateInY
        try:
            if (self.tableWidgetIndex == 7):
                self.tableWidgetIndex = 1
            self.tableWidget.setItem(self.tableWidgetIndex, 0, QTableWidgetItem(str(self.tableWidgetIndex)))
            self.tableWidget.setItem(self.tableWidgetIndex, 1, QTableWidgetItem(str(self.fireHeight)))
            self.tableWidget.setItem(self.tableWidgetIndex, 2, QTableWidgetItem(str(self.fireWidget)))
            self.tableWidgetIndex += 1
        except Exception as e:
            print(e)

    def setAutoAnalysisFireInfo(self):
        self.th.autoAnalysisFireInfo = (not self.th.autoAnalysisFireInfo)

    def fireLayerInfo(self, fireLayerDiameter_, fireLayerHeight_):
        # print("setfirelayinfo")
        self.fireLayerDiameter =[float("{:.2f}".format(x/self.rateInX)) for x in fireLayerDiameter_]
        self.fireLayerHeight = [float("{:.2f}".format(x/self.rateInY)) for x in fireLayerHeight_]
        # self.fireLayerDiameter = fireLayerDiameter_
        # self.fireLayerHeight = fireLayerHeight_
        self.algorithmMap["fireLayerDiameter"] = self.fireLayerDiameter
        self.algorithmMap["fireLayerHeight"] = self.fireLayerHeight

    def addHeatFluxParam(self):
        if(self.lineEdit_7.text()==""):
            return
        self.fireHeatFluxparam = int(self.lineEdit_7.text())

    def writeRequestandMsgToQueue(self):
        # print("writeRequestandMsgToQueue")
        algorithmMapCopy = self.algorithmMap.copy()
        self.queue.put(algorithmMapCopy)
        # print(self.algorithmMap)
        for key in self.algorithmMap.keys():
            self.algorithmMap[key] = False


    def addRDistanceMax(self):
        self.R_distance_max = self.lineEdit_14.text()

    def addk(self):
        self.k = self.lineEdit_10.text()

    def addT(self):
        self.T = self.lineEdit_13.text()

    def addRadioThresholds(self):
        self.RadioThreshold.clear()
        self.RadioThreshold.append(self.lineEdit_15.text())
        self.RadioThreshold.append(self.lineEdit_16.text())
        self.RadioThreshold.append(self.lineEdit_20.text())
        self.RadioThreshold.append(self.lineEdit_21.text())
        self.RadioThreshold.append(self.lineEdit_22.text())

    ######### 算法函数
    def draw_rad_heat_flux_curve_FH1(self):
        # try:
        #     global closed
        #     fig = plt.figure()
        #     fig.canvas.mpl_connect('close_event', close_handle)
        #
        #     while(1):
        #         if(closed):
        #             plt.close()
        #             closed = False
        #             break
        #         if(self.fireHeight != 0 and self.fireWidget != 0 and self.fireAngel != 0 ):
        #             tfm.draw_rad_heat_flux_curve_FH1(self.fireHeight, self.fireWidget, self.fireAngel)
        #             # self.th.PauseVideo()
        #         else:
        #             break
        # except Exception as e:
        #     traceback.print_exc()
        self.algorithmMap["draw_rad_heat_flux_curve_FH1"] = True
        # print(self.algorithmMap)

    def draw_rad_heat_flux_curve_FV2(self):
        # global  closed
        # fig = plt.figure()
        # fig.canvas.mpl_connect('close_event', close_handle)
        #
        # while(1):
        #     if (closed):
        #         plt.close()
        #         closed = False
        #         break
        #     if (self.fireHeight != 0 and self.fireWidget != 0 and self.fireAngel != 0):
        #         tfm.draw_rad_heat_flux_curve_FV2(self.fireHeight, self.fireWidget, self.fireAngel)
        #         # self.th.PauseVideo()
        #     else:
        #         break
        #
        self.algorithmMap['draw_rad_heat_flux_curve_FV2'] = True

    def plot_abc(self):

        self.algorithmMap['plot_abc'] = True
        # global closed
        # fig = plt.figure()
        # fig.canvas.mpl_connect('close_event', close_handle)
        #
        # while (1):
        #
        #         # if (closed):
                #     plt.close()
                #     closed = False
                #     return
                # if (self.fireHeatFluxparam == 0):
                #     alert(self, "请先添加火焰热流值参数")
                #     return
                # if(self.fireHeight != 0 and self.fireWidget != 0 and self.fireAngel != 0):
                #     # time.sleep(0.5)
                #     # print("plot_abc")
                #     # print(self.fireHeight, self.fireWidget, self.fireAngel, self.fireHeatFluxparam)
                #     tfm.plot_abc(self.fireHeight, self.fireWidget, self.fireAngel, self.fireHeatFluxparam, fig)

                    # self.th.PauseVideo()
                    # else:
                    #     return


    def tilt_flame_hazardous_radius_xa(self):
        # global closed
        # fig = plt.figure()
        # fig.canvas.mpl_connect('close_event', close_handle)
        # while (1):
        #     if (closed):
        #         plt.close()
        #         closed = False
        #         break
        #     if (self.fireHeight != 0 and self.fireWidget != 0 and self.fireAngel != 0):
        #         # print(self.fireHeight,self.fireWidget)
        #         tfm.tilt_flame_hazardous_radius_xa(self.fireHeight, self.fireWidget, self.fireAngel, fig)
        #
        #     else:
        #         return
        self.algorithmMap['tilt_flame_hazardous_radius_xa'] = True

    def tilt_flame_hazardous_radius_xb(self):
        # global closed
        # fig = plt.figure()
        # fig.canvas.mpl_connect('close_event', close_handle)
        # while (1):
        #     if (closed):
        #         plt.close()
        #         closed = False
        #         return
        #     # print(self.fireHeight, self.fireWidget)
        #     if (self.fireHeight != 0 and self.fireWidget != 0 and self.fireAngel != 0):
        #         fig.canvas.set_window_title("热流辐射")
        #         tfm.tilt_flame_hazardous_radius_xb(self.fireHeight, self.fireWidget, self.fireAngel, fig)
        #         # self.th.PauseVideo()
        #     else:
        #         return
        self.algorithmMap['tilt_flame_hazardous_radius_xb'] = True

    def tilt_flame_hazardous_radius_xc(self):
        # global closed
        # fig = plt.figure()
        # fig.canvas.mpl_connect('close_event', close_handle)
        #
        # while (1):
        #     if (closed):
        #         plt.close()
        #         closed = False
        #         break
        #     # print(self.fireHeight, self.fireWidget)
        #     if (self.fireHeight != 0 and self.fireWidget != 0 and self.fireAngel != 0):
        #         tfm.tilt_flame_hazardous_radius_xc(self.fireHeight, self.fireWidget, self.fireAngel, fig)
        #         # self.th.PauseVideo()
        #     else:
        #         break
        self.algorithmMap['tilt_flame_hazardous_radius_xc'] = True

    ########################## ufm


    def draw_rad_heat_flux_curve_Fh(self):
        # global closed
        # fig = plt.figure()
        # fig.canvas.mpl_connect('close_event', close_handle)
        #
        # while (1):
        #     if (closed):
        #         plt.close()
        #         closed = False
        #         break
        #     if(self.fireLayerDiameter!= [] and self.fireLayerHeight!= []):
        #         print("draw_rad_heat_flux_curve_Fh")
        #         print(self.fireLayerDiameter)
        #         print(self.fireLayerHeight)
        #         layer_thickness = 10
        #         # ufm.draw_rad_heat_flux_curve_Fh(self.fireLayerDiameter, self.fireLayerHeight, 400, layer_thickness/self.rateInY)
        #         self.queue.put([self.fireLayerDiameter,self.fireLayerHeight, 400, layer_thickness/self.rateInY])
        #         # self.th.PauseVideo()
        #     else:
        #         break

        self.algorithmMap["draw_rad_heat_flux_curve_Fh"] = True

    def draw_rad_heat_flux_curve_Fv(self):
        # global closed
        # fig = plt.figure()
        # fig.canvas.mpl_connect('close_event', close_handle)
        # while (1):
        # if (closed):
        #     plt.close()
        #     closed = False
        #     # break
        # if (len(self.fireLayerDiameter) != 0 and len(self.fireLayerHeight) != 0):
        #     print("draw_rad_heat_flux_curve_Fv")
        #     layer_thickness = 10
        #     ufm.draw_rad_heat_flux_curve_Fv(self.fireLayerDiameter, self.fireLayerHeight,
        #                                     layer_thickness / self.rateInY, 1)
        #     # self.th.PauseVideo()
        # else:
        #     return
        self.algorithmMap["draw_rad_heat_flux_curve_Fv"] = True


    def draw_rad_heat_flux_vertical_view(self):
        # global closed
        # fig = plt.figure()
        # fig.canvas.mpl_connect('close_event', close_handle)
        #
        # while(1):
        #     if (closed):
        #         plt.close()
        #         closed = False
        #         break
        #     if(self.fireLayerDiameter != [] and self.fireLayerHeight != []):
        #         print("draw_rad_heat_flux_vertical_view")
        #         ufm.draw_rad_heat_flux_vertical_view(self.fireLayerDiameter, self.fireLayerHeight, 10, 1, fig)
        #         # self.th.PauseVideo()
        #         # break
        #     else:
        #         break
        self.algorithmMap['draw_rad_heat_flux_vertical_view'] = True

    def flame_hazardous_radius_xa(self):
        # global closed
        # fig = plt.figure()
        # fig.canvas.mpl_connect('close_event', close_handle)
        #
        # while(1):
        #     if (closed):
        #         plt.close()
        #         closed = False
        #         break
        #     if(self.fireLayerDiameter != [] and self.fireLayerHeight != []):
        #             print("flame_hazardous_radius_xa")
        #             layer_thickness = 10
        #             ufm.flame_hazardous_radius_xa(self.fireLayerDiameter, self.fireLayerHeight, layer_thickness/self.rateInY, fig)
        #             # self.th.PauseVideo()
        #     else:
        #         break
        self.algorithmMap['flame_hazardous_radius_xa'] = True

#####算法函数


class Thread(QThread):

    changePixmap = pyqtSignal(QtGui.QImage)
    changeSegmentPic = pyqtSignal(QtGui.QImage)
    changeFireinfo = pyqtSignal(int, int, int)
    changeFireLayerInfo = pyqtSignal(list, list)
    writeRequestandMsgToQueueSignal = pyqtSignal()


    paused = False
    closeSignal = False
    rgbImage = True
    width = 0
    height = 0
    minbar = []
    maxbar = []
    segmented = False
    autoAnalysisFireInfo = False
    def run(self):
        try:
            self.cap = cv2.VideoCapture(videoName)
            print(videoName)
            flameNum = 0
            while (self.cap.isOpened()==True):
                if(self.closeSignal == True):
                    return
                if(not self.paused):
                    ret, frame = self.cap.read()
                    flameNum = flameNum + 1
                    if ret:
                        self.rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) #在这里可以对每帧图像进行处理，

                        if(self.segmented):
                            segImg = self.processImage(self.rgbImage, flameNum)
                            self.changeSegmentPic.emit(segImg)
                            # cv2.waitKey(1)
                        self.width,self.height = self.rgbImage.shape[1],self.rgbImage.shape[0]
                        convertToQtFormat = QtGui.QImage(self.rgbImage.data, self.rgbImage.shape[1], self.rgbImage.shape[0], QImage.Format_RGB888)
                        currentCaputre = convertToQtFormat.scaled(self.width/2, self.height/2, QtCore.Qt.KeepAspectRatio)
                        self.changePixmap.emit(currentCaputre)


                        time.sleep(0.1) #控制视频播放的速度

                    else:
                        return
                else:
                    continue
            #self.cap.release()
        except Exception as e:
            traceback.print_exc()

    def PauseVideo(self):
        try:
            if(self.paused == True):
                self.paused = False
            else:
                self.paused = True
        except Exception as e:
            print(e)






    def processImage(self, img, flameNum):
        try:
            if(self.segmented):
                # print("haha")
                #在下面添加处理函数

                imgSepert = self.color_seperate(img, self.minbar, self.maxbar)
                imgContours = self.findContours(imgSepert, flameNum)
                convertToQtFormat = QtGui.QImage(imgContours.data, imgContours.shape[1], imgContours.shape[0], QImage.Format_Grayscale8)
                currentCaputre = convertToQtFormat.scaled(self.width/2, self.height/2, QtCore.Qt.KeepAspectRatio)

        except Exception as e:
            traceback.print_exc()
        return currentCaputre

    def CloseVideo(self):


        self.closeSignal = True
        self.cap.release()
        self.closeSignal = False
        return

    def color_seperate(self, image, minBar, maxBar):
        try:
            #print(type(minBar),type(maxBar))
            lower_bgr = np.array(minBar)  # 设定bgr下限
            upper_bgr = np.array(maxBar)  # 设定bgr上 限
            # print(lower_bgr,upper_bgr)
            mask = cv2.inRange(image, lowerb=lower_bgr, upperb=upper_bgr)  # 依据设定的上下限对目标图像进行二值化转换
            # cv2.imshow("0", mask)
            kernel1 = np.uint8(np.zeros((8, 8)))
            for x in range(7):
                kernel1[x, 2] = 1
                kernel1[2, x] = 1

            kernel = np.uint8(np.zeros((3, 3)))
            for x in range(3):
                kernel[x, 1] = 1;
                kernel[1, x] = 1;
            # 膨胀图像
            dilated = cv2.dilate(mask, kernel1)
            # 腐蚀图像
            eroded = cv2.erode(dilated, kernel);

            # mask = eroded
            # dst = cv2.bitwise_and(image, image, mask=mask)  # 将二值化图像与原图进行“与”操作；实际是提取前两个frame 的“与”结果，然后输出mask 为1的部分

        except Exception as e:
            traceback.print_exc()
        return eroded

    def findContours(self, img, flameNum):
        try:
            # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            # cv2.drawContours(img, contours, -1, (255, 0, 0), 3)
            maxArea = 0
            maxContour = None
            for i in contours:
                area = cv2.contourArea(i)
                # print(area)
                if (area > maxArea):
                    maxArea = area
                    maxContour = i
            # cv2.imshow('max',maxArea)
            if(maxContour is not None ):
                x, y, w, h = cv2.boundingRect(maxContour)
                if(self.autoAnalysisFireInfo == True):
                    # print(x,x+w,y,y+h)
                    try:
                        img = cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), 1)  #框选出火焰区域
                        roiArea = img[y:y+h, x:x+w]
                        angel = self.getFireAngel(roiArea) #获取火焰角度
                        self.changeFireinfo.emit(w,h,angel+10)
                        if(flameNum % 10 == 0):
                            fireLayerDiameter, fireLayerHeight = self.getFireLayerDiameter(roiArea,flameNum)  # 获取火焰每一层的宽度和高度
                            self.changeFireLayerInfo.emit(fireLayerDiameter, fireLayerHeight)
                            self.writeRequestandMsgToQueueSignal.emit()

                    except Exception as e:
                        traceback.print_exc()

                return  img
            # 用红色表示有旋转角度的矩形框架
            # rect = cv2.minAreaRect(maxContour)
            # box = cv2.cv.BoxPoints(rect)
            # box = np.int0(box)
            # cv2.drawContours(img, [box], 0, (0, 0, 255), 2)
            return img

        except Exception as e:
            traceback.print_exc()




    def threshold_demo(self,image,lowBar, highBar):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # ret, binary = cv2.threshold(gray,0,255,cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        # ret, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_TRIANGLE)
        # ret, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_TRUNC)
        ret, binary = cv2.threshold(gray, lowBar, highBar, cv2.THRESH_BINARY)


        print("阈值：", ret)
        # cv2.imshow("binary", binary)
        return binary

    def setThresholdValue(self,minBar_, maxBar_):
        self.minbar = minBar_
        self.maxbar = maxBar_
        self.segmented = True


    def getFireLayerDiameter(self, img, flameNum):
        preciseFireDiameter = []  # 包含每一个像素层的火焰宽度
        preciseFireHeight = []
        layer_thickness = 10

        layerNum = int(img.shape[1] / layer_thickness)  # 获取每层的高度
        for i in range(1, layerNum):
            preciseFireHeight.append(layer_thickness * i)
        preciseFireHeight.reverse()
        # print("layerNum:", layerNum)
        try:
            for row in img:
                # print(row)
                head = False
                tail = False
                length = len(row)
                for pix in range(length - 1):
                    if (head == False and row[pix] == 255):
                        head = pix
                    if (tail == False and row[length - pix - 1] == 255):
                        tail = length - pix
                    if (tail and head):
                        break
                preciseFireDiameter.append(tail - head)
                row[int((tail + head) / 2)] = 128
                # print(head, " ", tail, " ", (tail + head) / 2)
            # preciseFireDiameter = preciseFireDiameter.reverse()
            preciseFireDiameter.reverse()
            # cv2.imshow('b', img)
            # cv2.waitKey(0)
        except Exception as e:
            traceback.print_exc()

        roughFireDiameter = []
        layerNum = 0
        # if(type(preciseFireDiameter)==None):
        #     return [],[]
        for i in range(len(preciseFireDiameter)):
            layerNum = layerNum + preciseFireDiameter[i]
            if (i % 10 == 0):
                roughFireDiameter.append(int(layerNum / layer_thickness))
                layerNum = 0

        return roughFireDiameter, preciseFireHeight

    def getFireAngel(self,img):
        # cv2.imshow('a',img)


        rowLength = len(img)
        colLength = len(img[0])
        head = False
        tail = False
        for i in range(colLength):
            if(img[0][i] == 255 and head == False):
                head = i
            if(img[0][colLength-i-1] and tail == False):
                tail = i
            if(head and tail):
                break
        firstmiddle = int((head+tail)/2)

        head = False
        tail = False
        tailCol = rowLength -1
        for i in range(colLength):
            if (img[tailCol][i] == 255 and head == False):
                head = i
            if (img[tailCol][colLength - i - 1] and tail == False):
                tail = i
            if (head and tail):
                break
        import math
        secondMiddle = int((head+tail)/2)
        # print(rowLength,abs(firstmiddle-secondMiddle) )
        # print("angle: ",  math.degrees(math.atan(rowLength/abs(firstmiddle-secondMiddle))))

        angel = math.degrees(math.atan(rowLength / (abs(firstmiddle - secondMiddle)+1)))
        return angel