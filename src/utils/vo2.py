from statistics import mean
from utils.hr import get_baseline_hr

def parse_vo2_max(runs: list[dict]) -> float:
    valid = [r["vo2_max"] for r in runs if "vo2_max" in r and r["vo2_max"] is not None]
    return round(mean(valid), 2) if valid else 0.0

def calculate_vo2_max(avg_speed: float, hr_max: float, hr_rest: float, hr_avg: float) -> float:
    if hr_max == hr_avg or not all(isinstance(x, (int, float)) for x in [avg_speed, hr_max, hr_rest, hr_avg]):
        return 0.0
    
    speed_kmh = avg_speed * 3.6
    
    heart_rate_factor = (hr_max - hr_rest) / (hr_max - hr_avg)
    vo2_max = 15.3 * heart_rate_factor * speed_kmh
    return round(min(max(vo2_max, 2), 95), 2)