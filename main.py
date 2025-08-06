from flask import Flask, request, jsonify
import requests
import re
from urllib.parse import urlencode

app = Flask(__name__)

@app.route('/')
def get_session():
    try:
        # Get username and password from URL parameters
        username = request.args.get('username')
        password = request.args.get('password')
        
        if not username or not password:
            return jsonify({
                "error": "Username and password required",
                "usage": "/?username=your_username&password=your_password"
            }), 400
        
        # Create session
        session = requests.Session()
        
        # Set headers to mimic real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        session.headers.update(headers)
        
        # First visit homepage to get initial cookies
        home_response = session.get('https://www.instagram.com/')
        if home_response.status_code != 200:
            return jsonify({"error": "Failed to access Instagram"}), 500
        
        # Get login page
        login_response = session.get('https://www.instagram.com/accounts/login/')
        if login_response.status_code != 200:
            return jsonify({"error": "Failed to access login page"}), 500
        
        # Extract CSRF token with multiple methods
        csrf_token = None
        
        # Method 1: From cookies
        csrf_token = session.cookies.get('csrftoken')
        
        # Method 2: From HTML if cookie method failed
        if not csrf_token:
            csrf_patterns = [
                r'"csrf_token":"([^"]+)"',
                r'"csrfToken":"([^"]+)"',
                r'csrftoken=([^;]+)',
                r'csrf_token":\s*"([^"]+)"',
                r'window\._sharedData[^}]*"csrf_token":"([^"]+)"'
            ]
            
            for pattern in csrf_patterns:
                match = re.search(pattern, login_response.text)
                if match:
                    csrf_token = match.group(1)
                    break
        
        if not csrf_token:
            return jsonify({"error": "Could not extract CSRF token"}), 500
        
        # Prepare login data
        login_data = {
            'username': username,
            'password': password,
            'queryParams': '{}',
            'optIntoOneTap': 'false',
            'trustedDeviceRecords': '{}'
        }
        
        # Login headers
        login_headers = {
            'X-CSRFToken': csrf_token,
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/accounts/login/',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Instagram-AJAX': '1',
            'X-IG-App-ID': '936619743392459'
        }
        
        # Perform login
        login_url = 'https://www.instagram.com/accounts/login/ajax/'
        login_request = session.post(
            login_url,
            data=urlencode(login_data),
            headers=login_headers
        )
        
        if login_request.status_code != 200:
            return jsonify({"error": f"Login failed with status {login_request.status_code}"}), 500
        
        try:
            login_result = login_request.json()
        except:
            return jsonify({"error": "Invalid response from Instagram"}), 500
        
        # Check if login was successful
        if not login_result.get('authenticated'):
            error_msg = login_result.get('message', 'Invalid credentials')
            return jsonify({"error": f"Login failed: {error_msg}"}), 401
        
        # Extract session ID from cookies
        session_id = session.cookies.get('sessionid')
        
        if not session_id:
            return jsonify({"error": "Session ID not found in cookies"}), 500
        
        # Get user info
        user_id = login_result.get('userId', 'unknown')
        
        return jsonify({
            "success": True,
            "username": username,
            "session_id": session_id,
            "user_id": user_id,
            "csrf_token": csrf_token,
            "message": "Session extracted successfully!"
        })
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/health')
def health():
    return jsonify({"status": "API is running ✅"})

@app.route('/test')
def test():
    return jsonify({
        "message": "Instagram Session ID Extractor",
        "usage": {
            "url": "/?username=YOUR_USERNAME&password=YOUR_PASSWORD",
            "example": "/?username=testuser&password=testpass"
        },
        "endpoints": {
            "GET /": "Extract session ID (requires username & password params)",
            "GET /health": "Health check",
            "GET /test": "This help page"
        }
    })

if __name__ == '__main__':
    app.run(debug=True)
