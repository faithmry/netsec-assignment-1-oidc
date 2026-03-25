import os
from urllib.parse import urlencode
from flask import Flask, redirect, session, url_for, render_template
from authlib.integrations.flask_client import OAuth
from flask_session import Session
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(__file__), '.flask_sessions')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_NAME'] = 'flask_session'
app.config['SESSION_COOKIE_PATH'] = '/'
Session(app)

oauth = OAuth(app)


def provider_from_env(prefix):
    return {
        'discovery_url': os.getenv(f'{prefix}_DISCOVERY_URL'),
        'client_id': os.getenv(f'{prefix}_CLIENT_ID'),
        'client_secret': os.getenv(f'{prefix}_CLIENT_SECRET'),
        'issuer': os.getenv(f'{prefix}_ISSUER'),
    }


def provider_has_required(config):
    return all([config.get('discovery_url'), config.get('client_id'), config.get('client_secret')])


def fetch_oidc_config(discovery_url):
    try:
        return requests.get(discovery_url, timeout=5).json()
    except Exception as e:
        print(f"Warning: Could not fetch OIDC config from {discovery_url}: {e}")
        return {}


providers = {
    'keycloak': provider_from_env('KEYCLOAK'),
    'hydra': provider_from_env('HYDRA'),
}

# Backward compatibility with legacy single-provider env names.
if not provider_has_required(providers['keycloak']):
    legacy = {
        'discovery_url': os.getenv('DISCOVERY_URL'),
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'issuer': os.getenv('ISSUER'),
    }
    if provider_has_required(legacy):
        providers['keycloak'] = legacy

configured_providers = {}
provider_metadata = {}

for provider_name, config in providers.items():
    if not provider_has_required(config):
        continue

    metadata = fetch_oidc_config(config['discovery_url'])
    if config.get('issuer') and metadata.get('issuer') and metadata.get('issuer') != config['issuer']:
        raise RuntimeError(f"{provider_name} issuer does not match discovery document issuer")

    oauth.register(
        provider_name,
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        server_metadata_url=config['discovery_url'],
        client_kwargs={'scope': 'openid profile email'},
    )
    configured_providers[provider_name] = config
    provider_metadata[provider_name] = metadata

if not configured_providers:
    raise RuntimeError(
        'No OIDC provider configured. Set KEYCLOAK_* and/or HYDRA_* environment variables.'
    )

default_provider = os.getenv('DEFAULT_PROVIDER', 'keycloak')
if default_provider not in configured_providers:
    default_provider = next(iter(configured_providers.keys()))


@app.route('/')
def index():
    callback_uri = os.getenv('REDIRECT_URI') or url_for('callback', _external=True)
    return render_template(
        'index.html',
        providers=sorted(configured_providers.keys()),
        callback_uri=callback_uri,
        default_provider=default_provider,
    )


@app.route('/login')
def login():
    return redirect(url_for('login_provider', provider=default_provider))


@app.route('/login/<provider>')
def login_provider(provider):
    if provider not in configured_providers:
        return 'Unknown OIDC provider', 400

    session['auth_provider'] = provider
    redirect_uri = os.getenv('REDIRECT_URI') or url_for('callback', _external=True)
    client = oauth.create_client(provider)
    return client.authorize_redirect(redirect_uri=redirect_uri)


@app.route('/callback')
def callback():
    try:
        provider = session.get('auth_provider', default_provider)
        if provider not in configured_providers:
            return 'No valid OIDC provider found in session', 400

        client = oauth.create_client(provider)
        token = client.authorize_access_token()
        session['token'] = token

        user_info = token.get('userinfo')

        # Parse and validate ID token via OIDC provider metadata/JWKS when
        # userinfo is not returned in the token response.
        if not user_info:
            user_info = client.parse_id_token(token)

        session['auth_provider'] = provider
        session['user_info'] = user_info
        session['id_token'] = token.get('id_token')
        return redirect(url_for('profile'))

    except Exception as e:
        return f"Security Validation Failed: {str(e)}", 400


@app.route('/profile')
def profile():
    if 'user_info' not in session:
        return redirect(url_for('login_provider', provider=default_provider))
    
    user_info = session.get('user_info', {})
    token = session.get('token', {})
    id_token = session.get('id_token') or token.get('id_token', '')
    auth_provider = session.get('auth_provider', 'unknown')
    
    return render_template(
        'profile.html',
        user_info=user_info,
        id_token=id_token,
        auth_provider=auth_provider,
    )


@app.route('/logout')
def logout():
    provider = session.get('auth_provider', default_provider)
    id_token = session.get('id_token')
    session.clear()

    metadata = provider_metadata.get(provider, {})
    end_session_endpoint = metadata.get('end_session_endpoint')
    if end_session_endpoint:
        params = {
            'post_logout_redirect_uri': url_for('index', _external=True)
        }
        if id_token:
            params['id_token_hint'] = id_token

        return redirect(f"{end_session_endpoint}?{urlencode(params)}")

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)