# Solver Selection & OR-Tools Architecture

Google OR-Tools (`https://developers.google.com/optimization`) is not a single solver—it is a suite of specialized optimization engines and unified modeling layers. Selecting the wrong module can make a model 100x slower or impossible to express cleanly.

---

## 1. Decision Tree for Solver Selection

```text
What is the structure of your problem?
│
├─► Pure Graph / Network Structure?
│   ├─► Maximum throughput s -> t               ──► ortools.graph.python.max_flow (SimpleMaxFlow)
│   ├─► Cheapest flow with supplies/demands     ──► ortools.graph.python.min_cost_flow (SimpleMinCostFlow)
│   └─► 1-to-1 Bipartite matching               ──► ortools.graph.python.linear_sum_assignment
│
├─► Pure 0-1 Knapsack (weights + values, no extra logic)?
│   └─► Single or multi-dimensional capacity    ──► ortools.algorithms.python.knapsack_solver
│
├─► Vehicle Fleet Routing (TSP, VRP, CVRP, VRPTW, Pickup/Delivery)?
│   ├─► Distance/time matrix + route dimensions ──► ortools.constraint_solver.pywrapcp (RoutingModel)
│   └─► Small tightly-coupled routing + custom logic ──► ortools.sat.python.cp_model (add_multiple_circuit)
│
├─► Scheduling (Intervals, Shifts, Job-Shop, Cumulative Resources)?
│   └─► Always use CP-SAT                       ──► ortools.sat.python.cp_model
│
├─► Continuous Variables (x ∈ ℝ) Required?
│   ├─► Pure Linear Programming (LP)            ──► pywraplp ("GLOP" or "PDLP") or mathopt (SolverType.GLOP / PDLP)
│   ├─► Mixed-Integer Linear Programming (MILP) ──► pywraplp ("SCIP", "HIGHS", "CBC", "GUROBI") or mathopt
│   └─► Quadratic Objective / Constraints (QP)  ──► ortools.math_opt.python.mathopt (SolverType.GSCIP / GUROBI)
│
└─► Pure Discrete / Integer / Combinatorial / Logical Problem?
    └─► Default & strongest choice              ──► ortools.sat.python.cp_model (CP-SAT)
```

---

## 2. Comparing Core Engines

### CP-SAT (`ortools.sat.python.cp_model`)
* **Engine Type**: Portfolio solver combining SAT (Boolean Satisfiability), Lazy Clause Generation (LCG), Constraint Programming propagators, LP relaxation cuts, and Large Neighborhood Search (LNS).
* **Strengths**:
  * World-class performance on scheduling (`IntervalVar`, `add_no_overlap`, `add_cumulative`), assignment, rostering, configuration, packing (`add_no_overlap_2d`), and logical constraints (`only_enforce_if`).
  * Automatically utilizes multi-core parallelism (`num_search_workers`).
  * Built-in infeasibility diagnostics via assumptions (`sufficient_assumptions_for_infeasibility()`).
* **Limitations**:
  * **Integers only**: Does not support continuous floating-point variables directly. Floating-point coefficients/bounds must be scaled to integers (e.g., `int(round(val * 1000))`).
  * Does not produce LP dual values (shadow prices) or reduced costs.

### MPSolver (`ortools.linear_solver.pywraplp`)
* **Engine Type**: Classical mathematical programming wrapper for LP and MILP solvers.
* **Supported Backends**:
  * `"GLOP"`: Google's in-house Revised Simplex LP solver. Fast, exact for small-to-medium continuous LPs. Supports dual values and basis status.
  * `"PDLP"`: Google's Primal-Dual Hybrid Gradient (first-order) LP solver. Scales to **millions of variables/constraints** where simplex/barrier runs out of memory.
  * `"SCIP"`: Bundled high-performance Mixed-Integer Programming solver (check license terms for commercial use).
  * `"CBC"`: Coin-OR Branch and Cut open-source MILP solver (EPL-2.0).
  * `"HIGHS"`: Modern high-performance open-source LP/MILP/QP solver (MIT).
  * `"SAT"`: Runs CP-SAT behind the `pywraplp` interface (automatically discretizes/scales or requires integer variables, though using `cp_model` directly is preferred).
  * `"GUROBI"` / `"CPLEX"` / `"XPRESS"`: Commercial solvers (requires local license installation).

### MathOpt (`ortools.math_opt.python.mathopt`)
* **Engine Type**: Google's next-generation C++/Python mathematical optimization modeling layer replacing `pywraplp` for advanced use cases.
* **Why Choose MathOpt over `pywraplp`**:
  * First-class Pythonic operator overloading and type annotations.
  * Supports **Quadratic Objectives and Constraints** (QP / MIQP).
  * Supports **Incremental Solves** (`UpdateTracker`), **Warm Starts / Solution Hints**, **Solver-Independent Callbacks** (branch-and-cut lazy constraints), and **Multiple Objectives**.
  * Switches seamlessly between `SolverType.GLOP`, `SolverType.PDLP`, `SolverType.CP_SAT`, `SolverType.GSCIP`, `SolverType.HIGHS`, `SolverType.OSQP`, and `SolverType.GUROBI`.

### Routing Library (`ortools.constraint_solver.pywrapcp`)
* **Engine Type**: Constraint Programming solver specialized for graph path/tour construction + metaheuristic local search.
* **Strengths**:
  * Scales to thousands of stops using fast construction heuristics (`PATH_CHEAPEST_ARC`, `PARALLEL_CHEAPEST_INSERTION`) and metaheuristics (`GUIDED_LOCAL_SEARCH`, `TABU_SEARCH`, `SIMULATED_ANNEALING`).
  * Native `RoutingDimension` accumulator tracks cumulative quantities along vehicle routes (time with waiting/slack, load capacity, battery state-of-charge).
* **When NOT to use**:
  * If your routing problem has very few nodes ($N \le 40$) and requires proving exact optimality or complex non-route resource constraints, `cp_model.add_multiple_circuit` in CP-SAT can be easier to customize and proves optimality bounds.
