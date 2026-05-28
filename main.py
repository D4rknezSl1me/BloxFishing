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
        # Detect Blue (Fish), Green (Player), Yellow (Chest)
        # Typically these are in a specific bar area.
        # For simplicity, we search the middle-bottom area.
        
        screen_width, screen_height = pyautogui.size()
        # Define minigame area - adjust as needed
        # Assuming the bar is in the lower half
        monitor = {"top": int(screen_height * 0.6), "left": int(screen_width * 0.2), 
                   "width": int(screen_width * 0.6), "height": int(screen_height * 0.3)}
        
        timeout = time.time() + 60 # Max 60 seconds for minigame
        
        with mss.MSS() as sct:
            while self.running and time.time() < timeout:
                img = np.array(sct.grab(monitor))
                hsv = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
                
                # Define color ranges
                # Blue (Fish)
                lower_blue = np.array([100, 150, 50])
                upper_blue = np.array([130, 255, 255])
                
                # Green (Player)
                lower_green = np.array([40, 100, 50])
                upper_green = np.array([80, 255, 255])
                
                # Yellow (Chest)
                lower_yellow = np.array([20, 100, 100])
                upper_yellow = np.array([40, 255, 255])
                
                # Find positions (x-coordinates)
                mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
                mask_green = cv2.inRange(hsv, lower_green, upper_green)
                mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
                
                # Check for Chest first
                y_coords = np.where(mask_yellow > 0)[1]
                b_coords = np.where(mask_blue > 0)[1]
                g_coords = np.where(mask_green > 0)[1]
                
                if len(g_coords) == 0:
                    # If minigame not found or finished, exit loop
                    # But we need a better check. Let's check for the green bar or absence of fish.
                    if len(b_coords) == 0:
                        break
                    time.sleep(0.05)
                    continue
                
                player_x = np.mean(g_coords)
                target_x = None
                
                if len(y_coords) > 0:
                    target_x = np.mean(y_coords)
                elif len(b_coords) > 0:
                    target_x = np.mean(b_coords)
                
                if target_x is not None:
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
