def get_baseline_hr(baseline: dict) -> tuple[float, float]:
    return (
        baseline.get("avg_max_hr", 180),
        baseline.get("resting_hr", 52)
    )
