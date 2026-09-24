"""
Run and display validation for all 10 test cases.
"""

import glob
import json
import os
from simulator import run_simulation, load_input_data, euclidean_distance


def evaluate_test_case(filepath: str, test_number: int) -> dict:
    print("=" * 65)
    print(f"TEST CASE {test_number:02d}: {os.path.basename(filepath)}")
    print("=" * 65)

    warehouses, agents, packages = load_input_data(filepath)
    print(f"Input Summary: {len(warehouses)} Warehouses, {len(agents)} Agents, {len(packages)} Packages")

    # Run simulation
    report = run_simulation(filepath, output_report_path="report.json", output_csv_path="top_performer.csv")

    print("\nACTUAL OUTPUT (report.json):")
    print(json.dumps(report, indent=4))

    # Verification against assignment requirements
    errors = []

    # 1. Total delivered packages must match input package count
    total_delivered = sum(report[k]["packages_delivered"] for k in report if k != "best_agent")
    if total_delivered != len(packages):
        errors.append(f"Package count mismatch: delivered {total_delivered}, expected {len(packages)}")

    # 2. Every agent in input must be in report with valid metrics
    for a_id in agents.keys():
        if a_id not in report:
            errors.append(f"Missing agent {a_id} in report")
        else:
            rec = report[a_id]
            pkg_cnt = rec["packages_delivered"]
            dist = rec["total_distance"]
            expected_eff = round(dist / pkg_cnt, 2) if pkg_cnt > 0 else 0.0
            if abs(rec["efficiency"] - expected_eff) > 0.01:
                errors.append(f"Efficiency mismatch for {a_id}: got {rec['efficiency']}, expected {expected_eff}")

    # 3. Check best agent
    best_agent = report.get("best_agent")
    if len(packages) > 0:
        if not best_agent or best_agent not in agents:
            errors.append(f"Invalid best_agent: {best_agent}")
        else:
            best_eff = report[best_agent]["efficiency"]
            for a_id in agents.keys():
                if report[a_id]["packages_delivered"] > 0:
                    if report[a_id]["efficiency"] < best_eff:
                        errors.append(f"Agent {a_id} has lower efficiency ({report[a_id]['efficiency']}) than best_agent {best_agent} ({best_eff})")

    status = "PASS" if not errors else "FAIL"
    print(f"\nSTATUS: {status}")
    if errors:
        for err in errors:
            print(f"  - Problem: {err}")
    print()
    return {"number": test_number, "file": filepath, "status": status, "report": report}


if __name__ == "__main__":
    files = sorted(glob.glob("test_inputs/test_case_*.json"))
    results = []
    for idx, f in enumerate(files, start=1):
        res = evaluate_test_case(f, idx)
        results.append(res)

    print("=" * 65)
    print("FINAL SUMMARY OF ALL 10 TEST CASES:")
    print("=" * 65)
    for r in results:
        print(f"Test Case {r['number']:02d} ({os.path.basename(r['file'])}): {r['status']} | Best Agent: {r['report'].get('best_agent')}")
    print("=" * 65)
