import requests
import time

def send_text(text):
    try:
        url = "http://localhost:5003/text"
        data = {"text": text}
        response = requests.post(url, json=data)
        print(f"Server response: {response.json()}")
    except Exception as e:
        print(f"Error sending text: {e}")

if __name__ == '__main__':
    # Example usage
    print("Sending test messages to text server...")
    
    # Send a simple message
    send_text("Hello, World!")
    time.sleep(1)  # Wait a bit between messages
    
    # Send a longer message
    send_text("This is a longer message with multiple words!")
    time.sleep(1)
    
    # Send a message with special characters
    send_text("Special chars: !@#$%^&*()")