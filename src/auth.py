import os
import json
import time
from stravalib.client import Client
from dotenv import load_dotenv

load_dotenv()

TOKEN_FILE = "data/tokens.json"
CONFIG_FILE = "data/config.json"

class StravaAuth:
    def __init__(self):
        self.load_config()
        self.client = Client()

    def load_config(self):
        # Default from env
        self.client_id = os.getenv("STRAVA_CLIENT_ID")
        self.client_secret = os.getenv("STRAVA_CLIENT_SECRET")
        self.redirect_uri = os.getenv("STRAVA_REDIRECT_URI", "http://localhost:8501")

        # Overlay with local config if exists
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                self.client_id = config.get("client_id", self.client_id)
                self.client_secret = config.get("client_secret", self.client_secret)
                self.redirect_uri = config.get("redirect_uri", self.redirect_uri)

    def save_config(self, client_id, client_secret, redirect_uri=None):
        self.client_id = client_id
        self.client_secret = client_secret
        if redirect_uri:
            self.redirect_uri = redirect_uri
        
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump({
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri
            }, f)

    def get_auth_url(self):
        return self.client.authorization_url(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=['read', 'profile:read_all', 'activity:read', 'activity:read_all', 'activity:write']
        )

    def exchange_code(self, code):
        token_response = self.client.exchange_code_for_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            code=code
        )
        self.save_tokens(token_response)
        return token_response

    def save_tokens(self, token_response):
        tokens = {
            'access_token': token_response['access_token'],
            'refresh_token': token_response['refresh_token'],
            'expires_at': token_response['expires_at']
        }
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, 'w') as f:
            json.dump(tokens, f)

    def load_tokens(self):
        if not os.path.exists(TOKEN_FILE):
            return None
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)

    def get_client(self):
        tokens = self.load_tokens()
        if not tokens:
            return None

        if time.time() > tokens['expires_at']:
            try:
                refresh_response = self.client.refresh_access_token(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    refresh_token=tokens['refresh_token']
                )
                self.save_tokens(refresh_response)
                tokens = refresh_response
            except Exception as e:
                print(f"Error refreshing token: {e}")
                return None

        self.client.access_token = tokens['access_token']
        return self.client
