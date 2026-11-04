import polars as pl

# section, abandoned, historical, destroyed, religious (cemetery)
EXCLUDE = ["PPLX", "PPLQ", "PPLH", "PPLW", "PPLR"]

COLUMNS = [
    "geonameid", "name", "feature_code", "admin1_code", "admin2_code",
    "latitude", "longitude", "population",
]


def big_municipality(code: str, min_pop: int = 100_000) -> pl.Expr:
    """City key for `build_towns`: the municipality code, but only for big cities (else null).

    Small municipalities are left alone, so their villages are not merged into one place.
    """
    return pl.when(pl.col("population").max().over(code) >= min_pop).then(pl.col(code))


def build_towns(geo: pl.DataFrame, city_key: pl.Expr | None = None) -> pl.DataFrame:
    """Populated places from GeoNames.

    `city_key`: places with the same (non-null) key are districts of one city, keep only the biggest one.
    """
    places = geo.filter(
        pl.col("feature_class") == "P",
        pl.col("feature_code").str.starts_with("PPL"),
        ~pl.col("feature_code").is_in(EXCLUDE),
    )
    if city_key is not None:
        places = places.with_columns(city=city_key)
        not_city = places.filter(pl.col("city").is_null())
        biggest_per_city = (
            places.filter(pl.col("city").is_not_null())
            .sort(["population", "geonameid"], descending=[True, False])
            .unique("city", keep="first")
        )
        places = pl.concat([not_city, biggest_per_city])
    towns = places.select(COLUMNS).sort("geonameid")
    assert towns["geonameid"].is_unique().all()
    return towns
