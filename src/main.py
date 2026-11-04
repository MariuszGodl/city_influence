import importlib
from pathlib import Path

import polars as pl

from assign import pick, straight_pairs
from iterate import iterate
from load import read_geo
from metros import select_metros
from plot import plot_metro_ranges
from roads import build_graph, road_pairs
from towns import build_towns

TOWN_COLS = ["geonameid", "name", "population"]
METRO_COLS = ["metro_id", "metro_name"]


def out_path(cfg, name: str) -> Path:
    """e.g. output/PL/PL_towns.parquet"""
    return cfg.OUT / f"{cfg.COUNTRY}_{name}"


def save(df: pl.DataFrame, path: Path) -> None:
    df.write_parquet(path)
    print(f"  {path.name}: {df.height:,} rows")


def load_road_graph(cfg) -> tuple[pl.DataFrame, pl.DataFrame] | None:
    """Road graph from the cache; built from the OSM file the first time. None if there is no OSM file."""
    nodes_path, edges_path = out_path(cfg, "road_nodes.parquet"), out_path(cfg, "road_edges.parquet")
    if not nodes_path.exists() or not edges_path.exists():
        if not cfg.PBF.exists():
            return None
        nodes, edges = build_graph(cfg.PBF, cfg.IMPLICIT_MAXSPEED)  # slow, a few minutes
        save(nodes, nodes_path)
        save(edges, edges_path)
    return pl.read_parquet(nodes_path), pl.read_parquet(edges_path)


def add_names(df: pl.DataFrame, pairs: pl.DataFrame, towns: pl.DataFrame, metros: pl.DataFrame, unit: str) -> pl.DataFrame:
    """Add town/metro names and the distance, so the output file is readable."""
    df = (
        df.join(pairs, on=["geonameid", "metro_id"])
        .join(towns.select(TOWN_COLS), on="geonameid")
        .join(metros.select(METRO_COLS), on="metro_id")
    )
    other_cols = [c for c in df.columns if c not in TOWN_COLS + METRO_COLS]
    return df.select(TOWN_COLS + METRO_COLS + other_cols).rename({"radius": f"radius_{unit}"}).sort("geonameid")


def run(cfg, label: str, suffix: str, towns, metros, pairs, col: str) -> None:
    """Static and iterative assignment for one kind of distance: col is "dist_km" or "minutes"."""
    unit = "km" if col == "dist_km" else "min"
    print(f"\n== {label}")

    static = pick(pairs, metros, col)
    assigned, rounds, power = iterate(towns, metros, pairs, col)
    # sanity check: the first round of the iterative version is the static version
    assert static.equals(assigned.filter(pl.col("round") == 1).drop("round"))

    save(add_names(static, pairs, towns, metros, unit), out_path(cfg, f"assign_static{suffix}.parquet"))
    save(add_names(assigned, pairs, towns, metros, unit), out_path(cfg, f"assign_iter{suffix}.parquet"))
    save(rounds, out_path(cfg, f"assign_iter_rounds{suffix}.parquet"))

    power = (
        power.join(metros.select(METRO_COLS), on="metro_id")
        .select("metro_id", "metro_name", pl.exclude("metro_id", "metro_name"))
        .rename({"radius_static": f"radius_static_{unit}", "radius_final": f"radius_final_{unit}"})
        .sort("power_final", descending=True)
    )
    save(power, out_path(cfg, f"metro_power{suffix}.parquet"))

    plot_metro_ranges(towns, metros, static, out_path(cfg, f"metro_ranges_static{suffix}.png"),
                      f"{cfg.COUNTRY} metro ranges: {label}, static")
    plot_metro_ranges(towns, metros, assigned, out_path(cfg, f"metro_ranges_iter{suffix}.png"),
                      f"{cfg.COUNTRY} metro ranges: {label}, iterative")

    summary = f"  static: {static.height:,} towns | iterative: {rounds.height} rounds, {assigned.height:,} towns"
    with pl.Config(tbl_rows=20, thousands_separator=True, float_precision=1, tbl_hide_dataframe_shape=True):
        report = f"{summary}\n{rounds}\n{power.drop('metro_id')}"
    print(report)
    with out_path(cfg, "log.txt").open("a", encoding="utf-8") as f:
        f.write(f"== {label}\n{report}\n\n")


def main(country: str) -> None:
    cfg = importlib.import_module(f"configs.{country.lower()}_config")
    cfg.OUT.mkdir(parents=True, exist_ok=True)
    out_path(cfg, "log.txt").write_text("", encoding="utf-8")

    print("== places")
    geo = read_geo(cfg.GEONAMES_TXT)
    save(geo, out_path(cfg, "geo.parquet"))
    towns = build_towns(geo, cfg.CITY_KEY)
    save(towns, out_path(cfg, "towns.parquet"))
    metros = select_metros(towns, cfg.METRO_MIN_POP)
    save(metros, out_path(cfg, "metros.parquet"))

    # a metro is never assigned to another metro
    candidates = towns.join(metros, left_on="geonameid", right_on="metro_id", how="anti")

    run(cfg, "straight line (km)", "", towns, metros, straight_pairs(candidates, metros), "dist_km")

    graph = load_road_graph(cfg)
    if graph is None:
        print(f"\n== road travel time skipped: no {cfg.PBF.name}")
        return
    nodes, edges = graph
    run(cfg, "road travel time (min)", "_roads", towns, metros, road_pairs(candidates, metros, nodes, edges), "minutes")


if __name__ == "__main__":
    # PL, CZ, ES, IT, AT
    main("PL")
