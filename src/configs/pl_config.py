"""Poland. For another country copy this file as <cc>_config.py and run `python main.py <cc>`."""
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]

COUNTRY = "PL"  # prefix of every output file, e.g. output/PL/PL_towns.parquet

GEONAMES_TXT = ROOT / "data" / "PL" / "PL.txt"
PBF = ROOT / "data" / "osm" / "poland-latest.osm.pbf"
OUT = ROOT / "output" / COUNTRY

METRO_MIN_POP = 200_000

# implicit maxspeed tag values (https://wiki.openstreetmap.org/wiki/Key:maxspeed)
IMPLICIT_MAXSPEED = {"PL:urban": 50, "PL:rural": 90, "PL:expressway": 120, "PL:motorway": 140, "PL:living_street": 20}

# places with the same non-null key are one city (keep only its most populous row); None = no dedup
# here: city counties (admin2 suffix >= 61) also list their districts
CITY_KEY = pl.when(pl.col("admin2_code").str.slice(2, 2).cast(pl.Int64, strict=False) >= 61).then(pl.col("admin2_code"))
