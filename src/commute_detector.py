from .location_analyzer import LocationAnalyzer

class CommuteDetector:
    def __init__(self, home, work, radius_meters=300, max_time_gap_hours=2):
        self.home = home
        self.work = work
        self.radius_meters = radius_meters
        self.max_time_gap_hours = max_time_gap_hours
        self.analyzer = LocationAnalyzer()

    def is_commute(self, activity):
        if not activity.start_latlng or not activity.end_latlng:
            return False

        starts_at_home = self.analyzer.is_near(activity.start_latlng, self.home, self.radius_meters)
        ends_at_work = self.analyzer.is_near(activity.end_latlng, self.work, self.radius_meters)
        
        starts_at_work = self.analyzer.is_near(activity.start_latlng, self.work, self.radius_meters)
        ends_at_home = self.analyzer.is_near(activity.end_latlng, self.home, self.radius_meters)

        return (starts_at_home and ends_at_work) or (starts_at_work and ends_at_home)

    def detect_commutes(self, activities):
        commutes = []
        regular_rides = []
        
        for activity in activities:
            if self.is_commute(activity):
                commutes.append(activity)
            else:
                regular_rides.append(activity)

        # Chained activity detection (Bonus)
        chained_commutes, remaining_rides = self.detect_chained_commutes(regular_rides, self.max_time_gap_hours)
        commutes.extend(chained_commutes)
        
        return commutes

    def detect_chained_commutes(self, rides, max_time_gap_hours=None):
        if max_time_gap_hours is None:
            max_time_gap_hours = self.max_time_gap_hours
        # Sort rides by start time
        sorted_rides = sorted(rides, key=lambda r: r.start_date)
        
        chained_groups = []
        current_chain = []
        
        for ride in sorted_rides:
            if not current_chain:
                current_chain.append(ride)
                continue
            
            last_ride = current_chain[-1]
            # Strava activities don't always have end_date, so we calculate it
            # elapsed_time might be a stravalib Duration object, timedelta, or float
            from datetime import timedelta
            def get_seconds(obj):
                if hasattr(obj, 'total_seconds') and callable(obj.total_seconds):
                    return float(obj.total_seconds())
                try:
                    return float(obj)
                except:
                    # Some versions might have a 'seconds' attribute
                    return float(getattr(obj, 'seconds', 0))

            elapsed = timedelta(seconds=get_seconds(last_ride.elapsed_time))
            last_end_date = last_ride.start_date + elapsed
            
            time_gap = (ride.start_date - last_end_date).total_seconds() / 3600.0
            
            # Check if geographically and temporally chained
            is_same_spot = self.analyzer.is_near(last_ride.end_latlng, ride.start_latlng, self.radius_meters)
            
            if time_gap < max_time_gap_hours and is_same_spot:
                current_chain.append(ride)
            else:
                # Check if the finished chain matches Home -> Work or Work -> Home
                if len(current_chain) > 1:
                    if self.is_chain_commute(current_chain):
                        chained_groups.append(current_chain)
                
                current_chain = [ride]
        
        # Check last chain
        if len(current_chain) > 1 and self.is_chain_commute(current_chain):
            chained_groups.append(current_chain)

        # Flatten chained groups into single "virtual" commute objects or just mark them
        # For simplicity, we'll return them as a list of lists of activities
        # And we need to filter out the rides that are now part of a chain from the "remaining"
        
        used_ids = {r.id for group in chained_groups for r in group}
        remaining = [r for r in rides if r.id not in used_ids]
        
        # Instead of returning list of lists, let's treat each group as a set of activities
        return chained_groups, remaining

    def is_chain_commute(self, chain):
        first = chain[0]
        last = chain[-1]
        
        starts_at_home = self.analyzer.is_near(first.start_latlng, self.home, self.radius_meters)
        ends_at_work = self.analyzer.is_near(last.end_latlng, self.work, self.radius_meters)
        
        starts_at_work = self.analyzer.is_near(first.start_latlng, self.work, self.radius_meters)
        ends_at_home = self.analyzer.is_near(last.end_latlng, self.home, self.radius_meters)
        
        return (starts_at_home and ends_at_work) or (starts_at_work and ends_at_home)
