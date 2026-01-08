import os
import time
import streamlit as st
from stravalib.client import Client
from dotenv import load_dotenv

load_dotenv()

# Cloud-ready redirect URI
DEFAULT_REDIRECT_URI = "https://stravaautomation.streamlit.app"


class StravaAuth:
    """OAuth2 authentication for Strava with session-based token storage (multi-user support)."""
    
    def __init__(self):
        # Load credentials from environment/secrets
        self.client_id = os.getenv("STRAVA_CLIENT_ID") or st.secrets.get("STRAVA_CLIENT_ID")
        self.client_secret = os.getenv("STRAVA_CLIENT_SECRET") or st.secrets.get("STRAVA_CLIENT_SECRET")
        self.redirect_uri = os.getenv("STRAVA_REDIRECT_URI") or st.secrets.get("STRAVA_REDIRECT_URI", DEFAULT_REDIRECT_URI)
        self.client = Client()

    def is_configured(self):
        """Check if API credentials are configured."""
        return bool(self.client_id and self.client_secret)

    def get_auth_url(self):
        """Generate the Strava OAuth authorization URL."""
        return self.client.authorization_url(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=['read', 'profile:read_all', 'activity:read', 'activity:read_all', 'activity:write']
        )

    def exchange_code(self, code):
        """Exchange authorization code for access tokens and store in session."""
        token_response = self.client.exchange_code_for_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            code=code
        )
        self._save_tokens_to_session(token_response)
        return token_response

    def _save_tokens_to_session(self, token_response):
        """Store tokens in Streamlit session state (per-user)."""
        st.session_state['strava_tokens'] = {
            'access_token': token_response['access_token'],
            'refresh_token': token_response['refresh_token'],
            'expires_at': token_response['expires_at']
        }

    def _get_tokens_from_session(self):
        """Retrieve tokens from session state."""
        return st.session_state.get('strava_tokens')

    def clear_tokens(self):
        """Clear stored tokens (disconnect user)."""
        if 'strava_tokens' in st.session_state:
            del st.session_state['strava_tokens']

    def get_client(self):
        """Get an authenticated Strava client, refreshing tokens if needed."""
        tokens = self._get_tokens_from_session()
        if not tokens:
            return None

        # Check if token is expired and refresh if needed
        if time.time() > tokens['expires_at']:
            try:
                refresh_response = self.client.refresh_access_token(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    refresh_token=tokens['refresh_token']
                )
                self._save_tokens_to_session(refresh_response)
                tokens = refresh_response
            except Exception as e:
                print(f"Error refreshing token: {e}")
                self.clear_tokens()
                return None

        self.client.access_token = tokens['access_token']
        return self.client

    def is_authenticated(self):
        """Check if the user is currently authenticated."""
        return self.get_client() is not None
