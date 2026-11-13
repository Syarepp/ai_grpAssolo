# Traffic-to-travel-time calculation (A2B)

This module implements the lecturer's **Traffic Flow to Travel Time Conversion v1.0** formula and prepares **travel time in minutes** as the weight for each directed road edge.

## Run the tests

From the repository root:

```bash
python -m unittest discover -s tests -v
```

The module uses only Python's standard library. The tests use invented examples, not measured SCATS data.

## Use it with predicted traffic

```python
from calculation import hourly_flow_from_quarters, weight_road_edges

# Four successive predicted 15-minute counts for SCATS site 2000.
flow_2000 = hourly_flow_from_quarters([200, 250, 300, 250])

# Directed graph edges: (start SCATS, end SCATS, distance in km).
# Example IDs and distances below are placeholders, NOT verified road links.
edges = [(2000, 3002, 2.0)]

weighted = weight_road_edges(edges, {2000: flow_2000})
for edge in weighted:
    print(edge.origin_scats, edge.destination_scats, edge.travel_time_minutes)

# A2A adapter, if its graph accepts (origin, destination, cost):
weighted_edge_tuples = [
    (edge.origin_scats, edge.destination_scats, edge.travel_time_minutes)
    for edge in weighted
]
```

## Important integration decisions

1. **SCATS IDs vs ML indices:** ML members must map predictions to actual SCATS site IDs; a dataset row index is not necessarily a SCATS ID.
2. **Time units:** The model may predict 15-minute counts. Sum four consecutive intervals for an hourly count; do not multiply an already-hourly value by four.
3. **Flow site:** The detailed conversion PDF specifies the **starting** SCATS site for each directed edge, while the main assignment brief refers to the **destination** site. Ask the tutor to resolve the conflict before final submission. This module follows the detailed PDF.
4. **Road distances:** Use verified road-network distances in **kilometres**. The provided SCATS map alone does not define directed road connections or accurate driving distances.
5. **Intersection delay:** Default is one controlled intersection (30 seconds) per edge. Confirm the counting convention with the A2A teammate to prevent double-counting.
6. **Under-capacity assumption:** This module accepts 0–1500 vehicles/hour and uses the high-speed quadratic root, capped at 60 km/h. Do not use the lower-speed congested branch without revising the assumptions.
7. **Missing prediction:** A missing starting-site prediction raises `KeyError` rather than silently substituting zero traffic.
8. **Current repo limitation:** The existing `_main.py` references `core/` and `route_finding/` modules that are not present on the main branch. This calculation module can be tested independently, but A2A integration requires those modules to be committed.

## Research-ready experiments

Vary the predicted hourly flow (e.g. 300, 600, 900, 1200) at a fixed distance and record the travel times. Compare the resulting edge weights and routes once the graph is available. Clearly label hypothetical inputs versus actual predictions in the report.
