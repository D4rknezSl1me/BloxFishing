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
        # Scan center of screen for RED color (typical for exclamation mark)
        screen_width, screen_height = pyautogui.size()
        region_width, region_height = 200, 200 # Smaller region for efficiency
        left = (screen_width - region_width) // 2
        top = (screen_height - region_height) // 2
        
        with mss.MSS() as sct:
            monitor = {"top": top, "left": left, "width": region_width, "height": region_height}
            img = np.array(sct.grab(monitor))
            # Convert to HSV
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
            
            # Red color has two ranges in HSV
            lower_red1 = np.array([0, 150, 150])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 150, 150])
            upper_red2 = np.array([180, 255, 255])
            
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask = cv2.bitwise_or(mask1, mask2)
            
            # Count red pixels
            red_pixels = cv2.countNonZero(mask)
            
            # If we find enough red pixels in a cluster, it's likely the exclamation mark
            return red_pixels > 50 # Threshold can be adjusted

    def run_minigame(self):
        # Logic for minigame:
        # Detect Blue (Fish), Green/Grey (Player), Yellow (Chest)
        # We scan a large area to find the minigame bar first
        
        screen_width, screen_height = pyautogui.size()
        # Scan the bottom half of the screen where the bar usually is
        monitor = {"top": int(screen_height * 0.4), "left": int(screen_width * 0.1), 
                   "width": int(screen_width * 0.8), "height": int(screen_height * 0.5)}
        
        timeout = time.time() + 60 # Max 60 seconds for minigame
        last_check_time = time.time()
        
        with mss.MSS() as sct:
            while self.running and time.time() < timeout:
                img = np.array(sct.grab(monitor))
                # Convert to HSV
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
                
                # Define color ranges
                # Blue (Fish)
                lower_blue = np.array([90, 100, 100])
                upper_blue = np.array([130, 255, 255])
                
                # Green (Player - Active)
                lower_green = np.array([35, 50, 50])
                upper_green = np.array([85, 255, 255])
                
                # Grey (Player - Inactive/Not pressing)
                # Grey has low saturation
                lower_grey = np.array([0, 0, 40])
                upper_grey = np.array([180, 50, 200])
                
                # Yellow (Chest)
                lower_yellow = np.array([20, 100, 100])
                upper_yellow = np.array([35, 255, 255])
                
                # Find masks
                mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
                mask_green = cv2.inRange(hsv, lower_green, upper_green)
                mask_grey = cv2.inRange(hsv, lower_grey, upper_grey)
                mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
                
                # Player is either green or grey
                # We filter grey to only look for rectangles (horizontal bar parts)
                mask_player = cv2.bitwise_or(mask_green, mask_grey)
                
                # Find coordinates
                y_coords_y, x_coords_y = np.where(mask_yellow > 0)
                y_coords_b, x_coords_b = np.where(mask_blue > 0)
                y_coords_p, x_coords_p = np.where(mask_player > 0)
                
                # If we don't see the player or fish for a while, the minigame might have ended
                if len(x_coords_p) == 0 and len(x_coords_b) == 0:
                    if time.time() - last_check_time > 2: # 2 seconds of nothing = ended
                        break
                    continue
                
                last_check_time = time.time()
                
                # Logic: Find the center X of the player and the target
                if len(x_coords_p) > 0:
                    player_x = np.mean(x_coords_p)
                    
                    target_x = None
                    if len(x_coords_y) > 10: # Minimum pixels to avoid noise
                        target_x = np.mean(x_coords_y)
                    elif len(x_coords_b) > 10:
                        target_x = np.mean(x_coords_b)
                    
                    if target_x is not None:
                        # Control: If player is to the left of target, press (go right)
                        # If player is to the right, release (go left)
                        if player_x < target_x:
                            pyautogui.mouseDown()
                        else:
                            pyautogui.mouseUp()
                
                time.sleep(MINIGAME_CHECK_INTERVAL)
            
            pyautogui.mouseUp()

if __name__ == "__main__":
    if not os.path.exists(EXCLAMATION_IMAGE):
        print(f"Error: {EXCLAMATION_IMAGE} not found.")
    
    root = tk.Tk()
    app = BloxFishingBot(root)
    root.mainloop()
