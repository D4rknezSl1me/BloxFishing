import tkinter as tk
from tkinter import ttk
import threading
import time
import pyautogui
import cv2
import numpy as np
import mss
import keyboard
import os

# Configuration
EXCLAMATION_IMAGE = 'exclamation.png'
MINIGAME_IMAGE = 'minigame.png' # Used for reference if needed
CHECK_INTERVAL = 0.1
MINIGAME_CHECK_INTERVAL = 0.01

class BloxFishingBot:
    def __init__(self, root):
        self.root = root
        self.root.title("BloxFishing Bot")
        self.root.geometry("300x250")
        
        self.running = False
        self.status_var = tk.StringVar(value="Status: Stopped")
        
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="BloxFishing Bot", font=("Helvetica", 16)).pack(pady=10)
        
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.pack(pady=5)
        
        self.debug_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Debug Mode (Visual)", variable=self.debug_var).pack(pady=5)
        
        self.start_btn = ttk.Button(main_frame, text="Start (F6)", command=self.toggle_bot)
        self.start_btn.pack(pady=5)
        
        ttk.Label(main_frame, text="Press F7 to Emergency Stop").pack(pady=5)
        
        # Hotkeys
        keyboard.add_hotkey('f6', self.toggle_bot)
        keyboard.add_hotkey('f7', self.stop_bot)

    def toggle_bot(self):
        if self.running:
            self.stop_bot()
        else:
            self.start_bot()

    def start_bot(self):
        if not self.running:
            self.running = True
            self.status_var.set("Status: Running")
            self.thread = threading.Thread(target=self.bot_loop, daemon=True)
            self.thread.start()

    def stop_bot(self):
        self.running = False
        self.status_var.set("Status: Stopped")

    def bot_loop(self):
        while self.running:
            # 1. Hold mouse for 1 second
            self.status_var.set("Status: Casting...")
            pyautogui.mouseDown()
            time.sleep(1)
            pyautogui.mouseUp()
            
            # 2. Wait for exclamation mark
            self.status_var.set("Status: Waiting for bite...")
            found_bite = False
            while self.running and not found_bite:
                if self.check_for_exclamation():
                    found_bite = True
                    pyautogui.click()
                    time.sleep(0.1) # Small delay before minigame starts
                time.sleep(CHECK_INTERVAL)
            
            if not self.running: break
            
            # 3. Minigame
            self.status_var.set("Status: Minigame!")
            self.run_minigame()
            
            if not self.running: break
            
            # 4. Post-minigame sequence
            self.status_var.set("Status: Wrapping up...")
            time.sleep(1)
            pyautogui.click()
            time.sleep(0.5)
            pyautogui.click()
            time.sleep(1) # Extra wait before restarting

    def check_for_exclamation(self):
        # ROI for exclamation mark (center-top)
        screen_width, screen_height = pyautogui.size()
        region_width, region_height = 400, 300 
        left = (screen_width - region_width) // 2
        top = (screen_height // 2) - 250
        
        with mss.MSS() as sct:
            monitor = {"top": top, "left": left, "width": region_width, "height": region_height}
            img = np.array(sct.grab(monitor))
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
            
            # Try matching with different reference images
            templates = ['exclamation.png', 'exclamation 2.png', 'exclamation3.png']
            
            for t_path in templates:
                if not os.path.exists(t_path):
                    continue
                    
                template = cv2.imread(t_path, 0)
                if template is None:
                    continue
                
                # Resize template if it's too large for the ROI
                th, tw = template.shape[:2]
                if th > region_height or tw > region_width:
                    scale = min(region_width/tw, region_height/th) * 0.8
                    template = cv2.resize(template, None, fx=scale, fy=scale)
                
                res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
                threshold = 0.65 # Balance between accuracy and sensitivity
                loc = np.where(res >= threshold)
                
                if len(loc[0]) > 0:
                    return True
            
            return False

    def run_minigame(self):
        screen_width, screen_height = pyautogui.size()
        # SUPER RESTRICTED AREA: Only a thin horizontal slice
        monitor = {"top": int(screen_height * 0.72), "left": int(screen_width * 0.3), 
                   "width": int(screen_width * 0.4), "height": int(screen_height * 0.1)}
        
        timeout = time.time() + 60
        last_check_time = time.time()
        
        with mss.MSS() as sct:
            while self.running and time.time() < timeout:
                img = np.array(sct.grab(monitor))
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
                
                # EXTREMELY SPECIFIC FILTERS
                # Blue (Fish) - Focused on a very saturated blue
                mask_blue = cv2.inRange(hsv, np.array([115, 200, 100]), np.array([125, 255, 255]))
                # Green (Player Active)
                mask_green = cv2.inRange(hsv, np.array([55, 180, 100]), np.array([70, 255, 255]))
                # Grey (Player Inactive)
                mask_grey = cv2.inRange(hsv, np.array([0, 0, 40]), np.array([180, 20, 160]))
                # Yellow (Chest)
                mask_yellow = cv2.inRange(hsv, np.array([28, 180, 180]), np.array([32, 255, 255]))
                
                # Noise reduction
                kernel = np.ones((3,3), np.uint8)
                mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_OPEN, kernel)
                
                mask_player = cv2.bitwise_or(mask_green, mask_grey)
                
                if self.debug_var.get():
                    debug_img = img_bgr.copy()
                    debug_img[mask_blue > 0] = [255, 0, 0]
                    debug_img[mask_player > 0] = [0, 255, 0]
                    debug_img[mask_yellow > 0] = [0, 255, 255]
                    cv2.imshow("Debug", debug_img)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.debug_var.set(False)
                        cv2.destroyAllWindows()

                y_coords_y, x_coords_y = np.where(mask_yellow > 0)
                y_coords_b, x_coords_b = np.where(mask_blue > 0)
                y_coords_p, x_coords_p = np.where(mask_player > 0)
                
                if len(x_coords_p) < 5 and len(x_coords_b) < 5:
                    if time.time() - last_check_time > 4:
                        break
                    continue
                
                last_check_time = time.time()
                
                if len(x_coords_p) > 10:
                    player_x = np.median(x_coords_p)
                    
                    target_x = None
                    if len(x_coords_y) > 20:
                        target_x = np.median(x_coords_y)
                    elif len(x_coords_b) > 10:
                        target_x = np.median(x_coords_b)
                    
                    if target_x is not None:
                        if player_x < target_x - 3:
                            pyautogui.mouseDown()
                        elif player_x > target_x + 3:
                            pyautogui.mouseUp()
                
                time.sleep(MINIGAME_CHECK_INTERVAL)
            
            pyautogui.mouseUp()
            if self.debug_var.get():
                cv2.destroyAllWindows()

if __name__ == "__main__":
    if not os.path.exists(EXCLAMATION_IMAGE):
        print(f"Error: {EXCLAMATION_IMAGE} not found.")
    
    root = tk.Tk()
    app = BloxFishingBot(root)
    root.mainloop()
