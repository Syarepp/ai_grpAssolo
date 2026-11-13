"""Convert predicted SCATS traffic flow to travel-time edge weights.

Based on 'Traffic Flow to Travel Time Conversion v1.0.pdf':
    flow = -1.4648375 * speed**2 + 93.75 * speed

Use the higher-speed (under-capacity) branch, capped at 60 km/h.
For an edge A -> B, the detailed conversion handout specifies the flow
at the STARTING SCATS site A. Confirm with the tutor because the A2B
brief describes destination-site volume instead.

Inputs are predictions, not raw traffic counts; the same functions can
be exercised with historical observations for testing.
"""

from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Iterable, Mapping, Sequence

QUADRATIC_A = 1.4648375
QUADRATIC_B = 93.75
SPEED_LIMIT_KMH = 60.0
MAX_SUPPORTED_FLOW_VPH = 1500.0
INTERSECTION_DELAY_SECONDS = 30.0


def _nonnegative_finite(value: float, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    result = float(value)
    if not isfinite(result) or result < 0:
        raise ValueError(f"{label} must be finite and non-negative")
    return result


def hourly_flow_from_quarters(quarter_hour_counts: Sequence[float]) -> float:
    """Sum exactly four consecutive, non-overlapping 15-minute counts.

    These must be counts of vehicles per interval, not already-hourly rates.
    The caller is responsible for selecting the correct site's time window.
    """
    if len(quarter_hour_counts) != 4:
        raise ValueError("Exactly four 15-minute counts are required")
    return sum(
        _nonnegative_finite(value, f"quarter_hour_counts[{index}]")
        for index, value in enumerate(quarter_hour_counts)
    )


def flow_to_speed_kmh(flow_vehicles_per_hour: float) -> float:
    """Convert hourly flow to km/h on the lecturer's under-capacity branch."""
    flow = _nonnegative_finite(flow_vehicles_per_hour, "flow_vehicles_per_hour")
    if flow > MAX_SUPPORTED_FLOW_VPH:
        raise ValueError(
            "Flow exceeds the assignment's under-capacity range (0-1500 v/h)"
        )
    discriminant = QUADRATIC_B**2 - 4 * QUADRATIC_A * flow
    if discriminant < 0:
        raise ValueError("Traffic flow has no real speed on this curve")
    high_speed_root = (
        QUADRATIC_B + sqrt(discriminant)
    ) / (2 * QUADRATIC_A)
    return min(SPEED_LIMIT_KMH, high_speed_root)


def calculate_travel_time_minutes(
    flow_vehicles_per_hour: float,
    distance_km: float,
    controlled_intersections: int = 1,
) -> float:
    """Calculate edge travel time in minutes, including intersection delays.

    Default counts one controlled intersection for a directed edge. Set this
    to zero or another value according to the team's graph convention;
    do not double-count shared intersections across consecutive edges.
    """
    distance = _nonnegative_finite(distance_km, "distance_km")
    if distance <= 0:
        raise ValueError("distance_km must be positive")
    if (
        isinstance(controlled_intersections, bool)
        or not isinstance(controlled_intersections, int)
        or controlled_intersections < 0
    ):
        raise ValueError("controlled_intersections must be a non-negative integer")
    speed = flow_to_speed_kmh(flow_vehicles_per_hour)
    driving_minutes = (distance / speed) * 60
    delay_minutes = (
        controlled_intersections * INTERSECTION_DELAY_SECONDS / 60
    )
    return driving_minutes + delay_minutes


@dataclass(frozen=True)
class EdgeTravelTime:
    origin_scats: int
    destination_scats: int
    distance_km: float
    starting_site_flow_vph: float
    speed_kmh: float
    travel_time_minutes: float


def weight_road_edges(
    road_edges: Iterable[tuple[int, int, float]],
    predicted_hourly_flows: Mapping[int, float],
    controlled_intersections: int = 1,
) -> list[EdgeTravelTime]:
    """Assign travel times to directed edges using origin-site predicted flow.

    road_edges: (origin_scats_id, destination_scats_id, distance_km).
    predicted_hourly_flows: {scats_id: predicted_vehicles_per_hour}.
    Raises KeyError for missing site predictions rather than silently
    inventing traffic volumes. Returns results in the input edge order.
    """
    weighted = []
    for origin, destination, distance in road_edges:
        if origin not in predicted_hourly_flows:
            raise KeyError(f"Missing predicted flow for starting SCATS site {origin}")
        flow = predicted_hourly_flows[origin]
        weighted.append(
            EdgeTravelTime(
                origin_scats=origin,
                destination_scats=destination,
                distance_km=distance,
                starting_site_flow_vph=flow,
                speed_kmh=flow_to_speed_kmh(flow),
                travel_time_minutes=calculate_travel_time_minutes(
                    flow, distance, controlled_intersections
                ),
            )
        )
    return weighted
