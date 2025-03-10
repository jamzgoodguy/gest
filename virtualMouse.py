import cv2 as cv2
import time
import numpy as np
import math
import HandTracking as ht
import gestureControl as gc
import pyautogui as pygui
import signal
import sys

# Tambahkan konstanta untuk ukuran kamera
WIDTH_CAM = 640
HIGHT_CAM = 480

def signal_handler(sig, frame):
    print("\nProgram terminated by user (Ctrl+C)")
    capCam.release()
    cv2.destroyAllWindows()
    sys.exit(0)

def main():
    # Tambahkan handler untuk Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Variable to use on the cam
    controlMovenmt = gc.gestureControll()

    # Inisialisasi variabel untuk FPS
    pTime = 0
    last_valid_imgList = None

    # Setting camera
    capCam = cv2.VideoCapture(0)
    capCam.set(3, WIDTH_CAM)
    capCam.set(4, HIGHT_CAM)

    if not capCam.isOpened():
        print("Error: Cannot open camera")
        return

    # Setting hand recognition based on Mediapipe from Google
    handTracking = ht.handDetector(detectionCon=0.3)

    try:
        while True:
            (success, img) = capCam.read()
            if not success:
                print("Failed to grab frame")
                break

            img = cv2.resize(img, (WIDTH_CAM, HIGHT_CAM), interpolation=cv2.INTER_AREA)
            img = cv2.flip(img, 1)
            
            img = handTracking.findHands(img, draw=True)
            
            # Deteksi tangan kanan dan kiri
            rightHandList = None
            leftHandList = None
            
            try:
                # Cek tangan pertama
                hand1List, hand1Type = handTracking.findPositionFingers(img, draw=True, handNo=0)
                
                # Tambahkan pengecekan confidence
                if hand1List and hand1Type and len(hand1List) >= 21:  # Pastikan semua landmark terdeteksi
                    # Hitung rata-rata jarak antar landmark untuk validasi
                    avg_distance = sum([handTracking.getDistance(hand1List[i], hand1List[i+1]) 
                                     for i in range(0, 20)]) / 20
                    
                    if avg_distance > 10:  # Threshold minimal untuk tangan valid
                        if hand1Type == "Right":
                            rightHandList = hand1List
                        elif hand1Type == "Left":
                            leftHandList = hand1List
                
                # Cek tangan kedua dengan cara yang sama
                if handTracking.results.multi_hand_landmarks and len(handTracking.results.multi_hand_landmarks) > 1:
                    hand2List, hand2Type = handTracking.findPositionFingers(img, draw=True, handNo=1)
                    
                    if hand2List and hand2Type and len(hand2List) >= 21:
                        avg_distance = sum([handTracking.getDistance(hand2List[i], hand2List[i+1]) 
                                         for i in range(0, 20)]) / 20
                        
                        if avg_distance > 10:
                            if hand2Type == "Right":
                                rightHandList = hand2List
                            elif hand2Type == "Left":
                                leftHandList = hand2List

            except Exception as e:
                print(f"Hand detection error: {e}")
                rightHandList = None
                leftHandList = None

            # Deteksi gesture aktivasi dan deaktivasi sistem
            if leftHandList and len(leftHandList) > 0:
                try:
                    # tambahan sendiri
                    distanceLeftThumb = int(handTracking.getDistance(leftHandList[4], leftHandList[5]))
                    distanceLeftIndex = int(handTracking.getDistance(leftHandList[8], leftHandList[5]))
                    distanceLeftMiddle = int(handTracking.getDistance(leftHandList[12], leftHandList[9]))
                    distanceLeftRing = int(handTracking.getDistance(leftHandList[16], leftHandList[13]))
                    distanceLeftPinky = int(handTracking.getDistance(leftHandList[20], leftHandList[17]))
                    
                    # Pastikan semua jari terdeteksi sebelum melakukan deaktivasi
                    if (len(leftHandList) >= 21 and  # Pastikan semua landmark terdeteksi
                        distanceLeftThumb >= 50 and 
                        distanceLeftIndex <= 40 and 
                        distanceLeftMiddle <= 40 and 
                        distanceLeftRing <= 40 and 
                        distanceLeftPinky >= 50):
                        
                        # Tambahkan delay kecil sebelum deaktivasi
                        time.sleep(0.1)
                        controlMovenmt.deactivateSystem()
                except Exception as e:
                    print(f"Error in deactivation gesture: {e}")

            if rightHandList and len(rightHandList) > 0:

                # tambahan sendiri
                distanceRightThumb = int(handTracking.getDistance(rightHandList[4], rightHandList[5]))
                distanceRightIndex = int(handTracking.getDistance(rightHandList[8], rightHandList[5]))
                distanceRightMiddle = int(handTracking.getDistance(rightHandList[12], rightHandList[9]))
                distanceRightRing = int(handTracking.getDistance(rightHandList[16], rightHandList[13]))
                distanceRightPinky = int(handTracking.getDistance(rightHandList[20], rightHandList[17]))
                #if distanceLeftThumb >= 50 and distanceLeftIndex <= 40 and distanceLeftMiddle <= 40 and distanceLeftRing <= 40 and distanceLeftPinky <= 40:
                #    controlMovenmt.deactivateSystem()
                

                if distanceRightThumb >= 50 and distanceRightIndex <= 40 and distanceRightMiddle <= 40 and distanceRightRing <= 40 and distanceRightPinky >= 50:
                    controlMovenmt.activateSystem()
            
            # Status sistem
            status_text = "ACTIVE" if controlMovenmt.is_system_active else "INACTIVE"
            status_color = (0, 255, 0) if controlMovenmt.is_system_active else (0, 0, 255)
            cv2.putText(img, f'System: {status_text}', (40, 50), 
                       cv2.FONT_HERSHEY_COMPLEX, 1, status_color, 2)
            
            # Hanya proses gesture jika sistem aktif
            if controlMovenmt.is_system_active:
                # Proses tangan kanan untuk kontrol mouse
                if rightHandList and len(rightHandList) > 0:
                    # Deteksi gesture Alt terlebih dahulu
                    distanceAlt = int(handTracking.getDistance(rightHandList[4], rightHandList[20]))
                    
                    # Hanya lakukan mouse movement jika Alt tidak aktif
                    if distanceAlt > 30:  # Alt tidak aktiff
                        # 1. Movement tracking menggunakan id 8 (ujung telunjuk)
                        x, y = rightHandList[8][1], rightHandList[12][2]
                        controlMovenmt.mouseMovement(x, y)
                    
                    # 2. Right click: jarak antara ibu jari (4) dan jari kelingking (20)
                    distanceRightClick = int(handTracking.getDistance(rightHandList[20], rightHandList[16]))
                    distanceRingFingerRightClick = int(handTracking.getDistance(rightHandList[16], rightHandList[13]))
                    # 3. Left click: jarak antara ibu jari (4) dan jari tengah (12)
                    distanceLeftClick = int(handTracking.getDistance(rightHandList[4], rightHandList[15]))
                    
                    # 4. Middle click: cek jari tengah (12), manis (16), dan kelingking (20) menggenggam
                    distanceMiddleFinger = int(handTracking.getDistance(rightHandList[12], rightHandList[0]))
                    distanceRingFinger = int(handTracking.getDistance(rightHandList[16], rightHandList[0]))
                    distancePinkyFinger = int(handTracking.getDistance(rightHandList[20], rightHandList[0]))
                    
                    distanceBackButton = int(handTracking.getDistance(rightHandList[4], rightHandList[8]))
                    distanceForwardButton = int(handTracking.getDistance(rightHandList[4], rightHandList[12]))
                    # Status teks
                    status = "Moving"
                    status_color = (0, 255, 0)  # Hijau untuk moving
                    
                    # Debug info untuk jarak
                    cv2.putText(img, f'Right Click: {distanceRightClick}', (40, 130), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                    cv2.putText(img, f'Left Click: {distanceLeftClick}', (30, 150), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                    
                    # Deteksi gesture dengan prioritas
                    if distanceRightClick >= 50 and distanceRingFingerRightClick <= 40:  # Right click dengan ibu jari dan kelingking
                        if not controlMovenmt.is_right_click_pressed:
                            controlMovenmt.pressRightClick()
                        status = "Right Click"
                        status_color = (255, 0, 0)  # Biru
                    else:
                        controlMovenmt.releaseRightClick()
                    
                    # Left click detection
                    if distanceLeftClick <= 30:  # Left click dengan ibu jari dan jari tengah
                        if not controlMovenmt.is_left_click_pressed:
                            controlMovenmt.pressLeftClick()
                        status = "Left Click"
                        status_color = (0, 0, 255)  # Merah
                    else:
                        controlMovenmt.releaseLeftClick()
                    
                    # Middle click detection
                    if (distanceMiddleFinger >= 100 and 
                        distanceRingFinger >= 100 and 
                        distancePinkyFinger >= 100):
                        #controlMovenmt.middleClickMovement()
                        #status = "Middle Click"
                        x_pos = rightHandList[8][1]
                        y_pos = rightHandList[8][2]
                        controlMovenmt.handleScroll(x_pos, y_pos)
                        status_color = (255, 165, 0)  # Orange
                    else:
                        controlMovenmt.releaseClick()  # Untuk middle click
                    
                    # Back button detection (ibu jari ke telunjuk)
                    if distanceBackButton <= 40:
                        if not controlMovenmt.is_back_pressed:
                            controlMovenmt.pressBackButton()
                        status = "Back"
                        status_color = (255, 255, 0)  # Kuning
                    else:
                        controlMovenmt.releaseBackButton()
                    
                    # Forward button detection (ibu jari ke jari tengah)
                    if distanceForwardButton <= 40:
                        if not controlMovenmt.is_forward_pressed:
                            controlMovenmt.pressForwardButton()
                        status = "Forward"
                        status_color = (255, 255, 0)  # Kuning
                    else:
                        controlMovenmt.releaseForwardButton()
                    
                    # Tampilkan status
                    cv2.putText(img, f'Status: {status}', (40, 170), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, status_color, 2)

                # Proses tangan kiri untuk left click, print screen, ESC, dan zoom
                if leftHandList and len(leftHandList) > 0:
                    # Deteksi gesture left click (jarak antara telunjuk dan ibu jari)
                    distanceLeftClick = int(handTracking.getDistance(leftHandList[8], leftHandList[4]))
                    distanceLeftThumb = int(handTracking.getDistance(leftHandList[4], leftHandList[15]))
                    
                    # Deteksi gesture ESC (jari kelingking ke pangkal)
                    distancePinky = int(handTracking.getDistance(leftHandList[20], leftHandList[17]))   # Kelingking
                    
                    # Deteksi gesture print screen (jari manis ke pangkal)
                    distanceRing = int(handTracking.getDistance(leftHandList[16], leftHandList[13]))    # Jari manis
                    
                    # Deteksi gesture zoom (ibu jari dan jari tengah)
                    
                    # Deteksi gesture volume (ibu jari dan jari manis)
                    distanceVolume = int(handTracking.getDistance(leftHandList[4], leftHandList[16]))  # Jarak ibu jari ke jari manis
                    
                    # Deteksi gesture tombol F (ibu jari dan jari tengah)
                    distanceF = int(handTracking.getDistance(leftHandList[4], leftHandList[12]))  # Jarak ibu jari ke jari tengah
                    
                    # Debug info untuk jarak
                    cv2.putText(img, f'Left Click: {distanceLeftClick}', (40, 210), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                    cv2.putText(img, f'Pinky (ESC): {distancePinky}', (40, 250), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                    
                    # Aktifkan left click jika jari telunjuk dan ibu jari berdekatan
                    if distanceLeftClick <= 30 and distancePinky >= 50:
                        if not controlMovenmt.is_left_click_pressed:  # Hanya tekan jika belum ditekan
                            controlMovenmt.pressLeftClick()
                        cv2.putText(img, 'LEFT CLICK', (40, 290), 
                                  cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    else:
                        controlMovenmt.releaseLeftClick()  # Lepas hanya jika gesture tidak terdeteksi
                    
                    # Aktifkan ESC jika jari kelingking ditekuk
                    if distancePinky <= 40:
                        controlMovenmt.pressEsc()
                        cv2.putText(img, 'ESC PRESSED', (40, 330), 
                                  cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    else:
                        controlMovenmt.releaseEsc()
                    
                    # Cek gesture print screen dengan validasi tambahan
                    if distanceRing <= 50 and distancePinky <= 50 and distanceLeftThumb < 50:
                        # Tambahkan pengecekan posisi jari lain
                        distanceIndex = int(handTracking.getDistance(leftHandList[8], leftHandList[0]))
                        distanceMiddle = int(handTracking.getDistance(leftHandList[12], leftHandList[0]))
                        
                        # Print screen hanya aktif jika jari lain juga menggenggam
                        if distanceIndex > 100 and distanceMiddle > 100:
                            elapsed_time = controlMovenmt.pressPrintScreen()
                            if elapsed_time > 0:
                                remaining = max(0, 2.0 - elapsed_time)
                                cv2.putText(img, f'PRINT SCREEN in {remaining:.1f}s', (40, 370), 
                                          cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                            if controlMovenmt.is_prtsc_pressed:
                                cv2.putText(img, 'PRINT SCREEN!', (40, 370), 
                                          cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    else:
                        controlMovenmt.releasePrintScreen()
                    
                    # Debug info untuk zoom
                    
                    
                    # Debug info untuk volume
                    cv2.putText(img, f'Volume Distance: {distanceVolume}', (40, 470), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                    
                    # Aktifkan volume control jika ibu jari dan jari manis berdekatan
                    if distanceVolume <= 30:
                        # Gunakan posisi Y dari jari manis untuk kontrol volume
                        y_pos = leftHandList[16][2]
                        controlMovenmt.handleVolume(y_pos)
                        
                        # Visual feedback
                        if y_pos < controlMovenmt.last_volume_y:  # Bergerak ke atas
                            cv2.putText(img, 'VOLUME UP', (40, 510), 
                                      cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                        else:  # Bergerak ke bawah
                            cv2.putText(img, 'VOLUME DOWN', (40, 510), 
                                      cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    else:
                        controlMovenmt.releaseVolume()
                    
                    # Debug info untuk jarak F
                    cv2.putText(img, f'F Distance: {distanceF}', (40, 530), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                    
                    # Aktifkan tombol F jika ibu jari dan jari tengah berdekatan
                    if distanceF <= 30 and distancePinky >= 50:
                        if not controlMovenmt.is_f_pressed:
                            controlMovenmt.pressF()
                        cv2.putText(img, 'F PRESSED', (40, 550), 
                                  cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    else:
                        controlMovenmt.releaseF()

                # Proses tangan kiri untuk scroll
                if leftHandList and len(leftHandList) > 0:
                    # Deteksi gesture scroll
                    # Cek jari manis dan kelingking tertekuk
                    ring_bent = handTracking.getDistance(leftHandList[16], leftHandList[13]) <= 30
                    pinky_bent = handTracking.getDistance(leftHandList[20], leftHandList[17]) <= 30
                    
                    # Cek jari tengah, telunjuk dan ibu jari berdiri
                    thumb_up = handTracking.getDistance(leftHandList[4], leftHandList[2]) >= 50
                    index_up = handTracking.getDistance(leftHandList[8], leftHandList[5]) >= 50
                    middle_up = handTracking.getDistance(leftHandList[12], leftHandList[9]) >= 50
                    
                    # Aktifkan scroll jika gesture sesuai
                    if ring_bent and pinky_bent and thumb_up and index_up and middle_up:
                        # Gunakan posisi telunjuk untuk kontrol scroll
                        x_pos = leftHandList[8][1]
                        y_pos = leftHandList[8][2]
                        controlMovenmt.handleScroll(x_pos, y_pos)
                        
                        # Visual feedback
                        cv2.putText(img, 'SCROLLING', (40, 570), 
                                  cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    else:
                        controlMovenmt.releaseScroll()

                # Deteksi zoom dengan dua tangan (jari telunjuk dan tengah)
                if rightHandList and leftHandList:
                    # Cek jarak antara telunjuk kanan dan kiri
                    right_index = rightHandList[8]  # Telunjuk kanan
                    right_index_mid = rightHandList[5]
                    right_middle = rightHandList[12]  # Tengah kanan
                    right_middle_mid =  rightHandList[9]
                    right_ring = rightHandList[16]  # Jari manis kanan
                    right_ring_mid = rightHandList[13]
                    right_pinky = rightHandList[20]  # Jari kelingking kanan
                    right_pinky_mid = rightHandList[17]
                    left_index = leftHandList[8]    # Telunjuk kiri
                    left_index_mid = leftHandList[5]
                    left_middle = leftHandList[12]  # Tengah kiri
                    left_middle_mid = leftHandList[9]
                    left_ring = leftHandList[16]  # Jari manis kiri
                    left_ring_mid = leftHandList[13]
                    left_pinky = leftHandList[20]  # Jari kelingking kiri
                    left_pinky_mid = leftHandList[17]
                    # Hitung jarak antara kedua telunjuk
                    distance_between_hands = handTracking.getDistance(right_index, left_index)
                    
                    # Debug info untuk jarak zoom
                    cv2.putText(img, f'Two Hands Zoom: {int(distance_between_hands)}', (40, 410), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                    
                    # Cek apakah kedua tangan menunjukkan gesture yang benar
                    right_fingers_dist = handTracking.getDistance(right_index, right_middle)
                    left_fingers_dist = handTracking.getDistance(left_index, left_middle)
                    right_fingers_dist_ring = handTracking.getDistance(right_ring, right_ring_mid)
                    left_fingers_dist_ring = handTracking.getDistance(left_ring, left_ring_mid)
                    right_fingers_dist_middle = handTracking.getDistance(right_middle, right_middle_mid)
                    right_fingers_dist_index = handTracking.getDistance(right_index, right_index_mid)
                    left_fingers_dist_index = handTracking.getDistance(left_index, left_index_mid)
                    left_fingers_dist_middle = handTracking.getDistance(left_middle, left_middle_mid)
                    right_fingers_dist_pinky = handTracking.getDistance(right_pinky, right_pinky_mid)
                    left_fingers_dist_pinky = handTracking.getDistance(left_pinky, left_pinky_mid)
                    
                    if right_fingers_dist <= 50 and left_fingers_dist <= 50 and right_fingers_dist_ring <= 50 and left_fingers_dist_ring <= 50 and right_fingers_dist_middle >= 60 and left_fingers_dist_middle >= 60 and right_fingers_dist_index >= 60 and left_fingers_dist_index >= 60 and right_fingers_dist_pinky <= 50 and left_fingers_dist_pinky <= 50:  # Kedua tangan menunjukkan gesture
                        controlMovenmt.handleTwoHandZoom(distance_between_hands)
                        
                        # Visual feedback
                        if distance_between_hands > controlMovenmt.last_two_hand_distance:  # Menjauh
                            cv2.putText(img, 'ZOOM IN', (40, 450), 
                                      cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                        else:  # Mendekat
                            cv2.putText(img, 'ZOOM OUT', (40, 450), 
                                      cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    else:
                        controlMovenmt.releaseTwoHandZoom()
                else:
                    controlMovenmt.releaseTwoHandZoom()

                # Proses tangan kiri untuk copy dan paste
                if leftHandList and len(leftHandList) > 0:
                    # Deteksi gesture copy (semua jari menggenggam)
                    thumb_bent = handTracking.getDistance(leftHandList[4], leftHandList[7]) <= 50
                    index_bent = handTracking.getDistance(leftHandList[8], leftHandList[5]) <= 50
                    middle_bent = handTracking.getDistance(leftHandList[12], leftHandList[9]) <= 50
                    ring_bent = handTracking.getDistance(leftHandList[16], leftHandList[13]) <= 50
                    pinky_bent = handTracking.getDistance(leftHandList[20], leftHandList[17]) <= 50
                    
                    # Deteksi gesture paste (hanya ibu jari menggenggam)
                    thumb_bent_paste = handTracking.getDistance(leftHandList[4], leftHandList[5]) <= 40
                    index_up = handTracking.getDistance(leftHandList[8], leftHandList[5]) >= 65
                    middle_up = handTracking.getDistance(leftHandList[12], leftHandList[9]) >= 65
                    ring_up = handTracking.getDistance(leftHandList[16], leftHandList[13]) >= 65
                    pinky_up = handTracking.getDistance(leftHandList[20], leftHandList[17]) >= 65
                    
                    # Aktifkan copy jika semua jari menggenggam1. Data Pribadi:


                    if thumb_bent and index_bent and middle_bent and ring_bent and pinky_bent:
                        if not controlMovenmt.is_copy_pressed:
                            controlMovenmt.pressCopy()
                        cv2.putText(img, 'COPY', (40, 590), 
                                  cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    else:
                        controlMovenmt.releaseCopy()
                    
                    # Aktifkan paste jika gesture "empat" (hanya ibu jari menggenggam)
                    if thumb_bent_paste and index_up and middle_up and ring_up and pinky_up:
                        if not controlMovenmt.is_paste_pressed:
                            controlMovenmt.pressPaste()
                        cv2.putText(img, 'PASTE', (40, 610), 
                                  cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    else:
                        controlMovenmt.releasePaste()

                # Proses tangan kanan untuk Alt dan Tab
                if rightHandList and len(rightHandList) > 0:
                    # Deteksi gesture Alt (ibu jari dan kelingking bersentuhan)
                    distanceAlt = int(handTracking.getDistance(rightHandList[4], rightHandList[20]))  # Jarak ibu jari ke kelingking
                    
                    # Deteksi gesture Tab (ibu jari dan jari tengah bersentuhan)
                    distanceTabThumb = int(handTracking.getDistance(rightHandList[4], rightHandList[12]))  # Jarak ibu jari ke jari tengah
                    distanceTabMiddle = int(handTracking.getDistance(rightHandList[20], rightHandList[12]))  # Jarak jari tengah ke pangkal
                    
                    # Debug info
                    cv2.putText(img, f'Alt Distance: {distanceAlt}', (40, 630), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                    cv2.putText(img, f'Tab Distance: {distanceTabThumb}', (40, 650),    
                               cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                    
                    # Aktifkan Alt jika ibu jari dan kelingking bersentuhan
                    if distanceAlt <= 30:
                        if not controlMovenmt.is_alt_pressed:
                            controlMovenmt.pressAlt()
                        cv2.putText(img, 'ALT PRESSED', (40, 670), 
                                  cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    else:
                        controlMovenmt.releaseAlt()
                    
                    # Aktifkan Tab jika ibu jari dan jari tengah bersentuhan, dan jari tengah tertekuk
                    if distanceTabThumb <= 40 and distanceTabMiddle <= 40:
                        if not controlMovenmt.is_tab_pressed:
                            controlMovenmt.pressTab()
                        cv2.putText(img, 'TAB PRESSED', (40, 690), 
                                  cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    else:
                        controlMovenmt.releaseTab()

                # Proses tangan kiri untuk Ctrl dan Tab
                if leftHandList and len(leftHandList) > 0:
                    # Deteksi gesture Ctrl (icv2.putTextbu jari dan kelingking bersentuhan)
                    distanceCtrl = int(handTracking.getDistance(leftHandList[4], leftHandList[20]))  # Jarak ibu jari ke kelingking
                    
                    # Deteksi gesture Tab (ibu jari dan jari tengah bersentuhan)
                    distanceTabThumbLeft = int(handTracking.getDistance(leftHandList[4], leftHandList[12]))  # Jarak ibu jari ke jari tengah
                    distanceTabMiddleLeft = int(handTracking.getDistance(leftHandList[20], leftHandList[12]))  # Jarak jari tengah ke kelingking
                    distanceTabRingLeft = int(handTracking.getDistance(leftHandList[16], leftHandList[13]))  # Jarak jari manis ke pangkal
                    distanceTabIndexLeft = int(handTracking.getDistance(leftHandList[8], leftHandList[5]))  # Jarak jari telunjuk ke pangkal
                    
                    # Debug info
                    cv2.putText(img, f'Ctrl Distance: {distanceCtrl}', (40, 710), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                    cv2.putText(img, f'Left Tab Distance: {distanceTabThumbLeft}', (40, 730), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                    
                    # Aktifkan Ctrl jika ibu jari dan kelingking bersentuhan    f
                    if distanceCtrl <= 40:
                        if not controlMovenmt.is_ctrl_pressed:
                            controlMovenmt.pressCtrl()
                        cv2.putText(img, 'CTRL PRESSED', (40, 750), 
                                  cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    else:
                        controlMovenmt.releaseCtrl()
                    
                    # Aktifkan Tab jika ibu jari dan jari tengah bersentuhan, dan jari tengah ke kelingking
                    if distanceTabThumbLeft <= 40 and distanceTabMiddleLeft <= 40 and distanceTabRingLeft >= 50 and distanceTabIndexLeft >= 50:
                        if not controlMovenmt.is_tab_pressed:
                            controlMovenmt.pressTab()
                        cv2.putText(img, 'TAB PRESSED', (40, 770), 
                                  cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                else:
                    controlMovenmt.releaseTab()

            # Tampilkan status jika tidak ada tangan terdeteksi
            if not rightHandList and not leftHandList:
                cv2.putText(img, 'No Hand Detected', (40, 130), 
                           cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
                controlMovenmt.releaseClick()
                controlMovenmt.releaseLeftClick()
            
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        print("Cleaning up...")
        capCam.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
