import cv2
import numpy as np
import HandTrackingModule as htm
import time
import pyautogui as pg
from ctypes import cast, POINTER   # pip install pycaw
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Intialization for mouse
#####################
wCam, hCam = 640, 480
wScr, hScr = pg.size()
# print(wScr,hScr)
frameR = 100  # frame Reduction
smoothening = 8
ptime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0
#####################


# Volume Intialization
vol = 0
volBar = 400
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
# volume.GetMute()
# volume.GetMasterVolumeLevel()
volRange = volume.GetVolumeRange() # volume range (-65.25, 0.0)
minVol = volRange[0]
maxVol = volRange[1]


cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

detector = htm.handDetector(maxHands=1)

#

while True:

    #  Find hand Landmarks
    success, img = cap.read()
    # img = cv2.flip(img, 1)
    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img)

    #  Get the tip of the index and middle fingers
    if len(lmList) != 0:
        Ix, Iy = lmList[8][1:]
        Mx, My = lmList[12][1:]
        Tx, Ty = lmList[4][1:]
        Rx, Ry = lmList[16][1:]
        # print(Ix,Iy,Mx,My)

        #  Check which fingers are up
        fingers = detector.fingersUp()
        # print(fingers)
        cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (255, 0, 255), 2)

        #  Only Index Finger : Moving Mode
        if fingers[1] == 1 and fingers[2] == 0 and fingers[0]==0 and fingers[3] == 0:

            #  Convert Coordinates
            x3 = np.interp(Ix, (frameR, wCam - frameR), (0, wScr))
            y3 = np.interp(Iy, (frameR, hCam - frameR), (0, hScr))

            #  Smoothen Values
            clocX = plocX + (x3 - plocX) / smoothening
            clocY = plocY + (y3 - plocY) / smoothening

            #  Move Mouse
            pg.moveTo(wScr - clocX, clocY)
            cv2.circle(img, (Ix, Iy), 15, (255, 0, 255), cv2.FILLED)
            plocX, plocY = clocX, clocY

        #  Both Index and middle fingers are up : Clicking Mode
        if fingers[1] == 1 and fingers[2] == 1 and fingers[0] == 0 and fingers[3] == 0:
            #  Find distance between index finger
            lengthIM, img, lineInfo = detector.findDistance(8, 12, img)
            # print(lengthIM)

            #  Click mouse if distance short
            if lengthIM < 40:
                cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                pg.click()
        
        # Both Thumb and index figer are up : Volume mode
        if fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0:
            # Find distance between finger and thumb
            lengthTI, img, lineInfo = detector.findDistance(4, 8, img)
            # print(length)
            # Hand Range 50 to 300
            # volume Range -65 to 0
            vol = np.interp(lengthTI,[50,250],[minVol,maxVol])
            volBar = np.interp(lengthTI,[50,250],[400,150])
            # print(int(length),vol)
            volume.SetMasterVolumeLevel(vol, None)
            cv2.rectangle(img,(50,150),(85,400),(255, 0, 0),3)
            cv2.rectangle(img,(50,int(volBar)),(85,400),(255, 0, 0),cv2.FILLED)


            if lengthTI < 50:
                cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)


    #  Frame Rate
    ctime = time.time()
    fps = 1 / (ctime - ptime)
    ptime = ctime
    cv2.putText(img, str(int(fps)), (20, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)

    # Display
    cv2.imshow("Image", img)
    cv2.waitKey(1)
