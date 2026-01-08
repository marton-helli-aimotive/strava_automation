import datetime
import streamlit as st
from .auth import StravaAuth


class StravaClient:
    """Strava API client wrapper with session-aware authentication."""
    
    def __init__(self):
        self._auth = None
    
    @property
    def auth(self):
        """Lazy-load auth to ensure session state is available."""
        if self._auth is None:
            self._auth = StravaAuth()
        return self._auth
    
    @property
    def client(self):
        """Get the authenticated Strava client."""
        return self.auth.get_client()

    def is_authenticated(self):
        return self.auth.is_authenticated()

    def disconnect(self):
        """Disconnect the user by clearing their tokens."""
        self.auth.clear_tokens()
        self._auth = None  # Reset auth instance

    def fetch_rides(self, year, month):
        if not self.client:
            return []

        # Calculate after and before timestamps
        after = datetime.datetime(year, month, 1)
        if month == 12:
            before = datetime.datetime(year + 1, 1, 1)
        else:
            before = datetime.datetime(year, month + 1, 1)

        activities = self.client.get_activities(after=after, before=before)
        rides = [a for a in activities if a.type == 'Ride']
        return rides

    def update_activity(self, activity_id, commute=None, trainer=None, hide_from_home=None, visibility=None):
        if not self.client:
            return False
        
        update_params = {}
        if commute is not None: update_params['commute'] = commute
        if trainer is not None: update_params['trainer'] = trainer
        if hide_from_home is not None: update_params['hide_from_home'] = hide_from_home
        
        try:
            self.client.update_activity(activity_id, **update_params)
            return True
        except Exception as e:
            print(f"Error updating activity {activity_id}: {e}")
            return False

    def get_athlete(self):
        if not self.client:
            return None
        return self.client.get_athlete()
