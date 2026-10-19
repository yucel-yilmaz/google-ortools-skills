# Multi-Language Cheatsheet (Python, C++, Java, C#)

Google OR-Tools provides native APIs for **Python**, **C++**, **Java**, and **C# (.NET)**. Use this translation reference when porting models or assisting users in non-Python environments.

---

## 1. Package & Namespace Imports

| Component | Python | C++ (`#include`) | Java (`import`) | C# (`using`) |
| :--- | :--- | :--- | :--- | :--- |
| **CP-SAT** | `from ortools.sat.python import cp_model` | `"ortools/sat/cp_model.h"` (`operations_research::sat`) | `com.google.ortools.sat.*` | `Google.OrTools.Sat` |
| **Linear / MIP (`MPSolver`)** | `from ortools.linear_solver import pywraplp` | `"ortools/linear_solver/linear_solver.h"` | `com.google.ortools.linearsolver.*` | `Google.OrTools.LinearSolver` |
| **Vehicle Routing** | `from ortools.constraint_solver import pywrapcp, routing_enums_pb2` | `"ortools/constraint_solver/routing.h"` | `com.google.ortools.constraintsolver.*` | `Google.OrTools.ConstraintSolver` |
| **Network Flows** | `from ortools.graph.python import max_flow, min_cost_flow` | `"ortools/graph/max_flow.h"`, `"ortools/graph/min_cost_flow.h"` | `com.google.ortools.graph.*` | `Google.OrTools.Graph` |
| **Native Loader** | *(Automatic)* | *(Linked via CMake/Bazel)* | `Loader.loadNativeLibraries();` | *(Automatic via NuGet `Google.OrTools`)* |

> **Java Reminder:** Always call `Loader.loadNativeLibraries();` at the start of `main()` before instantiating any OR-Tools classes in Java!

---

## 2. CP-SAT API Mapping Across Languages

| Operation | Python (`snake_case`) | C++ | Java | C# (.NET) |
| :--- | :--- | :--- | :--- | :--- |
| **Create Model** | `model = cp_model.CpModel()` | `CpModelBuilder model;` | `CpModel model = new CpModel();` | `var model = new CpModel();` |
| **Int Variable** | `x = model.new_int_var(0, 10, "x")` | `IntVar x = model.NewIntVar({0, 10}).WithName("x");` | `IntVar x = model.newIntVar(0, 10, "x");` | `IntVar x = model.NewIntVar(0, 10, "x");` |
| **Bool Variable** | `b = model.new_bool_var("b")` | `BoolVar b = model.NewBoolVar().WithName("b");` | `BoolVar b = model.newBoolVar("b");` | `BoolVar b = model.NewBoolVar("b");` |
| **Negate Bool** | `~b` or `b.negated()` | `b.Not()` or `~b` | `b.not()` | `b.Not()` |
| **Linear Constraint** | `model.add(2 * x + y <= 15)` | `model.AddLessOrEqual(2 * x + y, 15);` | `model.addLessOrEqual(LinearExpr.weightedSum(new IntVar[]{x, y}, new long[]{2, 1}), 15);` | `model.Add(2 * x + y <= 15);` |
| **Half-Reification** | `.only_enforce_if(b)` | `.OnlyEnforceIf(b)` | `.onlyEnforceIf(b)` | `.OnlyEnforceIf(b)` |
| **AllDifferent** | `model.add_all_different(vars)` | `model.AddAllDifferent(vars);` | `model.addAllDifferent(vars);` | `model.AddAllDifferent(vars);` |
| **Interval Variable** | `model.new_interval_var(s, d, e, "iv")` | `model.NewIntervalVar(s, d, e)` | `model.newIntervalVar(s, d, e, "iv")` | `model.NewIntervalVar(s, d, e, "iv")` |
| **NoOverlap** | `model.add_no_overlap(intervals)` | `model.AddNoOverlap(intervals);` | `model.addNoOverlap(intervals);` | `model.AddNoOverlap(intervals);` |
| **Objective** | `model.minimize(expr)` | `model.Minimize(expr);` | `model.minimize(expr);` | `model.Minimize(expr);` |
| **Solve** | `solver = cp_model.CpSolver()`<br>`status = solver.solve(model)` | `const CpSolverResponse resp = Solve(model.Build());` | `CpSolver solver = new CpSolver();`<br>`CpSolverStatus status = solver.solve(model);` | `var solver = new CpSolver();`<br>`CpSolverStatus status = solver.Solve(model);` |
| **Read Value** | `solver.value(x)` | `SolutionIntegerValue(resp, x)` | `solver.value(x)` | `solver.Value(x)` |

---

## 3. MPSolver (`pywraplp`) API Mapping Across Languages

| Operation | Python | C++ | Java | C# (.NET) |
| :--- | :--- | :--- | :--- | :--- |
| **Create Solver** | `pywraplp.Solver.CreateSolver("SCIP")` | `MPSolver::CreateSolver("SCIP")` | `MPSolver.createSolver("SCIP")` | `Solver.CreateSolver("SCIP")` |
| **Continuous Var** | `solver.NumVar(0.0, inf, "x")` | `solver->MakeNumVar(0.0, inf, "x")` | `solver.makeNumVar(0.0, inf, "x")` | `solver.MakeNumVar(0.0, inf, "x")` |
| **Integer Var** | `solver.IntVar(0.0, 10.0, "y")` | `solver->MakeIntVar(0.0, 10.0, "y")` | `solver.makeIntVar(0.0, 10.0, "y")` | `solver.MakeIntVar(0.0, 10.0, "y")` |
| **Solve** | `status = solver.Solve()` | `auto status = solver->Solve();` | `MPSolver.ResultStatus status = solver.solve();` | `Solver.ResultStatus status = solver.Solve();` |
| **Read Value** | `x.solution_value()` | `x->solution_value()` | `x.solutionValue()` | `x.SolutionValue()` |
