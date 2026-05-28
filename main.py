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
        # Focus on a smaller, higher region above center to avoid the floor
        screen_width, screen_height = pyautogui.size()
        region_width, region_height = 300, 200 
        left = (screen_width - region_width) // 2
        # Move the scan area UP to avoid the floor/character body
        top = (screen_height // 2) - 200
        
        with mss.MSS() as sct:
            monitor = {"top": top, "left": left, "width": region_width, "height": region_height}
            img = np.array(sct.grab(monitor))
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
            
            # Narrower, BRIGHTER Red range to avoid floor/dull colors
            lower_red1 = np.array([0, 150, 150])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 150, 150])
            upper_red2 = np.array([180, 255, 255])
            
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask = cv2.bitwise_or(mask1, mask2)
            
            red_pixels = cv2.countNonZero(mask)
            # Threshold needs to be specific enough to be the exclamation
            return 50 < red_pixels < 2000 

    def run_minigame(self):
        screen_width, screen_height = pyautogui.size()
        # Narrow the scan area horizontally and vertically to avoid UI/Menus
        # Focusing on the lower-center where the bar actually resides
        monitor = {"top": int(screen_height * 0.65), "left": int(screen_width * 0.25), 
                   "width": int(screen_width * 0.5), "height": int(screen_height * 0.15)}
        
        timeout = time.time() + 60
        last_check_time = time.time()
        
        with mss.MSS() as sct:
            while self.running and time.time() < timeout:
                img = np.array(sct.grab(monitor))
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
                
                # Refined Minigame Colors
                # Blue (Fish) - Very saturated
                mask_blue = cv2.inRange(hsv, np.array([100, 150, 100]), np.array([130, 255, 255]))
                # Green (Player Active)
                mask_green = cv2.inRange(hsv, np.array([40, 100, 100]), np.array([80, 255, 255]))
                # Grey (Player Inactive) - Very low saturation
                mask_grey = cv2.inRange(hsv, np.array([0, 0, 50]), np.array([180, 30, 150]))
                # Yellow (Chest) - Specific saturated yellow
                mask_yellow = cv2.inRange(hsv, np.array([25, 150, 150]), np.array([35, 255, 255]))
                
                mask_player = cv2.bitwise_or(mask_green, mask_grey)
                
                y_coords_y, x_coords_y = np.where(mask_yellow > 0)
                y_coords_b, x_coords_b = np.where(mask_blue > 0)
                y_coords_p, x_coords_p = np.where(mask_player > 0)
                
                if len(x_coords_p) < 10 and len(x_coords_b) < 10:
                    if time.time() - last_check_time > 3:
                        break
                    continue
                
                last_check_time = time.time()
                
                if len(x_coords_p) > 20: # Ensure we see a significant part of the player bar
                    player_x = np.median(x_coords_p)
                    
                    target_x = None
                    # Prioritize Treasure (Yellow) ONLY if it's a significant cluster
                    if len(x_coords_y) > 50:
                        target_x = np.median(x_coords_y)
                    elif len(x_coords_b) > 20:
                        target_x = np.median(x_coords_b)
                    
                    if target_x is not None:
                        if player_x < target_x - 5:
                            pyautogui.mouseDown()
                        elif player_x > target_x + 5:
                            pyautogui.mouseUp()
                
                time.sleep(MINIGAME_CHECK_INTERVAL)
            
            pyautogui.mouseUp()

if __name__ == "__main__":
    if not os.path.exists(EXCLAMATION_IMAGE):
        print(f"Error: {EXCLAMATION_IMAGE} not found.")
    
    root = tk.Tk()
    app = BloxFishingBot(root)
    root.mainloop()
eep(MINIGAME_CHECK_INTERVAL)
            
            pyautogui.mouseUp()
            if self.debug_var.get():
                cv2.destroyAllWindows()

if __name__ == "__main__":
    if not os.path.exists(EXCLAMATION_IMAGE):
        print(f"Error: {EXCLAMATION_IMAGE} not found.")
    
    root = tk.Tk()
    app = BloxFishingBot(root)
    root.mainloop()
