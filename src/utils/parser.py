from datetime import datetime
from utils.vo2 import calculate_vo2_max

def parse_activity(activity):
    try:
        return {
            'id': activity['id'],
            'type': activity['type'],
            'name': activity['name'],
            'distance': activity['distance'],
            'moving_time': activity['moving_time'],
            'elapsed_time': activity['elapsed_time'],
            'total_elevation_gain': activity['total_elevation_gain'],
            'start_date': datetime.fromisoformat(activity['start_date']),
            'average_hr': activity.get('average_heartrate'),
            'max_hr': activity.get('max_heartrate'),
            'average_speed': activity.get('average_speed'),
            'max_speed': activity.get('max_speed'),
            'calories': activity.get('calories', None),
            'vo2_max': calculate_vo2_max(
                avg_speed=activity.get('average_speed'),
                hr_max=activity.get('max_heartrate'),
                hr_rest=41,
                hr_avg=activity.get('average_heartrate')
            )

        }
    except Exception as e:
        print(f"Error parsing activity {activity['id']}: {e}")
        return None
    

