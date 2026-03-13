from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import re
import threading
import os
from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# تأكد من وجود مجلد للكتابة
if not os.path.exists('data'):
    os.makedirs('data')
codes_file = os.path.join('data', 'codes.txt')

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>استخراج أكواد eSIM</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Arial', sans-serif;
        }
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 15px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 25px;
        }
        .input-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: bold;
            font-size: 16px;
        }
        input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            font-size: 18px;
            text-align: center;
        }
        button {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 20px;
            font-weight: bold;
            cursor: pointer;
            margin: 10px 0;
            transition: 0.3s;
        }
        button:hover {
            transform: scale(1.02);
            box-shadow: 0 10px 30px rgba(102,126,234,0.4);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .status-box {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
            border-right: 4px solid #667eea;
        }
        .codes-container {
            margin: 20px 0;
            max-height: 400px;
            overflow-y: auto;
        }
        .code-box {
            background: #f0f4ff;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            border-right: 4px solid #38a169;
            font-family: monospace;
            font-size: 20px;
            text-align: center;
            font-weight: bold;
            letter-spacing: 2px;
        }
        .download-btn {
            background: #38a169;
            font-size: 18px;
            padding: 15px;
        }
        .progress {
            color: #667eea;
            font-weight: bold;
            margin: 10px 0;
        }
        @media (max-width: 480px) {
            .container { padding: 15px; }
            h1 { font-size: 24px; }
            .code-box { font-size: 16px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 استخراج أكواد eSIM</h1>
        <p class="subtitle">أكواد حقيقية من Hubby eSIM</p>
        
        <div class="input-group">
            <label>كم كود تريد استخراجهم؟</label>
            <input type="number" id="codeCount" min="1" max="20" value="5">
        </div>
        
        <button onclick="startExtraction()" id="startBtn">ابدأ الاستخراج</button>
        <button onclick="stopExtraction()" id="stopBtn" style="background: #e53e3e;" disabled>إيقاف</button>
        
        <div class="status-box" id="status">
            <div class="progress" id="progressText">⏳ انتظر...</div>
            <div id="currentStatus">غير نشط</div>
        </div>
        
        <div class="codes-container" id="codesList"></div>
        
        <button class="download-btn" onclick="downloadCodes()" id="downloadBtn" disabled>📥 تحميل الأكواد</button>
    </div>

    <script>
        const socket = io();
        let codes = [];
        
        socket.on('new_code', function(data) {
            codes.push(data.code);
            updateCodesDisplay();
            document.getElementById('downloadBtn').disabled = false;
        });
        
        socket.on('progress', function(data) {
            document.getElementById('progressText').innerHTML = 
                `✅ تم استخراج ${data.completed} من ${data.total}`;
            document.getElementById('currentStatus').innerHTML = data.message;
        });
        
        socket.on('finished', function() {
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            document.getElementById('currentStatus').innerHTML = '✨ اكتمل الاستخراج!';
        });
        
        function startExtraction() {
            const count = document.getElementById('codeCount').value;
            codes = [];
            updateCodesDisplay();
            
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            document.getElementById('downloadBtn').disabled = true;
            
            fetch('/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({count: count})
            });
        }
        
        function stopExtraction() {
            fetch('/stop');
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
        }
        
        function updateCodesDisplay() {
            const html = codes.map((code, index) => 
                `<div class="code-box">${index + 1}. ${code}</div>`
            ).join('');
            document.getElementById('codesList').innerHTML = html;
        }
        
        function downloadCodes() {
            const text = codes.join('\\n');
            const blob = new Blob([text], {type: 'text/plain'});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'esim_codes.txt';
            a.click();
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/start', methods=['POST'])
def start():
    count = request.json.get('count', 5)
    thread = threading.Thread(target=extract_codes, args=(int(count),))
    thread.daemon = True
    thread.start()
    return jsonify({'status': 'started'})

@app.route('/stop')
def stop():
    global running
    running = False
    return jsonify({'status': 'stopped'})

running = True

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.binary_location = "/usr/bin/google-chrome"
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def extract_codes(total):
    global running
    completed = 0
    
    for i in range(total):
        if not running:
            break
            
        socketio.emit('progress', {
            'completed': completed,
            'total': total,
            'message': f'جاري استخراج الكود {completed + 1} من {total}'
        })
        
        try:
            code = get_single_code()
            if code:
                socketio.emit('new_code', {'code': code})
                completed += 1
                with open(codes_file, 'a') as f:
                    f.write(code + '\n')
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(2)
    
    socketio.emit('finished')
    running = True

def get_single_code():
    driver = None
    try:
        driver = get_driver()
        
        driver.get('https://besttemporaryemail.com/')
        time.sleep(3)
        
        email_element = driver.find_element(By.CSS_SELECTOR, '.email-address, input[readonly]')
        email = email_element.get_attribute('value') or email_element.text
        
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get('https://platform.hubbyesim.com/free-esim/canadian-travel-news-jnn58d')
        time.sleep(3)
        
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]'))
        )
        email_input.send_keys(email)
        
        submit_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_btn.click()
        
        driver.switch_to.window(driver.window_handles[0])
        
        time.sleep(30)
        driver.refresh()
        time.sleep(3)
        
        messages = driver.find_elements(By.CSS_SELECTOR, '.message-item, .email-item')
        
        for message in messages:
            try:
                message.click()
                time.sleep(2)
                
                content = driver.find_element(By.CSS_SELECTOR, '.message-content, .email-body').text
                
                match = re.search(r'Enter your promo code:\s*([A-Z0-9]{10})', content)
                if match:
                    code = match.group(1)
                    return code
            except:
                continue
        
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 25px;
        }
        .input-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: bold;
            font-size: 16px;
        }
        input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            font-size: 18px;
            text-align: center;
        }
        button {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 20px;
            font-weight: bold;
            cursor: pointer;
            margin: 10px 0;
            transition: 0.3s;
        }
        button:hover {
            transform: scale(1.02);
            box-shadow: 0 10px 30px rgba(102,126,234,0.4);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .status-box {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
            border-right: 4px solid #667eea;
        }
        .codes-container {
            margin: 20px 0;
            max-height: 400px;
            overflow-y: auto;
        }
        .code-box {
            background: #f0f4ff;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            border-right: 4px solid #38a169;
            font-family: monospace;
            font-size: 20px;
            text-align: center;
            font-weight: bold;
            letter-spacing: 2px;
        }
        .download-btn {
            background: #38a169;
            font-size: 18px;
            padding: 15px;
        }
        .progress {
            color: #667eea;
            font-weight: bold;
            margin: 10px 0;
        }
        @media (max-width: 480px) {
            .container { padding: 15px; }
            h1 { font-size: 24px; }
            .code-box { font-size: 16px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 استخراج أكواد eSIM</h1>
        <p class="subtitle">أكواد حقيقية من Hubby eSIM</p>
        
        <div class="input-group">
            <label>كم كود تريد استخراجهم؟</label>
            <input type="number" id="codeCount" min="1" max="20" value="5">
        </div>
        
        <button onclick="startExtraction()" id="startBtn">ابدأ الاستخراج</button>
        <button onclick="stopExtraction()" id="stopBtn" style="background: #e53e3e;" disabled>إيقاف</button>
        
        <div class="status-box" id="status">
            <div class="progress" id="progressText">⏳ انتظر...</div>
            <div id="currentStatus">غير نشط</div>
        </div>
        
        <div class="codes-container" id="codesList"></div>
        
        <button class="download-btn" onclick="downloadCodes()" id="downloadBtn" disabled>📥 تحميل الأكواد</button>
    </div>

    <script>
        const socket = io();
        let codes = [];
        
        socket.on('new_code', function(data) {
            codes.push(data.code);
            updateCodesDisplay();
            document.getElementById('downloadBtn').disabled = false;
        });
        
        socket.on('progress', function(data) {
            document.getElementById('progressText').innerHTML = 
                `✅ تم استخراج ${data.completed} من ${data.total}`;
            document.getElementById('currentStatus').innerHTML = data.message;
        });
        
        socket.on('finished', function() {
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            document.getElementById('currentStatus').innerHTML = '✨ اكتمل الاستخراج!';
        });
        
        function startExtraction() {
            const count = document.getElementById('codeCount').value;
            codes = [];
            updateCodesDisplay();
            
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            document.getElementById('downloadBtn').disabled = true;
            
            fetch('/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({count: count})
            });
        }
        
        function stopExtraction() {
            fetch('/stop');
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
        }
        
        function updateCodesDisplay() {
            const html = codes.map((code, index) => 
                `<div class="code-box">${index + 1}. ${code}</div>`
            ).join('');
            document.getElementById('codesList').innerHTML = html;
        }
        
        function downloadCodes() {
            const text = codes.join('\\n');
            const blob = new Blob([text], {type: 'text/plain'});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'esim_codes.txt';
            a.click();
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/start', methods=['POST'])
def start():
    count = request.json.get('count', 5)
    thread = threading.Thread(target=extract_codes, args=(int(count),))
    thread.daemon = True
    thread.start()
    return jsonify({'status': 'started'})

@app.route('/stop')
def stop():
    global running
    running = False
    return jsonify({'status': 'stopped'})

running = True

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.binary_location = "/usr/bin/google-chrome"
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def extract_codes(total):
    global running
    completed = 0
    
    for i in range(total):
        if not running:
            break
            
        socketio.emit('progress', {
            'completed': completed,
            'total': total,
            'message': f'جاري استخراج الكود {completed + 1} من {total}'
        })
        
        try:
            code = get_single_code()
            if code:
                socketio.emit('new_code', {'code': code})
                completed += 1
                with open('codes.txt', 'a') as f:
                    f.write(code + '\n')
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(2)
    
    socketio.emit('finished')
    running = True

def get_single_code():
    driver = None
    try:
        driver = get_driver()
        
        driver.get('https://besttemporaryemail.com/')
        time.sleep(3)
        
        email_element = driver.find_element(By.CSS_SELECTOR, '.email-address, input[readonly]')
        email = email_element.get_attribute('value') or email_element.text
        
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get('https://platform.hubbyesim.com/free-esim/canadian-travel-news-jnn58d')
        time.sleep(3)
        
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]'))
        )
        email_input.send_keys(email)
        
        submit_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_btn.click()
        
        driver.switch_to.window(driver.window_handles[0])
        
        time.sleep(30)
        driver.refresh()
        time.sleep(3)
        
        messages = driver.find_elements(By.CSS_SELECTOR, '.message-item, .email-item')
        
        for message in messages:
            try:
                message.click()
                time.sleep(2)
                
                content = driver.find_element(By.CSS_SELECTOR, '.message-content, .email-body').text
                
                match = re.search(r'Enter your promo code:\s*([A-Z0-9]{10})', content)
                if match:
                    code = match.group(1)
                    return code
            except:
                continue
        
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
