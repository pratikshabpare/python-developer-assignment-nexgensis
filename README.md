# FastBox Logistics Simulator - Mystery Delivery System

A logistics delivery simulator implemented in Python for FastBox operations.

---

## 📋 Problem Overview

FastBox operates a delivery network comprising:
- **Warehouses**: Storage hubs where packages are initially stored.
- **Agents**: Delivery personnel with initial positions on a 2D coordinate grid.
- **Packages**: Delivery requests with a designated source warehouse and delivery destination.

### Core Objectives
1. **JSON Parsing**: Ingest scenario data (supporting both dict mappings and list structures).
2. **Euclidean Distance & Nearest Agent Assignment**: Each package is assigned to the nearest agent based on Euclidean distance from the agent's initial position to the package's warehouse.
3. **Simulation**: Agents start at their home locations, travel to the warehouse to pick up packages, travel to the destinations to deliver them, and update their locations. Total distance is tracked.
4. **Report Generation**: Output operational metrics (`packages_delivered`, `total_distance`, `efficiency` = distance / package) and determine the `best_agent` (lowest distance per delivery).
5. **Persistence**: Save output to `report.json`.

---

## 📐 Engineering Assumptions & Edge Cases Handled

In accordance with robust software engineering practices, the following design decisions and assumptions have been implemented:

### 1. Delivery Routing Model
- **Movement Flow**: An agent begins at their initial location $(x_0, y_0)$. For each assigned package:
  $$\text{Leg 1 (Pickup)}: \text{Current Location} \to \text{Package Warehouse}$$
  $$\text{Leg 2 (Delivery)}: \text{Package Warehouse} \to \text{Package Destination}$$
- **Location Continuity**: Upon completion of Leg 2, the agent's current position is set to the package destination. For subsequent packages assigned to that agent, the next trip originates from this updated position.
- **Dispatch Order**:
  - **Default (Standard FIFO Queue)**: Packages are dispatched in the exact sequence they appear in the JSON input file. This ensures deterministic, reproducible evaluation across all standardized test suites.
  - **Greedy Route Optimization (`--optimize`)**: An optional heuristic route optimizer (Traveling Salesperson heuristic) that greedily selects the next remaining package minimizing incremental transit distance $\Delta d$.

### 2. Tie-Breaking Hierarchy
- **Package-to-Agent Assignment**: If two or more agents have the exact same Euclidean distance to a warehouse, ties are broken **alphabetically by agent ID** (`A1` precedes `A2`).
- **Best Agent Selection**:
  1. **Primary Metric**: Minimum `efficiency` ($\text{total\_distance} / \text{packages\_delivered}$). Lower is better.
  2. **First Tie-Breaker**: Maximum `packages_delivered` (higher delivery volume for the same efficiency).
  3. **Second Tie-Breaker**: Minimum `total_distance` traveled.
  4. **Final Tie-Breaker**: Alphabetical by agent ID.

### 3. Edge Cases Handled
- **Idle Agents**: Agents assigned zero packages remain at their starting coordinates with `packages_delivered: 0`, `total_distance: 0.0`, and `efficiency: 0.0`. They are strictly excluded from consideration for `best_agent`.
- **Empty / Zero Packages**: If an input scenario has no packages, `best_agent` safely defaults to `null` (`None`) without raising DivisionByZero or IndexError exceptions.
- **Warehouse-Destination Overlap**: If a package's destination coordinate is identical to its warehouse coordinate, the delivery leg distance is correctly computed as `0.0`.
- **Schema Permutations**: The parser transparently ingests both:
  - Coordinate dictionaries: `{"warehouses": {"W1": [x, y]}, "agents": {"A1": [x, y]}}`
  - Object lists: `{"warehouses": [{"id": "W1", "location": [x, y]}], "agents": [{"id": "A1", "location": [x, y]}]}`
  - Attribute aliases: `warehouse` vs. `warehouse_id`, `destination` vs. `location`.

---

## 🌟 Bonus Features Included

- **ASCII Route & Network Map Visualizer**: Visual representation of agents, warehouses, and destinations on an ASCII grid.
- **Random Delivery Delay Simulator**: Incorporates traffic / handling delay variations.
- **Mid-Day Dynamic Agent Joining**: Re-optimizes assignments dynamically when a new courier joins mid-day.
- **Top Performer CSV Export**: Automatically exports agent rankings to `top_performer.csv`.

---

## 🚀 How to Run

### Run Simulator on Default Data
```bash
python simulator.py data.json
```

### Run on Any Specific Input File
```bash
python simulator.py test_inputs/input_1.json
```

### Run All Test Cases & Validation
```bash
python run_all_tests.py
```

### Run Unit Tests
```bash
python -m unittest test_simulator.py
```

---

## 📁 Project Structure

```text
├── data.json              # Base assignment dataset
├── simulator.py           # Core simulator engine & bonus modules
├── test_simulator.py      # Automated unit tests
├── run_all_tests.py       # Comprehensive multi-test runner
├── top_performer.csv      # CSV export of agent metrics
├── report.json            # Final output report
└── test_inputs/           # 10 test case datasets
    ├── test_case_01.json  # Base assignment scenario
    ├── test_case_02.json
    ├── test_case_03.json
    ├── test_case_04.json
    ├── test_case_05.json
    ├── test_case_06.json
    ├── test_case_07.json
    ├── test_case_08.json
    ├── test_case_09.json
    └── test_case_10.json
```
