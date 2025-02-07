from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/text', methods=['POST'])
def capture_text():
    try:
        data = request.json
        text = data.get('text', '')
        print(f"Received text: {text}")
        return jsonify({"status": "success", "message": "Text received"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    return '''
    <html>
        <head>
            <title>Text Capture Server</title>
        </head>
        <body>
            <h1>Text Capture Server</h1>
            <p>Send POST requests to /text endpoint with JSON data:</p>
            <pre>
{
    "text": "Your text here"
}
            </pre>
            
            <h2>Example using Python requests:</h2>
            <pre>
import requests

url = "http://localhost:5003/text"
data = {"text": "Hello, World!"}
response = requests.post(url, json=data)
print(response.json())
            </pre>
            
            <h2>Example using cURL:</h2>
            <pre>
curl -X POST http://localhost:5003/text \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, World!"}'
            </pre>
        </body>
    </html>
    '''

if __name__ == '__main__':
    print("Starting text capture server at http://localhost:5003")
    app.run(host='0.0.0.0', port=5003, debug=False)