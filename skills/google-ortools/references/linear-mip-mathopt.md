# Linear Programming (LP), MILP & MathOpt Guide

Google OR-Tools provides two interfaces for continuous Linear Programming (LP), Mixed-Integer Linear Programming (MILP), and Quadratic Programming (QP):
1. **`ortools.linear_solver.pywraplp` (`MPSolver`)**: The classic, battle-tested LP/MILP wrapper documented across `developers.google.com/optimization/lp` and `mip`.
2. **`ortools.math_opt.python.mathopt` (`MathOpt`)**: The modern, solver-agnostic modeling toolkit supporting LP, MILP, QP, incremental updates, warm starts, and callbacks.

---

## 1. Classical LP & MILP with `pywraplp` (`MPSolver`)

### Choosing the Solver String in `pywraplp.Solver.CreateSolver(solver_id)`

| `solver_id` | Problem Type | Notes |
| :--- | :--- | :--- |
| `"GLOP"` | Continuous LP | Google's exact Revised Simplex solver. Fast, supports duals & reduced costs. **Cannot solve integer variables.** |
| `"PDLP"` | Large Continuous LP | First-order primal-dual hybrid gradient solver. Ideal for huge LPs ($10^5$–$10^7$ nonzeros). |
| `"SCIP"` | MILP | High-performance mixed-integer solver bundled with OR-Tools. |
| `"HIGHS"` | LP / MILP | Modern open-source solver (MIT license); very strong simplex, interior point, and MIP performance. |
| `"CBC"` | MILP | Coin-OR Branch & Cut open-source MILP solver. |
| `"SAT"` | Integer / MILP | Uses CP-SAT under the hood. (Prefer `cp_model` directly when using CP-SAT). |
| `"GUROBI"` / `"CPLEX"` | LP / MILP | Requires external commercial license on host machine. |

### Complete `pywraplp` Pattern (LP with Duals & Reduced Costs)
```python
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver("GLOP")
if not solver:
    raise RuntimeError("GLOP solver could not be initialized.")

inf = solver.infinity()
x = solver.NumVar(0.0, inf, "x")
y = solver.NumVar(0.0, inf, "y")

# Keep references to constraints to inspect dual values (shadow prices)
c1 = solver.Add(x + 2 * y <= 14.0, "resource_A")
c2 = solver.Add(3 * x - y >= 0.0, "balance")
c3 = solver.Add(x - y <= 2.0, "limit")

solver.Maximize(3 * x + 4 * y)

status = solver.Solve()
if status == pywraplp.Solver.OPTIMAL:
    print(f"Optimal Objective: {solver.Objective().Value():.4f}")
    print(f"x = {x.solution_value():.4f} (reduced cost: {x.reduced_cost():.4f})")
    print(f"y = {y.solution_value():.4f} (reduced cost: {y.reduced_cost():.4f})")
    print(f"Shadow price of resource_A: {c1.dual_value():.4f}")
elif status == pywraplp.Solver.FEASIBLE:
    print("Suboptimal feasible solution found before limit.")
elif status in (pywraplp.Solver.INFEASIBLE, pywraplp.Solver.UNBOUNDED):
    print("Model is infeasible or unbounded.")
```

### Defining MILP Arrays in `pywraplp`
```python
solver = pywraplp.Solver.CreateSolver("SCIP")
# Binary variable:
b = solver.BoolVar("b")
# General integer variable:
n = solver.IntVar(0, 50, "n")

# Fast summation using solver.Sum()
items = [solver.BoolVar(f"item_{i}") for i in range(100)]
weights = [i * 1.5 for i in range(100)]
solver.Add(solver.Sum(items[i] * weights[i] for i in range(100)) <= 120.0)
```

---

## 2. Modern Mathematical Optimization with `MathOpt`

`ortools.math_opt.python.mathopt` is Google's modern modeling library designed to cleanly separate the model from the solver engine (`SolverType`).

### Complete `mathopt` Pattern (LP / MILP / QP)
```python
from ortools.math_opt.python import mathopt

model = mathopt.Model(name="production_plan")

# Variables
x = model.add_variable(lb=0.0, ub=100.0, is_integer=False, name="x")
y = model.add_integer_variable(lb=0, ub=50, name="y")
z = model.add_binary_variable(name="z")

# Constraints
c1 = model.add_linear_constraint(2.5 * x + 3.0 * y <= 120.0, name="capacity")
# Indicator constraint: z == 1 => y >= 10
model.add_indicator_constraint(indicator=z, implied_constraint=(y >= 10), activate_on_zero=False)

# Objective (Linear or Quadratic!)
model.maximize(10.0 * x + 15.0 * y - 50.0 * z)

# Configure solve parameters
params = mathopt.SolveParameters(time_limit=mathopt.datetime.timedelta(seconds=30))

# Solve with any supported SolverType: GSCIP, HIGHS, CP_SAT, GLOP, PDLP, GUROBI, OSQP
result = mathopt.solve(model, mathopt.SolverType.HIGHS, params=params)

if result.termination.reason in (
    mathopt.TerminationReason.OPTIMAL,
    mathopt.TerminationReason.FEASIBLE,
):
    print(f"Objective: {result.objective_value():.4f}")
    vals = result.variable_values()
    print(f"x={vals[x]:.4f}, y={vals[y]:.0f}, z={vals[z]:.0f}")
else:
    print(f"Termination: {result.termination}")
```

### Quadratic Programming (QP) in `MathOpt`
Unlike `pywraplp`, `mathopt` natively supports quadratic objectives and constraints:
```python
model = mathopt.Model(name="portfolio_qp")
w1 = model.add_variable(lb=0.0, ub=1.0, name="w1")
w2 = model.add_variable(lb=0.0, ub=1.0, name="w2")
model.add_linear_constraint(w1 + w2 == 1.0)

# Minimize portfolio variance: w1^2 + 0.5*w1*w2 + 2*w2^2 - expected return
model.minimize(w1 * w1 + 0.5 * w1 * w2 + 2.0 * w2 * w2 - 0.08 * w1 - 0.12 * w2)

# Solve continuous/mixed-integer QP out-of-the-box with GSCIP (or GUROBI if licensed)
result = mathopt.solve(model, mathopt.SolverType.GSCIP)
```

---

## 3. Common LP/MILP Pitfalls & Best Practices

1. **Avoid Huge Big-M Constants**:
   * Writing `x <= 1e9 * z` causes severe numerical instability (trickle flow where `z = 1e-9` lets `x = 1.0`).
   * **Fix**: Use the tightest valid upper bound $M = \max(x)$ (e.g., `M = capacity`), or use `mathopt` indicator constraints / CP-SAT `only_enforce_if`.
2. **Never Call `GLOP` on Models with `IntVar` / `BoolVar`**:
   * `GLOP` ignores integrality constraints and solves the continuous LP relaxation! Always use `"SCIP"`, `"HIGHS"`, `"CBC"`, or `cp_model` when variables are discrete.
3. **Exporting Models for Debugging**:
   * In `pywraplp`: `lp_str = solver.ExportModelAsLpFormat(False)` or `mps_str = solver.ExportModelAsMpsFormat(False, False)`.
