from flask import Flask, request, jsonify
import requests
import time
from bs4 import BeautifulSoup

app = Flask(__name__)

def insta_login(username, password):
    session = requests.Session()

    # Set headers
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.instagram.com/accounts/login/",
        "Accept-Language": "en-US,en;q=0.9"
    })

    # Step 1: Get CSRF token
    try:
        resp = session.get("https://www.instagram.com/accounts/login/")
    except Exception as e:
        return {"status": "error", "message": f"Failed to get CSRF token: {str(e)}"}

    csrf_token = session.cookies.get_dict().get('csrftoken')

    if not csrf_token:
        return {"status": "error", "message": "CSRF token not found."}

    # Step 2: Login
    enc_password = f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}"

    payload = {
        "username": username,
        "enc_password": enc_password,
        "queryParams": "{}",
        "optIntoOneTap": "false"
    }

    session.headers.update({
        "X-CSRFToken": csrf_token,
        "Content-Type": "application/x-www-form-urlencoded"
    })

    try:
        login_resp = session.post(
            "https://www.instagram.com/api/v1/web/accounts/login/ajax/",
            data=payload
        )
    except Exception as e:
        return {"status": "error", "message": f"Login request failed: {str(e)}"}

    try:
        data = login_resp.json()
    except Exception:
        return {"status": "error", "message": "Failed to parse login response."}

    if data.get("authenticated"):
        sessionid = session.cookies.get_dict().get("sessionid")
        return {
            "status": "success",
            "message": "Login successful.",
            "Developer": "@nobi_shop",
            "sessionid": sessionid
        }
    else:
        return {
            "status": "failed",
            "message": data.get("message", "Login failed."),
            "error": data
        }

@app.route('/api', methods=['GET'])
def api_login():
    username = request.args.get('username')
    password = request.args.get('password')

    if not username or not password:
        return jsonify({"status": "error", "message": "Missing username or password parameter."})

    result = insta_login(username, password)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
