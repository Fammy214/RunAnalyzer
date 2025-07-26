import requests     
import yaml 
import json
import argparse
from utils.save_json import save_json, load_json
from datetime import datetime, timedelta
from pathlib import Path
from utils.parser import parse_activity
from utils.strava_db import create_db, save_activities, DB_PATH, get_activities, get_new_activities


CONFIG_PATH = Path("config/strava.yaml").resolve().parents[2] / "config" / "strava.yaml"
DATA_DIR = Path("data").resolve().parents[1] / "data"

def load_config():
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    return config


def refresh_access_token(config):
    response = """ Replacing because was hardcoded for testing"""
    data = response.json()
    print("Token response:", data)
    return data['access_token']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Import full activity history")
    args = parser.parse_args()

    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True)

    if not DB_PATH.exists():
        print("Creating new database...")
        create_db()
    else:
        print("Database already exists.")

    config = load_config()
    token = refresh_access_token(config)

    if args.all:
        print("Importing full history...")
        activities = get_activities(token)
    else:
        print("Importing only new activities...")
        activities = get_new_activities(token)

    if activities:
        print(f"Found {len(activities)} new activities.")
        parsed = [parse_activity(a) for a in activities if parse_activity(a) is not None]
        save_activities(parsed)
    else:
        print("No new activities found.")



if __name__ == "__main__":
    main()