package main

import (
    "bytes"
    "image/jpeg"
    "log"
    "net/http"
    "sync/atomic"
    "text/template"
    "time"

    "github.com/disintegration/imaging"
    "github.com/kbinani/screenshot"
)

var (
    currentFPS uint64
    frameCount uint64
)

func calculateFPS() {
    ticker := time.NewTicker(time.Second)
    for range ticker.C {
        fps := atomic.LoadUint64(&frameCount)
        atomic.StoreUint64(&currentFPS, fps)
        atomic.StoreUint64(&frameCount, 0)
    }
}

func streamHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "multipart/x-mixed-replace; boundary=frame")

    for {
        // Capture the first display
        img, err := screenshot.CaptureDisplay(0)
        if err != nil {
            log.Println("Error capturing screen:", err)
            continue
        }

        // Rotate image 90 degrees clockwise
        rotated := imaging.Rotate270(img)

        // Resize image to 50% for better performance
        resized := imaging.Resize(rotated, rotated.Bounds().Dx()/2, rotated.Bounds().Dy()/2, imaging.Lanczos)

        // Encode the image to JPEG with quality 70
        var buf bytes.Buffer
        err = jpeg.Encode(&buf, resized, &jpeg.Options{Quality: 70})
        if err != nil {
            log.Println("Error encoding image:", err)
            continue
        }

        // Write the MJPEG frame
        w.Write([]byte("--frame\r\n"))
        w.Write([]byte("Content-Type: image/jpeg\r\n\r\n"))
        w.Write(buf.Bytes())
        w.Write([]byte("\r\n"))

        if flusher, ok := w.(http.Flusher); ok {
            flusher.Flush()
        }

        // Increment frame counter
        atomic.AddUint64(&frameCount, 1)

        // Sleep for roughly 16ms to aim for ~60 FPS
        time.Sleep(16 * time.Millisecond)
    }
}

func fpsHandler(w http.ResponseWriter, r *http.Request) {
    fps := atomic.LoadUint64(&currentFPS)
    w.Header().Set("Content-Type", "application/json")
    w.Write([]byte(`{"fps": ` + string(rune(fps)) + `}`))
}

func indexHandler(w http.ResponseWriter, r *http.Request) {
    tmpl := template.Must(template.New("index").Parse(`
    <!DOCTYPE html>
    <html>
    <head>
        <title>Screen Share</title>
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
            #stream {
                max-width: 100%;
                max-height: 100vh;
                width: auto;
                height: auto;
            }
            #fps {
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
        <img id="stream" src="/stream">
        <div id="fps">FPS: <span id="fpsValue">0</span></div>
        <script>
            const fpsValue = document.getElementById('fpsValue');
            
            function updateFPS() {
                fetch('/fps')
                    .then(response => response.json())
                    .then(data => {
                        const fps = data.fps;
                        fpsValue.textContent = fps;
                        
                        if (fps >= 30) {
                            fpsValue.className = 'good';
                        } else if (fps >= 15) {
                            fpsValue.className = 'medium';
                        } else {
                            fpsValue.className = 'poor';
                        }
                    })
                    .catch(console.error);
            }
            
            // Update FPS every second
            setInterval(updateFPS, 1000);
        </script>
    </body>
    </html>
    `))
    tmpl.Execute(w, nil)
}

func main() {
    // Start FPS calculation in background
    go calculateFPS()

    // Set up routes
    http.HandleFunc("/", indexHandler)
    http.HandleFunc("/stream", streamHandler)
    http.HandleFunc("/fps", fpsHandler)

    log.Println("Screen sharing server started at http://localhost:8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
