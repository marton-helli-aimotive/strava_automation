import numpy as np
from sklearn.cluster import DBSCAN
from geopy.distance import geodesic

class LocationAnalyzer:
    def __init__(self, eps_meters=200, min_samples=2):
        self.eps_km = eps_meters / 1000.0
        self.min_samples = min_samples

    def _robust_latlng(self, latlng):
        if latlng is None:
            return None
        try:
            # Try subscripting
            return [float(latlng[0]), float(latlng[1])]
        except (TypeError, KeyError, IndexError):
            try:
                # Try attributes
                lat = getattr(latlng, 'lat', None)
                lon = getattr(latlng, 'lon', getattr(latlng, 'lng', None))
                if lat is not None and lon is not None:
                    return [float(lat), float(lon)]
            except (AttributeError, TypeError):
                pass
        return None

    def estimate_locations(self, activities):
        if not activities:
            return None, None

        # 1. Collect all points for clustering
        point_data = [] # List of (coords, activity, is_start)
        for activity in activities:
            start = self._robust_latlng(activity.start_latlng)
            if start:
                point_data.append({'coords': start, 'activity': activity, 'is_start': True})
            end = self._robust_latlng(activity.end_latlng)
            if end:
                point_data.append({'coords': end, 'activity': activity, 'is_start': False})

        if not point_data:
            return None, None

        coords = np.array([p['coords'] for p in point_data])
        coords_rad = np.radians(coords)
        
        # DBSCAN clustering
        kms_per_radian = 6371.0088
        epsilon = self.eps_km / kms_per_radian
        db = DBSCAN(eps=epsilon, min_samples=self.min_samples, metric='haversine', algorithm='ball_tree').fit(coords_rad)
        labels = db.labels_

        # 2. Group by day and count cluster roles
        from collections import defaultdict
        
        # Map each point_data index to its cluster label
        clusters = {}
        for i, label in enumerate(labels):
            if label != -1:
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(point_data[i])

        if not clusters:
            return None, None

        # Sort activities by date
        sorted_activities = sorted(activities, key=lambda a: a.start_date)
        by_day = defaultdict(list)
        for a in sorted_activities:
            day = a.start_date.date()
            by_day[day].append(a)

        # Count how often each cluster is a "home" candidate (start of first ride or end of last ride)
        # and "work" candidate (mid-day point)
        home_scores = defaultdict(int)
        overall_counts = defaultdict(int)
        
        # Helper to get cluster for a coordinate
        def get_cluster(latlng):
            if latlng is None: return -1
            p = self._robust_latlng(latlng)
            # Find closest cluster center
            best_dist = float('inf')
            best_label = -1
            for label, data_list in clusters.items():
                center = np.mean([pl['coords'] for pl in data_list], axis=0)
                center_coords = (float(center[0]), float(center[1]))
                dist = geodesic(p, center_coords).meters
                if dist < 300 and dist < best_dist:
                    best_dist = dist
                    best_label = label
            return best_label

        for day, day_activities in by_day.items():
            first_ride = day_activities[0]
            last_ride = day_activities[-1]
            
            c_start = get_cluster(first_ride.start_latlng)
            c_end = get_cluster(last_ride.end_latlng)
            
            if c_start != -1: home_scores[c_start] += 1
            if c_end != -1: home_scores[c_end] += 1
            
            for a in day_activities:
                s = get_cluster(a.start_latlng)
                e = get_cluster(a.end_latlng)
                if s != -1: overall_counts[s] += 1
                if e != -1: overall_counts[e] += 1

        # Calculate cluster centers
        cluster_centers = {}
        for label, data_list in clusters.items():
            cluster_centers[label] = np.mean([p['coords'] for p in data_list], axis=0).tolist()

        # Decide Home: Highest home_score
        if not home_scores:
            # Fallback to overall counts if no daily patterns found
            sorted_by_count = sorted(overall_counts.items(), key=lambda x: x[1], reverse=True)
            home_label = sorted_by_count[0][0]
            work_label = sorted_by_count[1][0] if len(sorted_by_count) > 1 else -1
        else:
            sorted_home = sorted(home_scores.items(), key=lambda x: x[1], reverse=True)
            home_label = sorted_home[0][0]
            
            # Decide Work: Highest overall count among remaining clusters
            other_clusters = [(l, c) for l, c in overall_counts.items() if l != home_label]
            if other_clusters:
                sorted_work = sorted(other_clusters, key=lambda x: x[1], reverse=True)
                work_label = sorted_work[0][0]
            else:
                work_label = -1

        home = cluster_centers[home_label]
        work = cluster_centers[work_label] if work_label != -1 else None

        return home, work

    def is_near(self, point1, point2, radius_meters=300):
        p1 = self._robust_latlng(point1)
        p2 = self._robust_latlng(point2)
        if p1 is None or p2 is None:
            return False
        return geodesic(p1, p2).meters <= radius_meters
