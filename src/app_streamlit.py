# app_Streamlitapp.py
import json
from typing import List

import osmnx as ox
import streamlit as st
import streamlit.components.v1 as components

from osm_real.download_osm import load_graph_for_place
from osm_real.router import (
    nearest_nodes,
    route_travel_time_seconds,
    route_length_meters,
    apply_travel_mode,
    filter_avoid_highways,
    k_shortest_routes,
    summarize_steps,
)
from osm_real.map_draw import build_multi_route_map


# -------------------- Page setup --------------------
st.set_page_config(page_title="Router", layout="centered")
st.title("Route")
st.caption("Find optimized routes with multiple options, travel modes, and highway controls.")


# -------------------- Caching --------------------
@st.cache_resource(show_spinner=False)
def get_graph(place: str):
    """Heavy OSM graph cache (persists across reruns)."""
    return load_graph_for_place(place)

@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def geocode_cached(q: str):
    """Cache geocoding results for a day to avoid rate limits."""
    return ox.geocode(q)  # (lat, lon)



MODE_LABELS = ["drive", "bike", "walk"]
MODE_MAP = {m: m for m in MODE_LABELS}

def _route_coords_latlon(G, route: List[int]):
    """Return [(lat, lon), ...] for a route's nodes."""
    nodes = ox.graph_to_gdfs(G, edges=False)
    return [(nodes.loc[n].y, nodes.loc[n].x) for n in route]

def route_to_geojson(G, route: List[int]) -> dict:
    """Build a minimal GeoJSON LineString for the given route."""
    coords_latlon = _route_coords_latlon(G, route)

    coords_lonlat = [[lon, lat] for (lat, lon) in coords_latlon]
    return {
        "type": "Feature",
        "properties": {"name": "Router Route"},
        "geometry": {"type": "LineString", "coordinates": coords_lonlat},
    }


# -------------------- Inputs --------------------
with st.sidebar:
    st.header(" Router Options")
    place = st.text_input(" City/Area", "Boston, Massachusetts, USA")
    mode_label = st.selectbox(" Travel Mode", MODE_LABELS, index=0)
    mode = MODE_MAP[mode_label]
    avoid_hw = st.toggle("Avoid Highways", value=False)
    k_routes = st.slider(" Number of Routes", 1, 5, 3)

start = st.text_input(" Start Location", "Northeastern University, Boston")
end = st.text_input(" Destination", "Logan International Airport, Boston")

col1, col2 = st.columns(2)
go = col1.button("Find Routes", use_container_width=True)
clear = col2.button("Clear", use_container_width=True)

if clear:
    st.session_state.clear()
    st.rerun()


# -------------------- Action --------------------
if go:
    try:
        with st.spinner("Loading graph & computing routes..."):
            # Load and prepare graph
            G0 = get_graph(place)
            G1 = apply_travel_mode(G0, mode=mode)
            G2 = filter_avoid_highways(G1, avoid=avoid_hw)

            # Geocode inputs (cached)
            (s_lat, s_lon) = geocode_cached(start)
            (e_lat, e_lon) = geocode_cached(end)

            # Snap to nearest nodes
            s_node = nearest_nodes(G2, s_lat, s_lon)
            e_node = nearest_nodes(G2, e_lat, e_lon)

            # Compute K shortest routes (by travel_time)
            routes = k_shortest_routes(G2, s_node, e_node, weight="travel_time", k=k_routes)
            if not routes:
                st.error("No route found with the current settings. Try disabling 'Avoid Highways' or reducing K.")
            else:
                # Score and summarize
                scored = []
                for r in routes:
                    secs = route_travel_time_seconds(G2, r)
                    dist_m = route_length_meters(G2, r)
                    scored.append(
                        {
                            "route": r,
                            "minutes": secs / 60.0,
                            "km": dist_m / 1000.0,
                            "steps": summarize_steps(G2, r),
                        }
                    )

                scored.sort(key=lambda x: x["minutes"])
                st.session_state["scored"] = scored
                st.session_state["place"] = place
                st.session_state["mode"] = mode
                st.session_state["avoid"] = avoid_hw
    except Exception as e:
        st.error(f"Something went wrong: {e}")



if "scored" in st.session_state and st.session_state["scored"]:
    # Summary for the best route
    best = st.session_state["scored"][0]
    st.success(
        f"Best route: **{best['minutes']:.1f} min** • **{best['km']:.2f} km**  "
        f"(mode: **{st.session_state['mode']}**, avoid_highways={st.session_state['avoid']})"
    )

    # Build multi-route map and embed (robust, no flicker)
    try:
        fmap = build_multi_route_map(get_graph(st.session_state["place"]),
                                     [x["route"] for x in st.session_state["scored"]])
        components.html(fmap.get_root().render(), height=560, scrolling=False)
    except Exception as e:
        st.warning(f"Map rendering fallback triggered: {e}")
        st.info("Try refreshing the page or reducing K.")


    try:
        G_view = get_graph(st.session_state["place"])
        geojson = route_to_geojson(G_view, best["route"])
        st.download_button(
            "⬇️ Download Best Route (GeoJSON)",
            data=json.dumps(geojson),
            file_name="route.geojson",
            mime="application/geo+json",
        )
    except Exception as e:
        st.warning(f"Export unavailable: {e}")


    for idx, x in enumerate(st.session_state["scored"], start=1):
        with st.expander(f"🛣️ Route {idx}: {x['minutes']:.1f} min • {x['km']:.2f} km"):
            for s in x["steps"]:
                st.write(s)
else:
    st.info("Enter a start & destination, choose options, then click **Find Routes**.")

# -------------------- Footer --------------------
st.markdown("---")
st.caption("Router • Built with Python, Streamlit, OSMnx, and Folium")
