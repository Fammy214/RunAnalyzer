import sqlite3
from pathlib import Path
from datetime import datetime
import requests
import json

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "strava.db"

def create_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS activities (id INTEGER PRIMARY KEY, name TEXT, distance REAL, moving_time INTEGER, elapsed_time INTEGER, total_elevation_gain REAL, start_date TEXT, average_hr REAL, max_hr REAL, average_speed REAL, max_speed REAL, calories REAL)")
    conn.close()


def save_activities(parsed_activities):
    conn = sqlite3.connect(DB_PATH)

    flattened = [
    (
        a['id'],
        a['name'],
        a['distance'],
        a['moving_time'],
        a['elapsed_time'],
        a['total_elevation_gain'],
        a['start_date'].isoformat() if isinstance(a['start_date'], datetime) else a['start_date'],
        a.get('average_hr'),
        a.get('max_hr'),
        a.get('average_speed'),
        a.get('max_speed'),
        a.get('calories'),
    )
    for a in parsed_activities
    ]

    conn.executemany("""INSERT OR IGNORE INTO activities
        (id, name, distance, moving_time, elapsed_time,
         total_elevation_gain, start_date, average_hr,
         max_hr, average_speed, max_speed, calories)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", flattened)
    conn.commit()
    conn.close()

def get_activities(token, after=None):
    headers = {'Authorization': f'Bearer {token}'}
    params = {'per_page': 200, 'page': 1}
    if after:
        params['after'] = int(after.timestamp())

    all_activities = []
    while True:
        response = requests.get(
            'https://www.strava.com/api/v3/athlete/activities',
            headers=headers,
            params=params
        )
        response.raise_for_status()
        page_data = json.loads(response.text)
        if not page_data:
            break
        all_activities.extend(page_data)
        params['page'] += 1
    return all_activities

def get_new_activities(token):
    # Step 1: Get existing IDs from the DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM activities")
    existing_ids = {row[0] for row in cursor.fetchall()}
    conn.close()

    # Step 2: Fetch all activities from Strava (paginated)
    new_activities = []
    page = 1
    headers = {'Authorization': f'Bearer {token}'}
    params = {'per_page': 200, 'page': page}

    while True:
        response = requests.get(
            'https://www.strava.com/api/v3/athlete/activities',
            headers=headers,
            params=params
        )
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break

        # Step 3: Filter only new activities
        for activity in batch:
            if activity['id'] not in existing_ids:
                new_activities.append(activity)

        page += 1
        params['page'] = page

    return new_activities

