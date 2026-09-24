"""
Test Suite for FastBox Logistics Simulator
===========================================
Validates:
1. JSON loading & manual parsing
2. Euclidean distance accuracy
3. Nearest-agent assignment logic
4. Simulation calculations and constraints
5. Total packages delivered matching total input packages
6. Efficiency and best_agent determination
7. Execution across all provided test cases (data.json, input_1.json through input_9.json)
"""

import unittest
import os
import json
import glob
from simulator import (
    euclidean_distance,
    parse_json_manually,
    load_input_data,
    assign_packages_to_nearest_agents,
    simulate_delivery_operations,
    generate_report,
    run_simulation
)


class TestFastBoxSimulator(unittest.TestCase):

    def test_euclidean_distance(self):
        # 3-4-5 right triangle
        self.assertAlmostEqual(euclidean_distance([0, 0], [3, 4]), 5.0)
        self.assertAlmostEqual(euclidean_distance([5, 5], [0, 0]), 7.0710678, places=4)
        self.assertAlmostEqual(euclidean_distance([10, 20], [10, 20]), 0.0)

    def test_manual_json_parser(self):
        sample = '{"a": 1, "b": [2.5, "text", true, false, null], "c": {"nested": -42}}'
        parsed = parse_json_manually(sample)
        self.assertEqual(parsed["a"], 1)
        self.assertEqual(parsed["b"], [2.5, "text", True, False, None])
        self.assertEqual(parsed["c"]["nested"], -42)

    def test_base_assignment_and_package_count(self):
        wh, ag, pkgs = load_input_data("data.json")
        self.assertEqual(len(wh), 3)
        self.assertEqual(len(ag), 3)
        self.assertEqual(len(pkgs), 5)

        assignments = assign_packages_to_nearest_agents(wh, ag, pkgs)
        total_assigned = sum(len(p_list) for p_list in assignments.values())
        self.assertEqual(total_assigned, len(pkgs))

        # Check nearest mapping:
        # A1 is closest to W1
        # A2 is closest to W2
        # A3 is closest to W3
        self.assertEqual(len(assignments["A1"]), 2) # P1, P4
        self.assertEqual(len(assignments["A2"]), 2) # P2, P5
        self.assertEqual(len(assignments["A3"]), 1) # P3

        sim = simulate_delivery_operations(wh, ag, assignments)
        report = generate_report(sim)

        self.assertIn("A1", report)
        self.assertIn("A2", report)
        self.assertIn("A3", report)
        self.assertIn("best_agent", report)

        total_delivered = sum(
            report[k]["packages_delivered"] for k in report if k != "best_agent"
        )
        self.assertEqual(total_delivered, len(pkgs))

    def test_all_provided_inputs(self):
        """
        Runs the simulation across all 10 test cases
        and verifies strict integrity checks.
        """
        test_files = sorted(glob.glob("test_inputs/test_case_*.json"))
        self.assertEqual(len(test_files), 10)

        for filepath in test_files:
            with self.subTest(filepath=filepath):
                wh, ag, pkgs = load_input_data(filepath)
                report = run_simulation(filepath, output_report_path="temp_report.json")

                # 1. Check all agents exist in report
                for a_id in ag.keys():
                    self.assertIn(a_id, report)
                    self.assertIn("packages_delivered", report[a_id])
                    self.assertIn("total_distance", report[a_id])
                    self.assertIn("efficiency", report[a_id])

                # 2. Check total delivered packages == input packages
                total_delivered = sum(
                    report[k]["packages_delivered"]
                    for k in report
                    if k != "best_agent"
                )
                self.assertEqual(
                    total_delivered,
                    len(pkgs),
                    f"Delivered count {total_delivered} does not match total packages {len(pkgs)} for {filepath}"
                )

                # 3. Check best_agent validity
                best_agent = report["best_agent"]
                if len(pkgs) > 0:
                    self.assertIsNotNone(best_agent)
                    self.assertIn(best_agent, ag)
                    best_eff = report[best_agent]["efficiency"]
                    # Verify best_eff is indeed minimum among active agents
                    for a_id in ag.keys():
                        if report[a_id]["packages_delivered"] > 0:
                            self.assertLessEqual(best_eff, report[a_id]["efficiency"])

        if os.path.exists("temp_report.json"):
            os.remove("temp_report.json")

    def test_edge_cases_and_tie_breaking(self):
        # 1. Equidistant agents tie-breaking: A1 and A2 at same distance to W1
        wh = {"W1": [0.0, 0.0]}
        ag = {"A2": [5.0, 0.0], "A1": [0.0, 5.0]} # Both distance 5.0
        pkgs = [{"id": "P1", "warehouse": "W1", "destination": [0.0, 10.0]}]

        assignments = assign_packages_to_nearest_agents(wh, ag, pkgs)
        # Ties must break alphabetically to A1
        self.assertEqual(len(assignments["A1"]), 1)
        self.assertEqual(len(assignments["A2"]), 0)

        sim = simulate_delivery_operations(wh, ag, assignments)
        report = generate_report(sim)

        self.assertEqual(report["best_agent"], "A1")
        self.assertEqual(report["A2"]["packages_delivered"], 0)
        self.assertEqual(report["A2"]["total_distance"], 0.0)
        self.assertEqual(report["A2"]["efficiency"], 0.0)

    def test_route_optimization(self):
        # Test that route optimization handles reordering
        wh = {"W1": [0.0, 0.0]}
        ag = {"A1": [0.0, 0.0]}
        pkgs = [
            {"id": "P1", "warehouse": "W1", "destination": [50.0, 0.0]},
            {"id": "P2", "warehouse": "W1", "destination": [5.0, 0.0]}
        ]
        assignments = assign_packages_to_nearest_agents(wh, ag, pkgs)
        # Default order (P1 then P2):
        # (0,0) -> W1(0,0): 0
        # W1 -> P1(50,0): 50
        # P1(50,0) -> W1(0,0): 50
        # W1 -> P2(5,0): 5
        # Total = 105
        sim_default = simulate_delivery_operations(wh, ag, assignments, optimize_route=False)
        self.assertEqual(sim_default["A1"]["total_distance"], 105.0)

        # Optimized order (P2 then P1):
        # (0,0) -> W1(0,0): 0
        # W1 -> P2(5,0): 5
        # P2(5,0) -> W1(0,0): 5
        # W1 -> P1(50,0): 50
        # Total = 60
        sim_opt = simulate_delivery_operations(wh, ag, assignments, optimize_route=True)
        self.assertEqual(sim_opt["A1"]["total_distance"], 60.0)
        self.assertLess(sim_opt["A1"]["total_distance"], sim_default["A1"]["total_distance"])


if __name__ == "__main__":
    unittest.main()
