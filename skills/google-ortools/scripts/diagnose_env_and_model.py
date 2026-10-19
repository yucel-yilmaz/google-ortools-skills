#!/usr/bin/env python3
"""Diagnostic utility for Google OR-Tools environment, solver backends, and smoke tests.

Usage:
    python skills/google-ortools/scripts/diagnose_env_and_model.py
    python skills/google-ortools/scripts/diagnose_env_and_model.py --json
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from typing import Any


def check_ortools() -> dict[str, Any]:
    report: dict[str, Any] = {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "ortools_installed": False,
        "ortools_version": None,
        "modules": {},
        "pywraplp_backends": {},
        "mathopt_backends": {},
        "smoke_tests": {},
    }

    try:
        import ortools

        report["ortools_installed"] = True
        report["ortools_version"] = getattr(ortools, "__version__", "unknown")
    except ImportError as exc:
        report["error"] = f"ortools not installed: {exc}. Install via `pip install ortools`."
        return report

    # 1. Check core modules
    module_checks = {
        "cp_model": "ortools.sat.python.cp_model",
        "pywraplp": "ortools.linear_solver.pywraplp",
        "mathopt": "ortools.math_opt.python.mathopt",
        "pywrapcp": "ortools.constraint_solver.pywrapcp",
        "max_flow": "ortools.graph.python.max_flow",
        "min_cost_flow": "ortools.graph.python.min_cost_flow",
        "linear_sum_assignment": "ortools.graph.python.linear_sum_assignment",
        "knapsack_solver": "ortools.algorithms.python.knapsack_solver",
    }
    for short_name, mod_path in module_checks.items():
        try:
            __import__(mod_path)
            report["modules"][short_name] = True
        except Exception as exc:
            report["modules"][short_name] = f"Unavailable ({exc})"

    # 2. Check pywraplp backends
    try:
        from ortools.linear_solver import pywraplp

        for backend in ["GLOP", "PDLP", "SCIP", "CBC", "HIGHS", "SAT", "GLPK", "GUROBI", "CPLEX"]:
            solver = pywraplp.Solver.CreateSolver(backend)
            report["pywraplp_backends"][backend] = solver is not None
    except Exception as exc:
        report["pywraplp_backends"]["error"] = str(exc)

    # 3. Check MathOpt backends
    try:
        from ortools.math_opt.python import mathopt

        for st in [
            mathopt.SolverType.CP_SAT,
            mathopt.SolverType.GLOP,
            mathopt.SolverType.PDLP,
            mathopt.SolverType.GSCIP,
            mathopt.SolverType.HIGHS,
            mathopt.SolverType.OSQP,
            mathopt.SolverType.GUROBI,
        ]:
            try:
                m = mathopt.Model(name="probe")
                v = m.add_variable(lb=0.0, ub=1.0, name="v")
                m.maximize(v)
                res = mathopt.solve(m, st)
                report["mathopt_backends"][st.name] = (
                    res.termination.reason == mathopt.TerminationReason.OPTIMAL
                )
            except Exception:
                report["mathopt_backends"][st.name] = False
    except Exception as exc:
        report["mathopt_backends"]["error"] = str(exc)

    # 4. Run smoke test on CP-SAT
    try:
        from ortools.sat.python import cp_model

        model = cp_model.CpModel()
        x = model.new_int_var(0, 10, "x")
        y = model.new_int_var(0, 10, "y")
        model.add(x + y <= 15)
        model.maximize(2 * x + 3 * y)
        solver = cp_model.CpSolver()
        status = solver.solve(model)
        report["smoke_tests"]["cp_sat"] = (
            status == cp_model.OPTIMAL and int(round(solver.objective_value)) == 40
        )
    except Exception as exc:
        report["smoke_tests"]["cp_sat"] = f"Failed: {exc}"

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose Google OR-Tools installation and solvers.")
    parser.add_argument("--json", action="store_true", help="Output diagnostic report as JSON.")
    args = parser.parse_args()

    report = check_ortools()
    if args.json:
        print(json.dumps(report, indent=2))
        return 0 if report.get("ortools_installed") else 1

    print("=" * 60)
    print("Google OR-Tools Environment & Solver Diagnostic")
    print("=" * 60)
    print(f"Python Version   : {report['python_version']} ({report['platform']})")
    if not report["ortools_installed"]:
        print(f"ERROR            : {report.get('error')}")
        return 1

    print(f"OR-Tools Version : {report['ortools_version']}")
    print("\n[Modules]")
    for mod, ok in report["modules"].items():
        status_str = "OK" if ok is True else str(ok)
        print(f"  - {mod:<24}: {status_str}")

    print("\n[MPSolver (pywraplp) Backends]")
    avail_lp = [k for k, v in report["pywraplp_backends"].items() if v is True]
    unavail_lp = [k for k, v in report["pywraplp_backends"].items() if v is False]
    print(f"  Available   : {', '.join(avail_lp)}")
    print(f"  Unavailable : {', '.join(unavail_lp)}")

    print("\n[MathOpt Backends]")
    avail_mo = [k for k, v in report["mathopt_backends"].items() if v is True]
    unavail_mo = [k for k, v in report["mathopt_backends"].items() if v is False]
    print(f"  Available   : {', '.join(avail_mo)}")
    print(f"  Unavailable : {', '.join(unavail_mo)}")

    print("\n[Smoke Tests]")
    for test_name, passed in report["smoke_tests"].items():
        print(f"  - {test_name:<24}: {'PASSED' if passed is True else passed}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
