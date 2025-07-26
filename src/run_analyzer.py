import json
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import List, Dict, Any
from tqdm import tqdm_gui
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
from utils.strava_db import DB_PATH
from utils.load_runs_by_date import load_runs_by_date, load_runs_from_db, is_valid_run
from utils.vo2 import calculate_vo2_max, parse_vo2_max

DATA_DIR = Path("data").resolve().parents[1] / "data"
BASELINE_FILE = DATA_DIR / "baseline.json"
def save_baseline(baseline: dict):
    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, indent=2)

def load_baseline() -> dict:
    if BASELINE_FILE.exists():
        with open(BASELINE_FILE) as f:
            return json.load(f)
    return None



def compute_baseline(runs: list[dict]) -> dict:
    runs = [r for r in runs if is_valid_run(r)]

    for run in runs:
        resting_hr = run.get("resting_hr", 41.0)
        max_hr = run.get("max_hr", 0)
        average_hr = run.get("average_hr", 0)
        if None in (max_hr, average_hr, resting_hr):
            run["vo2_max"] = None
        else:
            run["vo2_max"] = calculate_vo2_max(run["average_speed"], max_hr, resting_hr, average_hr)

    return {
        "avg_distance": mean(r["distance"] for r in runs),
        "avg_moving_time": mean(r["moving_time"] for r in runs),
        "avg_speed": mean(r["average_speed"] for r in runs),
        "avg_heart_rate": mean(r["average_hr"] for r in runs if r.get("average_hr") is not None),
        "avg_max_hr": mean(r["max_hr"] for r in runs if r.get("max_hr") is not None),
        "avg_total_elevation_gain": mean(r["total_elevation_gain"] for r in runs),
        "avg_pace_min_per_km": mean(r["moving_time"] / (r["distance"] / 1000) for r in runs if r["distance"] > 0),
        "avg_elevation_gain_per_km": mean(r["total_elevation_gain"] / (r["distance"] / 1000) for r in runs if r["distance"] > 0),
        "avg_elevation_gain_per_min": mean(r["total_elevation_gain"] / (r["moving_time"] / 60) for r in runs if r["moving_time"] > 0),   
        "avg_elevation_gain_per_moving_time": mean(r["total_elevation_gain"] / r["moving_time"] for r in runs if r["moving_time"] > 0),
        "avg_vo2_max": parse_vo2_max(runs)
    }

def analyze_run(new_run: dict, baseline: dict) -> str:
    pace = new_run["moving_time"] / (new_run["distance"] / 1000)  # seconds per km
    pace_min = int(pace // 60)
    pace_sec = int(pace % 60)

    hr_max = new_run.get("max_hr", 0)
    hr_rest = new_run.get("resting_hr", 0)
    hr_avg = new_run.get("average_hr", 0)

    if isinstance(hr_max, (int, float)) and isinstance(hr_rest, (int, float)) and isinstance(hr_avg, (int, float)):
        vo2_max = calculate_vo2_max(new_run["average_speed"], hr_max, hr_rest, hr_avg)
        new_run["vo2_max"] = vo2_max
    else:
        vo2_max = "N/A"
        new_run["vo2_max"] = None

    summary = f"""
    New Run: {new_run["name"]}
    Date: {new_run["start_date"]}
    Distance: {new_run["distance"] / 1000:.2f} km
    Moving Time: {new_run["moving_time"] // 60:.0f} min
    Average Speed: {new_run["average_speed"]*3.6:.2f} km/h
    Average Heart Rate: {new_run.get("average_hr", 0)} bpm
    Max Heart Rate: {new_run.get("max_hr", 0)} bpm
    Average Pace: {pace_min}:{pace_sec:02d} min/km
    Total Elevation Gain: {new_run.get("total_elevation_gain", "N/A")} m
    Compared to baseline:
      Δ Average Heart Rate: {new_run.get("average_hr", "N/A") - baseline["avg_heart_rate"]:.2f} bpm ({(new_run.get("average_hr", "N/A") - baseline["avg_heart_rate"]) / baseline["avg_heart_rate"] * 100:.2f}%)
      Δ Moving Time: {(new_run["moving_time"] - baseline["avg_moving_time"]) / 60:.2f} min ({(new_run["moving_time"] - baseline["avg_moving_time"]) / baseline["avg_moving_time"] * 100:.2f}%)
      Δ Distance: {new_run["distance"] - baseline["avg_distance"]:.2f} m ({(new_run["distance"] - baseline["avg_distance"]) / baseline["avg_distance"] * 100:.2f}%)
      Δ Speed: {new_run["average_speed"] - baseline["avg_speed"]:.2f} km/h ({(new_run["average_speed"] - baseline["avg_speed"]) / baseline["avg_speed"] * 100:.2f}%)
      Δ Total Elevation Gain: {new_run["total_elevation_gain"] - baseline["avg_total_elevation_gain"]:.2f} m ({(new_run["total_elevation_gain"] - baseline["avg_total_elevation_gain"]) / baseline["avg_total_elevation_gain"] * 100:.2f}%)
      Δ Elevation Gain per km: {new_run["total_elevation_gain"] / (new_run["distance"] / 1000) - baseline["avg_elevation_gain_per_km"]:.2f} m/km ({(new_run["total_elevation_gain"] / (new_run["distance"] / 1000) - baseline["avg_elevation_gain_per_km"]) / baseline["avg_elevation_gain_per_km"] * 100:.2f}%)
      Δ Elevation Gain per min: {new_run["total_elevation_gain"] / (new_run["moving_time"] / 60) - baseline["avg_elevation_gain_per_min"]:.2f} m/min ({(new_run["total_elevation_gain"] / (new_run["moving_time"] / 60) - baseline["avg_elevation_gain_per_min"]) / baseline["avg_elevation_gain_per_min"] * 100:.2f}%)
      Δ Elevation Gain per moving time: {new_run["total_elevation_gain"] / new_run["moving_time"] - baseline["avg_elevation_gain_per_moving_time"]:.2f} m/min ({(new_run["total_elevation_gain"] / new_run["moving_time"] - baseline["avg_elevation_gain_per_moving_time"]) / baseline["avg_elevation_gain_per_moving_time"] * 100:.2f}%)
      Δ VO2 Max: {new_run.get("vo2_max", "N/A") - baseline["avg_vo2_max"]:.2f} ({(new_run.get("vo2_max", "N/A") - baseline["avg_vo2_max"]) / baseline["avg_vo2_max"] * 100:.2f}%)
    """
    return summary




def main():
    all_runs = load_runs_from_db()

    date_input = input("Enter a date (YYYY-MM-DD) or 'today' to analyze today's runs or 'refresh' to refresh the baseline: ").strip().lower()
    if date_input == "refresh":
        print("Refreshing baseline...")
        print("average_hr values:", [r.get("average_hr") for r in all_runs])
        print("max_hr values:", [r.get("max_hr") for r in all_runs])
        print("resting_hr values:", [r.get("resting_hr") for r in all_runs])
        print("average_speed values:", [r.get("average_speed") for r in all_runs])
        print("total_elevation_gain values:", [r.get("total_elevation_gain") for r in all_runs])
        print("moving_time values:", [r.get("moving_time") for r in all_runs])
        print("distance values:", [r.get("distance") for r in all_runs])
        print("vo2_max values:", [r.get("vo2_max") for r in all_runs])
        baseline = compute_baseline(all_runs)
        save_baseline(baseline)
        print("Baseline refreshed successfully.")
        return

    if date_input == "today" or date_input == "":
        target_date = datetime.now()
    else:
        try:
            target_date = datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            return

        today_str = target_date.strftime("%Y-%m-%d")
        today_runs = load_runs_by_date(today_str)

        if not today_runs:
            print(f"No runs found for {today_str}")
            return
        
        baseline = load_baseline()
        if not baseline:
            print("No baseline found. Computing baseline...")
            baseline = compute_baseline(all_runs)
            save_baseline(baseline)

        for run in today_runs:
            print(analyze_run(run, baseline))

if __name__ == "__main__":
    main()