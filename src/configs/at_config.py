"""Austria."""
from pathlib import Path

import polars as pl

from towns import big_municipality

ROOT = Path(__file__).resolve().parents[2]

COUNTRY = "AT"
GEONAMES_TXT = ROOT / "data" / "AT" / "AT.txt"
PBF = ROOT / "data" / "osm" / "austria-latest.osm.pbf"
OUT = ROOT / "output" / COUNTRY

# 6 metros: Vienna, Graz, Linz, Salzburg, Innsbruck, Klagenfurt (next is Villach at ~59k)
METRO_MIN_POP = 100_000

IMPLICIT_MAXSPEED = {"AT:urban": 50, "AT:rural": 100, "AT:trunk": 100, "AT:motorway": 130}

# Vienna (admin1 09) districts have no common municipality code; other cities share admin3 (Gemeindekennziffer)
CITY_KEY = (
    pl.when(pl.col("admin1_code") == "09").then(pl.lit("Wien"))
    .otherwise(big_municipality("admin3_code"))
)
