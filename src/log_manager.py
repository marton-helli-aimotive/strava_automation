import os
import json

LOG_DIR = "data/logs"

class LogManager:
    def __init__(self):
        os.makedirs(LOG_DIR, exist_ok=True)

    def _get_path(self, year, month):
        year_dir = os.path.join(LOG_DIR, str(year))
        os.makedirs(year_dir, exist_ok=True)
        return os.path.join(year_dir, f"{month:02d}.json")

    def upsert_log(self, year, month, analysis_data):
        path = self._get_path(year, month)
        
        # Merge if exists
        if os.path.exists(path):
            with open(path, 'r') as f:
                existing_data = json.load(f)
            
            # Simple merge: new data overwrites existing keys
            existing_data.update(analysis_data)
            analysis_data = existing_data

        with open(path, 'w') as f:
            json.dump(analysis_data, f, indent=4)

    def get_log(self, year, month):
        path = self._get_path(year, month)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return None

    def list_logs(self):
        logs = []
        if not os.path.exists(LOG_DIR):
            return logs
            
        for year in os.listdir(LOG_DIR):
            year_path = os.path.join(LOG_DIR, year)
            if os.path.isdir(year_path):
                for month_file in os.listdir(year_path):
                    if month_file.endswith(".json"):
                        month = int(month_file.replace(".json", ""))
                        logs.append({
                            'year': int(year),
                            'month': month,
                            'path': os.path.join(year_path, month_file)
                        })
        return sorted(logs, key=lambda x: (x['year'], x['month']), reverse=True)
