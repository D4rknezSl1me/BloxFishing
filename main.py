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
        self.root.geometry("300x200")
        
        self.running = False
        self.status_var = tk.StringVar(value="Status: Stopped")
        
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="BloxFishing Bot", font=("Helvetica", 16)).pack(pady=10)
        
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.pack(pady=5)
        
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
        # Scan a LARGER center region for RED
        screen_width, screen_height = pyautogui.size()
        region_width, region_height = 400, 400 
        left = (screen_width - region_width) // 2
        top = (screen_height - region_height) // 2
        
        with mss.MSS() as sct:
            monitor = {"top": top, "left": left, "width": region_width, "height": region_height}
            img = np.array(sct.grab(monitor))
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
            
            # More permissive Red range
            lower_red1 = np.array([0, 70, 70])
            upper_red1 = np.array([15, 255, 255])
            lower_red2 = np.array([160, 70, 70])
            upper_red2 = np.array([180, 255, 255])
            
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask = cv2.bitwise_or(mask1, mask2)
            
            red_pixels = cv2.countNonZero(mask)
            return red_pixels > 20 # Lower threshold for detection

    def run_minigame(self):
        screen_width, screen_height = pyautogui.size()
        # Scan almost the whole screen height to be safe, but focus horizontally
        monitor = {"top": int(screen_height * 0.2), "left": int(screen_width * 0.1), 
                   "width": int(screen_width * 0.8), "height": int(screen_height * 0.7)}
        
        timeout = time.time() + 60
        last_check_time = time.time()
        
        with mss.MSS() as sct:
            while self.running and time.time() < timeout:
                img = np.array(sct.grab(monitor))
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
                
                # Colors based on typical Roblox/BloxFishing palettes
                mask_blue = cv2.inRange(hsv, np.array([90, 50, 50]), np.array([130, 255, 255]))
                mask_green = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([90, 255, 255]))
                mask_grey = cv2.inRange(hsv, np.array([0, 0, 40]), np.array([180, 40, 180])) # Wide grey
                mask_yellow = cv2.inRange(hsv, np.array([15, 50, 50]), np.array([40, 255, 255]))
                
                mask_player = cv2.bitwise_or(mask_green, mask_grey)
                
                y_coords_y, x_coords_y = np.where(mask_yellow > 0)
                y_coords_b, x_coords_b = np.where(mask_blue > 0)
                y_coords_p, x_coords_p = np.where(mask_player > 0)
                
                if len(x_coords_p) < 5 and len(x_coords_b) < 5:
                    if time.time() - last_check_time > 3:
                        break
                    continue
                
                last_check_time = time.time()
                
                if len(x_coords_p) > 0:
                    # Calculate center of the player bar
                    player_x = np.median(x_coords_p)
                    
                    target_x = None
                    if len(x_coords_y) > 5:
                        target_x = np.median(x_coords_y)
                    elif len(x_coords_b) > 5:
                        target_x = np.median(x_coords_b)
                    
                    if target_x is not None:
                        # Deadzone to avoid jitter
                        if player_x < target_x - 10:
                            pyautogui.mouseDown()
                        elif player_x > target_x + 10:
                            pyautogui.mouseUp()
                        # If within 10px, keep current state or release? Let's release to avoid overshooting
                
                time.sleep(MINIGAME_CHECK_INTERVAL)
            
            pyautogui.mouseUp()

if __name__ == "__main__":
    if not os.path.exists(EXCLAMATION_IMAGE):
        print(f"Error: {EXCLAMATION_IMAGE} not found.")
    
    root = tk.Tk()
    app = BloxFishingBot(root)
    root.mainloop()
