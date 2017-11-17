#!/usr/bin/python

# import driver.MyDriverWrapper 
import threading
# import Timer
from time import sleep
# import serial
# import RPi.GPIO as GPIO ## Import GPIO library

from ip_cam import ipCam
import urllib.request

class ipCamTurret(ipCam):

    def pan(self, direction):
        if direction == 'left':
            self.pan_dir = 3
        elif direction == 'right':
            self.pan_dir = 4

        start_url = '{base_url}/?action=cmd&code={code}&value={direction}'.format(
                base_url=self.base_url, code=2, direction=self.pan_dir)
        urllib.request.urlopen(start_url)

    def pan_stop(self):
        if hasattr(self, 'pan_dir'):
            stop_url = '{base_url}/?action=cmd&code={code}&value={direction}'.format(
                    base_url=self.base_url, code=3, direction=self.pan_dir)
            urllib.request.urlopen(stop_url)

    def tilt(self, direction):
        if direction == 'up':
            self.tilt_dir = 1
        elif direction == 'down':
            self.tilt_dir = 2

        start_url = '{base_url}/?action=cmd&code={code}&value={direction}'.format(
                base_url=self.base_url, code=2, direction=self.tilt_dir)
        urllib.request.urlopen(start_url)

    def tilt_stop(self):
        if hasattr(self, 'tilt_dir'):
            stop_url = '{base_url}/?action=cmd&code={code}&value={direction}'.format(
                    base_url=self.base_url, code=3, direction=self.tilt_dir)
            urllib.request.urlopen(stop_url)

  
# #globals
# threadquit = threading.Event()
# 
# 
# class Controller(threading.Thread) : 
#   
#     def __init__(self):
#         # My Servo pins
#         GPIO.setmode(GPIO.BOARD) ## Use board pin numbering
#         GPIO.setwarnings(False)
#         self.servoX = 0 #pan servo
#         self.servoY = 3 #tilt servo
#         #self.Motor1A = 21
#         #self.ser = serial.Serial('/dev/ttyACM0', 9600)
#         self.driver = driver.MyDriverWrapper.ServoDriver()
#         #=========== 
#         self.center = [0.0, 0.0] #where to recenter
#         self.fps = 1.5 #frame per seconds  *** movement is wild if set too high ***
#         self.stepsleep = 0.05 #time per step (smoothness)
#         self.firesensitivity = .02 #how trigger happy
#         self.triggerwait = 3 #seconds between fire/reload
#         #variables
#         self.triggertimer = threading.Event()
#         self.armed = False #will fire
#         self.xy = self.center[:]  #current xy
#         self.deltaxy = [0.0, 0.0]  #current move
#         self.deltaxylast = [0.0, 0.0]  #prior move
#         self.stepxy = [0.0, 0.0]  #xy per step
#         self.steps = (1.0/self.fps)/self.stepsleep #steps per frame
#         self.stepcounter = 0 #motion step counter
#         threading.Thread.__init__(self)
#         
#     def fire(self): #pull trigger
#         GPIO.setup(18, GPIO.OUT) ## Setup GPIO Pin 24 to OUT
#         GPIO.output(18,True) ## Turn on GPIO pin 24
#         sleep(3)
#         GPIO.output(18,False) ## Turn off GPIO pin 24
#         Timer.Countdown(self.triggerwait, self.triggertimer).thread.start()  #between fire
#     
#     def reloadGun(self):
#         self.driver.move(self.servoY, -1)
#         
#     def recenter(self):
#         #zero to center
#         self.stepcounter = 0
#         self.sendTarget([-self.xy[0]+self.center[0], -self.xy[1]+self.center[1]], self.xy)
#         
#     def sendTarget(self, pulsexy, framexy): #pulsexy: delta from 0,0 / framexy: position at capture
#         self.deltaxylast = self.deltaxy[:]
#         #subtract distance since capture
#         self.deltaxy[0] = pulsexy[0]-(self.xy[0]-framexy[0])
#         self.deltaxy[1] = pulsexy[1]-(self.xy[1]-framexy[1])
#         #stay on newest delta
#         if self.stepcounter > 0:
#             if abs(self.deltaxy[0])<abs(self.deltaxylast[0]):
#                 self.stepxy[0] = 0.0
#             if abs(self.deltaxy[1])<abs(self.deltaxylast[1]):
#                 self.stepxy[1] = 0.0
#         '''
#         if abs(self.deltaxy[0])<abs(self.deltaxylast[0]) or abs(self.deltaxy[1])<abs(self.deltaxylast[1]):
#             self.stepcounter = 0
#         '''
#         #fire if on target
#         if self.armed and not self.triggertimer.isSet():
#             if (-(self.firesensitivity) < self.deltaxy[0] < self.firesensitivity) and (-(self.firesensitivity) < self.deltaxy[1] < self.firesensitivity):
#                 print(">>> PEW! PEW!")
#                 if not self.deltaxy[0] == 0:
#                     self.fire()
#                     
#     def moveLeft(self):
#         self.driver.move(self.servoX, self.xy[0]-1)
#                     
#     def quit(self): #cleanup
#         global threadquit
#         self.recenter()
#         sleep(1)
#         threadquit.set()
#         
#     def run(self):
#         global threadquit
#         while(not threadquit.isSet()):
#             sleep(self.stepsleep)
#             if self.stepcounter>0: #stepping to target
#                 self.xy[0] += self.stepxy[0]
#                 self.driver.move(self.servoX, self.xy[0] )
#                 self.xy[1] += self.stepxy[1]
#                 self.driver.move(self.servoY, self.xy[1] )
#                 self.stepcounter -= 1
#             else: #set next target
#                 self.stepxy[0] = self.deltaxy[0]/self.steps 
#                 self.stepxy[1] = self.deltaxy[1]/self.steps 
#                 self.deltaxy = [0.0, 0.0]
#                 self.stepcounter = self.steps
#                 
