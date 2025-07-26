import sqlite3
from utils.strava_db import DB_PATH

def is_valid_run(run: dict) -> bool:
    return run.get("type") == "Run" and run.get("distance", 0) > 1000

def load_runs_from_db() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, distance, moving_time, elapsed_time, total_elevation_gain,
               start_date, average_hr, max_hr, average_speed, max_speed, calories
        FROM activities
    """)
    rows = cursor.fetchall()
    conn.close()
    runs = []
    for row in rows:
        run = {
            "id": row[0],
            "name": row[1],
            "distance": row[2],
            "moving_time": row[3],
            "elapsed_time": row[4],
            "total_elevation_gain": row[5],
            "start_date": row[6],
            "average_hr": row[7],
            "max_hr": row[8],
            "average_speed": row[9],
            "max_speed": row[10],
            "calories": row[11],
            "type": "Run"  # Needed for is_valid_run()
        }
        runs.append(run)
    return runs

def load_runs_by_date(date_str: str) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Match against just the YYYY-MM-DD portion of start_date
    cursor.execute("""
        SELECT id, name, distance, moving_time, elapsed_time, total_elevation_gain,
               start_date, average_hr, max_hr, average_speed, max_speed, calories
        FROM activities
        WHERE DATE(start_date) = ?
    """, (date_str,))
    
    rows = cursor.fetchall()
    conn.close()

    runs = []
    for row in rows:
        run = {
            "id": row[0],
            "name": row[1],
            "distance": row[2],
            "moving_time": row[3],
            "elapsed_time": row[4],
            "total_elevation_gain": row[5],
            "start_date": row[6],
            "average_hr": row[7],
            "max_hr": row[8],
            "average_speed": row[9],
            "max_speed": row[10],
            "calories": row[11],
            "type": "Run"  # For is_valid_run check
        }
        runs.append(run)

    return [r for r in runs if is_valid_run(r)]