from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # save to file, no window
import matplotlib.pyplot as plt
import numpy as np
import polars as pl

UNASSIGNED = "lightgray"


def metro_colors(metros: pl.DataFrame) -> dict[int, tuple]:
    """One color per metro, biggest metro first.

    tab20 comes in pairs (dark blue, light blue, ...), so take the 10 dark ones first, then the light ones.
    """
    cmap = plt.get_cmap("tab20")
    order = list(range(0, 20, 2)) + list(range(1, 20, 2))
    ids = metros.sort("power", descending=True)["metro_id"]
    return {metro_id: cmap(order[i % 20]) for i, metro_id in enumerate(ids)}


def plot_metro_ranges(towns: pl.DataFrame, metros: pl.DataFrame, assigned: pl.DataFrame, path: Path, title: str) -> None:
    """Every town as a small dot, colored by its metro (gray if it has none)."""
    colors = metro_colors(metros)

    # a metro is not in `assigned`, so it is added as belonging to itself
    owner = pl.concat([
        assigned.select("geonameid", "metro_id"),
        metros.select(geonameid="metro_id", metro_id="metro_id"),
    ])
    points = towns.select("geonameid", "latitude", "longitude").join(owner, on="geonameid", how="left")
    free = points.filter(pl.col("metro_id").is_null())
    taken = points.filter(pl.col("metro_id").is_not_null())

    # 1 degree of longitude is shorter than 1 degree of latitude, so stretch y to avoid a squashed map
    aspect = 1 / np.cos(np.radians(points["latitude"].mean()))

    fig, ax = plt.subplots(figsize=(14, 14 * aspect * 0.62))
    ax.scatter(free["longitude"], free["latitude"], s=1.5, c=UNASSIGNED, linewidths=0)
    ax.scatter(taken["longitude"], taken["latitude"], s=1.5, c=[colors[m] for m in taken["metro_id"]], linewidths=0)
    ax.set_aspect(aspect)
    ax.set_title(title)
    ax.set_axis_off()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  {path.name}")
