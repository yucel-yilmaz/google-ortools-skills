# Network Flows, Assignment & Packing Guide

Google OR-Tools includes ultra-fast C++ graph and knapsack algorithms (`https://developers.google.com/optimization/flow` and `https://developers.google.com/optimization/pack`).

> **CRITICAL:** In OR-Tools v9.4+, the legacy `ortools.graph.pywrapgraph` and `ortools.algorithms.pywrapknapsack_solver` modules were replaced by pybind11 modules with `snake_case` methods.

---

## 1. Maximum Flow (`ortools.graph.python.max_flow`)

Finds the maximum total flow from a source node to a sink node through a directed capacitated network.

```python
import numpy as np
from ortools.graph.python import max_flow

smf = max_flow.SimpleMaxFlow()

# Batch add arcs (NumPy arrays or Python lists):
start_nodes = np.array([0, 0, 0, 1, 1, 2, 2, 3, 3])
end_nodes   = np.array([1, 2, 3, 2, 4, 3, 4, 2, 4])
capacities  = np.array([20, 30, 10, 40, 30, 10, 20, 5, 20])

all_arcs = smf.add_arcs_with_capacity(start_nodes, end_nodes, capacities)
# Or single arc: arc_id = smf.add_arc_with_capacity(tail, head, cap)

status = smf.solve(0, 4)  # (source_node, sink_node)
if status == smf.Status.OPTIMAL:
    print(f"Max Flow: {smf.optimal_flow()}")
    for arc in all_arcs:
        print(f"{smf.tail(arc)} -> {smf.head(arc)}: {smf.flow(arc)} / {smf.capacity(arc)}")
    print("Source-side min-cut nodes:", smf.get_source_side_min_cut())
```

---

## 2. Minimum-Cost Flow (`ortools.graph.python.min_cost_flow`)

Finds the cheapest way to route supplies to demands across a capacitated network.
* **Sign Convention for `supplies`**:
  * Positive (`> 0`): Supply node (source)
  * Negative (`< 0`): Demand node (sink)
  * Zero (`0`): Transshipment node
  * **Total supply MUST equal total demand** ($\sum_i \text{supply}_i = 0$), or `solve()` returns `Status.UNBALANCED` (use `solve_max_flow_with_min_cost()` if unbalanced).

```python
import numpy as np
from ortools.graph.python import min_cost_flow

smcf = min_cost_flow.SimpleMinCostFlow()

start_nodes = np.array([0, 0, 1, 1, 1, 2, 2, 3, 4])
end_nodes   = np.array([1, 2, 2, 3, 4, 3, 4, 4, 2])
capacities  = np.array([15, 8, 20, 4, 10, 15, 4, 20, 5])
unit_costs  = np.array([4, 4, 2, 2, 6, 1, 3, 2, 3])

all_arcs = smcf.add_arcs_with_capacity_and_unit_cost(
    start_nodes, end_nodes, capacities, unit_costs
)

supplies = [20, 0, 0, -5, -15]  # Sum == 0
smcf.set_nodes_supplies(np.arange(len(supplies)), supplies)

status = smcf.solve()
if status == smcf.Status.OPTIMAL:
    print(f"Minimum cost: {smcf.optimal_cost()}")
    for arc in all_arcs:
        if smcf.flow(arc) > 0:
            print(f"{smcf.tail(arc)} -> {smcf.head(arc)}: flow={smcf.flow(arc)}, cost={smcf.flow(arc) * smcf.unit_cost(arc)}")
```

---

## 3. Linear Sum Assignment (`ortools.graph.python.linear_sum_assignment`)

Solves 1-to-1 bipartite minimum-cost matching in $O(V^3)$ time (much faster than MIP for pure assignment):

```python
from ortools.graph.python import linear_sum_assignment

assignment = linear_sum_assignment.SimpleLinearSumAssignment()

# Add edges between left_node (worker 0..N-1) and right_node (task 0..N-1)
for w in range(num_workers):
    for t in range(num_tasks):
        assignment.add_arc_with_cost(w, t, cost_matrix[w][t])

status = assignment.solve()
if status == assignment.Status.OPTIMAL:
    print(f"Total assignment cost: {assignment.optimal_cost()}")
    for w in range(assignment.num_nodes()):
        print(f"Worker {w} -> Task {assignment.right_mate(w)} (cost={assignment.assignment_cost(w)})")
```

---

## 4. Knapsack Solver (`ortools.algorithms.python.knapsack_solver`)

For single or multi-dimensional 0-1 Knapsack problems without side constraints:

```python
from ortools.algorithms.python import knapsack_solver

solver = knapsack_solver.KnapsackSolver(
    knapsack_solver.SolverType.KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER,
    "knapsack_example",
)

values = [360, 83, 59, 130, 431, 67, 230, 52]
weights = [[7, 0, 30, 22, 80, 94, 11, 81]]  # List of weight dimensions!
capacities = [150]

solver.init(values, weights, capacities)
computed_value = solver.solve()

packed_items = [i for i in range(len(values)) if solver.best_solution_contains(i)]
print(f"Total value: {computed_value}, Packed indices: {packed_items}")
```

---

## 5. 1D Bin Packing & 2D Rectangle Packing in CP-SAT

### 1D Bin Packing (Minimize Number of Bins)
* Use `x[i, b]` (item $i$ in bin $b$) and `y[b]` (bin $b$ is used).
* **Symmetry Breaking**: Enforce `y[0] >= y[1] >= ... >= y[B-1]` so the solver does not waste time permuting identical bins!

```python
for b in range(max_bins - 1):
    model.add_implication(y[b + 1], y[b])  # Bin b+1 can only be used if bin b is used
```

### 2D Rectangle Packing (`add_no_overlap_2d`)
To pack 2D rectangles of size $(w_i, h_i)$ into a bounding box $(W, H)$ without overlapping:
```python
x_intervals = []
y_intervals = []
for i, (w, h) in enumerate(rectangles):
    x_start = model.new_int_var(0, W - w, f"x_{i}")
    y_start = model.new_int_var(0, H - h, f"y_{i}")
    x_intervals.append(model.new_fixed_size_interval_var(x_start, w, f"x_int_{i}"))
    y_intervals.append(model.new_fixed_size_interval_var(y_start, h, f"y_int_{i}"))

model.add_no_overlap_2d(x_intervals, y_intervals)
```
