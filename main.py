# -*- coding: utf-8 -*- 
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QPushButton, \
    QFileDialog, QDesktopWidget, QListWidget, QDialog, QLineEdit, QCheckBox, QComboBox
from PyQt5.QtGui import QBrush, QIcon, QPixmap, QPainter, QPen, QIntValidator
from PyQt5.QtCore import Qt, QRect, QPoint
import os, os.path
import cv2
import pandas
import shutil
import re 

class Main(QMainWindow):
    def __init__(self, parent=None):
        super(Main, self).__init__(parent)
        self.title = 'Image Annotation Tool for AI'
        self.width = 1420
        self.height = 820

        

        self.draw_rect = False

        self.draw_frame = QLabel(self)
        self.label = QLabel(self)
        self.label_tmp=QLabel(self)

        
        self.roi_annotation_list = QListWidget(self)
        self.roi_annotation_list.setStyleSheet("color: white;"
                        # "background-color: rgb(154,205,50);"
                        "background-color: black;"        
                        "selection-color: green;"
                        "font: 16px;"
                        "font-family: Comic Sans MS;"
                        "selection-background-color: black;")
        self.patient_information = QListWidget(self)
        self.patient_information.setStyleSheet("color: white;"
                        # "background-color: rgb(7, 78, 149);"
                        "background-color: black;"
                        "selection-color: blue;"
                        "font: 14px;"
                        "font-family: Comic Sans MS;"
                        "selection-background-color: black;")

        self.load_img=False

        self.begin, self.destination = QPoint(), QPoint()	

        self.ui_components()

        self.currentPatient = ""
        self.currentID = ""
        self.location = ""
        self.patientNo = "00000001"
        self.indexNo = "0000"
        self.parentFolder = ""
        self.nextPrevIndex = 0

        self.fileList = []
        self.text_list = []
        self.imageList = []

        self.fromNextOrPre = False

    def ui_components(self):
        self.resize(self.width, self.height)
        # self.setWindowFlag(Qt.FramelessWindowHint)
        self.center()
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(r'pic\icon\icon_win.png'))
        self.menu_bar()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def menu_bar(self):
        self.rectangle = QPushButton('Rectangle', self)
        self.rectangle.move(10, 23)
        self.rectangle.resize(105, 55)
        self.rectangle.setDisabled(True)
        self.rectangle.clicked.connect(self.draw_rectangle)
        
        self.load = QPushButton('Load Image', self)
        self.load.move(125, 23)
        self.load.resize(130, 55)
        self.load.clicked.connect(self.browse_image)

        self.save = QPushButton('Save Annotation', self)
        self.save.move(265, 23)
        self.save.resize(170, 55)
        self.save.setDisabled(True)
        # self.save.clicked.connect(self.save_annotation)
        
        self.delete = QPushButton('delete Annotation', self)
        self.delete.move(445, 23)
        self.delete.resize(170, 55)
        self.delete.setEnabled(False)
        self.delete.clicked.connect(self.delete_annotation)

        self.editPaientInfo = QPushButton('Edit Information', self)
        self.editPaientInfo.move(1000, 23)
        self.editPaientInfo.resize(150, 55)
        self.editPaientInfo.setDisabled(True)
        self.editPaientInfo.clicked.connect(self.editPatientInformation)

        self.downloadPatientInfo = QPushButton('Save Information', self)
        self.downloadPatientInfo.move(1170, 23)
        self.downloadPatientInfo.resize(150, 55)
        self.downloadPatientInfo.setDisabled(True)
        self.downloadPatientInfo.clicked.connect(self.downloadInfo)

        self.exit = QPushButton('Exit', self)
        self.exit.move(1340, 23)
        self.exit.resize(50, 55)
        self.exit.setStyleSheet("background-color: #C14242")
        self.exit.clicked.connect(self.exitbutton)

        self.next = QPushButton('Next', self)
        self.next.move(740, 450)
        self.next.resize(60,30)
        self.next.setVisible(False)
        self.next.clicked.connect(self.next_image)

        self.prev = QPushButton('Previous', self)
        self.prev.move(20, 450)
        self.prev.resize(60,30)
        self.prev.setVisible(False)
        self.prev.clicked.connect(self.prev_image)

        self.roi_annotation_list.move(830, 110)
        self.roi_annotation_list.resize(140, 700)
        self.roi_annotation_list.itemSelectionChanged.connect(self.roi_itemSelectionChange)

        self.patient_information.move(980, 110)
        self.patient_information.resize(430, 700)
        self.patient_information.itemSelectionChanged.connect(self.roi_itemSelectionChange)


        
    def roi_itemSelectionChange(self):        
        item = self.roi_annotation_list.currentItem()
        if(item == None):
            self.delete.setEnabled(False)
        else:
            self.delete.setEnabled(True)

    def delete_annotation(self):
        rn = self.roi_annotation_list.currentRow()

        counter = 0;
        
        draw_pixmap = QPixmap(self.label.size())
        draw_pixmap.fill(Qt.transparent)
        self.draw_frame.setPixmap(draw_pixmap)
        self.draw_frame.setGeometry(11, 110, draw_pixmap.size().width(), draw_pixmap.size().height())

        painter = QPainter(self.draw_frame.pixmap())
        
        del(self.annotation_content[self.roi_annotation_list.item(rn).text()])

        self.patient_information.clear()

        if rn==len(self.annotation_content):
            self.roi_annotation_list.clear()
            myKeys = list(self.annotation_content.keys())
            for j in range(len(myKeys)):
                self.roi_annotation_list.addItem(myKeys[j])
        else:
            oldKeys = list(self.annotation_content.keys())
            for i in range(len(self.annotation_content)):
                    self.annotation_content["Label_"+str(i)] = self.annotation_content[oldKeys[i]]
            del self.annotation_content[oldKeys[i]] 
            

            myKeys = list(self.annotation_content.keys())
            myKeys.sort(key = lambda l: int(re.search(r'\d+',l).group()))
            sort = {i: self.annotation_content[i] for i in myKeys}
            self.annotation_content = sort
            self.roi_annotation_list.clear()
        
            for j in range(len(myKeys)):
                self.roi_annotation_list.addItem(myKeys[j])

            

        for annotation_c in self.annotation_content:
            painter.setPen(QPen(Qt.green, 3, Qt.SolidLine))
            rect = QRect(round(int(self.annotation_content[annotation_c]['x0'])*self.img_scale),
                         round(int(self.annotation_content[annotation_c]['y0'])*self.img_scale),
                         round((int(self.annotation_content[annotation_c]['x1'])-int(self.annotation_content[annotation_c]['x0']))*self.img_scale),
                         round((int(self.annotation_content[annotation_c]['y1'])-int(self.annotation_content[annotation_c]['y0']))*self.img_scale))
            painter.drawRect(rect.normalized())

            rect2 = QRect(round(int(self.annotation_content[annotation_c]['x0'])*self.img_scale),
                          round(int(self.annotation_content[annotation_c]['y0'])*self.img_scale)-15,
                          round(int(self.annotation_content[annotation_c]['x1'])*self.img_scale)-round(
                              int(self.annotation_content[annotation_c]['x0'])*self.img_scale)+1, 15)
            painter.fillRect(round(int(self.annotation_content[annotation_c]['x0'])*self.img_scale)-1,
                             round(int(self.annotation_content[annotation_c]['y0'])*self.img_scale)-16,
                             round(int(self.annotation_content[annotation_c]['x1'])*self.img_scale)-round(
                                 int(self.annotation_content[annotation_c]['x0'])*self.img_scale)+3, 15, Qt.green)

            painter.setPen(QPen(Qt.black, 3, Qt.SolidLine))
            painter.drawText(rect2.normalized(), Qt.AlignLeft, self.roi_annotation_list.item(counter).text())
            counter += 1
        
        #update patient information
        patientInfo = open(self.parentFolder+'/patient_information.txt', 'rt',encoding='utf-8')
        patients = patientInfo.readlines()

        for i in patients:
            if i[0]==self.currentID:
                self.currentPatient = i
        ls = self.currentPatient.split(",")
        newLine = self.currentID +","
        for i in range(1,len(ls)):
            if i==4 or i==16 or i==17 or i==19 or i==20 or i==21 or i==24:
                temp = ls[i].split(":")
                newS = ""
                for i in range(len(temp)):
                    if i == rn:
                        continue
                    else:
                        newS+=temp[i]+":"
                newS = newS[:-1]
                newLine+= newS+","
            else:
                newLine+=ls[i]+","
        newLine = newLine[:-1]
        self.namingFormat(newLine)
        self.replace_line(self.parentFolder+'/patient_information.txt',self.currentPatient,newLine)
        self.currentPatient = newLine
        self.updateLabelList()
        self.delete.setEnabled(False)
        self.editPaientInfo.setDisabled(True)
        self.lbNo = 0
        self.roi_number-=1
        patientInfo.close()
        
        
    def browse_image(self):
        self.text_list.clear()
        self.fileList.clear()

        if not self.fromNextOrPre:
            self.filename, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'Image Files (*.png *.jpg *.jpeg)')

            #saving all available images in the current directory
            for f in os.listdir(os.path.split(self.filename)[0]):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
                    self.imageList.append(f)

            #intializing next prev button index
            self.nextPrevIndex = self.imageList.index(os.path.split(self.filename)[-1])
        else:
            self.filename = self.parentFolder+"/"+self.imageList[self.nextPrevIndex]
        
        self.image = cv2.imread(self.filename, 1)


        self.next.setVisible(True)
        self.prev.setVisible(True)

        if self.nextPrevIndex>=len(self.imageList)-1:
            self.next.setVisible(False)
        elif self.nextPrevIndex<=0:
            self.prev.setVisible(False)
        elif self.nextPrevIndex<len(self.imageList) and self.nextPrevIndex>=0:
            self.next.setVisible(True)
            self.prev.setVisible(True)
            self.next.setDisabled(False)
            self.prev.setDisabled(False)
            


        #make new directory 
        try:
            imageName = os.path.split(self.filename)[-1].split(".")[0]
            newPath = os.path.join(os.path.split(self.filename)[0]+'/', imageName)
            self.parentFolder = os.path.split(self.filename)[0]

            if not os.path.exists(newPath):
                os.mkdir(newPath)
                shutil.copy(self.filename, newPath)
                self.filename = newPath+'/' + os.path.split(self.filename)[-1]

            else:
                imageDetected = False
                for d in os.listdir(newPath):
                    if d.endswith(os.path.split(self.filename)[-1].split(".")[-1]):
                        self.filename = newPath+"/"+d 
                        imageDetected = True 
                
                if not imageDetected:
                    shutil.copy(self.filename, newPath)
                    self.filename = newPath+'/' + os.path.split(self.filename)[-1]

        except OSError as message: 
            print(message) 

        if self.filename:
            for file in os.listdir(os.path.split(self.filename)[0]):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
                    self.fileList.append(file)
                else:
                    self.text_list.append(file) if file not in self.text_list else self.text_list
            self.load_original_image(self.filename)

    def save_annotation(self):
        self.updateLabelList()

        # list of labels
        file1 = open(self.coord_path, 'r')
        self.label_list = file1.readlines()
        file1.close()

        #add new rectangle information to patient information
        patientInfo = open(self.parentFolder+'/patient_information.txt', 'rt',encoding='utf-8')
        patients = patientInfo.readlines()
        for i in patients:
            if i[0]==self.currentID:
                self.currentPatient = i
        ls = self.currentPatient.split(",")

        newLine = ""
        for i in range(1, len(ls)):
            if i==2:
                lbls = ""
                for k in range(len(self.annotation_content)):
                    lbls+="Label_"+str(k)+":"
                newLine+=lbls[:-1]+","
            elif i==16 or i==17 or i==19 or i==20 or i==21 or i==24:
                if len(ls[i])==0:
                    newLine+=ls[i]+"NA,"
                else:
                    newLine+=ls[i]+":NA,"
            else:
                newLine+=ls[i]+","
        newLine = newLine[:-1]
        newLine = self.namingFormat("Placeholder,"+newLine)+","+newLine
        self.replace_line(self.parentFolder+'/patient_information.txt',self.currentPatient,newLine)
        self.currentPatient = newLine
        patientInfo.close()
        
        file1 = open(self.coord_path, 'r')
        lines = file1.readlines()
        self.label_list = lines
        file1.close()

    def draw_rectangle(self):
        QLabel.setCursor(self, Qt.CrossCursor)
        draw_pixmap = QPixmap(self.label.size())
        draw_pixmap.fill(Qt.transparent)
        self.draw_frame.setPixmap(draw_pixmap)
        self.draw_frame.setGeometry(11, 110, draw_pixmap.size().width(), draw_pixmap.size().height())
        self.draw_rect = True

        painter = QPainter(self.draw_frame.pixmap())
        counter = 0
        for annotation_c in self.annotation_content:
            painter.setPen(QPen(Qt.green, 3, Qt.SolidLine))
            rect = QRect(round(int(self.annotation_content[annotation_c]['x0']) * self.img_scale),
                         round(int(self.annotation_content[annotation_c]['y0']) * self.img_scale),
                         round((int(self.annotation_content[annotation_c]['x1']) - int(
                             self.annotation_content[annotation_c][
                                 'x0'])) * self.img_scale),
                         round((int(self.annotation_content[annotation_c]['y1']) - int(
                             self.annotation_content[annotation_c][
                                 'y0'])) * self.img_scale))
            painter.drawRect(rect.normalized())

            rect2 = QRect(round(int(self.annotation_content[annotation_c]['x0']) * self.img_scale),
                          round(int(self.annotation_content[annotation_c]['y0']) * self.img_scale) - 15,
                          round(int(self.annotation_content[annotation_c]['x1']) * self.img_scale) - round(
                              int(self.annotation_content[annotation_c]['x0']) * self.img_scale) + 1, 15)
            painter.fillRect(round(int(self.annotation_content[annotation_c]['x0']) * self.img_scale) - 1,
                             round(int(self.annotation_content[annotation_c]['y0']) * self.img_scale) - 16,
                             round(int(self.annotation_content[annotation_c]['x1']) * self.img_scale) - round(
                                 int(self.annotation_content[annotation_c]['x0']) * self.img_scale) + 3, 15, Qt.green)

            painter.setPen(QPen(Qt.black, 3, Qt.SolidLine))
            painter.drawText(rect2.normalized(), Qt.AlignLeft, self.roi_annotation_list.item(counter).text())
            counter += 1
        
        #label signal
        self.roi_annotation_list.itemClicked.connect(self.setCurrentLabel)
    
 
                                     
    def load_original_image(self, x):
        # self.next.setVisible(True)
        # self.prev.setVisible(True)
        self.rectangle.setDisabled(False)
        # self.delete.setDisabled(False)
        self.save.setDisabled(False)
        self.downloadPatientInfo.setDisabled(False)

        self.roi_annotation_list.clear()
        self.patient_information.clear()
        self.annotation_content = {}
        name = os.path.split(x)[-1].split(".")[0]
        text = name + ".txt"
        path = x.replace(x.split("/")[-1], "")
        
        #getting patientId and index from sample
        id_index = name.split("_")
        if len(id_index)==2:
            self.patientNo = id_index[0]
            if len(id_index[1])==1:
                self.indexNo = "000"+id_index[1]
            elif len(id_index[1])==2:
                self.indexNo = "00" + id_index[1]
            elif len(id_index[1])==2:
                self.indexNo = "0" + id_index[1]
            else:
                self.indexNo = id_index[1]

        
        # patient name and label list txt file address
        self.currentID = name
        self.coord_path = path+text

        #path information txt file address
        self.location = os.path.split(x)[0]

        if (text in self.text_list):
            # self.image = cv2.imread(x, 1)
            self.print_image(x)
            full_path = path + text
            file1 = open(full_path, 'r')
            lines = file1.readlines()
            self.label_list = lines
            self.roi_number = 0
            counter = 0;

            draw_pixmap = QPixmap(self.label.size())
            draw_pixmap.fill(Qt.transparent)
            self.draw_frame.setPixmap(draw_pixmap)
            self.draw_frame.setGeometry(11, 110, draw_pixmap.size().width(), draw_pixmap.size().height())

            painter = QPainter(self.draw_frame.pixmap())

            for line in lines:
                self.annotation_content["Label_%d" % self.roi_number] = {'x0': line.split(",")[0],
                                                                     'y0': line.split(",")[1],
                                                                     'x1': line.split(",")[2],
                                                                     'y1': line.strip().split(",")[3]}
                                                
                self.roi_annotation_list.addItem("Label_%d" % self.roi_number)
                self.roi_number += 1

            for annotation_c in self.annotation_content:
                painter.setPen(QPen(Qt.green, 3, Qt.SolidLine))
                rect = QRect(round(int(self.annotation_content[annotation_c]['x0']) * self.img_scale),
                             round(int(self.annotation_content[annotation_c]['y0']) * self.img_scale),
                             round((int(self.annotation_content[annotation_c]['x1']) - int(self.annotation_content[annotation_c][
                                 'x0'])) * self.img_scale),
                             round((int(self.annotation_content[annotation_c]['y1']) - int(self.annotation_content[annotation_c][
                                 'y0'])) * self.img_scale))
                painter.drawRect(rect.normalized())

                rect2 = QRect(round(int(self.annotation_content[annotation_c]['x0']) * self.img_scale),
                              round(int(self.annotation_content[annotation_c]['y0']) * self.img_scale) - 15,
                              round(int(self.annotation_content[annotation_c]['x1']) * self.img_scale) - round(
                                  int(self.annotation_content[annotation_c]['x0']) * self.img_scale) + 1, 15)
                painter.fillRect(round(int(self.annotation_content[annotation_c]['x0']) * self.img_scale) - 1,
                                 round(int(self.annotation_content[annotation_c]['y0']) * self.img_scale) - 16,
                                 round(int(self.annotation_content[annotation_c]['x1']) * self.img_scale) - round(
                                     int(self.annotation_content[annotation_c]['x0']) * self.img_scale) + 3, 15, Qt.green)

                painter.setPen(QPen(Qt.black, 3, Qt.SolidLine))
                painter.drawText(rect2.normalized(), Qt.AlignLeft, self.roi_annotation_list.item(counter).text())
                counter += 1
        else:
            self.roi_annotation_list.clear()
            self.patient_information.clear()
            self.image = cv2.imread(x, 1)
            self.print_image(x)

            draw_pixmap = QPixmap(self.label.size())
            draw_pixmap.fill(Qt.transparent)
            self.draw_frame.setPixmap(draw_pixmap)
            self.draw_frame.setGeometry(11, 110, draw_pixmap.size().width(), draw_pixmap.size().height())

            painter = QPainter(self.draw_frame.pixmap())

            self.roi_number = 0

        #patient information txt file create if one doesn't exist 

        try:
            with open(self.parentFolder+'/patient_information.txt', 'rt',encoding='utf-8') as patientInfo:
                patients = patientInfo.readlines()
        except FileNotFoundError:
            patientInfo = open(self.parentFolder+'/patient_information.txt', 'w+',encoding='utf-8')
            header = "이미지 파일 명, 이미지 W H, ROI Label 넘버, ROI Label 좌표, 기관, 환자번호, 성, 나이, 진단일자, 수집 이미지 날짜, 키, 몸무게, 혈액형, 소화기 계통 가족력, 술, 담배, 기저질환, 위 식도 질환 과거력, 초기 치료, 종양위치1, 종양위치2, 병리결과, 장상피화생, Atrophy, Cancer depth, 판독결과, 병리결과, comment"
            patientInfo.seek(0)
            patientInfo.write(header+'\n')
            patientInfo.truncate()
            patientInfo = open(self.parentFolder+'/patient_information.txt', 'rt',encoding='utf-8')
            patients = patientInfo.readlines()

        #finding the patient related to the current image
        flag = True
        for i in patients:
            ii = i.split(",")
            if ii[0]==self.currentID:
                self.currentPatient = i
                flag = False   #current patient information found from the patient info txt file
                break 
        if flag:
            self.currentPatient = patients[0]
            ls = self.currentPatient.split(",")
            newLine = self.currentID +","
            for i in range(1,len(ls)):
                if i==4:
                    newLine+="NA,"
                elif i==7 or i==10 or i==11:
                    newLine+="0,"
                elif i==19 or i==20 or i==21 or i==24:
                    mask = ""
                    for j in self.annotation_content:
                        mask+=":NA"
                    mask=mask[1:]+","
                    newLine+=mask
                else:
                    newLine+=ls[i]+","
            newLine = newLine[:-1]
            # path = "C:/Users/ca/Desktop/Work_1/Image_annotation/images/patient_information.txt"
            self.replace_line(self.parentFolder+'/patient_information.txt',self.currentPatient,newLine)
            self.currentPatient = newLine
        
        self.roi_annotation_list.itemClicked.connect(self.setCurrentLabel)

    def setCurrentLabel(self,item):

        #displaying information on information widget
        infoList = self.currentPatient.split(",")

        file1 = open(self.coord_path, 'r')
        lines = file1.readlines()
        self.label_list = lines

        self.lbNo = item.text()[-1]
        self.editPaientInfo.setDisabled(False)
        self.currLabel = self.label_list[int(self.lbNo)][:-1]
        self.patient_information.clear()
        
        self.title = ["이미지 파일 명:  ", "이미지 W,H:  ", "ROI Label 넘버:  ", "ROI Label 좌표:  ", "기관: ", "환자번호:  ", "성:  ", "나이:  ",
        "진단일자:  ", "수집 이미지 날짜:  ", "키:  ", "몸무게:  ", "혈액형:  ", "소화기 계통 가족력:  ", "술:  ", "담배:  ", "기저질환:  ", "위,식도 질환 과거력:  ",
        "초기 치료:  ", "종양위치1:  ", "종양위치2:  ", "병리결과:  ", "장상피화생:  ", "Atrophy:  ", "Cancer depth:  ", "판독결과:  ", "병리결과: ", "comment: ",]
        for i in range(0,len(self.title)-1):
            title = self.title[i+1]
            if title == "ROI Label 넘버:  ":
                it = title+item.text() 
            elif title== "ROI Label 좌표:  ":
                it = title+self.currLabel
            elif title== "종양위치1:  " or title=="종양위치2:  " or title=="병리결과:  "or title=="Cancer depth:  ":# or title=="기관: ":#or title=="기저질환:  " or title=="위,식도 질환 과거력:  " or title=="기관: ":      
                curr = infoList[i+1].split(":")
                it = title+ curr[int(self.lbNo)]
            elif title=="기저질환:  " or title=="위,식도 질환 과거력:  ":
                curr = infoList[i+1].split(":")
                it=""
                for i in curr:
                    if i!="NA":
                        it+=i+","
                if len(it)>0:
                    it=it[:-1]
                if len(it)==0:
                    it = "No detection"
                it = title + it
            elif title== "환자번호:  ":
                it = title+self.patientNo
            else:

                it = title+infoList[i+1]
            self.patient_information.addItem(it)

    def print_image(self, filename):
        pix = QPixmap()
        pix.load(filename)
        raw_img_w=pix.size().width()
        pix = pix.scaledToWidth(800)
        re_img_w=pix.size().width()
        self.img_scale=re_img_w/raw_img_w
        
        self.label.setPixmap(pix)        
        self.label.setGeometry(11, 110, pix.size().width(), pix.size().height())
        self.label.lower()
        self.load_img = True

    def next_image(self):
        self.roi_annotation_list.clear()
        self.patient_information.clear()
        if self.nextPrevIndex<len(self.imageList)-1:
            self.nextPrevIndex+=1
            self.fromNextOrPre = True
            self.browse_image()
            self.fromNextOrPre = False
        # else:
        #     self.next.setVisible(False)
        

    def prev_image(self):
        self.roi_annotation_list.clear()
        self.patient_information.clear()
        if self.nextPrevIndex>0:
            self.nextPrevIndex-=1
            self.fromNextOrPre = True
            self.browse_image()
            self.fromNextOrPre = False
        # else:
        #     self.prev.setVisible(False)
        

    def paintEvent(self, event):
        tool_bar_rect = QPainter(self)
        tool_bar_rect.setBrush(QBrush(Qt.gray, Qt.SolidPattern))
        tool_bar_rect.drawRect(-1, 0, 1420, 97)

        if self.load_img and self.draw_rect:
            pix_tmp = QPixmap(self.label.size())
            pix_tmp.fill(Qt.transparent)
            self.label_tmp.setPixmap(pix_tmp)
            self.label_tmp.setGeometry(11, 110, pix_tmp.size().width(), pix_tmp.size().height())
            painter = QPainter(self.label_tmp.pixmap())
            painter.setPen(QPen(Qt.green, 3, Qt.SolidLine))
            painter.setBrush(QBrush(Qt.red, Qt.DiagCrossPattern))

            if not self.begin.isNull() and not self.destination.isNull():
                rect = QRect(self.begin, self.destination)
                painter.drawRect(rect.normalized())

    def mousePressEvent(self, event):
        if self.load_img and self.draw_rect:
            if event.buttons() & Qt.LeftButton:
                self.begin = event.pos()
                self.begin -= QPoint(11, 110)
                self.destination = self.begin
                self.update()
                QLabel.setCursor(self, Qt.CustomCursor)

    def mouseMoveEvent(self, event):
        if self.load_img and self.draw_rect:
            if event.buttons() & Qt.LeftButton:		
                self.destination = event.pos()
                self.destination -= QPoint(11, 110)
                self.update()

    def mouseReleaseEvent(self, event):
        if self.load_img and self.draw_rect:
            if event.button() & Qt.LeftButton:
                rect = QRect(self.begin, self.destination)
                
                x0=min([self.begin.x(),self.destination.x()])
                x1=max([self.begin.x(),self.destination.x()])
                y0=min([self.begin.y(),self.destination.y()])
                y1=max([self.begin.y(),self.destination.y()])

                if abs(x1-x0)>20 and abs(y1-y0)>20:

                    self.annotation_content["Label_%d"%self.roi_number]={'x0':round(x0/self.img_scale),'y0':round(y0/self.img_scale),
                                                                        'x1':round(x1/self.img_scale),'y1':round(y1/self.img_scale)}
                    
                    painter = QPainter(self.draw_frame.pixmap())
                    painter.setPen(QPen(Qt.green, 3, Qt.SolidLine))
                    painter.drawRect(rect.normalized())

                    rect = QRect(x0, y0-15, x1-x0+1, 15)
                    painter.fillRect(x0-1, y0-16, x1-x0+4, 15, Qt.green)
                    painter.setPen(QPen(Qt.black, 3, Qt.SolidLine))
                    painter.drawText(rect, Qt.AlignLeft, "Label %d"%self.roi_number)
                    
                    self.roi_annotation_list.addItem("Label_%d"%self.roi_number)
                    self.roi_number += 1

                    self.save_annotation()
                    
                    self.begin, self.destination = QPoint(), QPoint()
                    self.update()

            QLabel.setCursor(self, Qt.CustomCursor)
            # self.draw_rect = False
            

    def editPatientInformation(self):
        self.exit.setDisabled(True)
        dlg =  QDialog(self)
        dlg.setWindowFlag(Qt.FramelessWindowHint)
        dlg.setWindowOpacity(1)
        stylesheet = """
            QDialog {
                background-color:lightgrey;
                background-repeat: no-repeat;
                background-position: center;
                border-radius: 30px;
                font: 11px;
                font-family: Comic Sans MS;
            }
        """
        dlg.setStyleSheet(stylesheet)
        # dlg.move(1310, 216)
        dlg.move(self.pos().x()+981, self.pos().y()+141)
        dlg.resize(430, 700)

        infoList = self.currentPatient.split(",")
        labels = [0 for i in range(27)]

        initialWidth = 0
        
        for i in range(27):

            if i==0:
                (self.h, self.w, d) = self.image.shape
                # labels[i]= [QLabel(self.title[i+1], dlg), QLineEdit(str(self.h)+","+str(self.w), dlg)]
                labels[i]= [QLabel(self.title[i+1] + " "+str(self.h)+","+str(self.w), dlg)]
                initialWidth +=5
                labels[i][0].move(40,initialWidth)
                labels[i][0].setStyleSheet("font-weight: bold; color: Blue")
            elif i==1 :
                # initialWidth +=23
                labels[i]= [QLabel(self.title[i+1] + " "+"Label_"+self.lbNo, dlg)]
                labels[i][0].move(230,initialWidth)
                labels[i][0].setStyleSheet("font-weight: bold; color: Blue")
            elif i==2:
                labels[i]= [QLabel(self.title[i+1], dlg), QLineEdit(self.currLabel, dlg)]
                initialWidth +=23
                labels[i][0].move(5,initialWidth)
                labels[i][1].move(125,initialWidth-5)
                labels[i][1].setEnabled(False)
            
            elif i ==15:
                ls = ["HTN", "DM", "Heart disease (CAD/CHF)", "Dyslipidemia","Brain disease(CVA/hemorrhage)"]
                boxes = []
                for j in ls:
                    boxes.append(QCheckBox(j, dlg))
                labels[i]= [QLabel(self.title[i+1], dlg), boxes]
                initialWidth +=23
                labels[i][0].move(5,initialWidth)
                labels[i][1][0].move(125,initialWidth-5)
                labels[i][1][1].move(180,initialWidth-5)
                labels[i][1][2].move(230,initialWidth-5)
                initialWidth +=23
                labels[i][1][3].move(125,initialWidth-5)
                labels[i][1][4].move(225,initialWidth-5)

                checked =  infoList[i+1].split(":")
                for k in checked:
                    if not k in ls:
                        break
                    ind = int(ls.index(k))
                    if isinstance(ind, int):
                        labels[i][1][ind].setChecked(True)

            elif i ==16:
                ls = ["위염", "위축성", "궤양" ,"장상피화생 ","선종", "암"]
                boxes = []
                for j in ls:
                    boxes.append(QCheckBox(j, dlg))
                labels[i]= [QLabel(self.title[i+1], dlg), boxes]
                initialWidth +=23
                labels[i][0].move(5,initialWidth)
                labels[i][1][0].move(125,initialWidth-5)
                labels[i][1][1].move(220,initialWidth-5)
                labels[i][1][2].move(275,initialWidth-5)
                initialWidth +=23
                labels[i][1][3].move(125,initialWidth-5)
                labels[i][1][4].move(220,initialWidth-5)
                labels[i][1][5].move(275,initialWidth-5)

                checked =  infoList[i+1].split(":")
                for k in checked:
                    if not k in ls:
                        break
                    ind = int(ls.index(k))
                    if isinstance(ind, int):
                        labels[i][1][ind].setChecked(True)

            
            elif i==3 or i==18 or i==19 or i==20 or i==23:
                ls3 = ["길병원", "인천성모", "인하대", " 원주세브란스 ","부산대", "서울아산"]      
                ls18 = ["Cardia", "Fungus", "HB", "MB","LB","Antrum","Pylorus"]
                ls19 = ["GC", "LC", "AW", " PW"]
                ls20 = ["LGD", "HGD", "Cancer", "Gastritis","Ulcer","Other"]
                ls23 = ["CIS", "M", "SM1 (<500um)", "SM2 (>500um)","PM","OVER SEROSA"]
                if i==3:
                    ls=ls3
                elif i==18:
                    ls=ls18
                elif i==19:
                    ls=ls19
                elif i==20:
                    ls=ls20
                else:
                    ls = ls23
                labels[i]= [QLabel(self.title[i+1], dlg), QComboBox(dlg)]
                initialWidth +=23
                labels[i][0].move(5,initialWidth)
                labels[i][1].move(125,initialWidth-5)
                labels[i][1].addItems(ls)
                if i<18:
                    labels[i][1].setCurrentText(infoList[i+1])
                else:
                    curr = infoList[i+1].split(":")
                    labels[i][1].setCurrentText(curr[int(self.lbNo)])

            elif i==5:
                
                def checkingM():
                    if labels[5][1][0].isChecked():
                        labels[5][1][1].setChecked(False)
                    else:
                        labels[5][1][1].setChecked(True)
                def checkingF():
                    if labels[5][1][1].isChecked():
                        labels[5][1][0].setChecked(False)
                    else:
                        labels[5][1][0].setChecked(True)
                
                labels[i]= [QLabel(self.title[i+1], dlg), [QCheckBox("M", dlg),QCheckBox("F", dlg)]]
                initialWidth +=23
                labels[i][0].move(5,initialWidth)
                labels[i][1][0].move(125,initialWidth-5)
                labels[i][1][1].move(190,initialWidth-5)
                labels[i][1][0].stateChanged.connect(checkingM)
                labels[i][1][1].stateChanged.connect(checkingF)
                if infoList[i+1]=="M":
                    labels[5][1][0].setChecked(True)
                else:
                    labels[5][1][1].setChecked(True)
            elif i==11:
                def checkingA():
                    if labels[11][1][0].isChecked():
                        labels[11][1][1].setChecked(False)
                        labels[11][1][2].setChecked(False)
                        labels[11][1][3].setChecked(False)
                        # labels[11][1][0].setChecked(True)

                def checkingB():
                    if labels[11][1][1].isChecked():
                        labels[11][1][0].setChecked(False)
                        labels[11][1][2].setChecked(False)
                        labels[11][1][3].setChecked(False)

                def checkingO():
                    if labels[11][1][2].isChecked():
                        labels[11][1][1].setChecked(False)
                        labels[11][1][0].setChecked(False)
                        labels[11][1][3].setChecked(False)

                def checkingAB():
                    if labels[11][1][3].isChecked():
                        labels[11][1][1].setChecked(False)
                        labels[11][1][2].setChecked(False)
                        labels[11][1][0].setChecked(False)

                labels[i]= [QLabel(self.title[i+1], dlg), [QCheckBox("A", dlg),QCheckBox("B", dlg), QCheckBox("O", dlg),QCheckBox("AB", dlg)]]
                initialWidth +=23
                labels[i][0].move(5,initialWidth)
                labels[i][1][0].move(125,initialWidth-5)
                labels[i][1][1].move(180,initialWidth-5)
                labels[i][1][2].move(220,initialWidth-5)
                labels[i][1][3].move(260,initialWidth-5)
                labels[i][1][0].stateChanged.connect(checkingA)
                labels[i][1][1].stateChanged.connect(checkingB)
                labels[i][1][2].stateChanged.connect(checkingO)
                labels[i][1][3].stateChanged.connect(checkingAB)
                if infoList[i+1]=="A":
                    labels[11][1][0].setChecked(True)
                elif infoList[i+1]=="B":
                    labels[11][1][1].setChecked(True)
                elif infoList[i+1]=="O":
                    labels[11][1][2].setChecked(True)
                else:
                    labels[11][1][3].setChecked(True)
            elif i==4:
                # labels[i]= [QLabel(self.title[i+1], dlg), QLineEdit(infoList[i+1], dlg)]
                labels[i]= [QLabel(self.title[i+1], dlg), QLineEdit(self.patientNo, dlg)]
                initialWidth +=23
                labels[i][0].move(5,initialWidth)
                labels[i][1].move(125,initialWidth-5)
                labels[i][1].setFixedWidth(65)
                # labels[i][1].setInputMask("99999999")
                validator = QIntValidator(self)
                validator.setRange(0,99999999)
                labels[i][1].setValidator(validator)

            elif i==6:
                labels[i]= [QLabel(self.title[i+1], dlg), QLineEdit(infoList[i+1], dlg)]
                initialWidth +=23
                labels[i][0].move(5,initialWidth)
                labels[i][1].move(125,initialWidth-5)
                labels[i][1].setFixedWidth(30)
                # labels[i][1].setInputMask("999")
                validator = QIntValidator(self)
                validator.setRange(0,999)
                labels[i][1].setValidator(validator)
            elif i==9:
                labels[i]= [QLabel(self.title[i+1], dlg), QLineEdit(infoList[i+1], dlg),QLabel("Cm", dlg)]
                initialWidth +=23
                labels[i][0].move(5,initialWidth)
                labels[i][1].move(125,initialWidth-5)
                labels[i][2].move(165,initialWidth)
                labels[i][1].setFixedWidth(30)
                # labels[i][1].setInputMask("999")
                validator = QIntValidator(self)
                validator.setRange(0,999)
                labels[i][1].setValidator(validator)
            elif i==10:
                labels[i]= [QLabel(self.title[i+1], dlg), QLineEdit(infoList[i+1], dlg),QLabel("Kg", dlg)]
                initialWidth +=23
                labels[i][0].move(5,initialWidth)
                labels[i][1].move(125,initialWidth-5)
                labels[i][2].move(165,initialWidth)
                labels[i][1].setFixedWidth(30)
                # labels[i][1].setInputMask("999")
                validator = QIntValidator(self)
                validator.setRange(0,999)
                labels[i][1].setValidator(validator)
            elif i==7 or i==8:
                s = infoList[i+1].split("NA")
                if len(s)<3:
                    s = ["0000", "00", "00"]
                labels[i]= [QLabel(self.title[i+1], dlg), QLineEdit(s[0],dlg), QLineEdit(s[1], dlg),QLineEdit(s[2], dlg)]
                initialWidth +=23
                labels[i][0].move(5,initialWidth)
                labels[i][1].setFixedWidth(45)
                # labels[i][1].setInputMask("9999")
                validator1 = QIntValidator(self)
                validator1.setRange(0,9999)
                labels[i][1].setValidator(validator1)
                labels[i][1].move(125,initialWidth-5)
                labels[i][2].setFixedWidth(25)
                # labels[i][2].setInputMask("99")
                validator2 = QIntValidator(self)
                validator2.setRange(0,99)
                labels[i][2].setValidator(validator2)
                labels[i][2].move(180,initialWidth-5)
                labels[i][3].setFixedWidth(25)
                # labels[i][3].setInputMask("99")
                validator3 = QIntValidator(self)
                validator3.setRange(0,99)
                labels[i][3].setValidator(validator3)
                labels[i][3].move(215,initialWidth-5)

            elif i==12: 
                k = i
                def checkingYes():
                    if labels[12][1][0].isChecked():
                        labels[12][1][1].setChecked(False)
             
                def checkingNo():
                    if labels[12][1][1].isChecked():
                        labels[12][1][0].setChecked(False)
                
                labels[i]= [QLabel(self.title[i+1], dlg), [QCheckBox("Yes", dlg),QCheckBox("No", dlg)]]
                initialWidth +=23
                labels[i][0].move(5,initialWidth)
                labels[i][1][0].move(125,initialWidth-5)
                labels[i][1][1].move(190,initialWidth-5)
                labels[i][1][0].stateChanged.connect(checkingYes)
                labels[i][1][1].stateChanged.connect(checkingNo)

                if infoList[i+1]=="Yes":
                    labels[12][1][0].setChecked(True)
                else:
                    labels[12][1][1].setChecked(True)
            elif i==13:
                k2 = i
                def checkingYes():
                    if labels[k2][1][0].isChecked():
                        labels[k2][1][1].setChecked(False)
             
                def checkingNo():
                    if labels[k2][1][1].isChecked():
                        labels[k2][1][0].setChecked(False)
                
                labels[k2]= [QLabel(self.title[i+1], dlg), [QCheckBox("Yes", dlg),QCheckBox("No", dlg)]]
                initialWidth +=23
                labels[k2][0].move(5,initialWidth)
                labels[k2][1][0].move(125,initialWidth-5)
                labels[k2][1][1].move(190,initialWidth-5)
                labels[k2][1][0].stateChanged.connect(checkingYes)
                labels[k2][1][1].stateChanged.connect(checkingNo)

                if infoList[i+1]=="Yes":
                    labels[k2][1][0].setChecked(True)
                else:
                    labels[k2][1][1].setChecked(True)
            elif i==14 :
                k3 = i
                def checkingYes():
                    if labels[k3][1][0].isChecked():
                        labels[k3][1][1].setChecked(False)
             
                def checkingNo():
                    if labels[k3][1][1].isChecked():
                        labels[k3][1][0].setChecked(False)
                
                labels[k3]= [QLabel(self.title[i+1], dlg), [QCheckBox("Yes", dlg),QCheckBox("No", dlg)]]
                initialWidth +=23
                labels[k3][0].move(5,initialWidth)
                labels[k3][1][0].move(125,initialWidth-5)
                labels[k3][1][1].move(190,initialWidth-5)
                labels[k3][1][0].stateChanged.connect(checkingYes)
                labels[k3][1][1].stateChanged.connect(checkingNo)

                if infoList[i+1]=="Yes":
                    labels[k3][1][0].setChecked(True)
                else:
                    labels[k3][1][1].setChecked(True)
            elif i==17:
                k7 = i
                def checkingYes():
                    if labels[k7][1][0].isChecked():
                        labels[k7][1][1].setChecked(False)
             
                def checkingNo():
                    if labels[k7][1][1].isChecked():
                        labels[k7][1][0].setChecked(False)
                
                labels[k7]= [QLabel(self.title[i+1], dlg), [QCheckBox("ESD", dlg),QCheckBox("OP", dlg)]]
                initialWidth +=23
                labels[k7][0].move(5,initialWidth)
                labels[k7][1][0].move(125,initialWidth-5)
                labels[k7][1][1].move(190,initialWidth-5)
                labels[k7][1][0].stateChanged.connect(checkingYes)
                labels[k7][1][1].stateChanged.connect(checkingNo)

                if infoList[i+1]=="ESD":
                    labels[k7][1][0].setChecked(True)
                else:
                    labels[k7][1][1].setChecked(True)
            elif i==22:
                k6 = i
                def checkingYes():
                    if labels[k6][1][0].isChecked():
                        labels[k6][1][1].setChecked(False)
             
                def checkingNo():
                    if labels[k6][1][1].isChecked():
                        labels[k6][1][0].setChecked(False)
                
                labels[k6]= [QLabel(self.title[i+1], dlg), [QCheckBox("Yes", dlg),QCheckBox("No", dlg)]]
                initialWidth +=23
                labels[k6][0].move(5,initialWidth)
                labels[k6][1][0].move(125,initialWidth-5)
                labels[k6][1][1].move(190,initialWidth-5)
                labels[k6][1][0].stateChanged.connect(checkingYes)
                labels[k6][1][1].stateChanged.connect(checkingNo)

                if infoList[i+1]=="Yes":
                    labels[k6][1][0].setChecked(True)
                else:
                    labels[k6][1][1].setChecked(True)
            elif i==21 :
                k5 = i
                def checkingYes():
                    if labels[k5][1][0].isChecked():
                        labels[k5][1][1].setChecked(False)
             
                def checkingNo():
                    if labels[k5][1][1].isChecked():
                        labels[k5][1][0].setChecked(False)
                
                labels[k5]= [QLabel(self.title[i+1], dlg), [QCheckBox("Yes", dlg),QCheckBox("No", dlg)]]
                initialWidth +=23
                labels[k5][0].move(5,initialWidth)
                labels[k5][1][0].move(125,initialWidth-5)
                labels[k5][1][1].move(190,initialWidth-5)
                labels[k5][1][0].stateChanged.connect(checkingYes)
                labels[k5][1][1].stateChanged.connect(checkingNo)

                if infoList[i+1]=="Yes":
                    labels[k5][1][0].setChecked(True)
                else:
                    labels[k5][1][1].setChecked(True)
            elif i==26:
                precomment = infoList[i+1]
                if len(precomment)>0 and precomment[-1]=='\n':
                    precomment = precomment[:-1]
                labels[26]= [QLabel(self.title[i+1], dlg), QLineEdit(precomment, dlg)]
                initialWidth +=23
                labels[26][0].move(5,initialWidth)
                labels[26][1].move(125,initialWidth-5)
                labels[26][1].setCursorPosition(-1)
                labels[26][1].setFocus()
            else:
                labels[i]= [QLabel(self.title[i+1], dlg), QLineEdit(infoList[i+1], dlg)]
                initialWidth +=23
                labels[i][0].move(5,initialWidth)
                labels[i][1].move(125,initialWidth-5)
                labels[i][1].setCursorPosition(0)

        def save(): 
            infoList = self.currentPatient.split(',')
            newLine = self.currentID +","
            newLine = ""
            
            for i in range(len(labels)):
                if i==0: #이미지 W,H
                    newLine+=str(self.h)+" "+str(self.w)+","
                elif i==1: #ROI Label 넘버
                    lbls = ""
                    for k in range(len(self.annotation_content)):
                        lbls+="Label_"+str(k)+":"

                    newLine+=lbls[:-1]+","
                elif i==2:#ROI Label 좌표
                    ss = self.currLabel.replace(",",";")
                    newLine+=ss+","
                elif i==3:
                    newLine+= labels[i][1].currentText()+","
                elif i==15:
                    ls = ["HTN", "DM", "Heart disease (CAD/CHF)", "Dyslipidemia","Brain disease(CVA/hemorrhage)"]
                    checkedls = ""
                    for j, ch in enumerate(labels[i][1]):
                        if ch.isChecked():
                            checkedls+=ls[j]+":"
                            ch.setChecked(True)
                        else:
                            ch.setChecked(False)
                    if len(checkedls)==0:
                        newLine+="NA,"
                    else:
                        newLine+=checkedls[:-1]+","
                elif i==16 :
                    ls = ["위염", "위축성", "궤양" ,"장상피화생 ","선종", "암"]
                    checkedls = ""
                    for j, ch in enumerate(labels[i][1]):
                        if ch.isChecked():
                            checkedls+=ls[j]+":"
                            ch.setChecked(True)
                        else:
                            ch.setChecked(False)
                    if len(checkedls)==0:
                        newLine+="NA,"
                    else:
                        newLine+=checkedls[:-1]+","
                elif i==18 or i==19 or i==20 or i==23:
                    picked = labels[i][1].currentText()
                    curr = infoList[i+1].split(":")
                    if len(curr)<len(self.label_list):
                        curr= []
                        for i, it in enumerate(self.label_list):
                            curr.append("NA")
                    newS = ""
                    for i in range(len(curr)):
                        if i == int(self.lbNo):
                            newS+=picked+":"
                        else:
                            newS+=curr[i]+":"
                    newS = newS[:-1]
                    newLine+= newS+","
                elif i==5:
                    if labels[i][1][0].isChecked():
                        labels[i][1][0].setChecked(True)
                        labels[i][1][1].setChecked(False)
                        newLine+=  "M,"
                    else:
                        labels[i][1][1].setChecked(True)
                        labels[i][1][0].setChecked(False)
                        newLine+=  "F,"
                elif i==7 or i==8:
                    num = labels[i][1].text() +"-"+ labels[i][2].text() +"-"+ labels[i][3].text()+","
                    newLine+= num
                elif i==11:
                    if labels[i][1][0].isChecked():
                        labels[i][1][0].setChecked(True)
                        labels[i][1][1].setChecked(False)
                        labels[i][1][2].setChecked(False)
                        labels[i][1][3].setChecked(False)
                        newLine+=  "A,"
                    elif labels[i][1][1].isChecked():
                        labels[i][1][1].setChecked(True)
                        labels[i][1][0].setChecked(False)
                        labels[i][1][2].setChecked(False)
                        labels[i][1][3].setChecked(False)
                        newLine+=  "B,"
                    elif labels[i][1][2].isChecked():
                        labels[i][1][2].setChecked(True)
                        labels[i][1][1].setChecked(False)
                        labels[i][1][0].setChecked(False)
                        labels[i][1][3].setChecked(False)
                        newLine+=  "O,"
                    elif labels[i][1][3].isChecked():
                        labels[i][1][3].setChecked(True)
                        labels[i][1][1].setChecked(False)
                        labels[i][1][0].setChecked(False)
                        labels[i][1][2].setChecked(False)
                        newLine+=  "AB,"
                    else:
                        newLine+= "No Blood type selected,"
                elif i==12 or i==13 or i==14 or i==21 or i==22:
                    if labels[i][1][0].isChecked():
                        labels[i][1][0].setChecked(True)
                        labels[i][1][1].setChecked(False)
                        newLine+=  "Yes,"
                    else:
                        labels[i][1][1].setChecked(True)
                        labels[i][1][0].setChecked(False)
                        newLine+=  "No,"
                elif i==17:
                    if labels[i][1][0].isChecked():
                        labels[i][1][0].setChecked(True)
                        labels[i][1][1].setChecked(False)
                        newLine+=  "ESD,"
                    else:
                        labels[i][1][1].setChecked(True)
                        labels[i][1][0].setChecked(False)
                        newLine+=  "OP,"
                elif i==4:
                    if labels[i][1].text() == "":
                        newLine+=self.patientNo+","
                    else:
                        newLine+= (labels[i][1].text()) + ","
                        self.patientNo = labels[i][1].text()
                elif i==26:
                    s = labels[i][1].text()
                    s.replace("\n", "")
                    s.replace(" ", "")
                    newLine+=s+","
                else:
                    newLine+= (labels[i][1].text()) + ","

            newLine = newLine[:-1]
            # self.namingFormat(newLine)
            newLine = self.namingFormat("Placeholder,"+newLine)+","+newLine
            self.replace_line(self.parentFolder+'/patient_information.txt',self.currentPatient,newLine)
            self.patient_information.clear()

            #displaying information on information widget
            self.currentPatient = newLine
            infoList = self.currentPatient.split(",")
 
            for i in range(0,len(self.title)-1):
                title = self.title[i+1]
                if title == "ROI Label 넘버:  ":
                    it = title+"Label_"+self.lbNo
                elif title== "ROI Label 좌표:  ":
                    it = title+self.currLabel
                elif title== "종양위치1:  " or title=="종양위치2:  " or title=="병리결과:  "or title=="Cancer depth:  ":# or title=="기관: ":#or title=="기저질환:  " or title=="위,식도 질환 과거력:  " or title=="기관: ":      
                    curr = infoList[i+1].split(":")
                    it = title+ curr[int(self.lbNo)]
                elif title=="기저질환:  " or title=="위,식도 질환 과거력:  ":
                    curr = infoList[i+1].split(":")
                    it=""
                    for i in curr:
                        if i!="NA":
                            it+=i+","
                    if len(it)>0:
                        it=it[:-1]
                    if len(it)==0:
                        it = "No detection"
                    it = title + it
                elif title== "환자번호:  ":
                    it = title+self.patientNo
                else:
                    it = title+infoList[i+1]
                self.patient_information.addItem(it)

            self.exit.setDisabled(False)
            dlg.close()

        def cancel():
            self.exit.setDisabled(False)
            dlg.close()

        self.rectangle = QPushButton('Save', dlg)
        self.rectangle.move(65,650)
        self.rectangle.resize(90, 27)
        self.rectangle.clicked.connect(save)

        self.rectangle = QPushButton('Cancel', dlg)
        self.rectangle.move(175,650)
        self.rectangle.resize(90, 27)
        self.rectangle.clicked.connect(cancel)

        dlg.exec_()

    def replace_line(self, filepath, oldline, newline):
            f = open(filepath, "r+", encoding='utf-8')
            lines = f.readlines()
            oldID = oldline.split(",")[0]
            f.seek(0)
            if oldID=="이미지 파일 명":
                for line in lines:
                    lineID = line.split(",")[0]
                    if lineID!='\n' :
                        line.replace('\n', "")
                        f.write(line)
                f.write(newline+ '\n')
            else:
                for line in lines:
                    lineID = line.split(",")[0]
                    if lineID!=oldID and lineID!='\n' :
                        line.replace('\n', "")
                        f.write(line)
                f.write(newline+ '\n')
            f.truncate()

    def rename(self, path, filename, newName):
        os.chdir(path)
        for f in (os.listdir(path)):
            ff = f.split(".")
            if ff[0] == filename:
                try:
                    os.rename(path + "/"+f, path + "/"+newName +"."+ ff[1])
                    self.coord_path = self.location + "/"+self.currentID+".txt"
                    # print("renamed to-->", self.coord_path)
                except Exception as e: 
                    print(e)
                    break
    def namingFormat(self, newline):
        listForNaming = newline.split(",")
        naming = ""
        for i in listForNaming[21].split(":"):
            naming+=i+"|"
        naming = naming[:-1]
        naming+="-"
        for i in listForNaming[19].split(":"):
            naming+=i+"|"
        naming = naming[:-1]
        naming+="-"
        for i in listForNaming[20].split(":"):
            naming+=i+"|"

        newName = self.patientNo+"-"+listForNaming[6]+"-"+listForNaming[7]+"-"+naming[:-1]+r"-"+self.indexNo
        newName = newName.replace("|","_")
        if len(newName)>240:
            newName = newName[:250]+"END"
        self.rename(self.location, self.currentID, newName)
        self.currentID = newName
        suffixs = self.filename.split("/")[-1]
        suffix = suffixs.split(".")[-1]
        self.filename = self.location + "/" + newName + "." + suffix
        self.coord_path = self.location + "/" + newName + ".txt"
        return newName

    def downloadInfo(self):
        df = pandas.read_csv(self.parentFolder+'/patient_information.txt')
        df.to_excel(self.parentFolder+ '/patient_information_saved.xlsx', 'Sheet1')
    
    def updateLabelList(self):
        f=open(self.filename.replace(".jpg",".txt").replace(".jpeg",".txt").replace(".png",".txt"),"w")
        for ann in self.annotation_content:
            f.write(str(self.annotation_content[ann]['x0'])+","+str(self.annotation_content[ann]['y0'])+","+
                    str(self.annotation_content[ann]['x1'])+","+str(self.annotation_content[ann]['y1'])+"\n")

        self.text_list.append(f.name.split("/")[-1]) if f.name.split("/")[-1] not in self.text_list else self.text_list
        f.close()
    



    def exitbutton(self):
        sys.exit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Main()
    win.show()
    sys.exit(app.exec_())
