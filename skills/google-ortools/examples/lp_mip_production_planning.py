#!/usr/bin/env python3
"""Reference Example: Production Planning & Blending using pywraplp (MPSolver) and MathOpt.

Demonstrates:
1. Continuous LP with Dual Values (Shadow Prices) and Reduced Costs using `pywraplp` ("GLOP")
2. Mixed-Integer Linear Programming (MILP) with Fixed Setup Costs using `mathopt`
"""

from __future__ import annotations

from ortools.linear_solver import pywraplp
from ortools.math_opt.python import mathopt


def solve_continuous_lp_with_duals() -> None:
    print("--- 1. Continuous LP with Duals (GLOP) ---")
    solver = pywraplp.Solver.CreateSolver("GLOP")
    if not solver:
        raise RuntimeError("GLOP solver unavailable.")

    inf = solver.infinity()
    x1 = solver.NumVar(0.0, inf, "Product_A")
    x2 = solver.NumVar(0.0, inf, "Product_B")

    # Resource constraints (save handles to inspect shadow prices)
    c_labor = solver.Add(2.0 * x1 + 1.0 * x2 <= 100.0, "Labor_Hours")
    c_machine = solver.Add(1.0 * x1 + 3.0 * x2 <= 90.0, "Machine_Hours")

    solver.Maximize(40.0 * x1 + 50.0 * x2)

    status = solver.Solve()
    if status != pywraplp.Solver.OPTIMAL:
        raise RuntimeError(f"Unexpected LP status: {status}")

    print(f"Optimal Profit : ${solver.Objective().Value():.2f}")
    print(f"Product A      : {x1.solution_value():.2f} (Reduced Cost: {x1.reduced_cost():.2f})")
    print(f"Product B      : {x2.solution_value():.2f} (Reduced Cost: {x2.reduced_cost():.2f})")
    print(f"Shadow Price (Labor)   : ${c_labor.dual_value():.2f} / hour")
    print(f"Shadow Price (Machine) : ${c_machine.dual_value():.2f} / hour")


def solve_milp_with_mathopt() -> None:
    print("\n--- 2. Mixed-Integer Production Planning (MathOpt + HIGHS) ---")
    model = mathopt.Model(name="fixed_charge_production")

    # Continuous production quantities + binary line activation indicators
    prod_a = model.add_variable(lb=0.0, ub=80.0, name="prod_a")
    batch_b = model.add_integer_variable(lb=0, ub=60, name="batch_b")
    open_a = model.add_binary_variable(name="open_a")
    open_b = model.add_binary_variable(name="open_b")

    # Tight Big-M linking constraints: production > 0 => line must be open
    model.add_linear_constraint(prod_a <= 80.0 * open_a, name="link_a")
    model.add_linear_constraint(batch_b <= 60.0 * open_b, name="link_b")

    # Shared resource constraint
    model.add_linear_constraint(1.5 * prod_a + 2.0 * batch_b <= 120.0, name="raw_material")

    # Maximize net profit (revenue - fixed setup cost)
    model.maximize(35.0 * prod_a + 48.0 * batch_b - 250.0 * open_a - 300.0 * open_b)

    result = mathopt.solve(model, mathopt.SolverType.HIGHS)
    if result.termination.reason not in (
        mathopt.TerminationReason.OPTIMAL,
        mathopt.TerminationReason.FEASIBLE,
    ):
        raise RuntimeError(f"MathOpt failed: {result.termination}")

    vals = result.variable_values()
    print(f"Optimal Net Profit : ${result.objective_value():.2f}")
    print(f"Line A Open={int(round(vals[open_a]))}, Quantity={vals[prod_a]:.2f}")
    print(f"Line B Open={int(round(vals[open_b]))}, Batches={vals[batch_b]:.0f}")


if __name__ == "__main__":
    solve_continuous_lp_with_duals()
    solve_milp_with_mathopt()
