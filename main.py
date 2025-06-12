from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
import time, requests
from bs4 import BeautifulSoup

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def homepage():
    return """
    <html>
    <head>
        <title>🔐 Insta Session API</title>
        <style>
            body {
                background-color: black;
                color: #00FF00;
                font-family: monospace;
                text-align: center;
                padding: 30px;
            }
            .button {
                background-color: #00FF00;
                color: black;
                padding: 10px 20px;
                text-decoration: none;
                font-weight: bold;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <h1>💀 Insta SessionID API</h1>
        <p>This API provides Instagram session ID using username & password.</p>
        <p><b>POST:</b> <code>/get_sessionid</code></p>
        <p>🧠 Made by <b>@nobi_shops</b></p>
        <br><br>
        <a href="https://t.me/nobi_shops" class="button" target="_blank">🔗 Join Our Telegram</a>
    </body>
    </html>
    """

@app.post("/get_sessionid")
def get_sessionid(username: str = Form(...), password: str = Form(...)):
    session = requests.Session()

    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.instagram.com/accounts/login/",
        "Accept-Language": "en-US,en;q=0.9"
    })

    # Get CSRF
    resp = session.get("https://www.instagram.com/accounts/login/")
    csrf_token = session.cookies.get_dict().get('csrftoken')
    if not csrf_token:
        return {"status": "fail", "error": "CSRF token missing", "developer": "@nobi_shops"}

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

    login_resp = session.post("https://www.instagram.com/api/v1/web/accounts/login/ajax/", data=payload)
    data = login_resp.json()

    if data.get("authenticated"):
        sessionid = session.cookies.get_dict().get("sessionid")
        return {
            "status": "success",
            "sessionid": sessionid,
            "developer": "@nobi_shops"
        }
    else:
        return {
            "status": "fail",
            "error": data.get("message", "Login failed"),
            "developer": "@nobi_shops"
        }
