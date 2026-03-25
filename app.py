import os
import json
from urllib.parse import urlencode
from flask import Flask, redirect, request, session, url_for, render_template
from authlib.integrations.flask_client import OAuth
from secrets import token_urlsafe
import jwt
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_NAME'] = 'flask_session'
app.config['SESSION_COOKIE_PATH'] = '/'

oauth = OAuth(app)

# Configure OIDC client
discovery_url = os.getenv('DISCOVERY_URL')
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
redirect_uri = os.getenv('REDIRECT_URI')

# Fetch OIDC configuration
try:
    oidc_config = requests.get(discovery_url).json()
except Exception as e:
    print(f"Warning: Could not fetch OIDC config: {e}")
    oidc_config = {}

oauth.register(
    'oidc',
    client_id=client_id,
    client_secret=client_secret,
    server_metadata_url=discovery_url,
    client_kwargs={'scope': 'openid profile email'},
    redirect_uri=redirect_uri,
)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    return oauth.oidc.authorize_redirect(redirect_uri=redirect_uri)


@app.route('/callback')
def callback():
    try:
        token = oauth.oidc.authorize_access_token()
        session['token'] = token
        
        user_info = token.get('userinfo')
        
        if not user_info:
            id_token = token.get('id_token')
            user_info = jwt.decode(id_token, options={"verify_signature": True}) 

        session['user_info'] = user_info
        return redirect(url_for('profile'))

    except Exception as e:
        return f"Security Validation Failed: {str(e)}", 400


@app.route('/profile')
def profile():
    if 'user_info' not in session:
        return redirect(url_for('login'))
    
    user_info = session.get('user_info', {})
    token = session.get('token', {})
    id_token = token.get('id_token', '')
    
    return render_template('profile.html', user_info=user_info, id_token=id_token)


@app.route('/logout')
def logout():
    session.clear()
    end_session_endpoint = oidc_config.get('end_session_endpoint')
    if end_session_endpoint:
        return redirect(end_session_endpoint + '?post_logout_redirect_uri=' + url_for('index', _external=True))
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)