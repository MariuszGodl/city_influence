"""Spain."""
from pathlib import Path

from towns import big_municipality

ROOT = Path(__file__).resolve().parents[2]

COUNTRY = "ES"
GEONAMES_TXT = ROOT / "data" / "ES" / "ES.txt"
PBF = ROOT / "data" / "osm" / "spain-latest.osm.pbf"
OUT = ROOT / "output" / COUNTRY

# 13 metros: Madrid ... Valladolid
METRO_MIN_POP = 300_000

IMPLICIT_MAXSPEED = {"ES:urban": 50, "ES:rural": 90, "ES:motorway": 120, "ES:living_street": 20}

# admin3 = municipality (INE code); big cities also list their districts (Madrid-Ciudad Lineal, ...)
CITY_KEY = big_municipality("admin3_code")
