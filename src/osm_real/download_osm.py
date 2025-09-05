import os
from pathlib import Path
import osmnx as ox

CACHE = Path(__file__).resolve().parents[1] / "data"

def load_graph_for_place(place: str = "Boston, Massachusetts, USA"):
    """Download or load a drivable OSM graph for the place; caches to data/."""
    CACHE.mkdir(parents=True, exist_ok=True)
    graphml = CACHE / f"{place.replace(',','').replace(' ','_')}.graphml"
    if graphml.exists():
        G = ox.load_graphml(graphml)
    else:
        G = ox.graph_from_place(place, network_type="drive")
        ox.save_graphml(G, graphml)
    # Add edge speeds & travel time if missing
    G = ox.add_edge_speeds(G)        # km/h
    G = ox.add_edge_travel_times(G)  # seconds
    return G
