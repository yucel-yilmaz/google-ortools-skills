#!/usr/bin/env python3
"""Reference Example: Job-Shop Scheduling (JSP) using Google OR-Tools CP-SAT.

Demonstrates:
- PEP 8 snake_case CP-SAT API (`new_int_var`, `new_interval_var`, `add_no_overlap`, `add_max_equality`)
- Horizon computation and NamedTuple task modeling
- Post-solve schedule extraction and non-overlap verification
"""

from __future__ import annotations

import collections
from typing import NamedTuple
from ortools.sat.python import cp_model


class TaskVar(NamedTuple):
    start: cp_model.IntVar
    end: cp_model.IntVar
    interval: cp_model.IntervalVar
    duration: int
    machine: int


def solve_jobshop() -> None:
    # Each job is a sequence of (machine_id, processing_time) operations
    jobs_data = [
        [(0, 3), (1, 2), (2, 2)],  # Job 0
        [(0, 2), (2, 1), (1, 4)],  # Job 1
        [(1, 4), (2, 3)],          # Job 2
    ]

    num_machines = 1 + max(task[0] for job in jobs_data for task in job)
    horizon = sum(task[1] for job in jobs_data for task in job)

    model = cp_model.CpModel()
    all_tasks: dict[tuple[int, int], TaskVar] = {}
    machine_to_intervals: dict[int, list[cp_model.IntervalVar]] = collections.defaultdict(list)

    # 1. Create interval variables for each operation
    for job_id, job in enumerate(jobs_data):
        for task_id, (machine, duration) in enumerate(job):
            suffix = f"_j{job_id}_t{task_id}"
            start_var = model.new_int_var(0, horizon, f"start{suffix}")
            end_var = model.new_int_var(0, horizon, f"end{suffix}")
            interval_var = model.new_interval_var(
                start_var, duration, end_var, f"interval{suffix}"
            )
            all_tasks[job_id, task_id] = TaskVar(
                start=start_var,
                end=end_var,
                interval=interval_var,
                duration=duration,
                machine=machine,
            )
            machine_to_intervals[machine].append(interval_var)

    # 2. Disjunctive machine constraints (no two tasks on the same machine can overlap)
    for machine in range(num_machines):
        model.add_no_overlap(machine_to_intervals[machine])

    # 3. Precedence constraints within each job
    for job_id, job in enumerate(jobs_data):
        for task_id in range(len(job) - 1):
            model.add(
                all_tasks[job_id, task_id + 1].start >= all_tasks[job_id, task_id].end
            )

    # 4. Objective: Minimize makespan (completion time of the last job)
    makespan = model.new_int_var(0, horizon, "makespan")
    model.add_max_equality(
        makespan,
        [all_tasks[job_id, len(job) - 1].end for job_id, job in enumerate(jobs_data)],
    )
    model.minimize(makespan)

    # 5. Configure solver and solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    solver.parameters.num_search_workers = 4
    status = solver.solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"No solution found: {solver.status_name(status)}")

    print(f"Status: {solver.status_name(status)} | Optimal Makespan: {solver.objective_value:.0f}")
    for machine in range(num_machines):
        assigned = []
        for (job_id, task_id), t in all_tasks.items():
            if t.machine == machine:
                s_val = solver.value(t.start)
                e_val = solver.value(t.end)
                assigned.append((s_val, e_val, f"Job {job_id} Task {task_id} [{s_val}..{e_val}]"))
        assigned.sort()
        # Verify non-overlapping invariant on extracted solution
        for i in range(len(assigned) - 1):
            assert assigned[i][1] <= assigned[i + 1][0], f"Overlap detected on machine {machine}!"
        print(f"  Machine {machine}: " + " -> ".join(item[2] for item in assigned))


if __name__ == "__main__":
    solve_jobshop()
