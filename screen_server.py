from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
import pyautogui
import base64
from PIL import Image
import io
import threading
import time
from threading import Lock
import queue

app = Flask(__name__)
socketio = SocketIO(app,
                   cors_allowed_origins='*',
                   ping_timeout=10,
                   ping_interval=5,
                   async_mode='threading',
                   reconnection=True,
                   reconnection_attempts=10,
                   reconnection_delay=1)

# Global variables with thread safety
streaming = True
frame_count = 0
frame_lock = Lock()
frame_queue = queue.Queue(maxsize=3)  # Increased queue size slightly
current_fps = 0
last_emit_time = 0
def calculate_fps():
    global streaming, frame_count, current_fps, last_emit_time
    min_emit_interval = 0.2  # Minimum time between FPS updates (200ms)
    
    while streaming:
        try:
            with frame_lock:
                last_count = frame_count
            time.sleep(0.5)  # Calculate more frequently
            
            with frame_lock:
                current_time = time.time()
                elapsed = current_time - last_emit_time
                new_fps = (frame_count - last_count) * 2  # Multiply by 2 since we sleep 0.5s
                
                if new_fps >= 0:  # Avoid negative FPS
                    current_fps = new_fps
                    frame_count = last_count  # Don't reset to 0, just update baseline
                
                # Emit FPS update if enough time has passed
                if elapsed >= min_emit_interval:
                    socketio.emit('fps_update', {'fps': current_fps})
                    last_emit_time = current_time
                    
        except Exception as e:
            print(f"Error calculating FPS: {e}")
            time.sleep(0.1)


def capture_screen():
    global streaming, frame_count
    last_capture_time = time.time()
    target_delay = 1.0 / 60  # Target 60 FPS

    while streaming:
        try:
            current_time = time.time()
            elapsed = current_time - last_capture_time
            
            if elapsed < target_delay:
                # Skip this frame if we're running too fast
                time.sleep(target_delay - elapsed)
                continue

            # Capture screenshot
            screenshot = pyautogui.screenshot()
            
            # Rotate image 90 degrees
            rotated = screenshot.rotate(270, expand=True)
            
            # Reduce size by 50% for better performance
            width, height = rotated.size
            rotated = rotated.resize((width // 2, height // 2), Image.Resampling.LANCZOS)
            
            # Convert to bytes with lower quality for faster transmission
            img_byte_arr = io.BytesIO()
            rotated.save(img_byte_arr, format='JPEG', quality=35)  # Lower quality for better performance
            img_byte_arr = img_byte_arr.getvalue()
            
            # Convert to base64 for sending
            base64_frame = base64.b64encode(img_byte_arr).decode('utf-8')
            
            try:
                # Try to add frame to queue without blocking
                frame_queue.put_nowait(base64_frame)
                
                # Update frame counter thread-safely
                with frame_lock:
                    frame_count += 1
                    
                last_capture_time = current_time
                
            except queue.Full:
                # Skip frame if queue is full
                pass
                
        except Exception as e:
            print(f"Error capturing screen: {e}")
            time.sleep(0.1)

@app.route('/')
def index():
    return '''
    <html>
        <head>
            <title>Live Screen Share</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <style>
                * { 
                    margin: 0; 
                    padding: 0; 
                    box-sizing: border-box;
                }
                body { 
                    background: #000;
                    overflow: hidden;
                    width: 100vw;
                    height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                #screen {
                    max-width: 100%;
                    max-height: 100vh;
                    width: auto;
                    height: auto;
                }
                .status {
                    position: fixed;
                    top: 10px;
                    left: 10px;
                    color: #fff;
                    background: rgba(0,0,0,0.7);
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                    font-weight: bold;
                    text-shadow: 1px 1px 1px rgba(0,0,0,0.5);
                }
                .good { color: #4CAF50; }
                .medium { color: #FFC107; }
                .poor { color: #f44336; }
            </style>
        </head>
        <body>
            <img id="screen">
            <div class="status">FPS: <span id="fps">0</span></div>
            
            <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
            <script>
                const socket = io();
                const screen = document.getElementById('screen');
                const fpsDisplay = document.getElementById('fps');
                
                // Create image buffer with error handling
                const bufferImg = new Image();
                let framesPending = 0;
                let lastFrameTime = performance.now();
                
                bufferImg.onload = () => {
                    screen.src = bufferImg.src;
                    framesPending--;
                    
                    // Calculate client-side FPS
                    const now = performance.now();
                    const elapsed = now - lastFrameTime;
                    lastFrameTime = now;
                    
                    if (elapsed > 0) {
                        const clientFPS = Math.round(1000 / elapsed);
                        // Update FPS display if server hasn't sent an update recently
                        if (clientFPS > 0) {
                            fpsDisplay.textContent = clientFPS;
                            if (clientFPS >= 20) {
                                fpsDisplay.className = 'good';
                            } else if (clientFPS >= 10) {
                                fpsDisplay.className = 'medium';
                            } else {
                                fpsDisplay.className = 'poor';
                            }
                        }
                    }
                };
                
                bufferImg.onerror = () => {
                    framesPending--;
                    console.error('Failed to load frame');
                };
                
                socket.on('connect', () => {
                    console.log('Connected to server');
                    // Reset FPS display on new connection
                    fpsDisplay.textContent = '0';
                    fpsDisplay.className = 'poor';
                    framesPending = 0;
                });
                
                socket.on('disconnect', () => {
                    fpsDisplay.textContent = '0';
                    fpsDisplay.className = 'poor';
                    framesPending = 0;
                });
                
                socket.on('screen_frame', (data) => {
                    // Skip frame if too many are pending
                    if (framesPending > 2) return;
                    
                    framesPending++;
                    bufferImg.src = 'data:image/jpeg;base64,' + data.frame;
                });
                
                socket.on('fps_update', (data) => {
                    const fps = data.fps;
                    fpsDisplay.textContent = fps;
                    
                    // Update color based on FPS
                    if (fps >= 20) {
                        fpsDisplay.className = 'good';
                    } else if (fps >= 10) {
                        fpsDisplay.className = 'medium';
                    } else {
                        fpsDisplay.className = 'poor';
                    }
                });
            </script>
        </body>
    </html>
    '''

def send_frames():
    global streaming
    last_frame_time = time.time()
    min_frame_interval = 1.0 / 60  # Target 60 FPS max
    consecutive_errors = 0
    
    while streaming:
        try:
            current_time = time.time()
            elapsed = current_time - last_frame_time
            
            if elapsed < min_frame_interval:
                # Wait for minimum interval to maintain consistent frame rate
                time.sleep(min_frame_interval - elapsed)
                continue
                
            # Get frame from queue with short timeout
            frame = frame_queue.get(timeout=0.1)
            
            # Emit frame and track timing
            socketio.emit('screen_frame', {'frame': frame})
            last_frame_time = time.time()
            consecutive_errors = 0  # Reset error counter on success
            
        except queue.Empty:
            # No frames available, just continue
            continue
            
        except Exception as e:
            print(f"Error sending frame: {e}")
            consecutive_errors += 1
            
            # Add increasing delay on repeated errors
            if consecutive_errors > 3:
                time.sleep(min(0.5, 0.1 * consecutive_errors))
            else:
                time.sleep(0.1)

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    # Reset counters on new connection
    global frame_count, current_fps
    with frame_lock:
        frame_count = 0
        current_fps = 0
    # Clear frame queue
    while not frame_queue.empty():
        try:
            frame_queue.get_nowait()
        except queue.Empty:
            break

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")
    # Clear frame queue on disconnect
    while not frame_queue.empty():
        try:
            frame_queue.get_nowait()
        except queue.Empty:
            break

def start_threads():
    global streaming, frame_count, current_fps
    streaming = True
    frame_count = 0
    current_fps = 0
    
    # Start capture thread with higher priority
    capture_thread = threading.Thread(target=capture_screen)
    capture_thread.daemon = True
    capture_thread.start()
    
    # Start frame sender thread
    sender_thread = threading.Thread(target=send_frames)
    sender_thread.daemon = True
    sender_thread.start()
    
    # Start FPS calculation thread
    fps_thread = threading.Thread(target=calculate_fps)
    fps_thread.daemon = True
    fps_thread.start()

if __name__ == '__main__':
    print("Starting optimized screen sharing server at http://localhost:5002")
    print("FPS counter is always visible")
    
    # Optimize SocketIO settings for better performance
    socketio.server.eio.max_http_buffer_size = 5 * 1024 * 1024  # 5MB buffer
    socketio.server.max_queue = 30  # Limit event queue size
    
    # Start the threads
    start_threads()
    
    # Run the server with optimized settings
    socketio.run(app,
                host='0.0.0.0',
                port=5002,
                debug=False,
                use_reloader=False,  # Disable reloader for better performance
                log_output=False)    # Disable default logging
