"""Run: python -m unittest discover -s tests -v"""
import math
import unittest
from calculation import (
    hourly_flow_from_quarters, flow_to_speed_kmh,
    calculate_travel_time_minutes, travel_time_for_integration, weight_road_edges,
)


class CalculationTests(unittest.TestCase):
    def test_four_quarters_sum(self):
        self.assertEqual(hourly_flow_from_quarters([200, 250, 300, 250]), 1000)

    def test_three_quarters_fail(self):
        with self.assertRaises(ValueError):
            hourly_flow_from_quarters([200, 250, 300])

    def test_negative_quarter_fails(self):
        with self.assertRaises(ValueError):
            hourly_flow_from_quarters([200, -1, 300, 250])

    def test_nonfinite_quarter_fails(self):
        with self.assertRaises(ValueError):
            hourly_flow_from_quarters([200, math.nan, 300, 250])

    def test_zero_flow_speed_limit(self):
        self.assertEqual(flow_to_speed_kmh(0), 60)

    def test_low_flow_speed_limit(self):
        self.assertEqual(flow_to_speed_kmh(300), 60)

    def test_flow_1000_speed(self):
        self.assertAlmostEqual(flow_to_speed_kmh(1000), 50.48, delta=0.02)

    def test_flow_1500_speed(self):
        self.assertAlmostEqual(flow_to_speed_kmh(1500), 32, delta=1)

    def test_above_range_rejected(self):
        with self.assertRaises(ValueError):
            flow_to_speed_kmh(1501)

    def test_negative_flow_rejected(self):
        with self.assertRaises(ValueError):
            flow_to_speed_kmh(-1)

    def test_nan_flow_rejected(self):
        with self.assertRaises(ValueError):
            flow_to_speed_kmh(math.nan)

    def test_infinite_flow_rejected(self):
        with self.assertRaises(ValueError):
            flow_to_speed_kmh(math.inf)

    def test_bool_flow_rejected(self):
        with self.assertRaises(ValueError):
            flow_to_speed_kmh(True)

    def test_free_flow_two_km(self):
        self.assertAlmostEqual(calculate_travel_time_minutes(0, 2), 2.5)

    def test_heavy_flow_two_km(self):
        self.assertAlmostEqual(calculate_travel_time_minutes(1000, 2), 2.88, delta=0.01)

    def test_zero_intersections(self):
        self.assertAlmostEqual(calculate_travel_time_minutes(0, 2, 0), 2)

    def test_two_intersections(self):
        self.assertAlmostEqual(calculate_travel_time_minutes(0, 2, 2), 3)

    def test_negative_intersections_fails(self):
        with self.assertRaises(ValueError):
            calculate_travel_time_minutes(0, 2, -1)

    def test_bool_intersections_fails(self):
        with self.assertRaises(ValueError):
            calculate_travel_time_minutes(0, 2, True)

    def test_zero_distance_fails(self):
        with self.assertRaises(ValueError):
            calculate_travel_time_minutes(0, 0)

    def test_negative_distance_fails(self):
        with self.assertRaises(ValueError):
            calculate_travel_time_minutes(0, -2)

    def test_integration_function_arguments_order(self):
        self.assertAlmostEqual(travel_time_for_integration(2, 1000), 2.88, delta=0.01)

    def test_edges_use_origin_flow_by_default(self):
        result = weight_road_edges([(2000, 3002, 2), (3002, 2000, 2)],
                                   {2000: 1000, 3002: 0})
        self.assertEqual(result[0].traffic_site, 2000)
        self.assertEqual(result[1].traffic_site, 3002)
        self.assertGreater(result[0].travel_time_minutes,
                           result[1].travel_time_minutes)

    def test_edges_can_use_destination_flow(self):
        result = weight_road_edges([(2000, 3002, 2)], {3002: 1000},
                                   flow_site="destination")
        self.assertEqual(result[0].traffic_site, 3002)
        self.assertAlmostEqual(result[0].travel_time_minutes, 2.88, delta=0.01)

    def test_invalid_flow_site_rejected(self):
        with self.assertRaises(ValueError):
            weight_road_edges([], {}, flow_site="other")

    def test_missing_prediction_rejected(self):
        with self.assertRaises(KeyError):
            weight_road_edges([(2000, 3002, 2)], {})

    def test_flow_speed_monotone_while_under_capacity(self):
        values = [flow_to_speed_kmh(q) for q in [300, 600, 900, 1200, 1500]]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_time_increases_with_flow(self):
        values = [calculate_travel_time_minutes(q, 2)
                  for q in [300, 600, 900, 1200, 1500]]
        self.assertEqual(values, sorted(values))


if __name__ == "__main__":
    unittest.main()
