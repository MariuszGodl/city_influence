"""Italy."""
from pathlib import Path

from towns import big_municipality

ROOT = Path(__file__).resolve().parents[2]

COUNTRY = "IT"
GEONAMES_TXT = ROOT / "data" / "IT" / "IT.txt"
PBF = ROOT / "data" / "osm" / "italy-latest.osm.pbf"
OUT = ROOT / "output" / COUNTRY

METRO_MIN_POP = 250_000

IMPLICIT_MAXSPEED = {"IT:urban": 50, "IT:rural": 90, "IT:trunk": 110, "IT:motorway": 130, "IT:living_street": 10}

CITY_KEY = big_municipality("admin3_code")
