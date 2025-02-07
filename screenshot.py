import pyautogui
import time
from datetime import datetime
import os
from PIL import Image

def take_screenshot():
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"E:/screenshots/screenshot_{timestamp}.png"
    
    try:
        # Create directory if it doesn't exist
        os.makedirs("E:/screenshots", exist_ok=True)
        
        # Take the screenshot
        screenshot = pyautogui.screenshot()
        
        # Rotate image 90 degrees clockwise
        rotated_image = screenshot.rotate(270, expand=True)  # 270° clockwise = 90° counter-clockwise
        
        # Save the rotated screenshot
        rotated_image.save(filename)
        print(f"Screenshot saved as {filename}")
        
        # Keep only the latest 5 screenshots to save space
        files = sorted([f for f in os.listdir("E:/screenshots") if f.startswith("screenshot_")])
        if len(files) > 5:
            os.remove(os.path.join("E:/screenshots", files[0]))
            
    except Exception as e:
        print(f"Error taking screenshot: {e}")

def main():
#    print("Starting continuous screenshot monitoring...")
  #  print("Press Ctrl+C to stop")
    
    # try:
    #     while True:
    #         take_screenshot()
    #         # Take screenshot every second
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     print("\nStopping screenshot monitoring...")
    take_screenshot();

if __name__ == "__main__":
    main()