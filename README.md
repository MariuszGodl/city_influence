# Przypisanie miejscowości do metropolii

Wybieram zamieszkane miejscowości z GeoNames, wyznaczam metropolie i przypisuję do nich miejscowości. Odległość liczę na dwa sposoby:

- **linia prosta** (km),
- **czas dojazdu po drogach** z OpenStreetMap (min).

## Uruchomienie

```bash
python -m venv .venv && .venv/bin/pip install -r req.txt
cd task
../.venv/bin/python main.py   # kraj ustawiany w main.py: main("PL")
```

Dane wejściowe:

- `data/<KRAJ>/<KRAJ>.txt` z http://download.geonames.org/export/dump/
- `data/osm/<kraj>-latest.osm.pbf` z https://download.geofabrik.de/

Pliki OSM nie są w repo (kilka GB). Żeby policzyć wariant z czasem dojazdu po drogach, najpierw je pobierz:

```bash
.venv/bin/python download_osm.py   # kraje ustawiane w COUNTRIES w download_osm.py
```

Bez pliku `.osm.pbf` liczony jest tylko wariant w linii prostej. Pierwsze budowanie grafu dróg trwa kilka minut, potem graf jest czytany z `output/<KRAJ>/<KRAJ>_road_*.parquet`.

Wyniki (parquet i mapy PNG) zapisują się w `output/<KRAJ>/`.

## Wyniki (wersja iteracyjna)

Kolor oznacza metropolię, a szare punkty to miejscowości bez metropolii.

### Polska

| Linia prosta (km) | Drogi (min) |
|---|---|
| ![PL km](output/PL/PL_metro_ranges_iter.png) | ![PL min](output/PL/PL_metro_ranges_iter_roads.png) |

### Włochy

| Linia prosta (km) | Drogi (min) |
|---|---|
| ![IT km](output/IT/IT_metro_ranges_iter.png) | ![IT min](output/IT/IT_metro_ranges_iter_roads.png) |

### Austria

| Linia prosta (km) | Drogi (min) |
|---|---|
| ![AT km](output/AT/AT_metro_ranges_iter.png) | ![AT min](output/AT/AT_metro_ranges_iter_roads.png) |

### Czechy

| Linia prosta (km) | Drogi (min) |
|---|---|
| ![CZ km](output/CZ/CZ_metro_ranges_iter.png) | ![CZ min](output/CZ/CZ_metro_ranges_iter_roads.png) |

### Hiszpania

| Linia prosta (km) | Drogi (min) |
|---|---|
| ![ES km](output/ES/ES_metro_ranges_iter.png) | ![ES min](output/ES/ES_metro_ranges_iter_roads.png) |
