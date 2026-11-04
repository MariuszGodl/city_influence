"""Czech Republic."""
from pathlib import Path

import polars as pl

from towns import big_municipality

ROOT = Path(__file__).resolve().parents[2]

COUNTRY = "CZ"
GEONAMES_TXT = ROOT / "data" / "CZ" / "CZ.txt"
PBF = ROOT / "data" / "osm" / "czech-republic-latest.osm.pbf"
OUT = ROOT / "output" / COUNTRY

# 5 metros: Prague, Brno, Ostrava, Plzeň, Liberec
METRO_MIN_POP = 100_000

IMPLICIT_MAXSPEED = {"CZ:urban": 50, "CZ:rural": 90, "CZ:motorway": 130, "CZ:living_street": 20}

# Prague (admin1 52) and Brno (admin2 0642) districts have no common municipality code; other cities share admin3
CITY_KEY = (
    pl.when(pl.col("admin1_code") == "52").then(pl.lit("Praha"))
    .when(pl.col("admin2_code") == "0642").then(pl.lit("Brno"))
    .otherwise(big_municipality("admin3_code"))
)
