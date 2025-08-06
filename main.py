from flask import Flask, request, jsonify
import requests
import re
import json
import time
import random
from urllib.parse import urlencode

app = Flask(__name__)

def generate_device_id():
    """Generate a random device ID"""
    return f"android-{''.join(random.choices('0123456789abcdef', k=16))}"

def get_instagram_session(username, password):
    """Extract Instagram session using mobile API approach"""
    
    session = requests.Session()
    
    # Mobile Instagram headers
    headers = {
        'User-Agent': 'Instagram 219.0.0.12.117 Android (29/10; 420dpi; 1080x2130; OnePlus; ONEPLUS A6000; OnePlus6; qcom; en_US; 314665256)',
        'Accept': '*/*',
        'Accept-Language': 'en-US',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'X-IG-Capabilities': '3brTvx0=',
        'X-IG-Connection-Type': 'WIFI',
        'X-IG-Connection-Speed': '-1kbps',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }
    
    session.headers.update(headers)
    
    # Generate device info
    device_id = generate_device_id()
    
    try:
        # Step 1: Get sync data
        sync_data = {
            'id': device_id,
            'experiments': 'ig_android_prefill_main_account_username_on_login_screen_universe,ig_android_gmail_oauth_in_reg,ig_android_device_detection_info_upload,ig_android_gmail_auto_reg_initial_opt_in,ig_android_device_info_foreground_reporting,ig_android_device_verification_fb_signup,ig_android_passwordless_account_password_creation_universe,ig_android_direct_add_direct_to_android_native_photo_share_sheet,ig_android_end_to_end_encryption_consistent,ig_android_device_based_country_verification,ig_android_direct_add_direct_to_android_native_photo_share_sheet_v2'
        }
        
        # Step 2: Try mobile login endpoint
        login_data = {
            'username': username,
            'password': password,
            'guid': device_id.replace('android-', ''),
            'device_id': device_id,
            'phone_id': f"{random.randint(10**15, 10**16-1)}",
            'login_attempt_count': '0'
        }
        
        response = session.post(
            'https://i.instagram.com/api/v1/accounts/login/',
            data=urlencode(login_data)
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('logged_in_user'):
                    # Extract session from cookies
                    session_id = session.cookies.get('sessionid')
                    if session_id:
                        return {
                            'success': True,
                            'session_id': session_id,
                            'user_id': result['logged_in_user'].get('pk'),
                            'username': username
                        }
                return {'success': False, 'error': 'Login failed - no session'}
            except:
                pass
        
        # Fallback to web method if mobile fails
        return web_login_method(username, password)
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def web_login_method(username, password):
    """Fallback web login method"""
    
    session = requests.Session()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    session.headers.update(headers)
    
    try:
        # Get homepage
        home = session.get('https://www.instagram.com/')
        if home.status_code != 200:
            return {'success': False, 'error': 'Failed to access Instagram'}
        
        # Get login page  
        login_page = session.get('https://www.instagram.com/accounts/login/')
        if login_page.status_code != 200:
            return {'success': False, 'error': 'Failed to access login page'}
        
        # Extract CSRF
        csrf_token = session.cookies.get('csrftoken')
        if not csrf_token:
            csrf_match = re.search(r'"csrf_token":"([^"]+)"', login_page.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
        
        if not csrf_token:
            return {'success': False, 'error': 'CSRF token not found'}
        
        # Login attempt
        time.sleep(random.uniform(1, 3))  # Random delay
        
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
        
        login_resp = session.post(
            'https://www.instagram.com/accounts/login/ajax/',
            data=urlencode(login_data),
            headers=login_headers
        )
        
        if login_resp.status_code == 200:
            try:
                result = login_resp.json()
                if result.get('authenticated'):
                    session_id = session.cookies.get('sessionid')
                    if session_id:
                        return {
                            'success': True,
                            'session_id': session_id,
                            'user_id': result.get('userId'),
                            'username': username
                        }
                return {'success': False, 'error': result.get('message', 'Login failed')}
            except:
                return {'success': False, 'error': 'Invalid response'}
        
        return {'success': False, 'error': f'Request failed: {login_resp.status_code}'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/')
def get_session():
    try:
        username = request.args.get('username')
        password = request.args.get('password')
        
        if not username or not password:
            return jsonify({
                "error": "Missing parameters",
                "usage": "/?username=YOUR_USERNAME&password=YOUR_PASSWORD"
            }), 400
        
        # Try to get session
        result = get_instagram_session(username, password)
        
        if result['success']:
            return jsonify({
                "success": True,
                "data": {
                    "username": result['username'],
                    "session_id": result['session_id'],
                    "user_id": result.get('user_id', 'unknown')
                },
                "message": "Session extracted successfully! ✅"
            })
        else:
            return jsonify({
                "error": result['error'],
                "suggestion": "Check username/password or try again later"
            }), 400
            
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/test')
def test():
    return jsonify({
        "status": "Instagram Session Extractor ✅",
        "method": "Mobile + Web API",
        "usage": "/?username=YOUR_USERNAME&password=YOUR_PASSWORD",
        "note": "Uses mobile Instagram API with web fallback"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": int(time.time())})

if __name__ == '__main__':
    app.run(debug=True)
