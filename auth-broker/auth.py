from authlib.integrations.flask_client import OAuth2
import json
from flask import Flask, redirect, request, Session
import os

config = json.load(open("config.json"))

app = Flask(__name__)
app.secret_key = os.urandom(24) 

state_service_map = {}

@app.route("/login")
def login():
    service = request.args.get("service")
    if not service:
        return "No service provided", 400
    
    client = OAuth2Client(
        client_id=config[service]["client_id"],
        client_secret=config[service]["client_secret"],
        scope=config[service]["scope"],
    )
    url = client.create_authorization_url(config[service]["auth_url"], access_type="offline", prompt="consent", redirect_uri=config[service]["redirect_uri"])
    state = url[1]
    return redirect(url[0])

@app.route("/oauth/callback")
def callback():
    authorization_code = request.args.get("authorization_code")
    if not authorization_code:
        return "No authorization code provided", 400
    
    token = exchange_code_for_token(authorization_code, redirect_uri)
    return token, 200

service = "google_calendar"

client = OAuth2Client(
    client_id=config[service]["client_id"],
    client_secret=config[service]["client_secret"],
    scope=config[service]["scope"],
)

def exchange_code_for_token(code, redirect_uri):
    token = client.fetch_token(
        url=config[service]['token_url'],
        authorization_response=f"{redirect_uri}?code={code}"
    )
    print('received token', token)
    return token # Return access_token and refresh_token

if __name__ == '__main__':
    app.run(port=8888, debug=True)