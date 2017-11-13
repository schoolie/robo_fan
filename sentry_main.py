#!/usr/bin/python

import sys
import cv2
import numpy as np
import math
import turret_drivers
import kb_poller
import capture_drivers
import timer_driver
import threading
from time import sleep
# ===========================================================================
# This is the main executable for the robot.
# run "$python main.py" with 1(display) or 0(no display[default])
# Per your hardware, you'll want to adjust:
# - MyDriverWrapper for servo driver
# - MyDims.__init__ values below
#   - pixelPulseRatio is pixels your camera moves for 1.0 pulse
# - Turret.__init__ values
# ===========================================================================

class MyDims() :  
    def __init__(self):
        self.scaledown = 4.0 #shrink for processing speed
        self.displayscaledown = 1.0#3.0 #shrink for display speed
        self.pixelPulseRatio = 866.0/self.scaledown # cam image measured: 433px=.5 pulse
        self.areathreshold = 800/self.scaledown #min contour area 
        self.adjuststep = 5 # keys: asd(hsv+),zxc(hsv-), fv(area+-)
        self.hsvrange = [15,100,120] #HSV +/- range
        self.sampleradius = 10/int(self.scaledown) #to sample center

    def camDims(self,w,h):
        self.w = w
        self.h = h
        self.wmiddle = self.w/2.0
        self.hmiddle = self.h/2.0
        self.scalebackup = self.scaledown/self.displayscaledown
        self.displayw = int(self.w * self.scalebackup)
        self.displayh = int(self.h * self.scalebackup)
    
    def coordToPulse(self,coord):
        xpulse = (float(coord[0]) - self.wmiddle) / self.pixelPulseRatio
        ypulse = (self.hmiddle - float(coord[1])) / self.pixelPulseRatio
        return (xpulse,ypulse)
    
    def setHsvRange(self, hsvtarget):
        self.hsvlower = np.array([max(0,hsvtarget[0]-self.hsvrange[0]), max(0,hsvtarget[1]-self.hsvrange[1]), max(0,hsvtarget[2]-self.hsvrange[2])], dtype=np.uint8)
        self.hsvupper = np.array([min(180,hsvtarget[0]+self.hsvrange[1]), min(255,hsvtarget[1]+self.hsvrange[1]), min(255,hsvtarget[2]+self.hsvrange[2])], dtype=np.uint8)

def getBestContour(imgmask, threshold):
    image,contours,hierarchy = cv2.findContours(imgmask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    best_area = threshold
    best_cnt = None
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > best_area:
            best_area = area
            best_cnt = cnt            
    return best_cnt
        
def main(display) :
    
    #init
    dims = MyDims()   
    cam = capture_drivers.fileCapture('videos/sample.webm')
    # cam = capture_drivers.ipCamCapture()
    
    
    cam.scale(dims.scaledown)
    dims.camDims(cam.w, cam.h)    
     
    #start keyboard, turret
    kb_poller.WaitKey().thread.start()

    turret = turret_drivers.ipCamTurret()

    #turret = Turret.Controller()
    #turret.daemon = True
    #turret.recenter()
    #turret.start()
    
    #target
    hsvtarget = None #HSV:0-180,255,255   
    rgbtarget = None #for display only    
    #motion detect mode
    cam.getFrame()
    avgframe = np.float32(cam.frame)
    avgtimer = threading.Event()
    avgstarted = False
    modemotion = False
    #sound warning
    warningtimer = threading.Event()
    warningstarted = False
    
    while(1):
        sleep(1/40) 
        #capture frame,position
        # framexy = turret.xy
        cam.getFrame()        
        if display: #default display
            displayframe = cam.frame
         

        #track target - hsv target set
        if not hsvtarget == None:
            #10 second arm warning
            #if not turret.armed: 
            #    if not warningstarted:
            #        timer_driver.Countdown(1, warningtimer).thread.start()
            #        sleep(.1) #timer set
            #        warningstarted = True
            #    elif not warningtimer.isSet():
            #        warningtimer.set() #once per reset
            #        turret.armed = True
            #find best contour in hsv range
            framehsv = cv2.cvtColor(cam.frame, cv2.COLOR_BGR2HSV)
            framemask = cv2.inRange(framehsv, dims.hsvlower, dims.hsvupper) 
            if display: #color copy
                displaymaskframe = cv2.cvtColor(framemask.copy(), cv2.COLOR_GRAY2BGR)
                displayframe = cv2.addWeighted(cam.frame, 0.7, displaymaskframe, 0.3, 0)
            best_cnt = getBestContour(framemask, dims.areathreshold)  
            if not best_cnt == None: #if match found
                #get center
                M = cv2.moments(best_cnt)
                cx,cy = int(M['m10']/M['m00']), int(M['m01']/M['m00'])                    
                #update turret
                # turret.sendTarget(dims.coordToPulse((cx,cy)), framexy)

                hyst = 5
                if cx > cam.w / 2 + hyst:
                    turret.pan('left')
                elif cx < cam.w / 2 - hyst:
                    turret.pan('right')
                else:
                    turret.pan_stop()

                if cy > cam.h / 2 + hyst:
                    turret.tilt('down')
                elif cy < cam.h / 2 - hyst:
                    turret.tilt('up')
                else:
                    turret.tilt_stop()

                if display:
                    #display circle target
                    objcenter = (cx,cy)
                    objradius = int(round(math.sqrt(cv2.contourArea(best_cnt)),2))
                    cv2.circle(displayframe, objcenter, objradius, (0,0,0), 5)
                    cv2.circle(displayframe, objcenter, objradius, rgbtarget, 3)
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(displayframe, str(objcenter),(50,50), font, 0.5, 255)
        #wait for motion
        if hsvtarget == None and modemotion == True: 
            if not avgstarted:
                print("accumulating average..."  )
                timer_driver.Countdown(5, avgtimer).thread.start()
                sleep(.1) #timer set
                avgstarted = True   
            if avgtimer.isSet():
                cv2.accumulateWeighted(cam.frame, avgframe, 0.8) 
                resframe = cv2.convertScaleAbs(avgframe)
            else:  
                # cv2.imshow('Average', resframe)
                print("waiting for motion..."   )
                #mask all motion  
                motionmask = cv2.absdiff(cam.frame, resframe)
                motionmask = cv2.cvtColor(motionmask, cv2.COLOR_RGB2GRAY)
                _,motionmask = cv2.threshold(motionmask, 50, 255, cv2.THRESH_BINARY)
                if display:
                    displayframe = motionmask.copy()
                #find best
                cntmask = motionmask.copy()
                cnt = getBestContour(cntmask, dims.areathreshold)               
                if not cnt == None:
                    #motion found - mask best, get mean
                    cv2.rectangle(motionmask, tuple([0,0]), tuple([cam.w,cam.h]), (0,0,0), -1) 
                    cv2.drawContours(motionmask, tuple([cnt]), 0, (255,255,255), -1)
                    rgbtarget = cv2.mean(cam.frame, motionmask)
                    framehsv = cv2.cvtColor(cam.frame, cv2.COLOR_BGR2HSV)
                    hsvtarget = cv2.mean(framehsv, motionmask)
                    #set target
                    dims.setHsvRange(hsvtarget)
                    modemotion = False
                        
        if display:
            displayframe = cv2.resize(displayframe, (dims.displayw, dims.displayh))
            cv2.imshow('display', displayframe)
            key = cv2.waitKey(1)
            #transfer char from opencv window
            if key>0:
                kb_poller.keypressed.set()
                kb_poller.key = chr(key)            
                        
        #key handler
        if kb_poller.keypressed.isSet():  
            if kb_poller.key=="a":
                pass #turret.moveLeft()
            elif kb_poller.key=="q": #quit
                print("Exiting...")
                #turret.quit()
                cam.quit()
                cv2.destroyAllWindows()
                break
            elif kb_poller.key==" ": #reset all
                print("Reset.")
                hsvtarget = None
                #turret.armed = True
                avgstarted = False
                warningstarted = False
                #turret.recenter()
            if kb_poller.key=="r": #sample center of image
                print("reloading")
                #turret.reloadGun()
            elif kb_poller.key=="1": #start motion detect
                print("Start motion detect.")
                modemotion = True
            if kb_poller.key=="2": #sample center of image
                print("Sample center HSV."                       )
                framecenter = cam.frame[(dims.h/2)-dims.sampleradius:(dims.h/2)+dims.sampleradius, (dims.w/2)-dims.sampleradius:(dims.w/2)+dims.sampleradius]
                framecenterhsv = cv2.cvtColor(framecenter, cv2.COLOR_BGR2HSV)
                hsvtarget = [int(cv2.mean(framecenterhsv)[0]), int(cv2.mean(framecenterhsv)[1]), int(cv2.mean(framecenterhsv)[2])]
                rgbtarget = [int(cv2.mean(framecenter)[0]), int(cv2.mean(framecenter)[1]), int(cv2.mean(framecenter)[2])]
            if kb_poller.key=="p": #toggle armed
                pass#turret.armed = not turret.armed       
            if kb_poller.key=="f": #reset all
                print("Firing")
                #turret.fire()
                print("Fired")
            if kb_poller.key=="l": #target trigger sensitivity
                pass#turret.firesensitivity += .01
            if kb_poller.key=="m":
                pass#turret.firesensitivity -= .01                    
            #if kb_poller.key=="a": #hue
            #    dims.hsvrange[0] += dims.adjuststep
            if kb_poller.key=="z":
                dims.hsvrange[0] -= dims.adjuststep
            if kb_poller.key=="s": #sat
                dims.hsvrange[1] += dims.adjuststep
            if kb_poller.key=="x":
                dims.hsvrange[1] -= dims.adjuststep
            if kb_poller.key=="d": #val
                dims.hsvrange[2] += dims.adjuststep
            if kb_poller.key=="c":
                dims.hsvrange[2] -= dims.adjuststep
            if kb_poller.key=="f": #area
                dims.areathreshold += dims.adjuststep
            if kb_poller.key=="v":
                dims.areathreshold -= dims.adjuststep                    
                #adjust target settings/range
            if not hsvtarget == None:
                dims.setHsvRange(hsvtarget)
                print(">> HSV:",hsvtarget[0],hsvtarget[1],hsvtarget[2],"Range:",dims.hsvrange[0],dims.hsvrange[1],dims.hsvrange[2],"Area:",dims.areathreshold,)
            #reset key polling
            kb_poller.WaitKey().thread.start()
        
if __name__ == "__main__" :
    print("==========================")
    print("Terminal Commands:")
    print("q = quit")
    print("' ' = reset")
    print("1 = start motion detect")
    print("2 = sample center for target")
    print("f/v = +/- threshhold area")
    print("a,s,d/z,x,c = +/- H,S,V")
    print("p = toggle armed")
    print("l/m = +/- target sensitivity")
    print("==========================")
    display = 0 #default
    try:
        display = int(sys.argv[1])
    except:
        print("Usage: 0=none/default, 1=display")
    #start
    sys.exit(main(display))
    
