"""Standalone COS30019 A2B traffic-flow-to-travel-time calculation.

Q = -1.4648375*v**2 + 93.75*v. Q: vehicles/hour; v: km/hour.
Uses high-speed root with 60 km/h cap and 30 s per controlled intersection.
"""
from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Iterable, Mapping, Sequence

QUADRATIC_A = 1.4648375
QUADRATIC_B = 93.75
SPEED_LIMIT_KMH = 60.0
MAX_SUPPORTED_FLOW_VPH = 1500.0
INTERSECTION_DELAY_SECONDS = 30.0


def _finite_nonnegative(value: float, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f"{label} must be a finite, non-negative number")
    number = float(value)
    if not isfinite(number) or number < 0:
        raise ValueError(f"{label} must be finite and non-negative")
    return number


def hourly_flow_from_quarters(counts: Sequence[float]) -> float:
    """Sum four consecutive non-overlapping 15-minute vehicle counts."""
    if len(counts) != 4:
        raise ValueError("Exactly four 15-minute vehicle counts are required")
    return sum(_finite_nonnegative(v, f"counts[{i}]") for i, v in enumerate(counts))


def flow_to_speed_kmh(hourly_flow: float) -> float:
    """Find the higher-speed root and apply the road speed limit."""
    flow = _finite_nonnegative(hourly_flow, "hourly_flow")
    if flow > MAX_SUPPORTED_FLOW_VPH:
        raise ValueError("Flow above 1500 vehicles/hour is outside the supported model")
    discriminant = QUADRATIC_B**2 - 4 * QUADRATIC_A * flow
    if discriminant < 0:
        raise ValueError("Flow gives no real-valued speed")
    speed = (QUADRATIC_B + sqrt(discriminant)) / (2 * QUADRATIC_A)
    return min(SPEED_LIMIT_KMH, speed)


def calculate_travel_time_minutes(
    hourly_flow: float, distance_km: float, controlled_intersections: int = 1,
) -> float:
    """Return edge travel time, including 30-second intersection delays."""
    distance = _finite_nonnegative(distance_km, "distance_km")
    if distance == 0:
        raise ValueError("distance_km must be greater than zero")
    if (isinstance(controlled_intersections, bool)
        or not isinstance(controlled_intersections, int)
        or controlled_intersections < 0):
        raise ValueError("controlled_intersections must be a non-negative integer")
    speed = flow_to_speed_kmh(hourly_flow)
    return 60.0 * distance / speed + (
        controlled_intersections * INTERSECTION_DELAY_SECONDS / 60.0
    )


def travel_time_for_integration(distance_km: float, hourly_traffic: float) -> float:
    """Matches existing TrafficRouteProblem's (distance, flow) function signature.

    Does NOT activate this calculation in teammates' k_shortest_routes().
    """
    return calculate_travel_time_minutes(hourly_traffic, distance_km)


@dataclass(frozen=True)
class EdgeTravelTime:
    origin_scats: int
    destination_scats: int
    distance_km: float
    traffic_site: int
    hourly_flow_vph: float
    speed_kmh: float
    travel_time_minutes: float


def weight_road_edges(
    road_edges: Iterable[tuple[int, int, float]],
    predicted_hourly_flows: Mapping[int, float],
    controlled_intersections: int = 1,
    *,
    flow_site: str = "origin",
) -> list[EdgeTravelTime]:
    """Weight directed edges using actual SCATS IDs and site-specific predictions.

    Origin vs destination flow is unresolved across the assignment documents:
    default='origin' follows detailed handout, 'destination' is configurable.
    """
    if flow_site not in ("origin", "destination"):
        raise ValueError("flow_site must be 'origin' or 'destination'")
    results = []
    for origin, destination, distance in road_edges:
        site = origin if flow_site == "origin" else destination
        if site not in predicted_hourly_flows:
            raise KeyError(f"Missing hourly prediction for SCATS site {site}")
        flow = predicted_hourly_flows[site]
        results.append(EdgeTravelTime(
            origin_scats=origin,
            destination_scats=destination,
            distance_km=distance,
            traffic_site=site,
            hourly_flow_vph=float(flow),
            speed_kmh=flow_to_speed_kmh(flow),
            travel_time_minutes=calculate_travel_time_minutes(
                flow, distance, controlled_intersections
            ),
        ))
    return results
