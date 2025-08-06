from flask import Flask, request, jsonify
import requests
import re
from urllib.parse import urlencode

app = Flask(__name__)

@app.route('/')
def get_session():
    try:
        username = request.args.get('username')
        password = request.args.get('password')
        
        if not username or not password:
            return jsonify({
                "error": "Username and password required",
                "usage": "/?username=YOUR_USERNAME&password=YOUR_PASSWORD"
            }), 400
        
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
        
        # Get login page
        login_url = 'https://www.instagram.com/accounts/login/'
        response = session.get(login_url)
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to access Instagram"}), 500
        
        # Extract CSRF token
        csrf_token = None
        csrf_match = re.search(r'"csrf_token":"([^"]+)"', response.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)
        else:
            return jsonify({"error": "Could not extract CSRF token"}), 500
        
        # Login data
        login_data = {
            'username': username,
            'password': password,
            'queryParams': '{}',
            'optIntoOneTap': 'false'
        }
        
        # Login headers
        login_headers = {
            'X-CSRFToken': csrf_token,
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/accounts/login/',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Perform login
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
                "success": False,
                "error": "Login failed",
                "message": login_result.get('message', 'Invalid credentials')
            }), 401
        
        # Extract session ID
        session_id = None
        for cookie in session.cookies:
            if cookie.name == 'sessionid':
                session_id = cookie.value
                break
        
        if not session_id:
            return jsonify({"error": "Could not extract session ID"}), 500
        
        return jsonify({
            "success": True,
            "username": username,
            "session_id": session_id,
            "user_id": login_result.get('userId'),
            "csrf_token": csrf_token
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/validate')
def validate_session():
    try:
        session_id = request.args.get('session_id')
        
        if not session_id:
            return jsonify({
                "error": "Session ID required",
                "usage": "/validate?session_id=YOUR_SESSION_ID"
            }), 400
        
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
                "success": False,
                "valid": False,
                "message": "Session invalid or expired"
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy ✅",
        "service": "instagram-session-api",
        "endpoints": {
            "GET /": "?username=USER&password=PASS",
            "GET /validate": "?session_id=SESSION_ID",
            "GET /health": "Health check"
        }
    })

if __name__ == '__main__':
    app.run(debug=True)
