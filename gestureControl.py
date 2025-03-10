import pyautogui as pygui
import sys
import time
import numpy as np
import win32api
import win32con

# Tambahkan konstanta kamera
WIDTH_CAM = 640
HIGHT_CAM = 480

class gestureControll():
    def __init__(self) -> None:
        # Dapatkan ukuran total layar menggunakan win32api
        self.screenWidth = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        self.screenHeight = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        
        # Konfigurasi PyAutoGUI
        pygui.FAILSAFE = False
        pygui.MINIMUM_DURATION = 0
        pygui.PAUSE = 0.01
        
        # Tambahkan variabel untuk smoothing
        self.prev_x = 0
        self.prev_y = 0
        self.smoothing = 0.7
        self.is_dragging = False
        
        # Timer untuk berbagai gesture
        self.fingers_close_start = 0  # Waktu mulai jari berdekatan
        self.last_click_time = 0      # Waktu click terakhir
        self.DRAG_DELAY = 1.0         # Delay untuk aktivasi drag
        self.CLICK_INTERVAL = 0.3     # Interval maksimum untuk double click
        self.last_action = None       # Menyimpan action terakhir
        
        self.movement_threshold = 2  # Minimal pergerakan dalam pixel
        
        self.is_left_click_pressed = False  # Ganti is_space_pressed
        self.is_prtsc_pressed = False  # Tambahkan tracking untuk print screen
        self.prtsc_start_time = 0    # Waktu mulai gesture print screen
        self.PRTSC_DELAY = 2.0       # Delay 2 detik untuk print screen
        
        self.is_esc_pressed = False  # Tracking untuk tombol ESC
        
        
        
        self.is_right_click_pressed = False  # Tambahkan tracking untuk right click
        
        self.is_volume_active = False
        self.last_volume_y = 0
        self.volume_sensitivity = 1
        
        self.is_system_active = False  # Default state inactive
        self.activation_cooldown = 1.0  # Cooldown 1 detik untuk toggle
        self.last_activation_time = 0
        self.last_deactivation_time = 0
        
        self.is_two_hand_zooming = False
        self.last_two_hand_distance = 0
        self.two_hand_zoom_threshold = 2  # Minimal perubahan jarak untuk trigger zoom
        self.block_mouse_movement = False  # Tambahkan flag untuk block mouse movement
        
        self.is_back_pressed = False
        self.is_forward_pressed = False
        
        self.is_f_pressed = False  # Tambahkan tracking untuk tombol F
        
        self.is_scrolling = False
        self.scroll_start_x = 0
        self.scroll_start_y = 0
        self.last_scroll_x = 0
        self.last_scroll_y = 0
        self.scroll_threshold = 10
        self.scroll_speed = 4
        self.scroll_multiplier = 5
        
        self.is_copy_pressed = False
        self.is_paste_pressed = False
        
        self.is_alt_pressed = False
        self.is_tab_pressed = False
        
        self.is_ctrl_pressed = False
        
    def mouseMovement(self, x:int, y:int):
        # Skip mouse movement jika two hand zoom aktif atau Alt aktif
        if self.block_mouse_movement or self.is_alt_pressed:
            return
            
        try:
            # Konversi koordinat kamera ke koordinat seluruh layar
            # Gunakan range yang lebih kecil (100-540 untuk x, 100-380 untuk y)
            x = np.interp(x, (150, WIDTH_CAM-100), (0, self.screenWidth))  # Batasi 100px dari kiri dan kanan
            y = np.interp(y, (200, HIGHT_CAM-100), (0, self.screenHeight)) # Batasi 100px dari atas dan bawah
            
            # Smooth movement
            if self.prev_x == 0:
                self.prev_x = x
                self.prev_y = y
                return
            
            # Hitung perubahan posisi
            dx = abs(x - self.prev_x)
            dy = abs(y - self.prev_y)
            
            if dx > self.movement_threshold or dy > self.movement_threshold:
                smooth_x = int(self.prev_x + (x - self.prev_x) * (1 - self.smoothing))
                smooth_y = int(self.prev_y + (y - self.prev_y) * (1 - self.smoothing))
                
                self.prev_x = smooth_x
                self.prev_y = smooth_y
                
                # Gunakan win32api untuk kontrol mouse
                win32api.SetCursorPos((smooth_x, smooth_y))
            
        except Exception as e:
            print(f"Mouse movement error: {e}")

    def clickMovemnt(self, x:int, y:int):
        current_time = time.time()
        
        if not self.is_dragging:
            if self.fingers_close_start == 0:
                # Jari baru mulai berdekatan
                self.fingers_close_start = current_time
                
            elif current_time - self.fingers_close_start >= self.DRAG_DELAY:
                # Sudah lebih dari 1 detik, aktivasi drag
                pygui.mouseDown()
                self.is_dragging = True
                self.last_action = "drag"
                
            elif current_time - self.last_click_time < self.CLICK_INTERVAL:
                # Double click jika interval dengan click sebelumnya cukup pendek
                if self.last_action != "double_click":  # Prevent multiple double clicks
                    pygui.doubleClick()
                    self.last_action = "double_click"
                    
            else:
                # Single click
                pygui.click()
                self.last_click_time = current_time
                self.last_action = "click"
        
    def releaseClick(self):
        if self.is_dragging:
            if self.last_action == "middle_click":
                pygui.mouseUp(button='middle')  # Lepas tombol tengah
            else:
                pygui.mouseUp()  # Lepas tombol kiri (untuk drag normal)
            self.is_dragging = False
        # Reset timer dan status
        self.fingers_close_start = 0
        self.last_action = None

    def singleClickMovement(self):
        if not self.is_dragging and self.last_action != "click":
            pygui.click()
            self.last_action = "click"
    
    def doubleClickMovement(self):
        if not self.is_dragging and self.last_action != "double_click":
            pygui.doubleClick()
            self.last_action = "double_click"
    
    def dragMovement(self):
        if not self.is_dragging:
            # Langsung aktivasi drag tanpa delay
            pygui.mouseDown()
            self.is_dragging = True
            self.last_action = "drag"

    def middleClickMovement(self):
        if not self.is_dragging and self.last_action != "middle_click":
            pygui.mouseDown(button='middle')  # Tekan tombol tengah
            self.is_dragging = True  # Gunakan is_dragging untuk tracking status
            self.last_action = "middle_click"

    # Tambahkan method untuk kontrol keyboard
    def pressLeftClick(self):  # Ganti pressSpace
        if not self.is_left_click_pressed:
            pygui.mouseDown(button='left')
            self.is_left_click_pressed = True

    def releaseLeftClick(self):  # Ganti releaseSpace
        if self.is_left_click_pressed:
            pygui.mouseUp(button='left')
            self.is_left_click_pressed = False

    def pressPrintScreen(self):
        current_time = time.time()
        
        if not self.is_prtsc_pressed:
            if self.prtsc_start_time == 0:
                # Gesture baru dimulai
                self.prtsc_start_time = current_time
            elif current_time - self.prtsc_start_time >= self.PRTSC_DELAY:
                # Sudah 2 detik, eksekusi print screen
                pygui.hotkey('printscreen')
                self.is_prtsc_pressed = True
                
            return current_time - self.prtsc_start_time  # Return waktu yang sudah berlalu
        return 0

    def releasePrintScreen(self):
        if self.is_prtsc_pressed:
            self.is_prtsc_pressed = False
        self.prtsc_start_time = 0  # Reset timer

    def pressEsc(self):
        if not self.is_esc_pressed:
            pygui.keyDown('esc')
            self.is_esc_pressed = True

    def releaseEsc(self):
        if self.is_esc_pressed:
            pygui.keyUp('esc')
            self.is_esc_pressed = False

    

    def pressRightClick(self):
        if not self.is_right_click_pressed:
            pygui.mouseDown(button='right')
            self.is_right_click_pressed = True

    def releaseRightClick(self):
        if self.is_right_click_pressed:
            pygui.mouseUp(button='right')
            self.is_right_click_pressed = False

    def handleVolume(self, y_pos):
        if not self.is_volume_active:
            self.last_volume_y = y_pos
            self.is_volume_active = True
            return
        
        # Hitung perubahan posisi Y
        y_diff = y_pos - self.last_volume_y
        
        # Jika bergerak ke atas (y_diff < 0) = volume up
        # Jika bergerak ke bawah (y_diff > 0) = volume down
        if abs(y_diff) > 10:  # Threshold minimal pergerakan
            if y_diff < 0:  # Bergerak ke atas
                # Volume up
                pygui.press('volumeup')
            else:  # Bergerak ke bawah
                # Volume down
                pygui.press('volumedown')
            
            self.last_volume_y = y_pos  # Update posisi terakhir

    def releaseVolume(self):
        self.is_volume_active = False
        self.last_volume_y = 0

    def activateSystem(self):
        current_time = time.time()
        if not self.is_system_active and current_time - self.last_activation_time >= self.activation_cooldown:
            self.is_system_active = True
            self.last_activation_time = current_time

    def deactivateSystem(self):
        current_time = time.time()
        if self.is_system_active and current_time - self.last_deactivation_time >= self.activation_cooldown:
            try:
                # Release semua kontrol sebelum deaktivasi
                self.releaseAllControls()
                # Set status sistem
                self.is_system_active = False
                self.last_deactivation_time = current_time
            except Exception as e:
                print(f"Error in deactivateSystem: {e}")

    def releaseAllControls(self):
        try:
            # Release keyboard controls
            if self.is_ctrl_pressed:
                pygui.keyUp('ctrl')
            if self.is_alt_pressed:
                pygui.keyUp('alt')
            if self.is_tab_pressed:
                pygui.keyUp('tab')
            
            # Release mouse controls
            if self.is_left_click_pressed:
                pygui.mouseUp(button='left')
            if self.is_right_click_pressed:
                pygui.mouseUp(button='right')
            
            # Reset all flags
            self.is_ctrl_pressed = False
            self.is_alt_pressed = False
            self.is_tab_pressed = False
            self.is_left_click_pressed = False
            self.is_right_click_pressed = False
            self.is_dragging = False
            self.is_scrolling = False
            self.is_two_hand_zooming = False
            self.block_mouse_movement = False
            
            # Reset all positions
            self.prev_x = 0
            self.prev_y = 0
            self.last_scroll_x = 0
            self.last_scroll_y = 0
            self.last_two_hand_distance = 0
            
        except Exception as e:
            print(f"Error in releaseAllControls: {e}")

    def handleTwoHandZoom(self, distance):
        if not self.is_two_hand_zooming:
            self.last_two_hand_distance = distance
            self.is_two_hand_zooming = True
            self.block_mouse_movement = True  # Block mouse movement saat zoom aktif
            return
        
        # Hitung perubahan jarak
        distance_diff = distance - self.last_two_hand_distance
        
        # Jika jarak bertambah (menjauh) = zoom in
        # Jika jarak berkurang (mendekat) = zoom out
        if abs(distance_diff) > self.two_hand_zoom_threshold:
            if distance_diff > 0:  # Menjauh
                # Zoom in (Ctrl + Plus)
                pygui.keyDown('ctrl')
                pygui.press('+')
                pygui.keyUp('ctrl')
            else:  # Mendekat
                # Zoom out (Ctrl + Minus)
                pygui.keyDown('ctrl')
                pygui.press('-')
                pygui.keyUp('ctrl')
            
            self.last_two_hand_distance = distance

    def releaseTwoHandZoom(self):
        self.is_two_hand_zooming = False
        self.last_two_hand_distance = 0
        self.block_mouse_movement = False  # Aktifkan kembali mouse movement saat zoom selesai

    def pressBackButton(self):
        if not self.is_back_pressed:
            pygui.press('browserback')  # Simulasi tombol back browser
            self.is_back_pressed = True

    def releaseBackButton(self):
        if self.is_back_pressed:
            self.is_back_pressed = False

    def pressForwardButton(self):
        if not self.is_forward_pressed:
            pygui.press('browserforward')  # Simulasi tombol forward browser
            self.is_forward_pressed = True

    def releaseForwardButton(self):
        if self.is_forward_pressed:
            self.is_forward_pressed = False

    def pressF(self):
        if not self.is_f_pressed:
            pygui.press('f')
            self.is_f_pressed = True
    
    def releaseF(self):
        if self.is_f_pressed:
            self.is_f_pressed = False

    def handleScroll(self, x_pos, y_pos):
        if not self.is_scrolling:
            # Simpan posisi awal saat gesture pertama kali diaktifkan
            self.scroll_start_x = x_pos
            self.scroll_start_y = y_pos
            self.last_scroll_x = x_pos
            self.last_scroll_y = y_pos
            self.is_scrolling = True
            return
        
        # Hitung perubahan posisi dari titik awal
        x_diff = x_pos - self.scroll_start_x
        y_diff = y_pos - self.scroll_start_y
        
        # Tentukan arah scroll berdasarkan pergerakan yang lebih dominan
        if abs(x_diff) > abs(y_diff):  # Scroll horizontal
            if abs(x_diff) > self.scroll_threshold:
                scroll_amount = (abs(x_diff) // self.scroll_threshold) * self.scroll_speed * self.scroll_multiplier
                pygui.keyDown('shift')  # Tahan tombol shift untuk horizontal scroll
                if x_diff > 0:  # Scroll kanan
                    pygui.scroll(scroll_amount)
                else:  # Scroll kiri
                    pygui.scroll(-scroll_amount)
                pygui.keyUp('shift')
                # Update hanya last_scroll, bukan titik awal
                self.last_scroll_x = x_pos
        else:  # Scroll vertical
            if abs(y_diff) > self.scroll_threshold:
                scroll_amount = (abs(y_diff) // self.scroll_threshold) * self.scroll_speed * self.scroll_multiplier
                if y_diff > 0:  # Scroll bawah
                    pygui.scroll(-scroll_amount)
                else:  # Scroll atas
                    pygui.scroll(scroll_amount)
                # Update hanya last_scroll, bukan titik awal
                self.last_scroll_y = y_pos

    def releaseScroll(self):
        self.is_scrolling = False
        self.scroll_start_x = 0  # Reset titik awal
        self.scroll_start_y = 0
        self.last_scroll_x = 0
        self.last_scroll_y = 0

    def pressCopy(self):
        if not self.is_copy_pressed:
            pygui.hotkey('ctrl', 'c')
            self.is_copy_pressed = True
    
    def releaseCopy(self):
        if self.is_copy_pressed:
            self.is_copy_pressed = False

    def pressPaste(self):
        if not self.is_paste_pressed:
            pygui.hotkey('ctrl', 'v')
            self.is_paste_pressed = True
    
    def releasePaste(self):
        if self.is_paste_pressed:
            self.is_paste_pressed = False

    def pressAlt(self):
        if not self.is_alt_pressed:
            pygui.keyDown('alt')
            self.is_alt_pressed = True
    
    def releaseAlt(self):
        if self.is_alt_pressed:
            pygui.keyUp('alt')
            self.is_alt_pressed = False

    def pressTab(self):
        if not self.is_tab_pressed:
            pygui.press('tab')
            self.is_tab_pressed = True
    
    def releaseTab(self):
        if self.is_tab_pressed:
            self.is_tab_pressed = False

    def pressCtrl(self):
        if not self.is_ctrl_pressed:
            # Pastikan Alt dan Win key tidak aktif
            pygui.keyUp('alt')  # Release Alt key jika masih tertahan
            pygui.keyUp('win')  # Release Win key jika masih tertahan
            #time.sleep(0.1)     # Tunggu sebentar
            pygui.keyDown('ctrl')
            self.is_ctrl_pressed = True
        
    def releaseCtrl(self):
        if self.is_ctrl_pressed:
            pygui.keyUp('ctrl')
            #time.sleep(0.1)     # Tunggu sebentar setelah release
            self.is_ctrl_pressed = False

    