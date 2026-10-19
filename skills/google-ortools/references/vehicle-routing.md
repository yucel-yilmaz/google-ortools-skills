# Vehicle Routing (TSP, VRP, CVRP, VRPTW, Pickup & Delivery) Guide

The OR-Tools Routing library (`ortools.constraint_solver.pywrapcp`) solves Traveling Salesperson Problems (TSP) and complex Vehicle Routing Problems (VRP) at scale (`https://developers.google.com/optimization/routing`).

---

## 1. Core Architecture: Nodes vs. Internal Indices

The single most important concept in `pywrapcp` is the distinction between:
* **Node (`int`)**: Your application's location index ($0 \dots N-1$) into `distance_matrix`, `demands`, `time_windows`.
* **Routing Index (`int64`)**: The solver's internal variable index (where start/end nodes of multiple vehicles have distinct internal indices).

**Golden Rules:**
1. Inside any callback (`distance_callback`, `demand_callback`, `time_callback`), always convert `from_index` / `to_index` via `manager.IndexToNode(index)`.
2. When adding constraints on specific locations (`CumulVar`, `AddPickupAndDelivery`, `AddDisjunction`), convert location node IDs to internal indices via `manager.NodeToIndex(node)`.
3. For vehicle start/end locations, never call `manager.NodeToIndex(depot)` if there are multiple vehicles—use `routing.Start(vehicle_id)` and `routing.End(vehicle_id)`.

---

## 2. Multi-Depot Initialization

* **Single Depot** (all vehicles start and end at node `0`):
  ```python
  manager = pywrapcp.RoutingIndexManager(num_locations, num_vehicles, 0)
  ```
* **Multiple Start & End Depots** (each vehicle $v$ starts at `starts[v]` and ends at `ends[v]`):
  ```python
  starts = [0, 0, 1]
  ends = [0, 2, 1]
  manager = pywrapcp.RoutingIndexManager(num_locations, num_vehicles, starts, ends)
  ```
* **Open Routes (Vehicles do not return to depot)**:
  Create a dummy depot node `dummy_idx` whose distance from every node is `0` (`dist[i][dummy] = 0`), and set `ends = [dummy_idx] * num_vehicles`.

---

## 3. Dimensions: Capacity (CVRP) and Time Windows (VRPTW)

A **Dimension** tracks a quantity accumulated along each vehicle's route (e.g., load weight, travel + service time, distance, fuel).

### Capacitated VRP (CVRP)
```python
def demand_callback(from_index: int) -> int:
    from_node = manager.IndexToNode(from_index)
    return data["demands"][from_node]

demand_cb_idx = routing.RegisterUnaryTransitCallback(demand_callback)
routing.AddDimensionWithVehicleCapacity(
    demand_cb_idx,
    0,                          # slack_max (0 for load capacity)
    data["vehicle_capacities"], # list of max capacities per vehicle
    True,                       # fix_start_cumul_to_zero (start empty)
    "Capacity",
)
```

### VRP with Time Windows (VRPTW)
```python
def time_callback(from_index: int, to_index: int) -> int:
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return data["time_matrix"][from_node][to_node] + data["service_times"][from_node]

time_cb_idx = routing.RegisterTransitCallback(time_callback)
routing.AddDimension(
    time_cb_idx,
    max_waiting_time,  # slack_max: maximum allowed waiting time at a node
    max_route_time,    # capacity: maximum total time per vehicle route
    False,             # fix_start_cumul_to_zero: False allows flexible departure time!
    "Time",
)
time_dimension = routing.GetDimensionOrDie("Time")

# Apply time windows [earliest, latest] for each customer node
for node_idx, (earliest, latest) in enumerate(data["time_windows"]):
    if node_idx == data["depot"]:
        continue
    index = manager.NodeToIndex(node_idx)
    time_dimension.CumulVar(index).SetRange(earliest, latest)

# Apply depot time windows to vehicle starts/ends and minimize route span
for v in range(data["num_vehicles"]):
    start_idx = routing.Start(v)
    end_idx = routing.End(v)
    depot_early, depot_late = data["time_windows"][data["depot"]]
    time_dimension.CumulVar(start_idx).SetRange(depot_early, depot_late)
    time_dimension.CumulVar(end_idx).SetRange(depot_early, depot_late)
    routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(start_idx))
    routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(end_idx))
```

---

## 4. Pickup and Delivery Constraints

When item $k$ must be picked up at `pickup_node` and delivered to `delivery_node` by the **same vehicle** in the **correct order**:

```python
distance_dimension = routing.GetDimensionOrDie("Distance")
# Make routes balanced across vehicles (optional)
distance_dimension.SetGlobalSpanCostCoefficient(100)

for pickup_node, delivery_node in data["pickups_deliveries"]:
    pickup_index = manager.NodeToIndex(pickup_node)
    delivery_index = manager.NodeToIndex(delivery_node)
    routing.AddPickupAndDelivery(pickup_index, delivery_index)
    # 1. Same vehicle must visit both
    routing.solver().Add(
        routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index)
    )
    # 2. Pickup must occur before delivery
    routing.solver().Add(
        distance_dimension.CumulVar(pickup_index)
        <= distance_dimension.CumulVar(delivery_index)
    )
```
> **Tip for Capacity with Pickup & Delivery:** Set `demands[pickup_node] = +weight` and `demands[delivery_node] = -weight`.

---

## 5. Dropping Visits with Penalties (`AddDisjunction`)

In real-world VRP, capacity or time windows may make visiting every node impossible. Always recommend adding disjunctions so the solver drops unvisitable nodes for a penalty instead of returning `None` (infeasible):

```python
penalty = 100_000  # Must be larger than the marginal cost of visiting a node
for node in range(1, len(data["distance_matrix"])):
    routing.AddDisjunction([manager.NodeToIndex(node)], penalty)
```

To inspect dropped nodes after solving:
```python
dropped_nodes = []
for node in range(routing.Size()):
    if routing.IsStart(node) or routing.IsEnd(node):
        continue
    if solution.Value(routing.NextVar(node)) == node:
        dropped_nodes.append(manager.IndexToNode(node))
```

---

## 6. Routing Search Strategies & Status Codes

### First Solution Strategies (`routing_enums_pb2.FirstSolutionStrategy`)
* `AUTOMATIC`: Let the solver choose.
* `PATH_CHEAPEST_ARC`: Fast greedy extension from route end (great general default).
* `PARALLEL_CHEAPEST_INSERTION`: Best for Pickup & Delivery and tight VRPTW.
* `SAVINGS`: Clarke & Wright savings heuristic for CVRP.

### Local Search Metaheuristics (`routing_enums_pb2.LocalSearchMetaheuristic`)
* `GUIDED_LOCAL_SEARCH` (**GLS**): Best solution quality for VRP/CVRP/VRPTW. **Requires `time_limit`!**
* `TABU_SEARCH`: Strong alternative when escaping local minima.
* `SIMULATED_ANNEALING`: Probabilistic escape from local optima.

### Checking Routing Status (`routing.status()`)
* `0` (`ROUTING_NOT_SOLVED`): Before `SolveWithParameters`.
* `1` (`ROUTING_SUCCESS`): Feasible solution found.
* `2` (`ROUTING_PARTIAL_SUCCESS_LOCAL_OPTIMUM_NOT_REACHED`): Timeout reached with a feasible solution.
* `3` (`ROUTING_FAIL`): No solution found.
* `4` (`ROUTING_FAIL_TIMEOUT`): Time limit reached before finding even a first solution.
* `5` (`ROUTING_INVALID`): Invalid parameters or model configuration.
