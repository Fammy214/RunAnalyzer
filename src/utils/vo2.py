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
    
"""
replace with this equation

def vo2max_daniels_hr(pace_min_per_km, hr_avg, hr_max, hr_rest):
    if pace_min_per_km <= 0 or hr_max == hr_rest:
        return 0.0

    speed_m_per_min = 1000 / pace_min_per_km
    vo2_at_pace = 3.5 + 0.2 * speed_m_per_min

    hr_reserve = hr_max - hr_rest
    relative_effort = (hr_avg - hr_rest) / hr_reserve

    if relative_effort <= 0:
        return 0.0

    vo2max = vo2_at_pace / relative_effort
    return round(min(max(vo2max, 20), 95), 2)
"""