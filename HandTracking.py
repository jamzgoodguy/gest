"""
Hand Tracking Module
By: Murtaza Hassan
Youtube: http://www.youtube.com/c/MurtazasWorkshopRoboticsandAI
Website: https://www.computervision.zone
"""

import cv2
import mediapipe as mp
import time
import math

class handDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = 0.7
        self.trackCon = 0.7
        
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=False,
            max_num_hands=self.maxHands,
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackCon,
            model_complexity=1
        )
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]
        self.prev_landmarks_right = []  # Untuk tangan kanan
        self.prev_landmarks_left = []   # Untuk tangan kiri
        self.smoothing = 0.5

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img

    def findPositionFingers(self, img, draw=True, handNo=0):
        xPositionList = []
        yPositionList = []
        bbox = []
        self.fingersList = []
        self.lmList = []
        handType = None
        
        if self.results.multi_hand_landmarks:
            if handNo < len(self.results.multi_hand_landmarks):
                myHand = self.results.multi_hand_landmarks[handNo]
                
                # Deteksi tipe tangan (kanan/kiri)
                handType = self.results.multi_handedness[handNo].classification[0].label
                
                # Pilih prev_landmarks berdasarkan tipe tangan
                if handType == "Right":
                    if not self.prev_landmarks_right:
                        self.prev_landmarks_right = [[0, 0, 0] for _ in range(21)]
                    prev_landmarks = self.prev_landmarks_right
                else:
                    if not self.prev_landmarks_left:
                        self.prev_landmarks_left = [[0, 0, 0] for _ in range(21)]
                    prev_landmarks = self.prev_landmarks_left
                
                for id, fingerPosition in enumerate(myHand.landmark):
                    hightImage, widthImage, _ = img.shape
                    xScreen = int(fingerPosition.x * widthImage)
                    yScreen = int(fingerPosition.y * hightImage)
                    
                    # Aplikasikan smoothing berdasarkan tipe tangan
                    smooth_x = int(prev_landmarks[id][1] * self.smoothing + xScreen * (1 - self.smoothing))
                    smooth_y = int(prev_landmarks[id][2] * self.smoothing + yScreen * (1 - self.smoothing))
                    
                    # Update previous position untuk tangan yang sesuai
                    prev_landmarks[id] = [id, smooth_x, smooth_y]
                    
                    xPositionList.append(smooth_x)
                    yPositionList.append(smooth_y)
                    self.fingersList.append([id, smooth_x, smooth_y])
                    self.lmList.append([id, smooth_x, smooth_y])
                    
                    if draw:
                        cv2.circle(img, (smooth_x, smooth_y), 5, (255, 0, 255), cv2.FILLED)

                # Update prev_landmarks yang sesuai
                if handType == "Right":
                    self.prev_landmarks_right = prev_landmarks
                else:
                    self.prev_landmarks_left = prev_landmarks

                xmin, xmax = min(xPositionList), max(xPositionList)
                ymin, ymax = min(yPositionList), max(yPositionList)
                bbox = xmin, ymin, xmax, ymax

                if draw:
                    cv2.rectangle(img, (bbox[0] - 20, bbox[1] - 20),
                        (bbox[2] + 20, bbox[3] + 20), (0, 255, 0), 2)

        return self.fingersList, handType

    def getDistance(self, indexFingerTip, middleFingerTip):
        xIndex, yIndex = indexFingerTip[1], indexFingerTip[2]
        xMiddle, yMiddle = middleFingerTip[1], middleFingerTip[2]
        
        return(math.dist([xIndex,yIndex], [xMiddle, yMiddle]))
    
    def fingersUp(self):
        fingers = []
        # Thumb
        if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)
        # 4 Fingers
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers


