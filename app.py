# app.py
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

def get_user_info(sessionid, target_username):
    session = requests.Session()

    # Set headers
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://www.instagram.com/{target_username}/",
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": f"sessionid={sessionid};"
    })

    try:
        resp = session.get(f"https://www.instagram.com/api/v1/users/web_profile_info/?username={target_username}")
        data = resp.json()
    except Exception as e:
        return {"status": "error", "message": f"Failed to get user info: {str(e)}"}

    if "data" in data:
        return {
            "status": "success",
            "message": "User info fetched.",
            "Developer": "@meta_server",
            "result": data
        }
    else:
        return {
            "status": "failed",
            "message": "Failed to fetch user info.",
            "error": data
        }

@app.route('/api', methods=['GET'])
def api_get_user_info():
    sessionid = request.args.get('sessionid')
    target_username = request.args.get('target_username')

    if not sessionid or not target_username:
        return jsonify({"status": "error", "message": "Missing sessionid or target_username parameter."})

    result = get_user_info(sessionid, target_username)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
