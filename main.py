from flask import Flask, request, jsonify
import requests
import re
import json
import time
from urllib.parse import urlencode

app = Flask(__name__)

@app.route('/')
def get_session():
    try:
        # Get credentials from URL
        username = request.args.get('username')
        password = request.args.get('password')
        
        if not username or not password:
            return jsonify({
                "error": "Parameters missing",
                "usage": "/?username=your_username&password=your_password"
            }), 400
        
        # Create fresh session
        session = requests.Session()
        
        # Updated headers for 2024
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://www.instagram.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        session.headers.update(headers)
        
        # Step 1: Get homepage for initial cookies
        home = session.get('https://www.instagram.com/')
        if home.status_code != 200:
            return jsonify({"error": "Failed to load Instagram"}), 500
        
        # Step 2: Get login page
        login_page = session.get('https://www.instagram.com/accounts/login/')
        if login_page.status_code != 200:
            return jsonify({"error": "Failed to load login page"}), 500
        
        # Step 3: Extract required tokens
        csrf_token = session.cookies.get('csrftoken')
        
        # Extract additional required data
        app_id = None
        rollout_hash = None
        
        # Look for app ID and rollout hash in the page
        app_id_match = re.search(r'"APP_ID":"(\d+)"', login_page.text)
        if app_id_match:
            app_id = app_id_match.group(1)
        else:
            app_id = "936619743392459"  # Default Instagram app ID
            
        rollout_match = re.search(r'"rollout_hash":"([^"]+)"', login_page.text)
        if rollout_match:
            rollout_hash = rollout_match.group(1)
        
        if not csrf_token:
            return jsonify({"error": "Could not get CSRF token"}), 500
        
        # Step 4: Prepare login data
        login_payload = {
            'username': username,
            'password': password,
            'queryParams': '{}',
            'optIntoOneTap': 'false'
        }
        
        # Step 5: Set login headers
        login_headers = {
            'X-CSRFToken': csrf_token,
            'X-Instagram-AJAX': rollout_hash if rollout_hash else '1',
            'X-IG-App-ID': app_id,
            'X-IG-WWW-Claim': '0',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/accounts/login/',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Step 6: Perform login
        login_response = session.post(
            'https://www.instagram.com/accounts/login/ajax/',
            data=urlencode(login_payload),
            headers=login_headers
        )
        
        # Debug info
        if login_response.status_code != 200:
            return jsonify({
                "error": f"Login failed with status {login_response.status_code}",
                "response": login_response.text[:200] if login_response.text else "No response"
            }), 500
        
        try:
            result = login_response.json()
        except:
            return jsonify({
                "error": "Invalid JSON response",
                "response": login_response.text[:200]
            }), 500
        
        # Step 7: Check login result
        if not result.get('authenticated'):
            error_msg = result.get('message', 'Login failed')
            return jsonify({
                "error": f"Authentication failed: {error_msg}",
                "status": result.get('status'),
                "user": result.get('user')
            }), 401
        
        # Step 8: Extract session ID
        session_id = session.cookies.get('sessionid')
        
        if not session_id:
            return jsonify({
                "error": "Session ID not found",
                "cookies": [f"{c.name}={c.value}" for c in session.cookies]
            }), 500
        
        # Success response
        return jsonify({
            "success": True,
            "data": {
                "username": username,
                "session_id": session_id,
                "user_id": result.get('userId'),
                "csrf_token": csrf_token
            },
            "message": "Session extracted successfully! ✅"
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Server error: {str(e)}",
            "type": type(e).__name__
        }), 500

@app.route('/test')
def test():
    return jsonify({
        "status": "Instagram Session API Running ✅",
        "usage": "/?username=YOUR_USERNAME&password=YOUR_PASSWORD",
        "example": "/?username=testuser&password=testpass123",
        "note": "Make sure credentials are correct"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(debug=True)
