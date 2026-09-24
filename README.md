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
