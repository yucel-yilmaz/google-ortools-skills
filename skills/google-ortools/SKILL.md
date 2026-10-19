---
name: google-ortools
description: >-
  Model, solve, debug, and optimize combinatorial and mathematical optimization
  problems using Google OR-Tools (developers.google.com/optimization). Use when
  working with Constraint Programming (CP-SAT / cp_model), Linear and Mixed-Integer
  Programming (LP / MILP via pywraplp or MathOpt with GLOP, PDLP, SCIP, HIGHS, CBC,
  Gurobi), Vehicle Routing (TSP, VRP, CVRP, VRPTW, Pickup and Delivery via pywrapcp),
  Scheduling (Employee Shift Rostering, Job-Shop, FJSP, RCPSP, IntervalVar, NoOverlap,
  Cumulative), Network Flows (Max Flow, Min-Cost Flow, Linear Sum Assignment), or
  Packing (Knapsack, Multiple Knapsack, 1D/2D Bin Packing) in Python, C++, Java, or C#.
license: Apache-2.0
compatibility: Python 3.9+ with ortools>=9.10 (includes C++, Java, and C#/.NET API mappings).
metadata:
  author: yucel-yilmaz
  version: "1.0.0"
  repository: https://github.com/yucel-yilmaz/google-ortools-skills
  docs: https://developers.google.com/optimization
  tags: optimization, operations-research, google-ortools, cp-sat, mip, lp, vrp, tsp, scheduling, mathopt
---

# Google OR-Tools Optimization Skill

This skill provides authoritative workflows, modern API conventions (OR-Tools v9.10–v9.15+), solver selection rules, and anti-hallucination guardrails based on the official [Google OR-Tools Developer Guide](https://developers.google.com/optimization).

---

## 1. Solver & Module Selection Matrix

Before writing any code, classify the problem and select the appropriate OR-Tools module:

| Problem Class | Recommended Module | Underlying Engine(s) | When to Choose |
| :--- | :--- | :--- | :--- |
| **Discrete / Combinatorial / Logic / Scheduling** | `ortools.sat.python.cp_model` | **CP-SAT** | **Default choice** for integer/boolean variables, employee shift scheduling, job-shop (`NoOverlap`, `Cumulative`), circuit/assignment, and logical implications (`only_enforce_if`). |
| **Continuous LP & Classical MILP** | `ortools.linear_solver.pywraplp` | **GLOP** (LP), **PDLP** (Large LP), **SCIP** / **CBC** / **HIGHS** / **GUROBI** (MILP) | Continuous variables ($x \in \mathbb{R}$), blending, diet, production planning, or standard linear/mixed-integer formulations. |
| **Modern Solver-Agnostic LP / MILP / QP** | `ortools.math_opt.python.mathopt` | **CP-SAT**, **GLOP**, **PDLP**, **GSCIP**, **HIGHS**, **GUROBI**, **OSQP** | Models requiring quadratic objectives/constraints, incremental model updates, warm starts, solver-independent callbacks, or multi-objective optimization. |
| **Vehicle Routing (TSP / VRP / VRPTW)** | `ortools.constraint_solver.pywrapcp` | **Routing Solver** (CP + Local Search) | Visiting locations with fleets, capacity limits (CVRP), time windows (VRPTW), pickup & delivery, drop penalties (`AddDisjunction`), and multiple depots. |
| **Pure Network Flows & Bipartite Matching** | `ortools.graph.python.{max_flow, min_cost_flow, linear_sum_assignment}` | **C++ Graph Algorithms** | Dedicated high-speed solvers for Maximum Flow, Minimum-Cost Flow, and 1-to-1 Linear Sum Assignment ($O(V^3)$ / push-relabel). **10x–100x faster** than generic LP. |
| **Pure 0-1 / Multi-Dimensional Knapsack** | `ortools.algorithms.python.knapsack_solver` | **Branch & Bound / DP** | Selecting items with weights and profits to maximize value under capacity limits without side constraints. |

> **Rule of Thumb:** If all variables are integers/booleans (or can be scaled to integers) and constraints involve logic, intervals, or permutations, **start with CP-SAT (`cp_model`)**. If variables are continuous floats, **use `pywraplp` (`GLOP`/`PDLP`) or `mathopt`**. If it is a fleet routing problem on a distance/time matrix, **use `pywrapcp` (`RoutingModel`)**.

---

## 2. Critical Anti-Hallucination Rules (OR-Tools v9.10–v9.15+)

AI models frequently generate broken OR-Tools code due to deprecated v7/v8 APIs or Python operator misuse. **Strictly enforce these rules:**

### Rule 1: Never Import Removed SWIG Graph/Knapsack Wrappers
* **WRONG (Removed in v9.4+):**
  ```python
  from ortools.graph import pywrapgraph  # ImportError!
  from ortools.algorithms import pywrapknapsack_solver  # Deprecated/Removed!
  ```
* **CORRECT (Modern pybind11 C++ wrappers with `snake_case` methods):**
  ```python
  from ortools.graph.python import max_flow, min_cost_flow, linear_sum_assignment
  from ortools.algorithms.python import knapsack_solver
  ```

### Rule 2: Use PEP 8 `snake_case` in `cp_model`
OR-Tools v9.10+ standardized `cp_model` on PEP 8 `snake_case` (while retaining legacy `CamelCase` aliases). Always write modern `snake_case`:
* `model.new_int_var(lb, ub, name)` (not `NewIntVar`)
* `model.new_bool_var(name)` (not `NewBoolVar`)
* `model.new_interval_var(start, size, end, name)` (not `NewIntervalVar`)
* `model.new_optional_interval_var(start, size, end, is_present, name)`
* `model.add(...)`, `model.add_all_different(...)`, `model.add_no_overlap(...)`, `model.add_cumulative(...)`, `model.add_exactly_one(...)`, `model.add_at_most_one(...)`, `model.add_implication(a, b)`
* `constraint.only_enforce_if(lit)` and `~lit` (or `lit.negated()`) for boolean negation
* `solver.solve(model)`, `solver.value(x)`, `solver.boolean_value(b)`, `solver.objective_value`, `solver.best_objective_bound`, `solver.status_name(status)`

### Rule 3: CP-SAT Requires Integer Domains and Integer Constraint Coefficients
* `cp_model` variables and constraint coefficients **must be integers**.
* Passing floats to `model.add(0.5 * x <= 3.2)` raises `TypeError`.
* **Fix:** Multiply coefficients by a scaling factor (e.g., `SCALE = 100` or `1000` using `round(val * SCALE)`) or switch to `pywraplp` / `mathopt` if true continuous variables are required.

### Rule 4: Never Use Python `if`, `and`, `or`, `not`, `max()`, `min()`, `abs()` on Decision Variables
* **WRONG:** `if x > 5:`, `model.add(max(x, y) <= 10)`, `model.add(x == 1 and y == 1)`
* **CORRECT:**
  * Indicator / If-Then: `model.add(x > 5).only_enforce_if(b)` and `model.add(x <= 5).only_enforce_if(~b)`
  * Maximum: `z = model.new_int_var(lb, ub, "z"); model.add_max_equality(z, [x, y])`
  * Minimum: `z = model.new_int_var(lb, ub, "z"); model.add_min_equality(z, [x, y])`
  * Absolute value: `z = model.new_int_var(0, ub, "z"); model.add_abs_equality(z, x - y)`
  * Multiplication: `z = model.new_int_var(lb, ub, "z"); model.add_multiplication_equality(z, [x, y])`
  * Division: `z = model.new_int_var(lb, ub, "z"); model.add_division_equality(z, x, denom)`

### Rule 5: Use `cp_model.LinearExpr` or `sum()` Efficiently
* For large sums in CP-SAT, prefer `cp_model.LinearExpr.sum(vars)` or `cp_model.LinearExpr.weighted_sum(vars, coeffs)` over nested `+` loops to minimize Python object overhead.

### Rule 6: Routing (`pywrapcp`) Node vs. Index Conversion
* In `pywrapcp`, the solver operates on internal `int64` **indices**, NOT customer **node IDs**.
* Always convert inside callbacks and solution extractors using `manager.IndexToNode(index)` and `manager.NodeToIndex(node)`.
* Note: `routing.IsEnd(index)` must be checked **before** calling `manager.IndexToNode(index)` in route extraction loops.
* Always set a time limit (`search_parameters.time_limit.FromSeconds(10)`) whenever enabling a `LocalSearchMetaheuristic` (like `GUIDED_LOCAL_SEARCH`), or the solver will run forever!

### Rule 7: Always Check Solver Status Before Reading Values
* Reading `solver.value(x)` or `x.solution_value()` when the status is `INFEASIBLE`, `MODEL_INVALID`, or `NOT_SOLVED` raises an exception or returns garbage `0.0`.
* In CP-SAT: check `status in (cp_model.OPTIMAL, cp_model.FEASIBLE)`.
* In `pywraplp`: check `status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE)`.
* Always check `status == pywraplp.Solver.OPTIMAL` vs `FEASIBLE` and log warnings if only a suboptimal feasible solution was found before timeout.

---

## 3. Standard 6-Step Optimization Workflow

Follow this structured workflow when solving any user optimization problem:

1. **Formulate Mathematical Model**:
   * Identify **Sets & Indices**, **Parameters/Data** (with units & scaling factors), **Decision Variables** (bounds & types), **Hard vs. Soft Constraints**, and **Objective Function**.
2. **Verify Environment & Solver Availability**:
   * If running locally, execute `python scripts/diagnose_env_and_model.py` (or `python -c "import ortools"`) to verify available backends.
3. **Construct the Model**:
   * Prefer dictionary/tuple comprehension indexing (`x[i, j] = model.new_bool_var(f"x_{i}_{j}")`) with descriptive variable names for debugging.
   * Formulate soft constraints using non-negative slack/penalty variables in the objective rather than making the model brittle and infeasible.
4. **Configure Solver Parameters**:
   * Always set a finite time limit (`solver.parameters.max_time_in_seconds = 30.0` in CP-SAT; `solver.SetTimeLimit(30000)` in `pywraplp`; `search_parameters.time_limit.FromSeconds(30)` in Routing).
   * Enable parallel workers in CP-SAT (`solver.parameters.num_search_workers = 8` or `0` for all cores).
5. **Solve & Validate Status**:
   * Check status explicitly. If `MODEL_INVALID` in CP-SAT, call `print(model.validate())` to pinpoint invalid bounds or NaN/float errors.
   * If `INFEASIBLE`, use assumptions (`model.add_assumptions(...)` + `solver.sufficient_assumptions_for_infeasibility()`) or relax constraints with high-cost slack variables.
6. **Verify Business Constraints on Output**:
   * Write a post-solve assertion check in plain Python verifying that the extracted solution satisfies capacities, time windows, and conservation laws.

---

## 4. Minimal Canonical Blueprints

### A. CP-SAT (`ortools.sat.python.cp_model`)
```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
x = model.new_int_var(0, 10, "x")
y = model.new_int_var(0, 10, "y")
b = model.new_bool_var("b")

model.add(2 * x + 3 * y <= 25)
model.add(x >= 6).only_enforce_if(b)
model.add(x <= 5).only_enforce_if(~b)
model.maximize(4 * x + 5 * y + 2 * b)

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 10.0
solver.parameters.num_search_workers = 8

status = solver.solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"Status: {solver.status_name(status)}, Obj: {solver.objective_value}")
    print(f"x={solver.value(x)}, y={solver.value(y)}, b={solver.boolean_value(b)}")
else:
    print(f"No solution: {solver.status_name(status)} | Validate: {model.validate()}")
```

### B. Linear / MILP (`ortools.linear_solver.pywraplp`)
```python
from ortools.linear_solver import pywraplp

# Use "GLOP" or "PDLP" for continuous LP; "SCIP", "HIGHS", or "CBC" for MILP
solver = pywraplp.Solver.CreateSolver("SCIP")
if not solver:
    raise RuntimeError("SCIP solver unavailable.")

x = solver.NumVar(0.0, solver.infinity(), "x")   # Continuous
y = solver.IntVar(0.0, 10.0, "y")                # Integer

solver.Add(x + 2.5 * y <= 17.5)
solver.Maximize(3.2 * x + 4.0 * y)
solver.SetTimeLimit(15_000)  # milliseconds

status = solver.Solve()
if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    print(f"Obj: {solver.Objective().Value():.4f}, x={x.solution_value():.4f}, y={y.solution_value()}")
```

### C. Vehicle Routing (`ortools.constraint_solver.pywrapcp`)
```python
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

dist_matrix = [
    [0, 10, 15, 20],
    [10, 0, 35, 25],
    [15, 35, 0, 30],
    [20, 25, 30, 0],
]
manager = pywrapcp.RoutingIndexManager(len(dist_matrix), 1, 0)  # (num_nodes, num_vehicles, depot)
routing = pywrapcp.RoutingModel(manager)

def distance_callback(from_index: int, to_index: int) -> int:
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return dist_matrix[from_node][to_node]

transit_cb_idx = routing.RegisterTransitCallback(distance_callback)
routing.SetArcCostEvaluatorOfAllVehicles(transit_cb_idx)

params = pywrapcp.DefaultRoutingSearchParameters()
params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
params.time_limit.FromSeconds(5)

solution = routing.SolveWithParameters(params)
if solution:
    index = routing.Start(0)
    route = []
    while not routing.IsEnd(index):
        route.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    route.append(manager.IndexToNode(index))
    print(f"Cost: {solution.ObjectiveValue()}, Route: {route}")
```

---

## 5. Progressive Disclosure Reference Guides & Examples

Load only the specific reference file needed for your current task:

| Topic | Reference File | When to Read |
| :--- | :--- | :--- |
| **Solver Architecture & Selection** | [`references/solver-selection-and-architecture.md`](./references/solver-selection-and-architecture.md) | Deciding between CP-SAT, MathOpt, MPSolver (`pywraplp`), Routing, or Graph solvers; comparing GLOP, PDLP, SCIP, Highs, Gurobi. |
| **CP-SAT Complete Modeling Guide** | [`references/cp-sat-guide.md`](./references/cp-sat-guide.md) | Modeling logic, channeling (`only_enforce_if`), `add_all_different`, `add_circuit`, `add_element`, `add_automaton`, callbacks, solution pools, and hints. |
| **LP, MILP & MathOpt Guide** | [`references/linear-mip-mathopt.md`](./references/linear-mip-mathopt.md) | Using `pywraplp` (MPSolver) and modern `ortools.math_opt.python.mathopt`, dual values, reduced costs, QP, and warm starts. |
| **Vehicle Routing (TSP & VRP)** | [`references/vehicle-routing.md`](./references/vehicle-routing.md) | Capacitated VRP (CVRP), Time Windows (VRPTW), Pickup & Delivery, Dropped Visits (`AddDisjunction`), multi-depot, and search strategies. |
| **Scheduling Patterns** | [`references/scheduling-patterns.md`](./references/scheduling-patterns.md) | Employee/Nurse Shift Scheduling, Job-Shop (JSP), Flexible Job-Shop (FJSP), RCPSP with `new_interval_var`, `add_no_overlap`, `add_cumulative`. |
| **Network Flows & Packing** | [`references/network-flows-and-packing.md`](./references/network-flows-and-packing.md) | `SimpleMaxFlow`, `SimpleMinCostFlow`, `SimpleLinearSumAssignment`, `KnapsackSolver`, Multiple Knapsack, and 1D/2D Bin Packing (`add_no_overlap_2d`). |
| **Debugging & Performance Tuning** | [`references/debugging-and-performance.md`](./references/debugging-and-performance.md) | Diagnosing `INFEASIBLE` models (Unsat Core / Assumptions, Slack relaxation), fixing slow solves, symmetry breaking, and float scaling. |
| **C++, Java & C# Cheatsheet** | [`references/multi-language-cheatsheet.md`](./references/multi-language-cheatsheet.md) | Translating OR-Tools models across Python, C++, Java, and C# (.NET). |

### Runnable Examples & Diagnostic Script
* **Diagnostic Script**: [`scripts/diagnose_env_and_model.py`](./scripts/diagnose_env_and_model.py) — Run `python skills/google-ortools/scripts/diagnose_env_and_model.py` to inspect installed OR-Tools version, available solver engines, and run solver smoke tests.
* **CP-SAT Job-Shop & Shift Scheduling**: [`examples/cpsat_scheduling_jobshop.py`](./examples/cpsat_scheduling_jobshop.py)
* **LP / MILP & MathOpt Production Planning**: [`examples/lp_mip_production_planning.py`](./examples/lp_mip_production_planning.py)
* **CVRPTW (Vehicle Routing with Time Windows & Drops)**: [`examples/vrp_time_windows_capacity.py`](./examples/vrp_time_windows_capacity.py)
* **Min-Cost Flow, Assignment & Knapsack**: [`examples/network_flow_and_knapsack.py`](./examples/network_flow_and_knapsack.py)
