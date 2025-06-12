from flask import Flask, request, jsonify

import requests
import time
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/', methods=['GET'])
def homepage():
    return """
    <html>
    <head>
        <title>💀 Insta SessionID API</title>
        <style>
            body {
                background-color: #000;
                color: #00ff00;
                font-family: monospace;
                padding: 30px;
                text-align: center;
            }
            .btn {
                background-color: #00ff00;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                color: #000;
                text-decoration: none;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <h1>🔐 Insta Session API</h1>
        <p>This API returns Instagram session ID using username & password.</p>
        <p><b>GET:</b> <code>/api?username=your_ig&password=your_pass</code></p>
        <p>Made with 💚 by <b>@nobi_shops</b></p>
        <br>
        <a href="https://t.me/nobi_shops" class="btn" target="_blank">🔗 Join our Telegram</a>
    </body>
    </html>
    """

def insta_login(username, password):
    session = requests.Session()

    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.instagram.com/accounts/login/",
        "Accept-Language": "en-US,en;q=0.9"
    })

    try:
        resp = session.get("https://www.instagram.com/accounts/login/")
    except Exception as e:
        return {"status": "error", "message": f"Failed to get CSRF token: {str(e)}"}

    csrf_token = session.cookies.get_dict().get('csrftoken')

    if not csrf_token:
        return {"status": "error", "message": "CSRF token not found."}

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
            "Developer": "@nobi_shops",
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
