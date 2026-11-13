"""Run with: python -m unittest discover -s tests -v"""

import math
import unittest

from calculation.travel_time import (
    calculate_travel_time_minutes,
    flow_to_speed_kmh,
    hourly_flow_from_quarters,
    weight_road_edges,
)


class TravelTimeTests(unittest.TestCase):
    def test_quarter_hour_aggregation(self):
        self.assertEqual(hourly_flow_from_quarters([50, 60, 70, 80]), 260)

    def test_quarter_hour_requires_four_intervals(self):
        with self.assertRaises(ValueError):
            hourly_flow_from_quarters([50, 60, 70])

    def test_quarter_hour_rejects_negative_counts(self):
        with self.assertRaises(ValueError):
            hourly_flow_from_quarters([50, -1, 70, 80])

    def test_quarter_hour_rejects_nan(self):
        with self.assertRaises(ValueError):
            hourly_flow_from_quarters([50, math.nan, 70, 80])

    def test_zero_flow_speed_capped_at_sixty(self):
        self.assertAlmostEqual(flow_to_speed_kmh(0), 60)

    def test_low_flow_speed_capped_at_sixty(self):
        self.assertAlmostEqual(flow_to_speed_kmh(300), 60)

    def test_flow_at_capacity(self):
        self.assertAlmostEqual(flow_to_speed_kmh(1500), 32, delta=1)

    def test_flow_1000_reduces_speed(self):
        self.assertAlmostEqual(flow_to_speed_kmh(1000), 50.48, delta=0.02)

    def test_reject_over_capacity_flow(self):
        with self.assertRaises(ValueError):
            flow_to_speed_kmh(1600)

    def test_reject_negative_flow(self):
        with self.assertRaises(ValueError):
            flow_to_speed_kmh(-1)

    def test_reject_nonfinite_flow(self):
        with self.assertRaises(ValueError):
            flow_to_speed_kmh(float("inf"))

    def test_free_flow_two_km_one_intersection(self):
        self.assertAlmostEqual(calculate_travel_time_minutes(0, 2), 2.5)

    def test_heavy_flow_two_km_one_intersection(self):
        self.assertAlmostEqual(
            calculate_travel_time_minutes(1000, 2), 2.88, delta=0.01
        )

    def test_no_intersection_delay(self):
        self.assertAlmostEqual(
            calculate_travel_time_minutes(0, 2, 0), 2
        )

    def test_multiple_intersection_delays(self):
        self.assertAlmostEqual(
            calculate_travel_time_minutes(0, 2, 2), 3
        )

    def test_reject_zero_distance(self):
        with self.assertRaises(ValueError):
            calculate_travel_time_minutes(1000, 0)

    def test_reject_invalid_intersection_count(self):
        with self.assertRaises(ValueError):
            calculate_travel_time_minutes(1000, 2, -1)

    def test_directed_edges_use_starting_site_flow(self):
        edges = [(2000, 3002, 2), (3002, 2000, 2)]
        result = weight_road_edges(edges, {2000: 1000, 3002: 0})
        self.assertEqual(result[0].starting_site_flow_vph, 1000)
        self.assertEqual(result[1].starting_site_flow_vph, 0)
        self.assertGreater(result[0].travel_time_minutes, result[1].travel_time_minutes)

    def test_missing_site_prediction_raises(self):
        with self.assertRaises(KeyError):
            weight_road_edges([(2000, 3002, 2)], {})


if __name__ == "__main__":
    unittest.main()
