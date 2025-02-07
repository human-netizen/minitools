from flask import Flask, send_file
import os
import time

app = Flask(__name__)

def get_latest_screenshot():
    try:
        screenshot_dir = "E:/screenshots"
        files = [os.path.join(screenshot_dir, f) for f in os.listdir(screenshot_dir) 
                if f.startswith("screenshot_") and f.endswith(".png")]
        if not files:
            return None
        return max(files, key=os.path.getctime)
    except Exception as e:
        print(f"Error getting latest screenshot: {e}")
        return None

@app.route('/screenshot')
def serve_screenshot():
    latest = get_latest_screenshot()
    if latest is None:
        return "No screenshots available", 404
    try:
        return send_file(latest, mimetype='image/png')
    except Exception as e:
        print(f"Error serving screenshot: {e}")
        return "Error serving screenshot", 500

@app.route('/')
def home():
    return '''
    <html>
        <head>
            <title>Screenshot Viewer</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <style>
                * { 
                    margin: 0; 
                    padding: 0; 
                    box-sizing: border-box; 
                }
                html, body { 
                    width: 100%;
                    height: 100%;
                    overflow: hidden;
                    background: #000;
                }
                .container {
                    width: 100%;
                    height: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                img { 
                    display: block;
                }
                @media (max-width: 768px) {
                    img {
                        transform: rotate(90deg);
                        height: 100vw;
                        width: 100vh;
                        object-fit: cover;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <img src="/screenshot" id="screenshot" alt="">
            </div>
            <script>
                const img = document.getElementById('screenshot');
                
                function updateScreenshot() {
                    fetch('/screenshot?' + new Date().getTime())
                        .then(response => response.blob())
                        .then(blob => {
                            const url = URL.createObjectURL(blob);
                            img.src = url;
                        })
                        .catch(() => {});
                }
                
                setInterval(updateScreenshot, 1000);
                
                document.addEventListener('visibilitychange', () => {
                    if (!document.hidden) {
                        updateScreenshot();
                    }
                });
            </script>
        </body>
    </html>
    '''

if __name__ == '__main__':
    print("Starting server at http://localhost:5000")
    print("Make sure screenshot.py is running to capture screenshots")
    app.run(host='0.0.0.0', port=5000)