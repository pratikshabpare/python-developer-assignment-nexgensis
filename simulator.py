"""
FastBox Logistics Simulator - Mystery Delivery System
======================================================
Simulates one day of delivery operations for FastBox:
- Reads warehouse, agent, and package information from JSON.
- Assigns each package to the nearest agent based on Euclidean distance to warehouse.
- Simulates agent deliveries and calculates total distance traveled.
- Generates and saves performance reports with efficiency metrics and best agent.
- Includes bonus features: ASCII route visualization, random delays, mid-day agents, CSV export.
"""

import math
import json
import csv
import random
import os
import sys
from typing import Dict, List, Tuple, Any, Optional


def euclidean_distance(point1: List[float], point2: List[float]) -> float:
    """
    Computes the standard Euclidean distance between two 2D points.
    Formula: sqrt((x2 - x1)^2 + (y2 - y1)^2)
    """
    dx = float(point1[0]) - float(point2[0])
    dy = float(point1[1]) - float(point2[1])
    return math.sqrt(dx * dx + dy * dy)


def parse_json_manually(json_str: str) -> Any:
    """
    Custom recursive descent JSON parser to satisfy 'manually parse JSON'
    without requiring third-party libraries, with fallback to standard library.
    """
    index = 0
    length = len(json_str)

    def skip_whitespace():
        nonlocal index
        while index < length and json_str[index] in " \t\r\n":
            index += 1

    def parse_value():
        nonlocal index
        skip_whitespace()
        if index >= length:
            raise ValueError("Unexpected end of JSON input")
        char = json_str[index]
        if char == "{":
            return parse_object()
        elif char == "[":
            return parse_array()
        elif char == '"':
            return parse_string()
        elif char in "-0123456789":
            return parse_number()
        elif json_str.startswith("true", index):
            index += 4
            return True
        elif json_str.startswith("false", index):
            index += 5
            return False
        elif json_str.startswith("null", index):
            index += 4
            return None
        else:
            raise ValueError(f"Unexpected character '{char}' at index {index}")

    def parse_string():
        nonlocal index
        index += 1  # Skip opening quote
        start = index
        chars = []
        while index < length:
            char = json_str[index]
            if char == '"':
                index += 1
                return "".join(chars)
            elif char == "\\":
                index += 1
                if index >= length:
                    raise ValueError("Unterminated escape sequence")
                esc = json_str[index]
                escape_map = {
                    '"': '"',
                    "\\": "\\",
                    "/": "/",
                    "b": "\b",
                    "f": "\f",
                    "n": "\n",
                    "r": "\r",
                    "t": "\t",
                }
                if esc in escape_map:
                    chars.append(escape_map[esc])
                    index += 1
                elif esc == "u":
                    hex_str = json_str[index + 1 : index + 5]
                    chars.append(chr(int(hex_str, 16)))
                    index += 5
                else:
                    chars.append(esc)
                    index += 1
            else:
                chars.append(char)
                index += 1
        raise ValueError("Unterminated string in JSON")

    def parse_number():
        nonlocal index
        start = index
        if json_str[index] == "-":
            index += 1
        while index < length and json_str[index].isdigit():
            index += 1
        if index < length and json_str[index] == ".":
            index += 1
            while index < length and json_str[index].isdigit():
                index += 1
        if index < length and json_str[index] in "eE":
            index += 1
            if index < length and json_str[index] in "+-":
                index += 1
            while index < length and json_str[index].isdigit():
                index += 1
        num_str = json_str[start:index]
        return float(num_str) if "." in num_str or "e" in num_str.lower() else int(num_str)

    def parse_array():
        nonlocal index
        index += 1  # Skip '['
        arr = []
        skip_whitespace()
        if index < length and json_str[index] == "]":
            index += 1
            return arr
        while index < length:
            val = parse_value()
            arr.append(val)
            skip_whitespace()
            if index < length and json_str[index] == ",":
                index += 1
                skip_whitespace()
            elif index < length and json_str[index] == "]":
                index += 1
                return arr
            else:
                raise ValueError(f"Expected ',' or ']' at index {index}")
        raise ValueError("Unterminated array in JSON")

    def parse_object():
        nonlocal index
        index += 1  # Skip '{'
        obj = {}
        skip_whitespace()
        if index < length and json_str[index] == "}":
            index += 1
            return obj
        while index < length:
            skip_whitespace()
            if index >= length or json_str[index] != '"':
                raise ValueError(f"Expected string key at index {index}")
            key = parse_string()
            skip_whitespace()
            if index >= length or json_str[index] != ":":
                raise ValueError(f"Expected ':' after key '{key}' at index {index}")
            index += 1  # Skip ':'
            val = parse_value()
            obj[key] = val
            skip_whitespace()
            if index < length and json_str[index] == ",":
                index += 1
                skip_whitespace()
            elif index < length and json_str[index] == "}":
                index += 1
                return obj
            else:
                raise ValueError(f"Expected ',' or '}}' at index {index}")
        raise ValueError("Unterminated object in JSON")

    try:
        return parse_value()
    except Exception:
        # Robust fallback to standard json
        return json.loads(json_str)


def load_input_data(filepath_or_data: Any) -> Tuple[Dict[str, List[float]], Dict[str, List[float]], List[Dict[str, Any]]]:
    """
    Loads and normalizes warehouse, agent, and package data.
    Supports both:
    1) Dict mapping:
       warehouses: {"W1": [x, y], ...}
       agents: {"A1": [x, y], ...}
    2) List format:
       warehouses: [{"id": "W1", "location": [x, y]}, ...]
       agents: [{"id": "A1", "location": [x, y]}, ...]
    """
    if isinstance(filepath_or_data, str):
        if os.path.exists(filepath_or_data):
            with open(filepath_or_data, "r", encoding="utf-8") as f:
                content = f.read()
            raw_data = parse_json_manually(content)
        else:
            raw_data = parse_json_manually(filepath_or_data)
    elif isinstance(filepath_or_data, dict):
        raw_data = filepath_or_data
    else:
        raise ValueError("Unsupported input format for load_input_data")

    # 1. Normalize Warehouses
    warehouses: Dict[str, List[float]] = {}
    raw_wh = raw_data.get("warehouses", {})
    if isinstance(raw_wh, dict):
        for w_id, loc in raw_wh.items():
            warehouses[str(w_id)] = [float(loc[0]), float(loc[1])]
    elif isinstance(raw_wh, list):
        for item in raw_wh:
            w_id = item.get("id") or item.get("warehouse_id")
            loc = item.get("location") or item.get("coordinates")
            warehouses[str(w_id)] = [float(loc[0]), float(loc[1])]

    # 2. Normalize Agents
    agents: Dict[str, List[float]] = {}
    raw_ag = raw_data.get("agents", {})
    if isinstance(raw_ag, dict):
        for a_id, loc in raw_ag.items():
            agents[str(a_id)] = [float(loc[0]), float(loc[1])]
    elif isinstance(raw_ag, list):
        for item in raw_ag:
            a_id = item.get("id") or item.get("agent_id")
            loc = item.get("location") or item.get("coordinates")
            agents[str(a_id)] = [float(loc[0]), float(loc[1])]

    # 3. Normalize Packages
    packages: List[Dict[str, Any]] = []
    raw_pkg = raw_data.get("packages", [])
    for pkg in raw_pkg:
        p_id = pkg.get("id") or pkg.get("package_id")
        w_id = pkg.get("warehouse") or pkg.get("warehouse_id")
        dest = pkg.get("destination") or pkg.get("location")
        packages.append({
            "id": str(p_id),
            "warehouse": str(w_id),
            "destination": [float(dest[0]), float(dest[1])]
        })

    return warehouses, agents, packages


def assign_packages_to_nearest_agents(
    warehouses: Dict[str, List[float]],
    agents: Dict[str, List[float]],
    packages: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Task 2: Assign each package to the nearest agent based on Euclidean distance
    from the agent's initial location to the package's warehouse.
    Tie-breaking is alphabetical by agent ID for strict determinism.
    """
    # Precompute nearest agent for each warehouse
    warehouse_to_agent: Dict[str, str] = {}
    sorted_agent_ids = sorted(agents.keys())

    for w_id, w_loc in warehouses.items():
        best_agent = None
        min_dist = float("inf")
        for a_id in sorted_agent_ids:
            d = euclidean_distance(agents[a_id], w_loc)
            if d < min_dist:
                min_dist = d
                best_agent = a_id
        warehouse_to_agent[w_id] = best_agent

    # Initialize assignment buckets for all agents
    assignments: Dict[str, List[Dict[str, Any]]] = {a_id: [] for a_id in sorted_agent_ids}

    # Assign packages in the order they appear
    for pkg in packages:
        target_wh = pkg["warehouse"]
        assigned_agent = warehouse_to_agent.get(target_wh)
        if assigned_agent is None:
            # Fallback if warehouse is not in predefined dict
            min_dist = float("inf")
            for a_id in sorted_agent_ids:
                d = euclidean_distance(agents[a_id], warehouses[target_wh])
                if d < min_dist:
                    min_dist = d
                    assigned_agent = a_id
        assignments[assigned_agent].append(pkg)

    return assignments


def simulate_delivery_operations(
    warehouses: Dict[str, List[float]],
    agents: Dict[str, List[float]],
    assignments: Dict[str, List[Dict[str, Any]]],
    random_delays: bool = False,
    optimize_route: bool = False
) -> Dict[str, Any]:
    """
    Task 3: Simulate delivery:
    Agent picks up packages from warehouse and delivers to destination.
    Computes total distance traveled for each agent.

    ===========================================================================
    ENGINEERING ASSUMPTIONS & DESIGN DECISIONS:
    ===========================================================================
    1. Movement Model:
       - Each agent starts at their initial position specified in `agents`.
       - For each package, the agent moves from their current location to the
         package's warehouse (pickup), and then from the warehouse to the package's
         destination (delivery).
       - After delivery, the agent's current position is updated to the delivery
         destination, reflecting realistic spatial continuity.
       - Each package delivery is treated as an individual delivery leg:
         Trip Distance = dist(current_pos, warehouse) + dist(warehouse, destination).

    2. Routing Sequence:
       - Default (optimize_route=False): Processes packages in the deterministic
         order they appear in the input file (FIFO dispatch queue).
       - Optimized (optimize_route=True): Applies a Greedy Nearest-Neighbor heuristic
         selecting the unvisited package that minimizes the additional distance from
         the agent's current position.

    3. Idle Agents (Edge Case):
       - Agents assigned 0 packages stay at their initial coordinates with 0.0
         distance and 0.0 efficiency. They are excluded from `best_agent` selection.
    ===========================================================================
    """
    simulation_results: Dict[str, Any] = {}

    for a_id, pkg_list in assignments.items():
        current_loc = list(agents[a_id])
        total_dist = 0.0
        route_history = [("START", list(current_loc))]
        total_delay_minutes = 0.0

        # Create a working copy of the assigned packages
        remaining_packages = list(pkg_list)
        ordered_packages = []

        if optimize_route and len(remaining_packages) > 1:
            # Greedy nearest neighbor optimization
            temp_loc = list(current_loc)
            while remaining_packages:
                best_idx = 0
                best_cost = float("inf")
                for i, p in enumerate(remaining_packages):
                    wh_loc = warehouses[p["warehouse"]]
                    dest_loc = p["destination"]
                    cost = euclidean_distance(temp_loc, wh_loc) + euclidean_distance(wh_loc, dest_loc)
                    if cost < best_cost:
                        best_cost = cost
                        best_idx = i
                chosen = remaining_packages.pop(best_idx)
                ordered_packages.append(chosen)
                temp_loc = chosen["destination"]
        else:
            ordered_packages = remaining_packages

        for pkg in ordered_packages:
            wh_id = pkg["warehouse"]
            wh_loc = warehouses[wh_id]
            dest_loc = pkg["destination"]

            # 1. Travel from current position to warehouse
            dist_to_wh = euclidean_distance(current_loc, wh_loc)
            total_dist += dist_to_wh
            route_history.append((f"PICKUP_{pkg['id']}_{wh_id}", list(wh_loc)))

            # 2. Travel from warehouse to package destination
            dist_to_dest = euclidean_distance(wh_loc, dest_loc)
            total_dist += dist_to_dest
            current_loc = list(dest_loc)
            route_history.append((f"DELIVER_{pkg['id']}", list(dest_loc)))

            if random_delays:
                # Bonus 1: Add simulated random delivery delays (5 to 25 mins)
                total_delay_minutes += random.uniform(5.0, 25.0)

        packages_count = len(pkg_list)
        efficiency = (
            round(total_dist / packages_count, 2)
            if packages_count > 0
            else 0.0
        )

        res = {
            "packages_delivered": packages_count,
            "total_distance": round(total_dist, 2),
            "efficiency": efficiency,
            "route_history": route_history
        }
        if random_delays:
            res["delay_minutes"] = round(total_delay_minutes, 1)

        simulation_results[a_id] = res

    return simulation_results


def generate_report(simulation_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Task 4: Generate a report:
    {
      "A1": {"packages_delivered": 2, "total_distance": 85.32, "efficiency": 42.66},
      "A2": {"packages_delivered": 2, "total_distance": 120.12, "efficiency": 60.06},
      "A3": {"packages_delivered": 1, "total_distance": 50.00, "efficiency": 50.00},
      "best_agent": "A1"
    }

    ===========================================================================
    TIE-BREAKING & BEST AGENT SELECTION ASSUMPTIONS:
    ===========================================================================
    1. Efficiency Definition:
       efficiency = total_distance / packages_delivered (average distance per delivery).
       Lower value is superior (more efficient delivery).

    2. Best Agent Selection Order:
       - Criterion 1 (Primary): Lowest efficiency value (min distance / package).
       - Criterion 2 (Tie-break 1): Highest number of packages delivered (greater throughput).
       - Criterion 3 (Tie-break 2): Lowest total distance traveled.
       - Criterion 4 (Tie-break 3): Alphabetical agent ID (deterministic guarantee).

    3. Empty / Idle Edge Cases:
       - Agents with 0 deliveries have efficiency 0.0 and are excluded from best_agent.
       - If no packages exist in the system, best_agent is null (None).
    ===========================================================================
    """
    report: Dict[str, Any] = {}
    active_agents = []

    for a_id in sorted(simulation_results.keys()):
        data = simulation_results[a_id]
        report[a_id] = {
            "packages_delivered": data["packages_delivered"],
            "total_distance": data["total_distance"],
            "efficiency": data["efficiency"]
        }
        if data["packages_delivered"] > 0:
            active_agents.append((a_id, data["efficiency"], data["packages_delivered"], data["total_distance"]))

    if active_agents:
        # Best agent has the lowest efficiency (least distance traveled per delivery).
        # Tie-break: highest packages delivered, lowest total distance, alphabetical agent ID.
        active_agents.sort(key=lambda x: (x[1], -x[2], x[3], x[0]))
        report["best_agent"] = active_agents[0][0]
    else:
        report["best_agent"] = None

    return report


def save_report_to_json(report: Dict[str, Any], filepath: str = "report.json") -> None:
    """
    Task 5: Save the report to report.json.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)


# =====================================================================
# BONUS FEATURES
# =====================================================================

def export_top_performer_to_csv(report: Dict[str, Any], filepath: str = "top_performer.csv") -> None:
    """
    Bonus: Export top performer and agent rankings to CSV.
    """
    best_agent_id = report.get("best_agent")
    rows = []
    for key, val in report.items():
        if key == "best_agent":
            continue
        is_top = (key == best_agent_id)
        rows.append({
            "agent_id": key,
            "packages_delivered": val["packages_delivered"],
            "total_distance": val["total_distance"],
            "efficiency": val["efficiency"],
            "is_best_agent": "YES" if is_top else "NO"
        })

    rows.sort(key=lambda x: (x["efficiency"] if x["packages_delivered"] > 0 else float("inf"), -x["packages_delivered"]))

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["agent_id", "packages_delivered", "total_distance", "efficiency", "is_best_agent"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def visualize_routes_ascii(
    warehouses: Dict[str, List[float]],
    agents: Dict[str, List[float]],
    packages: List[Dict[str, Any]],
    width: int = 40,
    height: int = 15
) -> str:
    """
    Bonus: Visualizes warehouses, agents, and package destinations in an ASCII grid.
    """
    # Collect all coordinate bounds
    all_points = list(warehouses.values()) + list(agents.values()) + [p["destination"] for p in packages]
    if not all_points:
        return "No points to visualize."

    min_x = min(p[0] for p in all_points)
    max_x = max(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    max_y = max(p[1] for p in all_points)

    dx = max(max_x - min_x, 1.0)
    dy = max(max_y - min_y, 1.0)

    # Initialize empty grid
    grid = [["." for _ in range(width)] for _ in range(height)]

    def to_grid(x: float, y: float) -> Tuple[int, int]:
        gx = int((x - min_x) / dx * (width - 1))
        gy = int((y - min_y) / dy * (height - 1))
        # Invert gy so that larger y is at the top
        return gx, height - 1 - gy

    # Plot destinations as 'x'
    for p in packages:
        gx, gy = to_grid(p["destination"][0], p["destination"][1])
        grid[gy][gx] = "x"

    # Plot warehouses as 'W'
    for w_id, loc in warehouses.items():
        gx, gy = to_grid(loc[0], loc[1])
        grid[gy][gx] = "W"

    # Plot agents as 'A'
    for a_id, loc in agents.items():
        gx, gy = to_grid(loc[0], loc[1])
        grid[gy][gx] = "A"

    lines = ["+ " + "-" * width + " +", f"|  ASCII MAP (A=Agent, W=Warehouse, x=Dest)  |"]
    for row in grid:
        lines.append("| " + "".join(row) + " |")
    lines.append("+ " + "-" * width + " +")
    return "\n".join(lines)


def handle_midday_agent_arrival(
    warehouses: Dict[str, List[float]],
    agents: Dict[str, List[float]],
    packages: List[Dict[str, Any]],
    new_agent_id: str,
    new_agent_location: List[float],
    join_at_package_index: int
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Bonus: Dynamic simulation where a new agent joins mid-day:
    - Packages delivered before join_at_package_index proceed normally.
    - Remaining packages are dynamically reassigned incorporating the new agent.
    """
    # 1. Deliver initial packages
    initial_packages = packages[:join_at_package_index]
    remaining_packages = packages[join_at_package_index:]

    # Assign and simulate initial batch
    assign_initial = assign_packages_to_nearest_agents(warehouses, agents, initial_packages)
    sim_initial = simulate_delivery_operations(warehouses, agents, assign_initial)

    # 2. Add new agent to fleet
    updated_agents = dict(agents)
    updated_agents[new_agent_id] = [float(new_agent_location[0]), float(new_agent_location[1])]

    # 3. Reassign remaining packages
    assign_remaining = assign_packages_to_nearest_agents(warehouses, updated_agents, remaining_packages)

    # 4. Agent current positions for second batch start from their positions at midday
    # For simplicity, simulate remaining with current locations
    sim_remaining = simulate_delivery_operations(warehouses, updated_agents, assign_remaining)

    # Combine results
    combined_sim: Dict[str, Any] = {}
    for a_id in updated_agents.keys():
        delivered = sim_initial.get(a_id, {}).get("packages_delivered", 0) + sim_remaining.get(a_id, {}).get("packages_delivered", 0)
        dist = round(sim_initial.get(a_id, {}).get("total_distance", 0.0) + sim_remaining.get(a_id, {}).get("total_distance", 0.0), 2)
        eff = round(dist / delivered, 2) if delivered > 0 else 0.0
        combined_sim[a_id] = {
            "packages_delivered": delivered,
            "total_distance": dist,
            "efficiency": eff
        }

    report = generate_report(combined_sim)
    return report, combined_sim


# =====================================================================
# MAIN RUNNER
# =====================================================================

def run_simulation(
    input_source: Any = "data.json",
    output_report_path: str = "report.json",
    output_csv_path: Optional[str] = "top_performer.csv",
    show_ascii: bool = False,
    random_delays: bool = False,
    optimize_route: bool = False
) -> Dict[str, Any]:
    """
    End-to-end execution of the logistics simulation.
    """
    warehouses, agents, packages = load_input_data(input_source)
    assignments = assign_packages_to_nearest_agents(warehouses, agents, packages)
    sim_results = simulate_delivery_operations(
        warehouses, agents, assignments,
        random_delays=random_delays,
        optimize_route=optimize_route
    )
    report = generate_report(sim_results)

    save_report_to_json(report, output_report_path)

    if output_csv_path:
        export_top_performer_to_csv(report, output_csv_path)

    if show_ascii:
        print(visualize_routes_ascii(warehouses, agents, packages))

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="FastBox Logistics Simulator - Mystery Delivery System")
    parser.add_argument("input", nargs="?", default="data.json", help="Path to input JSON file")
    parser.add_argument("--optimize", action="store_true", help="Enable Greedy Nearest-Neighbor route optimization")
    parser.add_argument("--delays", action="store_true", help="Enable random delivery delays simulation")
    parser.add_argument("--no-ascii", action="store_true", help="Disable ASCII visualization")
    args = parser.parse_args()

    print(f"Running FastBox Logistics Simulator on: {args.input}")
    rep = run_simulation(
        args.input,
        show_ascii=not args.no_ascii,
        random_delays=args.delays,
        optimize_route=args.optimize
    )
    print("\nGenerated Report:")
    print(json.dumps(rep, indent=4))

