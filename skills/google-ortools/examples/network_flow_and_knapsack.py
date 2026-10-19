#!/usr/bin/env python3
"""Reference Example: Min-Cost Network Flow, Linear Sum Assignment, and Knapsack.

Demonstrates modern OR-Tools v9.10+ pybind11 APIs:
- `ortools.graph.python.min_cost_flow.SimpleMinCostFlow`
- `ortools.graph.python.linear_sum_assignment.SimpleLinearSumAssignment`
- `ortools.algorithms.python.knapsack_solver.KnapsackSolver`
"""

from __future__ import annotations

import numpy as np
from ortools.algorithms.python import knapsack_solver
from ortools.graph.python import linear_sum_assignment, min_cost_flow


def run_min_cost_flow() -> None:
    print("--- 1. Minimum-Cost Network Flow ---")
    smcf = min_cost_flow.SimpleMinCostFlow()

    start_nodes = np.array([0, 0, 1, 1, 1, 2, 2, 3, 4])
    end_nodes = np.array([1, 2, 2, 3, 4, 3, 4, 4, 2])
    capacities = np.array([15, 8, 20, 4, 10, 15, 4, 20, 5])
    unit_costs = np.array([4, 4, 2, 2, 6, 1, 3, 2, 3])
    supplies = [20, 0, 0, -5, -15]

    arcs = smcf.add_arcs_with_capacity_and_unit_cost(
        start_nodes, end_nodes, capacities, unit_costs
    )
    smcf.set_nodes_supplies(np.arange(len(supplies)), supplies)

    status = smcf.solve()
    if status != smcf.Status.OPTIMAL:
        raise RuntimeError(f"MinCostFlow failed with status {status}")

    print(f"Optimal Flow Cost: {smcf.optimal_cost()}")
    for arc in arcs:
        if smcf.flow(arc) > 0:
            print(
                f"  Arc {smcf.tail(arc)} -> {smcf.head(arc)}: "
                f"flow={smcf.flow(arc)}/{smcf.capacity(arc)} @ cost={smcf.unit_cost(arc)}"
            )


def run_linear_assignment() -> None:
    print("\n--- 2. Bipartite Linear Sum Assignment ---")
    costs = [
        [90, 76, 75, 70],
        [35, 85, 55, 65],
        [125, 95, 90, 105],
        [45, 110, 95, 115],
    ]
    assignment = linear_sum_assignment.SimpleLinearSumAssignment()
    for w, row in enumerate(costs):
        for t, cost in enumerate(row):
            assignment.add_arc_with_cost(w, t, cost)

    status = assignment.solve()
    if status != assignment.Status.OPTIMAL:
        raise RuntimeError(f"Assignment failed: {status}")

    print(f"Minimum Assignment Cost: {assignment.optimal_cost()}")
    for w in range(assignment.num_nodes()):
        print(
            f"  Worker {w} -> Task {assignment.right_mate(w)} (cost={assignment.assignment_cost(w)})"
        )


def run_knapsack() -> None:
    print("\n--- 3. Multi-Dimensional 0-1 Knapsack ---")
    solver = knapsack_solver.KnapsackSolver(
        knapsack_solver.SolverType.KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER,
        "demo_knapsack",
    )
    values = [360, 83, 59, 130, 431, 67, 230, 52, 93, 125]
    weights = [[7, 0, 30, 22, 80, 94, 11, 81, 70, 64]]
    capacities = [180]

    solver.init(values, weights, capacities)
    best_val = solver.solve()
    packed = [i for i in range(len(values)) if solver.best_solution_contains(i)]
    total_weight = sum(weights[0][i] for i in packed)
    assert total_weight <= capacities[0], "Knapsack capacity exceeded!"
    print(f"Optimal Value: {best_val} | Packed Items: {packed} | Weight: {total_weight}/{capacities[0]}")


if __name__ == "__main__":
    run_min_cost_flow()
    run_linear_assignment()
    run_knapsack()
