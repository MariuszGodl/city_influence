import polars as pl


def select_metros(towns: pl.DataFrame, min_pop: int) -> pl.DataFrame:
    return (
        towns.filter(pl.col("population") >= min_pop)
        .select(
            metro_id="geonameid",
            metro_name="name",
            mlat="latitude",
            mlon="longitude",
            own_pop="population",
            power="population",
        )
        .sort("power", descending=True)
    )
