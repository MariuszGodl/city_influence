import polars as pl

from assign import pick, radius

MAX_ITER = 100


def iterate(
    towns: pl.DataFrame, metros: pl.DataFrame, pairs: pl.DataFrame,
    col: str = "dist_km", max_iter: int = MAX_ITER,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Metros grow: each round, towns join a metro and their population is added to its power.
    A bigger power means a bigger radius, so in the next round it can reach more towns.
    Stops when no town joins.

    Returns (assigned towns with the round they joined, one row per round, final power per metro).
    """
    pop = towns.select("geonameid", "population")
    metros = metros.select("metro_id", "own_pop", power="own_pop").sort("metro_id")
    assigned = pl.DataFrame(schema={
        "geonameid": pl.Int64, "metro_id": pl.Int64, "radius": pl.Float64, "impact": pl.Float64, "round": pl.Int32,
    })
    log = []

    for k in range(1, max_iter + 1):
        new = pick(pairs, metros, col)
        if new.is_empty():
            break
        new = new.with_columns(round=pl.lit(k, pl.Int32))
        assigned = pl.concat([assigned, new])
        # a town that joined a metro stays there, remove it from the next rounds
        pairs = pairs.join(new, on="geonameid", how="anti")
        new_pop = new.join(pop, on="geonameid")
        gain = new_pop.group_by("metro_id").agg(gain=pl.col("population").sum())
        metros = metros.join(gain, on="metro_id", how="left", maintain_order="left").select(
            "metro_id", "own_pop", power=pl.col("power") + pl.col("gain").fill_null(0)
        )
        log.append({"round": k, "new_towns": new.height, "new_population": new_pop["population"].sum()})

    if not new.is_empty():
        raise RuntimeError(f"still growing after {max_iter} rounds")

    rounds = pl.DataFrame(log).with_columns(
        cum_towns=pl.col("new_towns").cum_sum(), cum_population=pl.col("new_population").cum_sum()
    )
    power = (
        metros.join(assigned.group_by("metro_id").agg(n_towns=pl.len()), on="metro_id", how="left")
        .select(
            "metro_id",
            base="own_pop",
            power_final="power",
            gain=pl.col("power") - pl.col("own_pop"),
            n_towns=pl.col("n_towns").fill_null(0),
            radius_static=radius(pl.col("own_pop")),
            radius_final=radius(pl.col("power")),
        )
    )
    # every town is in at most one metro, and no population got lost
    assert assigned["geonameid"].is_unique().all()
    assert power["gain"].sum() == assigned.join(pop, on="geonameid")["population"].sum()
    return assigned, rounds, power
