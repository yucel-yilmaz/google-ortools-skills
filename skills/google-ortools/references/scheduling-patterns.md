# Scheduling Patterns in CP-SAT (`cp_model`)

Google OR-Tools CP-SAT (`https://developers.google.com/optimization/scheduling`) is the industry-standard open-source solver for Employee Shift Rostering, Job-Shop Scheduling (JSP), Flexible Job-Shop Scheduling (FJSP), and Resource-Constrained Project Scheduling (RCPSP).

---

## 1. Employee / Nurse Shift Rostering Pattern

### Decision Variables
Create boolean variables indexed by `(employee, day, shift)`:
```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
shifts = {}
for e in range(num_employees):
    for d in range(num_days):
        for s in range(num_shifts):
            shifts[e, d, s] = model.new_bool_var(f"shift_e{e}_d{d}_s{s}")
```

### Standard Rostering Constraints
1. **Coverage Demand** (Each shift $s$ on day $d$ requires `demand[d, s]` employees):
   ```python
   for d in range(num_days):
       for s in range(num_shifts):
           model.add(
               cp_model.LinearExpr.sum([shifts[e, d, s] for e in range(num_employees)])
               == demand[d, s]
           )
   ```
2. **At Most One Shift per Employee per Day**:
   ```python
   for e in range(num_employees):
       for d in range(num_days):
           model.add_at_most_one([shifts[e, d, s] for s in range(num_shifts)])
   ```
3. **Forbidden Shift Transitions** (e.g., Night Shift `s=2` on day $d$ cannot be followed by Morning Shift `s=0` on day $d+1$):
   ```python
   for e in range(num_employees):
       for d in range(num_days - 1):
           model.add_implication(shifts[e, d, 2], ~shifts[e, d + 1, 0])
   ```
4. **Max Consecutive Working Days** (e.g., at most $K = 5$ consecutive days worked in any $(K+1)$-day rolling window):
   ```python
   for e in range(num_employees):
       worked_day = []
       for d in range(num_days):
           w = model.new_bool_var(f"worked_e{e}_d{d}")
           # Since at most one shift per day, w == sum_s shifts[e, d, s]
           model.add(w == cp_model.LinearExpr.sum([shifts[e, d, s] for s in range(num_shifts)]))
           worked_day.append(w)
       for d in range(num_days - K):
           model.add(cp_model.LinearExpr.sum(worked_day[d : d + K + 1]) <= K)
   ```
5. **Workload Balancing (Min-Max Fairness)**:
   ```python
   min_shifts_var = model.new_int_var(0, num_days, "min_shifts")
   max_shifts_var = model.new_int_var(0, num_days, "max_shifts")
   totals = [
       cp_model.LinearExpr.sum([shifts[e, d, s] for d in range(num_days) for s in range(num_shifts)])
       for e in range(num_employees)
   ]
   for t in totals:
       model.add(min_shifts_var <= t)
       model.add(t <= max_shifts_var)
   # Minimize spread (max - min) or combine with preference rewards
   model.minimize(max_shifts_var - min_shifts_var)
   ```

---

## 2. Interval Variables & Job-Shop Scheduling (JSP)

In CP-SAT, an `IntervalVar` enforces `start + size == end` automatically and powers global propagators (`add_no_overlap` and `add_cumulative`).

### Creating Interval Variables
```python
# Fixed duration interval:
start = model.new_int_var(0, horizon, "start")
end = model.new_int_var(0, horizon, "end")
interval = model.new_interval_var(start, duration, end, "task_interval")

# Or fixed-size shorthand (start + const_size):
interval_fixed = model.new_fixed_size_interval_var(start, duration, "fixed_interval")
```

### Job-Shop Scheduling Pattern (`add_no_overlap`)
1. **Disjunctive Machine Constraint** (No two tasks on machine $m$ can overlap in time):
   ```python
   model.add_no_overlap(machine_to_intervals[m])
   ```
2. **Precedence Within a Job** (Operation $t+1$ starts after operation $t$ finishes):
   ```python
   model.add(job_tasks[j, t + 1].start >= job_tasks[j, t].end)
   ```
3. **Minimizing Makespan** ($C_{\max} = \max_j \text{end}_j$):
   ```python
   makespan = model.new_int_var(0, horizon, "makespan")
   model.add_max_equality(makespan, [job_tasks[j, last_t].end for j in range(num_jobs)])
   model.minimize(makespan)
   ```

---

## 3. Flexible Job-Shop Scheduling (FJSP) with Optional Intervals

When task $(j, t)$ can be assigned to **one of several candidate machines** $m \in M_{j,t}$ with machine-dependent duration $d_{j,t,m}$:

```python
alt_presences = []
for m, duration in candidate_machines:
    is_selected = model.new_bool_var(f"sel_j{j}_t{t}_m{m}")
    alt_start = model.new_int_var(0, horizon, f"start_j{j}_t{t}_m{m}")
    alt_end = model.new_int_var(0, horizon, f"end_j{j}_t{t}_m{m}")
    alt_interval = model.new_optional_interval_var(
        alt_start, duration, alt_end, is_selected, f"opt_j{j}_t{t}_m{m}"
    )
    machine_to_intervals[m].append(alt_interval)
    alt_presences.append(is_selected)

    # Link alternative start/end to master task start/end when selected
    model.add(master_start == alt_start).only_enforce_if(is_selected)
    model.add(master_end == alt_end).only_enforce_if(is_selected)

# Exactly one candidate machine must be chosen for the task
model.add_exactly_one(alt_presences)
```

---

## 4. Cumulative Resource Scheduling (`add_cumulative`) & Sequence Setups

### Cumulative Capacity (RCPSP)
When tasks run in parallel and consume `demands[i]` units of a renewable resource (e.g., workers, power, memory) with total capacity `max_capacity`:
```python
model.add_cumulative(intervals, demands, max_capacity)
```

### Sequence-Dependent Setup Times (`add_circuit` + `add_no_overlap`)
When switching from task $i$ to task $j$ on the same machine requires `setup_time[i][j]`:
```python
arcs = []
for i in range(num_tasks):
    # Dummy node 0 represents start/end of the machine sequence
    first_lit = model.new_bool_var(f"first_{i}")
    last_lit = model.new_bool_var(f"last_{i}")
    arcs.append((0, i + 1, first_lit))
    arcs.append((i + 1, 0, last_lit))
    for j in range(num_tasks):
        if i == j:
            continue
        lit = model.new_bool_var(f"seq_{i}_to_{j}")
        arcs.append((i + 1, j + 1, lit))
        # Enforce setup time when j immediately follows i
        model.add(starts[j] >= ends[i] + setup_time[i][j]).only_enforce_if(lit)

model.add_circuit(arcs)
```
