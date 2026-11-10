import os
from flask import Flask, request, jsonify
import logging
import requests

app = Flask(__name__)

# Configure logging to a file
LOG_FILE = os.getenv('LOG_FILE', 'requests.log')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()])

# Optional Discord webhook URL (set as environment variable DISCORD_WEBHOOK_URL)
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

def forward_to_discord(data):
    if not DISCORD_WEBHOOK_URL:
        return
    try:
        payload = {
            "embeds": [
                {
                    "title": "New Request Logged",
                    "fields": [
                        {"name": "IP Address", "value": data.get('ip', 'N/A'), "inline": True},
                        {"name": "User Agent", "value": data.get('user_agent', 'N/A'), "inline": True},
                        {"name": "Path", "value": data.get('path', 'N/A'), "inline": False},
                        {"name": "Method", "value": data.get('method', 'N/A'), "inline": True},
                        {"name": "Headers", "value": "```" + data.get('headers', '') + "```", "inline": False}
                    ],
                    "color": 0x00ff00
                }
            ]
        }
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        logging.error(f"Failed to send Discord webhook: {e}")

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def log_request(path):
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'N/A')
    headers = '\n'.join([f"{k}: {v}" for k, v in request.headers.items()])
    log_data = {
        'ip': ip,
        'user_agent': user_agent,
        'path': '/' + path,
        'method': request.method,
        'headers': headers,
        'data': request.get_data(as_text=True) or ''
    }
    logging.info(f"IP: {ip} | UA: {user_agent} | Path: /{path} | Method: {request.method}")
    forward_to_discord(log_data)
    return jsonify({"status": "logged"}), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
