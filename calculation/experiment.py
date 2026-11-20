"""Reproducible illustrative formula-sensitivity experiment (not real traffic)."""
import csv
from pathlib import Path
from .travel_time import calculate_travel_time_minutes, flow_to_speed_kmh

FLOWS = (0, 300, 600, 900, 1200, 1500)
DISTANCE_KM = 2.0
INTERSECTIONS = 1


def main():
    output = Path(__file__).resolve().parent / "results" / "flow_sensitivity.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(("flow_vehicles_per_hour", "distance_km", "intersections",
                         "speed_kmh", "travel_time_minutes"))
        for q in FLOWS:
            writer.writerow((q, DISTANCE_KM, INTERSECTIONS,
                             round(flow_to_speed_kmh(q), 4),
                             round(calculate_travel_time_minutes(
                                 q, DISTANCE_KM, INTERSECTIONS), 4)))
    print(f"Wrote illustrative results to {output}")


if __name__ == "__main__":
    main()
