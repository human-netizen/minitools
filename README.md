# Remote Control Server Suite

This suite consists of multiple Python servers and utilities for remote control and monitoring.

## Components

### Main Servers

1. **text_server.py**
   - Command control server that accepts text commands
   - Port: 5003
   - Endpoints:
     - POST /text - Execute commands
     - GET / - Web interface with documentation
   - Available commands:
     - `run screenshot` - Take screenshot
     - `run cam` - Start camera capture
     - `run screen` - Start screen sharing
     - `run keylogger` - Start keylogging
     - `help` - Show available commands

2. **screen_server.py**
   - Screen sharing server with FPS counter
   - Port: 5002
   - Features:
     - Live screen streaming
     - FPS monitoring
     - Adaptive frame rate
     - Browser-based viewer

3. **server.py**
   - Screenshot viewer server
   - Port: 5000
   - Features:
     - Auto-refreshing screenshot view
     - Mobile-friendly interface
     - Rotation support for mobile devices
     - Endpoints:
       - GET / - Web interface
       - GET /screenshot - Latest screenshot

4. **log_server.py**
   - Keylogger monitoring server
   - Port: 5001
   - Features:
     - Real-time log viewing
     - Auto-scrolling log display
     - Terminal-style interface
     - Endpoints:
       - GET / - Web interface
       - GET /logs - Raw log data
     - Monitors daily log files in E:/logs/

### Utilities

1. **screenshot.py**
   - Screenshot capture utility
   - Can be triggered via text_server.py

2. **keylogger.py**
   - Keyboard input monitoring utility
   - Can be triggered via text_server.py

3. **test_text_client.py**
   - Example client for text_server.py
   - Demonstrates how to send commands

## Directory Structure

- `E:/screenshots/` - Screenshot storage directory
- `E:/logs/` - Keylogger output directory

## How to Use

1. Start the servers in this order:
```bash
python log_server.py     # Port 5001 - Keylogger monitor
python server.py         # Port 5000 - Screenshot viewer
python screen_server.py  # Port 5002 - Screen sharing
python text_server.py    # Port 5003 - Command control
```

2. Access web interfaces:
   - Screenshot viewer: http://localhost:5000
   - Keylogger monitor: http://localhost:5001
   - Screen sharing: http://localhost:5002
   - Command server: http://localhost:5003

3. Send commands using Postman:
   - POST to http://localhost:5003/text
   - Header: Content-Type: application/json
   - Body:
```json
{
    "text": "run screenshot"
}
```

4. Or use Python requests:
```python
import requests
url = "http://localhost:5003/text"
data = {"text": "run screenshot"}
response = requests.post(url, json=data)
print(response.json())
```

5. Monitor results:
   - View screenshots at http://localhost:5000
   - View keylogger output at http://localhost:5001
   - View screen sharing at http://localhost:5002

## Requirements

- Python 3.x
- Flask
- Flask-SocketIO
- pyautogui
- Pillow (PIL)
- requests (for client)

## Security Considerations

1. Network Security:
   - Servers are intended for local network use only
   - No authentication implemented by default
   - No encryption for data transmission
   - Consider using a firewall to restrict port access
   - Recommended to use only on trusted networks

2. File System Security:
   - Ensure proper permissions on log and screenshot directories
   - Regular cleanup of old files recommended
   - Monitor disk space usage
   - Keep sensitive data secure

3. Process Security:
   - Servers run with user privileges
   - Keylogger has system-wide keyboard access
   - Screen sharing exposes entire desktop
   - Consider the privacy implications

## Setup Instructions

1. Install Dependencies:
```bash
pip install flask flask-socketio pyautogui Pillow requests
```

2. Create Required Directories:
```bash
mkdir -p E:/screenshots
mkdir -p E:/logs
```

3. File Permissions:
   - Ensure write access to E:/screenshots and E:/logs
   - Set appropriate NTFS permissions if needed

## Troubleshooting

1. Port Conflicts:
   - Ensure no other services are using ports 5000-5003
   - Check Windows Task Manager for port usage
   - Can modify port numbers in respective server files

2. File Access Issues:
   - Verify directory permissions
   - Check paths exist: E:/screenshots and E:/logs
   - Run servers with appropriate user privileges

3. Common Problems:
   - Screenshot service requires display access
   - Keylogger needs keyboard access rights
   - Screen sharing may impact system performance
   - Antivirus might block keyboard monitoring

4. Performance Tips:
   - Adjust screen_server.py FPS for better performance
   - Regular cleanup of log files
   - Monitor system resource usage