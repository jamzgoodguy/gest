import cv2 as cv2
import time
import numpy as np
import math
import HandTracking as ht
import gestureControl as gc
import pyautogui as pygui

# Tambahkan konstanta untuk ukuran kamera
WIDTH_CAM = 640
HIGHT_CAM = 480

def main():
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
            if rightHandList and leftHandList:
                # Gesture aktivasi: ibu jari kanan dan kiri berdekatan
                rightThumb = rightHandList[4]  # ID 4 adalah ibu jari
                leftThumb = leftHandList[4]
                activationDistance = int(handTracking.getDistance(rightThumb, leftThumb))
                
                # Gesture deaktivasi: kelingking kanan dan kiri berdekatan
                rightPinky = rightHandList[20]  # ID 20 adalah kelingking
                leftPinky = leftHandList[20]
                deactivationDistance = int(handTracking.getDistance(rightPinky, leftPinky))
                
                # Debug info untuk aktivasi/deaktivasi
                cv2.putText(img, f'Activation: {activationDistance}', (40, 90), 
                           cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                cv2.putText(img, f'Deactivation: {deactivationDistance}', (40, 130), 
                           cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                
                # Aktivasi sistem dengan ibu jari
                if activationDistance <= 50:
                    controlMovenmt.activateSystem()
                
                # Deaktivasi sistem dengan kelingking
                if deactivationDistance <= 50:
                    controlMovenmt.deactivateSystem()
            
            # Status sistem
            status_text = "ACTIVE" if controlMovenmt.is_system_active else "INACTIVE"
            status_color = (0, 255, 0) if controlMovenmt.is_system_active else (0, 0, 255)
            cv2.putText(img, f'System: {status_text}', (40, 50), 
                       cv2.FONT_HERSHEY_COMPLEX, 1, status_color, 2)
            
            # Hanya proses gesture jika sistem aktif
            if controlMovenmt.is_system_active:
                # Proses tangan kanan untuk kontrol mouse
                if rightHandList and len(rightHandList) > 0:
                    # 1. Movement tracking menggunakan id 8 (ujung telunjuk)
                    x, y = rightHandList[8][1], rightHandList[8][2]
                    controlMovenmt.mouseMovement(x, y)
                    
                    # 2. Right click: jarak antara ibu jari (4) dan jari kelingking (20)
                    distanceRightClick = int(handTracking.getDistance(rightHandList[4], rightHandList[20]))
                    
                    # 3. Left click: jarak antara ibu jari (4) dan jari tengah (12)
                    distanceLeftClick = int(handTracking.getDistance(rightHandList[4], rightHandList[12]))
                    
                    # 4. Middle click: cek jari tengah (12), manis (16), dan kelingking (20) menggenggam
                    distanceMiddleFinger = int(handTracking.getDistance(rightHandList[12], rightHandList[0]))
                    distanceRingFinger = int(handTracking.getDistance(rightHandList[16], rightHandList[0]))
                    distancePinkyFinger = int(handTracking.getDistance(rightHandList[20], rightHandList[0]))
                    
                    # Status teks
                    status = "Moving"
                    status_color = (0, 255, 0)  # Hijau untuk moving
                    
                    # Debug info untuk jarak
                    cv2.putText(img, f'Right Click: {distanceRightClick}', (40, 130), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                    cv2.putText(img, f'Left Click: {distanceLeftClick}', (30, 150), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                    
                    # Deteksi gesture dengan prioritas
                    if distanceRightClick <= 40:  # Right click dengan ibu jari dan kelingking
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
                    if (distanceMiddleFinger <= 100 and 
                        distanceRingFinger <= 100 and 
                        distancePinkyFinger <= 100):
                        controlMovenmt.middleClickMovement()
                        status = "Middle Click"
                        status_color = (255, 165, 0)  # Orange
                    else:
                        controlMovenmt.releaseClick()  # Untuk middle click
                    
                    # Tampilkan status
                    cv2.putText(img, f'Status: {status}', (40, 170), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, status_color, 2)

                # Proses tangan kiri untuk left click, print screen, ESC, dan zoom
                if leftHandList and len(leftHandList) > 0:
                    # Deteksi gesture left click (jarak antara telunjuk dan ibu jari)
                    distanceLeftClick = int(handTracking.getDistance(leftHandList[8], leftHandList[4]))
                    
                    # Deteksi gesture ESC (jari kelingking ke pangkal)
                    distancePinky = int(handTracking.getDistance(leftHandList[20], leftHandList[17]))   # Kelingking
                    
                    # Deteksi gesture print screen (jari manis ke pangkal)
                    distanceRing = int(handTracking.getDistance(leftHandList[16], leftHandList[0]))    # Jari manis
                    
                    # Deteksi gesture zoom (ibu jari dan jari tengah)
                    distanceZoom = int(handTracking.getDistance(leftHandList[4], leftHandList[12]))  # Jarak ibu jari ke jari tengah
                    
                    # Deteksi gesture volume (ibu jari dan jari manis)
                    distanceVolume = int(handTracking.getDistance(leftHandList[4], leftHandList[16]))  # Jarak ibu jari ke jari manis
                    
                    # Debug info untuk jarak
                    cv2.putText(img, f'Left Click: {distanceLeftClick}', (40, 210), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                    cv2.putText(img, f'Pinky (ESC): {distancePinky}', (40, 250), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                    
                    # Aktifkan left click jika jari telunjuk dan ibu jari berdekatan
                    if distanceLeftClick <= 30:
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
                    if distanceRing <= 100 and distancePinky <= 40:
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
                    cv2.putText(img, f'Zoom Distance: {distanceZoom}', (40, 410), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)
                    
                    # Aktifkan zoom jika ibu jari dan jari tengah berdekatan
                    if distanceZoom <= 30:
                        # Gunakan posisi Y dari jari tengah untuk kontrol zoom
                        y_pos = leftHandList[12][2]
                        controlMovenmt.handleZoom(y_pos)
                        
                        # Visual feedback
                        if y_pos < controlMovenmt.last_zoom_y:  # Bergerak ke atas
                            cv2.putText(img, 'ZOOM IN', (40, 450), 
                                      cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                        else:  # Bergerak ke bawah
                            cv2.putText(img, 'ZOOM OUT', (40, 450), 
                                      cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    else:
                        controlMovenmt.releaseZoom()
                    
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
            
            # Tampilkan status jika tidak ada tangan terdeteksi
            if not rightHandList and not leftHandList:
                cv2.putText(img, 'No Hand Detected', (40, 130), 
                           cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
                controlMovenmt.releaseClick()
                controlMovenmt.releaseLeftClick()
            
            cv2.imshow("Gesture Recognition", img)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        print("Cleaning up...")
        capCam.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
