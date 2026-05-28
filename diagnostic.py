import cv2
import numpy as np
import mss
import pyautogui
import time
import os

def take_diagnostic_screenshot():
    print("Prepara il gioco... Scatto tra 5 secondi...")
    time.sleep(5)
    
    with mss.MSS() as sct:
        # Full screen screenshot
        screenshot = np.array(sct.grab(sct.monitors[1]))
        img_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        
        # 1. Check Red (Exclamation) - Center 400x400
        h, w = img_bgr.shape[:2]
        center_region = hsv[h//2-200:h//2+200, w//2-200:w//2+200]
        
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        
        mask_red = cv2.bitwise_or(cv2.inRange(center_region, lower_red1, upper_red1),
                                  cv2.inRange(center_region, lower_red2, upper_red2))
        
        # 2. Check Minigame colors in bottom half
        bottom_hsv = hsv[int(h*0.4):int(h*0.9), int(w*0.1):int(w*0.9)]
        
        # Blue (Fish)
        mask_blue = cv2.inRange(bottom_hsv, np.array([90, 100, 100]), np.array([130, 255, 255]))
        # Green (Player)
        mask_green = cv2.inRange(bottom_hsv, np.array([35, 50, 50]), np.array([85, 255, 255]))
        # Grey (Player Inactive)
        mask_grey = cv2.inRange(bottom_hsv, np.array([0, 0, 40]), np.array([180, 30, 150]))
        # Yellow (Chest)
        mask_yellow = cv2.inRange(bottom_hsv, np.array([20, 100, 100]), np.array([35, 255, 255]))
        
        # Save results
        os.makedirs("debug", exist_ok=True)
        cv2.imwrite("debug/original.png", img_bgr)
        cv2.imwrite("debug/mask_red_center.png", mask_red)
        cv2.imwrite("debug/mask_blue.png", mask_blue)
        cv2.imwrite("debug/mask_green.png", mask_green)
        cv2.imwrite("debug/mask_grey.png", mask_grey)
        cv2.imwrite("debug/mask_yellow.png", mask_yellow)
        
        print("Diagnostica completata. Controlla la cartella 'debug'.")
        print(f"Pixel Rossi rilevati al centro: {cv2.countNonZero(mask_red)}")
        print(f"Pixel Blu (Pesce): {cv2.countNonZero(mask_blue)}")
        print(f"Pixel Verdi (Player): {cv2.countNonZero(mask_green)}")
        print(f"Pixel Grigi (Player): {cv2.countNonZero(mask_grey)}")
        print(f"Pixel Gialli (Cassa): {cv2.countNonZero(mask_yellow)}")

if __name__ == "__main__":
    take_diagnostic_screenshot()
