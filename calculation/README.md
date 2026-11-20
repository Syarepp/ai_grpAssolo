# COS30019 Assignment 2B — Calculation Module

This package is isolated: it does **not** change `main.py`, `gui.py`, `integration.py`, ML, or route finding files.

## Lecturer formula

Traffic flow in vehicles per hour: `Q = -1.4648375 * v**2 + 93.75 * v`.

The higher-speed quadratic root is:

`v = (93.75 + sqrt(93.75**2 - 4*1.4648375*Q)) / (2*1.4648375)`

Cap speed at **60 km/h**. For a road segment:

`T_minutes = (distance_km / speed_kmh) * 60 + controlled_intersections * 0.5`

One intersection is counted by default (30 seconds). Valid flow range: **0–1500 vehicles/hour**. The high-speed branch assumes under-capacity operation and does not describe heavy stop-and-go congestion. Reject predictions outside the valid range rather than silently changing them.

## Testing (no third-party test library)

From the repository root:

```bash
python -m unittest discover -s tests -v
```

## Prediction-to-edge example

```python
from calculation import hourly_flow_from_quarters, weight_road_edges

# Invented counts for demonstration only (four consecutive 15-minute counts)
q_2000 = [200, 250, 300, 250]
flow_2000 = hourly_flow_from_quarters(q_2000)  # 1000 v/h
# Invented link: confirm real road connectivity and distances before report!
links = [(2000, 3002, 2.0)]
weighted = weight_road_edges(links, {2000: flow_2000})
graph_edges = [(e.origin_scats, e.destination_scats, e.travel_time_minutes)
               for e in weighted]
```

Use genuine SCATS IDs rather than row indices. The ML system must predict a value for each relevant site. Sum four 15-minute **counts** only if those outputs are per-interval counts (not already vehicles/hour).

## Safe integration handoff (no teammate file changed)

Existing `integration.TrafficRouteProblem` has `travel_time_fn(distance_km, hourly_traffic)`. This package provides:

```python
from calculation import travel_time_for_integration
from integration import TrafficRouteProblem

problem = TrafficRouteProblem(
    links, origin, destination, predictions_by_scats_id,
    travel_time_fn=travel_time_for_integration,
)
```

This does **not** automatically switch `integration.k_shortest_routes`, which still constructs its own default placeholder-cost problem. The integration teammate should update that API and check that its default missing-traffic value of zero is not used for unknown predictions.

**Resolve before group integration:** The detailed handout describes using each edge's starting SCATS flow but the main assignment brief refers to destination-site volume. `weight_road_edges(..., flow_site="origin"|"destination")` supports both; default is origin. Also confirm counting intersections once per road edge to prevent duplicate delays.

## Demonstration experiment

```bash
python -m calculation.experiment
```

Writes `calculation/results/flow_sensitivity.csv`, using hypothetical flows of 0, 300, 600, 900, 1200 and 1500 vehicles/hour, a fixed 2 km distance, and one intersection. These are calculation sensitivity results — **not** trained ML scores, real driving time, or route accuracy.
