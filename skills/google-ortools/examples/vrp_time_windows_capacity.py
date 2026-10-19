#!/usr/bin/env python3
"""Reference Example: Capacitated Vehicle Routing Problem with Time Windows (CVRPTW) & Penalty Drops.

Demonstrates:
- `RoutingIndexManager` and `RoutingModel` setup
- Proper `IndexToNode` and `NodeToIndex` conversion
- Capacity dimension (`AddDimensionWithVehicleCapacity`)
- Time Window dimension (`AddDimension` with slack + `CumulVar.SetRange`)
- Dropping unvisitable nodes gracefully with `AddDisjunction`
- Guided Local Search with a mandatory time limit
"""

from __future__ import annotations

from ortools.constraint_solver import pywrapcp, routing_enums_pb2


def solve_cvrptw() -> None:
    data = {
        "time_matrix": [
            [0, 6, 9, 8, 7, 3],
            [6, 0, 8, 3, 2, 6],
            [9, 8, 0, 11, 10, 6],
            [8, 3, 11, 0, 1, 7],
            [7, 2, 10, 1, 0, 6],
            [3, 6, 6, 7, 6, 0],
        ],
        "time_windows": [
            (0, 30),   # 0: Depot
            (7, 12),   # 1
            (10, 15),  # 2
            (5, 14),   # 3
            (5, 13),   # 4
            (0, 25),   # 5
        ],
        "demands": [0, 4, 6, 3, 5, 4],
        "service_times": [0, 1, 1, 1, 1, 1],
        "vehicle_capacities": [12, 12],
        "num_vehicles": 2,
        "depot": 0,
    }

    manager = pywrapcp.RoutingIndexManager(
        len(data["time_matrix"]), data["num_vehicles"], data["depot"]
    )
    routing = pywrapcp.RoutingModel(manager)

    # 1. Transit callback (travel time + service time at origin node)
    def time_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["time_matrix"][from_node][to_node] + data["service_times"][from_node]

    transit_cb_idx = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb_idx)

    # 2. Add Time Windows Dimension
    routing.AddDimension(
        transit_cb_idx,
        10,     # max waiting time (slack) at a location
        30,     # max total route duration per vehicle
        False,  # do not force start time to 0
        "Time",
    )
    time_dim = routing.GetDimensionOrDie("Time")

    for node_idx, (earliest, latest) in enumerate(data["time_windows"]):
        if node_idx == data["depot"]:
            continue
        index = manager.NodeToIndex(node_idx)
        time_dim.CumulVar(index).SetRange(earliest, latest)

    for v in range(data["num_vehicles"]):
        start_idx = routing.Start(v)
        end_idx = routing.End(v)
        depot_early, depot_late = data["time_windows"][data["depot"]]
        time_dim.CumulVar(start_idx).SetRange(depot_early, depot_late)
        time_dim.CumulVar(end_idx).SetRange(depot_early, depot_late)
        routing.AddVariableMinimizedByFinalizer(time_dim.CumulVar(start_idx))
        routing.AddVariableMinimizedByFinalizer(time_dim.CumulVar(end_idx))

    # 3. Add Capacity Dimension
    def demand_callback(from_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        return data["demands"][from_node]

    demand_cb_idx = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_cb_idx,
        0,
        data["vehicle_capacities"],
        True,
        "Capacity",
    )
    cap_dim = routing.GetDimensionOrDie("Capacity")

    # 4. Allow dropping customer visits at a high penalty to prevent hard infeasibility
    drop_penalty = 1_000
    for node_idx in range(1, len(data["time_matrix"])):
        routing.AddDisjunction([manager.NodeToIndex(node_idx)], drop_penalty)

    # 5. Search parameters
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    params.time_limit.FromSeconds(2)

    solution = routing.SolveWithParameters(params)
    if not solution:
        raise RuntimeError(f"Routing failed with status {routing.status()}")

    # 6. Extract and validate routes
    dropped = []
    for index in range(routing.Size()):
        if routing.IsStart(index) or routing.IsEnd(index):
            continue
        if solution.Value(routing.NextVar(index)) == index:
            dropped.append(manager.IndexToNode(index))

    print(f"Objective Cost: {solution.ObjectiveValue()} | Dropped Nodes: {dropped}")
    for v in range(data["num_vehicles"]):
        index = routing.Start(v)
        stops = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            t_var = time_dim.CumulVar(index)
            c_var = cap_dim.CumulVar(index)
            stops.append(
                f"Node {node} (t=[{solution.Min(t_var)}..{solution.Max(t_var)}], load={solution.Value(c_var)})"
            )
            index = solution.Value(routing.NextVar(index))
        node = manager.IndexToNode(index)
        t_var = time_dim.CumulVar(index)
        c_var = cap_dim.CumulVar(index)
        stops.append(
            f"Depot {node} (t=[{solution.Min(t_var)}..{solution.Max(t_var)}], load={solution.Value(c_var)})"
        )
        assert solution.Value(c_var) <= data["vehicle_capacities"][v], "Capacity exceeded!"
        print(f"  Vehicle {v}: " + " -> ".join(stops))


if __name__ == "__main__":
    solve_cvrptw()
