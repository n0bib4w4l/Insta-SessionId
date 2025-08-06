from flask import Flask, request, jsonify
import requests
import re
from urllib.parse import urlencode

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "Instagram Session ID API",
        "status": "running ✅",
        "endpoints": {
            "POST /get-session": "Extract session ID from Instagram login",
            "POST /validate-session": "Validate existing session ID", 
            "GET /health": "Health check"
        }
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy ✅"})

@app.route('/get-session', methods=['POST'])
def get_session_id():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        
        session = requests.Session()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        session.headers.update(headers)
        
        login_url = 'https://www.instagram.com/accounts/login/'
        response = session.get(login_url)
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to access Instagram"}), 500
        
        csrf_token = None
        csrf_match = re.search(r'"csrf_token":"([^"]+)"', response.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)
        else:
            return jsonify({"error": "Could not extract CSRF token"}), 500
        
        login_data = {
            'username': username,
            'password': password,
            'queryParams': '{}',
            'optIntoOneTap': 'false'
        }
        
        login_headers = {
            'X-CSRFToken': csrf_token,
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/accounts/login/',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        login_response = session.post(
            'https://www.instagram.com/accounts/login/ajax/',
            data=urlencode(login_data),
            headers=login_headers
        )
        
        if login_response.status_code != 200:
            return jsonify({"error": "Login request failed"}), 500
        
        try:
            login_result = login_response.json()
        except:
            return jsonify({"error": "Invalid response from Instagram"}), 500
        
        if not login_result.get('authenticated'):
            return jsonify({
                "error": "Login failed",
                "message": login_result.get('message', 'Invalid credentials')
            }), 401
        
        session_id = None
        for cookie in session.cookies:
            if cookie.name == 'sessionid':
                session_id = cookie.value
                break
        
        if not session_id:
            return jsonify({"error": "Could not extract session ID"}), 500
        
        return jsonify({
            "success": True,
            "data": {
                "session_id": session_id,
                "user_id": login_result.get('userId'),
                "username": username,
                "csrf_token": csrf_token
            }
        })
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/validate-session', methods=['POST'])
def validate_session():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({"error": "Session ID required"}), 400
        
        session = requests.Session()
        session.cookies.set('sessionid', session_id, domain='.instagram.com')
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        session.headers.update(headers)
        
        response = session.get('https://www.instagram.com/accounts/edit/')
        
        if response.status_code == 200:
            return jsonify({
                "success": True,
                "valid": True,
                "message": "Session is valid"
            })
        else:
            return jsonify({
                "success": True,
                "valid": False,
                "message": "Session invalid or expired"
            })
            
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
