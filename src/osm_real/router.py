from typing import Tuple, List, Dict
import networkx as nx
import osmnx as ox
from networkx.algorithms.simple_paths import shortest_simple_paths



def _edge_attrs(G, u, v):
    """Return a single edge-attribute dict for (u,v) regardless of Graph/MultiDiGraph."""
    data = G.get_edge_data(u, v)
    if data is None:
        return {}
    if isinstance(G, (nx.MultiDiGraph, nx.MultiGraph)):
        # pick the parallel edge with min travel_time, fallback to min length
        best = min(
            data.values(),
            key=lambda d: (d.get("travel_time", float("inf")), d.get("length", float("inf")))
        )
        return best
    # DiGraph/Graph: data is already a dict of attributes
    return data

def to_simple_digraph(G: nx.MultiDiGraph, weight_attr: str = "travel_time") -> nx.DiGraph:

    H = nx.DiGraph()
    H.add_nodes_from(G.nodes(data=True))
    for u, v, k, d in G.edges(keys=True, data=True):
        w = d.get(weight_attr, float("inf"))
        if H.has_edge(u, v):
            # keep the lower-weight edge
            if w < H[u][v].get(weight_attr, float("inf")):
                H[u][v].clear()
                H[u][v].update({
                    weight_attr: w,
                    "length": d.get("length", 0.0),
                    "name": d.get("name"),
                })
        else:
            H.add_edge(u, v, **{
                weight_attr: w,
                "length": d.get("length", 0.0),
                "name": d.get("name"),
            })
    return H



def nearest_nodes(G: nx.MultiDiGraph, lat: float, lon: float) -> int:

    return ox.nearest_nodes(G, X=lon, Y=lat)

def route_travel_time_seconds(G, route: List[int]) -> float:
    total = 0.0
    for u, v in zip(route, route[1:]):
        d = _edge_attrs(G, u, v)
        total += d.get("travel_time", 0.0)
    return total

def route_length_meters(G, route: List[int]) -> float:
    dist = 0.0
    for u, v in zip(route, route[1:]):
        d = _edge_attrs(G, u, v)
        dist += d.get("length", 0.0)
    return dist



def apply_travel_mode(G: nx.MultiDiGraph, mode: str = "drive"):

    H = G.copy()
    if mode == "drive":
        H = ox.add_edge_speeds(H)
        H = ox.add_edge_travel_times(H)
    else:
        kmph = 15.0 if mode == "bike" else 5.0
        mps = kmph * 1000 / 3600.0
        for u, v, k, d in H.edges(keys=True, data=True):
            length = d.get("length", 0.0)
            d["travel_time"] = (length / mps) if mps > 0 else float("inf")
    return H


AVOID_TAGS = {"motorway", "trunk", "motorway_link", "trunk_link"}

def filter_avoid_highways(G: nx.MultiDiGraph, avoid: bool):
    if not avoid:
        return G
    H = G.copy()
    to_remove = []
    for u, v, k, d in H.edges(keys=True, data=True):
        hwy = d.get("highway")
        hwys = set(hwy) if isinstance(hwy, list) else {hwy}
        if any(tag in AVOID_TAGS for tag in hwys):
            to_remove.append((u, v, k))
    H.remove_edges_from(to_remove)
    # drop isolated nodes
    isolates = [n for n in H.nodes if H.degree(n) == 0]
    H.remove_nodes_from(isolates)
    return H



def k_shortest_routes(G: nx.MultiDiGraph, s: int, t: int, weight: str = "travel_time", k: int = 3) -> List[List[int]]:

    DG = to_simple_digraph(G, weight_attr=weight)
    routes = []
    for path in shortest_simple_paths(DG, s, t, weight=weight):
        routes.append(path)
        if len(routes) >= k:
            break
    return routes



def summarize_steps(G, path: List[int]) -> List[str]:
    steps: List[str] = []
    prev_name = None
    accum_len = 0.0

    for u, v in zip(path, path[1:]):
        d = _edge_attrs(G, u, v)
        name = d.get("name") or "Unnamed road"
        length = d.get("length", 0.0)

        if name != prev_name and prev_name is not None:
            steps.append(f"Continue on {prev_name} for {accum_len:.0f} m")
            accum_len = 0.0
        prev_name = name
        accum_len += length

    if prev_name is not None:
        steps.append(f"Continue on {prev_name} for {accum_len:.0f} m")
    steps.append("Arrive at destination")
    return steps
