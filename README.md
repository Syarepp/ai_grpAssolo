# COS30019 Assignment 2 Part A: Route Finding AI Framework

This repository implements both uninformed and informed tree-based search algorithms to solve the 2D Route Finding problem. It includes a modular search engine, a command-line interface (CLI) supporting standardized batch execution, and an interactive Matplotlib Graphical User Interface (GUI) featuring dynamic algorithm and test-case switching.

---

## 1. Project Structure

```text
ai_grpAss/
├── core/
│   ├── graph.py             # Matplotlib GUI renderer with radio button controls
│   ├── load_test.py         # Parser for PathFinder text files (.txt)
│   └── search.py            # Generic search problem, search node, and result abstractions
├── route_finding/
│   ├── a_star_search.py     # A* Search algorithm implementation
│   ├── best_first_search.py # Greedy Best-First Search (GBFS) algorithm
│   ├── breadth_first_search.py # Breadth-First Search (BFS) algorithm
│   ├── depth_first_search.py   # Depth-First Search (DFS) algorithm
│   ├── hill_climbing_search.py # Hill Climbing Search
│   ├── uniform_cost_search.py  # Uniform Cost Search (UCS) algorithm
│   └── grid_problem.py      # Grid-based route problem adapter
├── PathFinder-test-1.txt to 16.txt # Benchmark problem graph instances
└── main.py                  # CLI entry point and interactive GUI application
```

---

## 2. Environment Setup

### Prerequisites
* **Python 3.11 or newer** (Python 3.13 recommended)
* **Git**

### Installation Steps

1. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd ai_grpAss
   ```

2. **Set Up a Virtual Environment (Optional but Recommended):**
   * **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   * **macOS / Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install Required Dependencies:**
   No heavy external framework dependencies (such as TensorFlow) are required. Install Matplotlib and NumPy for graph rendering:
   ```bash
   pip install matplotlib numpy
   ```

---

## 3. Program Execution & Usage

### Running via Command Line Interface (CLI)

The program can be executed from the terminal using command-line:

```bash
python main.py
```

#### Terminal Standard Output:
Upon execution, the solution state and search metrics are printed directly to the terminal:
```text
Algorithm: DepthFirstSearch
Path: 2 -> 1 -> 3 -> 6 -> 4
Reached destination 4 | cost 22 | expanded 5 | generated 8
```

---

## 4. Using the Interactive GUI

Running `python main.py` launches a Matplotlib-based interactive GUI window displaying:

1. **2D Coordinate Map:**
   * **Green Node:** Origin node
   * **Red Nodes:** Destination target nodes
   * **Crimson Line:** Active solution path sequence
   * **Curved Directed Arrows:** Directed edges labeled with their respective edge costs

2. **Search Result & Statistics Panel:**
   * Displays search status (`path found` / `no path found`), reached goal node, path cost, total steps, number of expanded nodes, and generated nodes.

3. **Interactive Control Panels (Radio Buttons):**
   * **Search Algorithm Selector:** Switch between $A^*$, Greedy Best-First, Breadth-First, Depth-First, Hill Climbing, and Uniform Cost Search in real time.
   * **Test Case Selector:** Switch between available test files (`PathFinder-test-1.txt` through `16.txt`) dynamically without restarting the application.