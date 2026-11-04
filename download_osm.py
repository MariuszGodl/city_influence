import os
import urllib.request

COUNTRIES = ["poland"] #["austria", "czech-republic", "italy", "poland", "spain"]
OUT_DIR = os.path.join(os.path.dirname(__file__), "data", "osm")

print(f"This can take a while... (Polish file 1.97GiB)")
os.makedirs(OUT_DIR, exist_ok=True)
for c in COUNTRIES:
    name = f"{c}-latest.osm.pbf"
    print(f"Downloading {name}...")
    urllib.request.urlretrieve(f"https://download.geofabrik.de/europe/{name}", os.path.join(OUT_DIR, name))
