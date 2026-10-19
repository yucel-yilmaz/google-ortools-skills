# Debugging Infeasibility & Performance Tuning Guide

When an OR-Tools model returns `INFEASIBLE`, `MODEL_INVALID`, or takes too long to converge, follow these systematic debugging and tuning workflows.

---

## 1. Diagnosing `MODEL_INVALID` in CP-SAT

If `solver.solve(model)` returns `cp_model.MODEL_INVALID`:
1. Call `print(model.validate())` immediately. It returns a human-readable string identifying the exact variable or constraint index causing the failure.
2. Common causes of `MODEL_INVALID`:
   * Lower bound greater than upper bound (`lb > ub`) in `new_int_var(lb, ub, name)`.
   * Negative duration (`size < 0`) or inconsistent `start + size != end` in `new_interval_var`.
   * Integer overflow: bounds or objective coefficients exceeding $2^{62}$ (keep variable bounds tight, e.g., `[0, horizon]`, never `[-10**18, 10**18]`).
   * Floating-point numbers or `NaN` accidentally passed into `cp_model`.

---

## 2. Diagnosing `INFEASIBLE` in CP-SAT

### Method A: Assumptions (Unsat Core Extraction)
Attach boolean assumption literals to suspect constraints to find a minimal conflicting subset:

```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
x = model.new_int_var(0, 10, "x")

# Create assumption literals for constraint groups
a_min_demand = model.new_bool_var("assume_min_demand")
a_max_budget = model.new_bool_var("assume_max_budget")
a_fixed_rule = model.new_bool_var("assume_fixed_rule")

model.add(x >= 8).only_enforce_if(a_min_demand)
model.add(2 * x <= 10).only_enforce_if(a_max_budget)
model.add(x != 5).only_enforce_if(a_fixed_rule)

# Tell CP-SAT to assume all three literals are True
model.add_assumptions([a_min_demand, a_max_budget, a_fixed_rule])

solver = cp_model.CpSolver()
status = solver.solve(model)

if status == cp_model.INFEASIBLE:
    conflicting_indices = solver.sufficient_assumptions_for_infeasibility()
    for idx in conflicting_indices:
        conflict_var = model.get_bool_var_from_proto_index(idx)
        print(f"Conflicting constraint assumption: {conflict_var.name}")
```
> **Note:** Assumptions only work on satisfaction checks or when finding why no feasible solution exists. Remove `add_assumptions` once the bug is fixed for maximum multi-worker speed.

### Method B: Soft Constraints with High-Penalty Slack Variables
In production systems (especially rostering and routing), hard constraints on demand or capacity often conflict on edge-case datasets. Replace brittle hard constraints with penalized slack variables:

```python
# Instead of: model.add(supply >= demand)
unmet_demand = model.new_int_var(0, demand, f"unmet_{d}")
model.add(supply + unmet_demand >= demand)
penalty_terms.append(10_000 * unmet_demand)
```
After solving, any `solver.value(unmet_demand) > 0` pinpoints exactly which constraint could not be satisfied and by how much.

---

## 3. Scaling Floating-Point Values for CP-SAT

Because CP-SAT operates strictly on integers, scale float inputs safely:

```python
SCALE = 1000  # 3 decimal places

def to_int(val: float) -> int:
    return int(round(val * SCALE))

# Example: 0.375 * x + 1.25 * y <= 10.5
model.add(to_int(0.375) * x + to_int(1.25) * y <= to_int(10.5))

# After solving, divide scaled objective by SCALE:
real_objective = solver.objective_value / SCALE
```
> **Caution:** Do not use an unnecessarily huge `SCALE` (e.g., `10**9`), which causes integer overflow or weak LP relaxations. Use the smallest scale factor that preserves required precision (`100` or `1000`).

---

## 4. Performance Tuning Checklist for CP-SAT

1. **Use Multi-Core Search**:
   * Set `solver.parameters.num_search_workers = 8` (or `0` to use all physical/logical cores). Different workers automatically run complementary strategies (LNS, LP cut generators, core-guided search, quick restart).
2. **Tighten Variable Bounds**:
   * Never initialize `model.new_int_var(0, 10**9, "t")` if the scheduling horizon is `sum(durations) == 1440`. Tight bounds dramatically strengthen LP relaxations and interval propagation.
3. **Break Symmetries**:
   * If vehicles, bins, or workers are identical, order them:
     * Bin packing: `model.add(bin_load[b] >= bin_load[b + 1])`
     * Identical workers: `model.add(total_shifts[w] >= total_shifts[w + 1])`
4. **Prefer Global Constraints over Pairwise Decompositions**:
   * Use `model.add_all_different(vars)` instead of $O(n^2)$ pairwise `x_i != x_j`.
   * Use `model.add_no_overlap(intervals)` instead of $O(n^2)$ pairwise disjunctive booleans.
   * Use `model.add_at_most_one(bools)` instead of pairwise `~b_i | ~b_j`.
5. **Provide Warm-Start Hints**:
   * If you have a greedy heuristic solution, pass it via `model.add_hint(var, val)` before calling `solver.solve(model)`.
