#!/usr/bin/python

import numpy as np
import urllib.request 
import cv2
import time
from ip_cam import ipCam

class ipCamDriver(ipCam):

    def read(self):
        imgResp = urllib.request.urlopen(self.url)
        resp = imgResp.read()
        imgNp = np.array(bytearray(resp),dtype=np.uint8)
        img = cv2.imdecode(imgNp,-1)
        return (True, img)

class webCamCapture(object):   

    def __init__(self):
        
        self.capture = cv2.VideoCapture(0)
        self.w = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.h = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def quit(self):
        self.capture.release()
    
    def scale(self, scaledown): #for faster processing
        self.w = int(self.w/scaledown)
        self.h = int(self.h/scaledown)
    
    def getFrame(self):
        _,frame = self.capture.read()
        self.frame = cv2.resize(frame, (self.w, self.h))

class fileCapture(webCamCapture):
    def __init__(self, filename):

        self.capture = cv2.VideoCapture(filename)
        self.w = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.h = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

class ipCamCapture(webCamCapture) :   
    def __init__(self,
            url='http://24.28.2.107:81/media',
            url_args='?action=snapshot',
            user='admin',
            pwd='Amanda09',
            ):

        self.capture = ipCamDriver(url, url_args, user, pwd)
        
        self.w = 640
        self.h = 480
