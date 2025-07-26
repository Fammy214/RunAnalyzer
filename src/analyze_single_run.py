import json
from pathlib import Path
from datetime import datetime
from run_analyzer import analyze_run, load_baseline, compute_baseline, load_past_runs, is_valid_run

DATA_DIR = Path("data")
RAW_FILE = DATA_DIR / "strava_2025-07-11.json"
ANALYZED_FILE = DATA_DIR / "strava_analyzed.json"

# Prompt user
target_id_input = input("Enter the Strava activity ID: ")
target_id = int(target_id_input)

# Load raw data
with open(RAW_FILE) as f:
    activities = json.load(f)

run = next((a for a in activities if a["id"] == target_id), None)
if not run:
    print(f"Run with ID {target_id} not found.")
    exit(1)

# Load or compute baseline
baseline = load_baseline()
if not baseline:
    print("No baseline found. Computing baseline...")
    all_runs = load_past_runs()
    baseline = compute_baseline(all_runs)

# Analyze run
summary = analyze_run(run, baseline)

# Format and append to master analyzed file
entry = {
    "id": run["id"],
    "name": run["name"],
    "date": run["start_date"],
    "summary": summary
}

if ANALYZED_FILE.exists():
    with open(ANALYZED_FILE) as f:
        all_entries = json.load(f)
else:
    all_entries = []

# Avoid duplicates
all_entries = [e for e in all_entries if e["id"] != run["id"]]
all_entries.append(entry)

with open(ANALYZED_FILE, "w") as f:
    json.dump(all_entries, f, indent=2)

print(f"Run {run['id']} analysis added to strava_analyzed.json.")
