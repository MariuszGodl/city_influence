from pathlib import Path

import polars as pl

SCHEMA = {
    "geonameid": pl.Int64,
    "name": pl.String,
    "asciiname": pl.String,
    "alternatenames": pl.String,
    "latitude": pl.Float64,
    "longitude": pl.Float64,
    "feature_class": pl.String,
    "feature_code": pl.String,
    "country_code": pl.String,
    "cc2": pl.String,
    "admin1_code": pl.String,
    "admin2_code": pl.String,  # keep String: leading zeros ("0264")
    "admin3_code": pl.String,
    "admin4_code": pl.String,
    "population": pl.Int64,  # 0 means unknown
    "elevation": pl.Int64,
    "dem": pl.Int64,
    "timezone": pl.String,
    "modification_date": pl.Date,
}


def read_geo(path: Path) -> pl.DataFrame:
    geo = pl.read_csv(path, separator="\t", has_header=False, schema=SCHEMA, quote_char=None)
    assert geo["geonameid"].is_unique().all()
    assert geo["population"].null_count() == 0
    return geo
