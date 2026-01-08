import datetime
from .auth import StravaAuth

class StravaClient:
    def __init__(self):
        self.auth = StravaAuth()
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            self._client = self.auth.get_client()
        return self._client

    def is_authenticated(self):
        return self.client is not None

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
        
        # Note: visibility might need a specific handling if not directly supported by update_activity in stravalib version
        # But usually it is. If not, we might need a raw request.
        
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
