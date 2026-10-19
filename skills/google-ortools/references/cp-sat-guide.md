# CP-SAT (`ortools.sat.python.cp_model`) Complete Modeling Guide

CP-SAT is the flagship solver of Google OR-Tools (`https://developers.google.com/optimization/cp/cp_solver`). Always use the PEP 8 `snake_case` API introduced in OR-Tools v9.10+.

---

## 1. Variables & Domains

```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()

# 1. Standard Integer Variable: x in [lb, ub] (inclusive)
x = model.new_int_var(0, 100, "x")

# 2. Boolean Variable: b in {0, 1}
b = model.new_bool_var("b")
not_b = ~b  # or b.negated()

# 3. Non-contiguous Domain Variable: y in {1, 3, 5} U [10, 15]
domain = cp_model.Domain.from_intervals([[1, 1], [3, 3], [5, 5], [10, 15]])
y = model.new_int_var_from_domain(domain, "y")

# 4. Constant
c = model.new_constant(42)

# 5. Pandas / Indexed Series (v9.10+)
# If using pandas Index `idx`, creates a pd.Series of variables:
# vars_series = model.new_int_var_series(name="flow", index=df.index, lower_bounds=0, upper_bounds=df["cap"])
```

---

## 2. Linear Constraints & Expressions

Always use `cp_model.LinearExpr` for large summations to avoid quadratic Python AST building overhead:

```python
vars_list = [model.new_int_var(0, 10, f"v_{i}") for i in range(100)]
weights = list(range(1, 101))

# Fast sum and weighted sum
model.add(cp_model.LinearExpr.sum(vars_list) <= 250)
model.add(cp_model.LinearExpr.weighted_sum(vars_list, weights) >= 1000)

# Two-sided range constraint: 10 <= expr <= 50
model.add_linear_constraint(cp_model.LinearExpr.sum(vars_list), 10, 50)
```

---

## 3. Logical Constraints & Reification (Channeling)

### Boolean Logic
```python
a = model.new_bool_var("a")
b = model.new_bool_var("b")
c = model.new_bool_var("c")

model.add_implication(a, b)          # a => b
model.add_bool_or([a, b, ~c])        # a OR b OR (NOT c)
model.add_bool_and([a, ~b])          # a AND (NOT b)
model.add_bool_xor([a, b])           # a XOR b (odd number of true literals)
model.add_at_most_one([a, b, c])     # a + b + c <= 1 (clique cut aware)
model.add_exactly_one([a, b, c])     # a + b + c == 1
```

### Half-Reification (`b => constraint`)
```python
model.add(x >= 10).only_enforce_if(b)
# Or conditioned on multiple literals (conjunction: b1 AND NOT b2 => x >= 10)
model.add(x >= 10).only_enforce_if([b, ~c])
```

### Full Equivalence Channeling (`b <=> (x >= 10)`)
CP-SAT does not allow `b == (x >= 10)` directly inside `model.add()`. Instead, post both directions of the implication:
```python
is_large = model.new_bool_var("is_large")
model.add(x >= 10).only_enforce_if(is_large)
model.add(x < 10).only_enforce_if(~is_large)  # Equivalent to x <= 9
```

### Reifying Equality (`b <=> (x == k)`)
To channel `b <=> (x == 5)` when `x` can be both `< 5` and `> 5`:
```python
is_five = model.new_bool_var("is_five")
model.add(x == 5).only_enforce_if(is_five)
model.add(x != 5).only_enforce_if(~is_five)
```

---

## 4. Global & Non-Linear Constraints

### AllDifferent
```python
# All variables take distinct values
model.add_all_different([x1, x2, x3, x4])
```

### Min, Max, Abs, Multiplication, Division, Modulo
```python
# target == max(x, y, 5)
target_max = model.new_int_var(0, 100, "target_max")
model.add_max_equality(target_max, [x, y, 5])

# target == min(x, y)
target_min = model.new_int_var(0, 100, "target_min")
model.add_min_equality(target_min, [x, y])

# target == |x - y|
diff_abs = model.new_int_var(0, 100, "diff_abs")
model.add_abs_equality(diff_abs, x - y)

# prod == x * y
prod = model.new_int_var(0, 10_000, "prod")
model.add_multiplication_equality(prod, [x, y])

# div == x // y (integer truncated division, y != 0)
div = model.new_int_var(0, 100, "div")
model.add_division_equality(div, x, y)

# mod == x % y
mod = model.new_int_var(0, 100, "mod")
model.add_modulo_equality(mod, x, y)
```

### Element Constraint (Variable Indexing: `target == array[index_var]`)
Never index a Python list with an `IntVar` (`arr[index_var]` raises `TypeError`). Use `add_element`:
```python
costs = [15, 40, 25, 90]
idx = model.new_int_var(0, len(costs) - 1, "idx")
selected_cost = model.new_int_var(0, max(costs), "selected_cost")
model.add_element(idx, costs, selected_cost)
```

### Table Constraints (`add_allowed_assignments` / `add_forbidden_assignments`)
```python
# Tuple (x, y, z) must match one of the allowed rows
allowed_tuples = [(1, 2, 10), (1, 3, 20), (2, 1, 15)]
model.add_allowed_assignments([x, y, z], allowed_tuples)
```

### Circuit & Multiple Circuit (TSP / Subtour Elimination)
```python
# arcs is a list of (tail_node, head_node, literal)
# Forces selected arcs (literal == True) to form a single Hamiltonian cycle
# Self-loops (i, i, lit_skip_i) allow skipping optional nodes!
model.add_circuit(arcs)

# Multiple sub-circuits (e.g. multi-vehicle tours through depot 0):
model.add_multiple_circuit(arcs)
```

---

## 5. Objectives, Multi-Objective / Lexicographic Optimization

### Single Objective
```python
model.minimize(total_cost)
# or
model.maximize(total_profit)
```

### Lexicographic (Hierarchical) Multi-Objective Optimization
To optimize Primary Objective $f_1$ first, and then Secondary Objective $f_2$ without degrading $f_1$:
```python
# Stage 1: Minimize primary objective (e.g., makespan)
model.minimize(makespan)
solver = cp_model.CpSolver()
status1 = solver.solve(model)

if status1 in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    best_makespan = int(round(solver.objective_value))
    # Lock primary objective (or allow a small tolerance, e.g., <= best_makespan)
    model.add(makespan <= best_makespan)
    # Hint previous solution for warm start!
    model.clear_hints()
    for v in all_vars:
        model.add_hint(v, solver.value(v))
    # Stage 2: Minimize secondary objective (e.g., total tardiness)
    model.minimize(total_tardiness)
    status2 = solver.solve(model)
```

---

## 6. Solution Callbacks, Enumeration & Search Parameters

### Enumerating All Solutions (Satisfaction Problems Only)
To enumerate all feasible solutions, the model **must not** have an objective function, and you must set `solver.parameters.enumerate_all_solutions = True`:

```python
class SolutionCollector(cp_model.CpSolverSolutionCallback):
    def __init__(self, variables: list[cp_model.IntVar], limit: int = 100):
        super().__init__()
        self._variables = variables
        self._limit = limit
        self.solutions = []

    def on_solution_callback(self) -> None:
        self.solutions.append({v.name: self.value(v) for v in self._variables})
        if len(self.solutions) >= self._limit:
            self.stop_search()

collector = SolutionCollector([x, y], limit=50)
solver = cp_model.CpSolver()
solver.parameters.enumerate_all_solutions = True
status = solver.solve(model, collector)
```
> **Note:** Both `on_solution_callback` and `OnSolutionCallback` are supported by `CpSolverSolutionCallback`. Inside the callback, use `self.value(v)`, `self.boolean_value(b)`, `self.objective_value`, `self.best_objective_bound`, and `self.wall_time`.

### Key Solver Parameters
```python
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60.0       # Always set a bound in production
solver.parameters.num_search_workers = 8           # Parallel portfolio search (0 = all CPU cores)
solver.parameters.relative_gap_limit = 0.01        # Stop within 1% of optimality bound
solver.parameters.absolute_gap_limit = 1.0         # Stop when gap <= 1
solver.parameters.log_search_progress = True       # Stream progress to stdout
solver.parameters.random_seed = 42                 # Improve reproducibility
```
