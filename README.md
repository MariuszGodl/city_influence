# Przypisanie miejscowości do metropolii (Polars)

Wybieram zamieszkane miejscowości z GeoNames, wyznaczam metropolie i przypisuję do nich miejscowości według wzoru z zadania ([task.md](task.md)). Odległość liczę na dwa sposoby:

- **linia prosta** (km),
- **czas dojazdu po drogach** z OpenStreetMap (min).

Założenia i ograniczenia: [notes.md](notes.md).

## Uruchomienie

```bash
python -m venv .venv && .venv/bin/pip install -r req.txt
cd task
../.venv/bin/python main.py   # kraj ustawiany w main.py: main("PL")
```

Dane wejściowe:

- `data/<KRAJ>/<KRAJ>.txt` z http://download.geonames.org/export/dump/
- `data/osm/<kraj>-latest.osm.pbf` z https://download.geofabrik.de/

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
