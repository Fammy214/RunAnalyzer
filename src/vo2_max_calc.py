"""
depreceated for utils file for modularity

from pathlib import Path
from statistics import mean
import sqlite3
from utils.strava_db import DB_PATH


DB_PATH = Path("data") / "strava.db"
BASELINE_FILE = Path("data") / "baseline.json"



def parse_vo2_max(runs: list[dict]) -> float:
    return mean(r["vo2_max"] for r in runs if r["vo2_max"] is not None)

def calculate_vo2_max(distance_m: float, avg_speed:float, hr_max:float, hr_rest:float, hr_avg:float) -> float:
    if hr_max == hr_avg:
        return 0.0
    
    speed_kmh = avg_speed
    heart_rate_factor = (hr_max - hr_rest) / (hr_max - hr_avg)
    vo2_max = 15.3 * heart_rate_factor * speed_kmh

    return round(vo2_max, 2)
    
"""