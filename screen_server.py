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
frame_queue = queue.Queue(maxsize=2)  # Smaller queue for more consistent timing
current_fps = 0
last_emit_time = 0
fps_history = []  # Store recent FPS values for smoothing
MAX_FPS_HISTORY = 10  # Number of samples to keep for moving average
def calculate_fps():
    global streaming, frame_count, current_fps, last_emit_time, fps_history
    min_emit_interval = 0.1  # More frequent updates (100ms)
    sample_interval = 0.2    # Sample FPS every 200ms
    
    while streaming:
        try:
            with frame_lock:
                last_count = frame_count
            
            time.sleep(sample_interval)
            
            with frame_lock:
                current_time = time.time()
                elapsed = current_time - last_emit_time
                
                # Calculate instantaneous FPS
                new_fps = (frame_count - last_count) * (1.0 / sample_interval)
                frame_count = last_count  # Update baseline without resetting
                
                if new_fps >= 0:
                    # Update moving average
                    fps_history.append(new_fps)
                    if len(fps_history) > MAX_FPS_HISTORY:
                        fps_history.pop(0)
                    
                    # Calculate smoothed FPS
                    if fps_history:
                        # Remove outliers before averaging
                        sorted_fps = sorted(fps_history)
                        trimmed_fps = sorted_fps[1:-1] if len(sorted_fps) > 3 else sorted_fps
                        current_fps = round(sum(trimmed_fps) / len(trimmed_fps))
                
                # Emit FPS update if enough time has passed
                if elapsed >= min_emit_interval:
                    socketio.emit('fps_update', {'fps': current_fps})
                    last_emit_time = current_time
                    
        except Exception as e:
            print(f"Error calculating FPS: {e}")
            time.sleep(0.1)


def capture_screen():
    global streaming, frame_count
    target_fps = 30  # Target more stable 30 FPS
    target_delay = 1.0 / target_fps
    frame_time_buffer = []  # Keep track of frame times for adaptive timing
    MAX_TIMING_SAMPLES = 5

    last_capture_time = time.time()

    while streaming:
        try:
            current_time = time.time()
            elapsed = current_time - last_capture_time

            # Adaptive timing based on recent frame times
            if frame_time_buffer:
                avg_frame_time = sum(frame_time_buffer) / len(frame_time_buffer)
                # Adjust delay based on average frame processing time
                adjusted_delay = max(0, target_delay - (avg_frame_time * 0.5))
            else:
                adjusted_delay = target_delay

            if elapsed < adjusted_delay:
                # Fine-grained sleep for more accurate timing
                time.sleep(max(0, adjusted_delay - elapsed))
                continue

            capture_start = time.time()

            # Capture screenshot
            screenshot = pyautogui.screenshot()
            
            # Rotate image 90 degrees
            rotated = screenshot.rotate(270, expand=True)
            
            # Reduce size by 66% for more stable performance
            width, height = rotated.size
            new_width = width * 2 // 3
            new_height = height * 2 // 3
            rotated = rotated.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to bytes with consistent quality
            img_byte_arr = io.BytesIO()
            rotated.save(img_byte_arr, format='JPEG', quality=30)  # Slightly lower quality for stability
            img_byte_arr = img_byte_arr.getvalue()
            
            # Convert to base64 for sending
            base64_frame = base64.b64encode(img_byte_arr).decode('utf-8')
            
            # Update timing information
            frame_time = time.time() - capture_start
            frame_time_buffer.append(frame_time)
            if len(frame_time_buffer) > MAX_TIMING_SAMPLES:
                frame_time_buffer.pop(0)

            if not frame_queue.full():
                frame_queue.put_nowait(base64_frame)
                with frame_lock:
                    frame_count += 1
            
            last_capture_time = current_time

        except Exception as e:
            print(f"Error capturing screen: {e}")
            time.sleep(0.1)
            frame_time_buffer.clear()  # Reset timing buffer on error

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
    target_interval = 1.0 / 30  # Match capture FPS
    min_interval = target_interval * 0.8  # Allow slight speedup if needed
    last_frame_time = time.time()
    consecutive_errors = 0
    frame_times = []  # Track recent frame send times
    MAX_FRAME_TIMES = 5
    
    while streaming:
        try:
            current_time = time.time()
            elapsed = current_time - last_frame_time
            
            # Adaptive timing based on recent frame times
            if frame_times:
                avg_frame_time = sum(frame_times) / len(frame_times)
                adjusted_interval = min(target_interval, max(min_interval, avg_frame_time * 1.1))
            else:
                adjusted_interval = target_interval
            
            if elapsed < adjusted_interval:
                time.sleep(min(adjusted_interval - elapsed, 0.016))  # Max 16ms sleep
                continue
            
            # Get frame with shorter timeout
            frame = frame_queue.get(timeout=0.05)  # Faster response to available frames
            
            # Track frame send time
            send_start = time.time()
            socketio.emit('screen_frame', {'frame': frame})
            
            # Update timing information
            frame_time = time.time() - send_start
            frame_times.append(frame_time)
            if len(frame_times) > MAX_FRAME_TIMES:
                frame_times.pop(0)
            
            last_frame_time = current_time
            consecutive_errors = 0
            
        except queue.Empty:
            if time.time() - last_frame_time > 1.0:  # Reset timing after long gaps
                last_frame_time = time.time()
                frame_times.clear()
            continue
            
        except Exception as e:
            print(f"Error sending frame: {e}")
            consecutive_errors += 1
            frame_times.clear()  # Reset timing on error
            
            if consecutive_errors > 3:
                time.sleep(min(0.5, 0.1 * consecutive_errors))
                if consecutive_errors > 5:
                    # Clear queue if too many errors
                    while not frame_queue.empty():
                        try:
                            frame_queue.get_nowait()
                        except queue.Empty:
                            break
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
