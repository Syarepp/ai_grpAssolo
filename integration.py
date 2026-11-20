"""Traffic aware routing helpers for the TBRGS application.

The network file is CSV with columns:
    from_site,to_site,distance_km,traffic_site

Each row represents one directed road link. ``traffic_site`` defaults to the
destination site. The default traffic-to-time conversion is a clearly marked
placeholder; replace it with the formula supplied with the assignment.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from core.search import SearchProblem, SearchResult
from route_finding.uniform_cost_search import UniformCostSearch


@dataclass(frozen=True)
class RoadLink:
    from_site: int
    to_site: int
    distance_km: float
    traffic_site: int


def load_road_links(path: str | Path) -> list[RoadLink]:
    """Load directed links from a CSV file."""
    links: list[RoadLink] = []
    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        required = {"from_site", "to_site", "distance_km"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("Road CSV needs columns: from_site,to_site,distance_km (optional: traffic_site).")
        for line, row in enumerate(reader, start=2):
            try:
                source = int(row["from_site"])
                target = int(row["to_site"])
                distance = float(row["distance_km"])
                traffic_site = int(row.get("traffic_site") or target)
            except (TypeError, ValueError) as error:
                raise ValueError(f"Invalid road link on CSV line {line}.") from error
            if not math.isfinite(distance) or distance <= 0:
                raise ValueError(f"distance_km must be positive on CSV line {line}.")
            links.append(RoadLink(source, target, distance, traffic_site))
    if not links:
        raise ValueError("The road CSV contains no links.")
    return links


def placeholder_travel_time_minutes(
    distance_km: float,
    hourly_traffic: float,
    speed_kmh: float = 60.0,
    intersection_delay_seconds: float = 30.0,
) -> float:
    """Temporary congestion estimate. Replace with the course conversion formula.

    It assumes traffic flow is vehicles/hour and applies a bounded congestion
    multiplier solely to make the integration runnable before the official
    conversion document is available.
    """
    if distance_km <= 0 or speed_kmh <= 0 or hourly_traffic < 0:
        raise ValueError("Distance and speed must be positive; traffic cannot be negative.")
    free_flow_minutes = distance_km / speed_kmh * 60.0
    congestion_multiplier = 1.0 + min(hourly_traffic / 1200.0, 2.0)
    return free_flow_minutes * congestion_multiplier + intersection_delay_seconds / 60.0


class TrafficRouteProblem(SearchProblem[int]):
    """A road graph whose non-negative edge costs are predicted minutes."""

    def __init__(
        self,
        links: list[RoadLink],
        origin: int,
        destination: int,
        predicted_hourly_flow: dict[int, float],
        travel_time_fn: Callable[[float, float], float] = placeholder_travel_time_minutes,
    ):
        self.origin = origin
        self.destination = destination
        self.adjacency: dict[int, list[tuple[int, float]]] = {}
        self.edge_times: dict[tuple[int, int], float] = {}
        self.nodes: set[int] = set()
        for link in links:
            flow = float(predicted_hourly_flow.get(link.traffic_site, 0.0))
            minutes = float(travel_time_fn(link.distance_km, flow))
            if not math.isfinite(minutes) or minutes < 0:
                raise ValueError("Travel-time calculation must return a finite non-negative value.")
            self.nodes.update((link.from_site, link.to_site))
            self.adjacency.setdefault(link.from_site, []).append((link.to_site, minutes))
            self.edge_times[(link.from_site, link.to_site)] = minutes
        if origin not in self.nodes or destination not in self.nodes:
            raise ValueError("Origin and destination must both exist in the road network.")

    def initial_state(self) -> int:
        return self.origin

    def is_goal(self, state: int) -> bool:
        return state == self.destination

    def successors(self, state: int) -> list[tuple[int, float]]:
        return self.adjacency.get(state, [])


def k_shortest_routes(
    links: list[RoadLink],
    origin: int,
    destination: int,
    predicted_hourly_flow: dict[int, float],
    k: int = 5,
) -> list[SearchResult[int]]:
    """Return up to k loopless routes, ordered by estimated travel time.

    Uses Yen's algorithm with the repository's Uniform Cost Search engine.
    """
    if k < 1:
        raise ValueError("k must be at least 1.")
    first_problem = TrafficRouteProblem(links, origin, destination, predicted_hourly_flow)
    first = UniformCostSearch().search(first_problem)
    if not first.found:
        return []

    routes = [first]
    candidates: list[tuple[float, tuple[int, ...], SearchResult[int]]] = []
    candidate_paths: set[tuple[int, ...]] = set()

    for _ in range(1, k):
        previous = routes[-1].path
        for spur_index in range(len(previous) - 1):
            root_path = previous[:spur_index + 1]
            blocked_edges = {
                (route.path[spur_index], route.path[spur_index + 1])
                for route in routes
                if len(route.path) > spur_index + 1
                and route.path[:spur_index + 1] == root_path
            }
            blocked_nodes = set(root_path[:-1])
            spur_node = root_path[-1]
            allowed_links = [
                link for link in links
                if (link.from_site, link.to_site) not in blocked_edges
                and link.from_site not in blocked_nodes
                and link.to_site not in blocked_nodes
            ]
            try:
                spur_problem = TrafficRouteProblem(
                    allowed_links, spur_node, destination, predicted_hourly_flow
                )
            except ValueError:
                continue
            spur_result = UniformCostSearch().search(spur_problem)
            if not spur_result.found:
                continue

            combined = root_path[:-1] + spur_result.path
            key = tuple(combined)
            if key in candidate_paths or any(tuple(route.path) == key for route in routes):
                continue
            root_cost = sum(
                first_problem.edge_times[(a, b)]
                for a, b in zip(root_path, root_path[1:])
            )
            cost = root_cost + spur_result.cost
            result = SearchResult(
                True,
                combined,
                cost,
                first.expanded_nodes + spur_result.expanded_nodes,
                first.generated_nodes + spur_result.generated_nodes,
            )
            candidate_paths.add(key)
            candidates.append((cost, key, result))

        if not candidates:
            break
        candidates.sort(key=lambda item: (item[0], item[1]))
        _, _, next_route = candidates.pop(0)
        routes.append(next_route)
    return routes


def predict_next_hourly_flow(model_name: str, traffic_file: str | Path = "data/traffic.npy") -> float:
    """Run the selected checkpoint against the latest available traffic window."""
    import numpy as np
    import torch
    from core.parser import load_model

    data = np.load(traffic_file)
    model, checkpoint, device = load_model(model_name)
    sequence_length = int(checkpoint["sequence_length"])
    if len(data) < sequence_length:
        raise ValueError(f"Traffic data needs at least {sequence_length} observations.")
    mean = checkpoint["mean"].cpu().numpy()
    std = checkpoint["std"].cpu().numpy()
    window = (data[-sequence_length:] - mean) / std
    inputs = torch.tensor(window, dtype=torch.float32).unsqueeze(0).to(device)
    with torch.no_grad():
        output = model(inputs).cpu().numpy()[0]
    output = output * std + mean
    # Models predict four 15-minute intervals. Sum to estimated vehicles/hour.
    return max(0.0, float(output.reshape(-1)[:4].sum()))
