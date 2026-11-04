import re
from array import array
from pathlib import Path

import numpy as np
import osmium
import polars as pl
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

from assign import KM_PER_DEG, flat_dist

# average driving speed per road type in km/h (my guess of real speed, not the legal limit)
CLASS_SPEED = {
    "motorway": 120, "motorway_link": 60,
    "trunk": 100, "trunk_link": 50,
    "primary": 70, "primary_link": 40,
    "secondary": 60, "secondary_link": 40,
    "tertiary": 50, "tertiary_link": 30,
}
# OSM oneway tag: 1 = only in drawing direction, -1 = only against it, 0 = both ways
ONEWAY = {"yes": 1, "true": 1, "1": 1, "-1": -1, "no": 0}

# from the town to the nearest road node we assume a small local road
ACCESS_SPEED_KMH = 40
ACCESS_DETOUR = 1.3  # a real road is ~30% longer than the straight line
MAX_DRIVE_MIN = 240  # stop searching after 4 hours, no metro radius is that big
# ignore small separate road networks (islands, pieces cut off at the border)
MIN_NETWORK_NODES = 1000


def way_speed(tags, implicit_maxspeed: dict[str, int]) -> int:
    """Speed for the road type, but not more than the maxspeed sign."""
    speed = CLASS_SPEED[tags.get("highway")]
    maxspeed = tags.get("maxspeed") or ""
    if maxspeed in implicit_maxspeed:
        return min(speed, implicit_maxspeed[maxspeed])
    number = re.match(r"\s*(\d+)", maxspeed)  # e.g. "90" or "90 mph"
    if number:
        return min(speed, int(number.group(1)))
    return speed


def way_oneway(tags) -> int:
    value = tags.get("oneway")
    if value in ONEWAY:
        return ONEWAY[value]
    # motorways and roundabouts are one-way even without the tag
    if tags.get("highway") == "motorway" or tags.get("junction") == "roundabout":
        return 1
    return 0


def build_graph(pbf: Path, implicit_maxspeed: dict[str, int]) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Read the OSM file into nodes (node, lat, lon) and directed edges (u, v, minutes, km).

    The file is read twice: first the roads, then the coordinates of only the nodes on those roads.
    Loading the coordinates of all nodes at once does not fit in memory.
    `array` is used instead of lists because it stores numbers much more compactly.
    """
    # 1st pass: every road is a list of nodes, split it into segments node -> next node
    u, v, speed, oneway = array("q"), array("q"), array("h"), array("b")
    for way in osmium.FileProcessor(str(pbf), osmium.osm.WAY).with_filter(osmium.filter.KeyFilter("highway")):
        if way.tags.get("highway") not in CLASS_SPEED or way.tags.get("access") in ("no", "private"):
            continue
        ids = [n.ref for n in way.nodes]
        n_segments = len(ids) - 1
        u.extend(ids[:-1])
        v.extend(ids[1:])
        speed.extend([way_speed(way.tags, implicit_maxspeed)] * n_segments)
        oneway.extend([way_oneway(way.tags)] * n_segments)
    segments = pl.DataFrame({"u": np.asarray(u), "v": np.asarray(v), "speed": np.asarray(speed), "oneway": np.asarray(oneway)})

    # 2nd pass: coordinates of the road nodes
    node_ids, lats, lons = array("q"), array("d"), array("d")
    road_nodes = osmium.filter.IdFilter(pl.concat([segments["u"], segments["v"]]).unique().to_list())
    for node in osmium.FileProcessor(str(pbf), osmium.osm.NODE).with_filter(road_nodes):
        node_ids.append(node.id)
        lats.append(node.location.lat)
        lons.append(node.location.lon)
    del road_nodes
    nodes = pl.DataFrame({"node": np.asarray(node_ids), "lat": np.asarray(lats), "lon": np.asarray(lons)})

    segments = (
        segments.join(nodes.rename({"node": "u", "lat": "u_lat", "lon": "u_lon"}), on="u")
        .join(nodes.rename({"node": "v", "lat": "v_lat", "lon": "v_lon"}), on="v")
        .filter(pl.col("u") != pl.col("v"))
        .with_columns(km=flat_dist(pl.col("u_lat"), pl.col("u_lon"), pl.col("v_lat"), pl.col("v_lon")))
        .with_columns(minutes=pl.col("km") / pl.col("speed") * 60)
    )
    forward = segments.filter(pl.col("oneway") >= 0).select("u", "v", "minutes", "km")
    backward = segments.filter(pl.col("oneway") <= 0).select(u="v", v="u", minutes="minutes", km="km")
    edges = pl.concat([forward, backward])
    # two roads can share the same segment; keep only the fastest
    # (scipy would add the duplicate weights together)
    edges = edges.sort("minutes").unique(["u", "v"], keep="first")
    return nodes, edges


def to_matrix(nodes: pl.DataFrame, edges: pl.DataFrame) -> csr_matrix:
    """Graph for scipy: matrix[a, b] = minutes from node a to node b, with a, b = row numbers in `nodes`.

    Every edge is reversed (v -> u). Dijkstra from a metro then gives the time from each town TO the metro.
    It matters because of one-way roads.
    """
    row_of = dict(zip(nodes["node"].to_list(), range(nodes.height)))
    u = edges["u"].replace_strict(row_of).to_numpy()
    v = edges["v"].replace_strict(row_of).to_numpy()
    return csr_matrix((edges["minutes"].to_numpy(), (v, u)), shape=(nodes.height, nodes.height))


def to_xy(lat: pl.Series, lon: pl.Series, lat0: float) -> np.ndarray:
    """Coordinates in km (good enough for finding the nearest road node)."""
    x = lon.to_numpy() * np.cos(np.radians(lat0)) * KM_PER_DEG
    y = lat.to_numpy() * KM_PER_DEG
    return np.column_stack([x, y])


def road_pairs(towns: pl.DataFrame, metros: pl.DataFrame, nodes: pl.DataFrame, edges: pl.DataFrame) -> pl.DataFrame:
    """(geonameid, metro_id, minutes): driving time from each town to each metro (pairs over 4 h are dropped)."""
    graph = to_matrix(nodes, edges)

    # Only connect towns to the big road network. If a town is snapped to a small separate piece
    # (an island, a one-way dead end), it can't reach any metro.
    # "strong" = you can drive from every node to every other node and back.
    _, network_of = connected_components(graph, directed=True, connection="strong")
    network_size = np.bincount(network_of)
    usable = np.flatnonzero(network_size[network_of] >= MIN_NETWORK_NODES)

    # nearest usable road node for every town and metro
    lat0 = (nodes["lat"].min() + nodes["lat"].max()) / 2  # middle of the country
    tree = cKDTree(to_xy(nodes["lat"][usable], nodes["lon"][usable], lat0))
    town_km, town_idx = tree.query(to_xy(towns["latitude"], towns["longitude"], lat0))
    metro_km, metro_idx = tree.query(to_xy(metros["mlat"], metros["mlon"], lat0))
    town_node = usable[town_idx]
    metro_node = usable[metro_idx]

    # time to drive from the town to its road node (and from the metro's road node to the metro)
    access_min_per_km = ACCESS_DETOUR / ACCESS_SPEED_KMH * 60

    results = []
    for metro_id, node, km in zip(metros["metro_id"], metro_node, metro_km):
        minutes_to_metro = dijkstra(graph, indices=node, limit=MAX_DRIVE_MIN)  # inf if not reached
        minutes = minutes_to_metro[town_node] + (town_km + km) * access_min_per_km
        df = pl.DataFrame({"geonameid": towns["geonameid"], "metro_id": metro_id, "minutes": minutes})
        results.append(df.cast({"metro_id": pl.Int64}))  # a single number would become Int32

    return pl.concat(results).filter(pl.col("minutes").is_finite())
