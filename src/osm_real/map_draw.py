from typing import List, Sequence
import folium
import osmnx as ox

def _coords_for_route(G, route: List[int]):
    nodes = ox.graph_to_gdfs(G, edges=False)
    return [(nodes.loc[n].y, nodes.loc[n].x) for n in route]

def build_multi_route_map(G, routes: Sequence[List[int]]) -> folium.Map:
    first_coords = _coords_for_route(G, routes[0])
    m = folium.Map(location=first_coords[0], zoom_start=13, tiles="OpenStreetMap")

    palette = ["blue", "orange", "green", "purple", "red"]
    for idx, path in enumerate(routes):
        coords = _coords_for_route(G, path)
        color = palette[idx % len(palette)]
        folium.PolyLine(coords, weight=5, opacity=0.8, color=color).add_to(m)
        if idx == 0:
            folium.Marker(coords[0], popup="Start", icon=folium.Icon(color="green")).add_to(m)
            folium.Marker(coords[-1], popup="End", icon=folium.Icon(color="red")).add_to(m)
    return m

