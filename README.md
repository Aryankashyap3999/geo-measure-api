# Geo Measure API

A small REST API that accepts geospatial files, extracts their features and calculates polygon areas and line lengths.

## Features

- Upload `.kml` files or `.zip` files containing a Shapefile
- Extracts every feature: index, geometry type, GeoJSON geometry, CRS and properties
- Polygon area and LineString length (MultiPolygon / MultiLineString are measured too)
- Points are returned without a measurement
- Unsupported geometries (e.g. GeometryCollection) get `measurement: null` plus a note explaining why, without failing the file
- Geographic CRS (EPSG:4326 etc.) is projected to a local UTM zone before measuring
- Clean JSON errors for bad extensions, broken KML/ZIP, ZIPs without a Shapefile, unsafe ZIP paths and missing CRS

## Tech stack

- **FastAPI** + Uvicorn: typed request/response models, automatic docs at `/docs`, very little boilerplate.
- **GeoPandas**: one call reads KML and Shapefile (via GDAL), gives us CRS handling and GeoJSON output.
- **Shapely** (geometry) and **PyProj** (CRS / transforms), both used through GeoPandas.
- **Pytest** for tests.

## Project structure

```text
app/
├── main.py                       app + error handler
├── config/settings.py            upload dir, size limit, allowed extensions
├── api/routes/files.py           HTTP endpoints only
├── api/schemas/file.py           response models
├── services/file_service.py      validate, store, orchestrate, read results
├── services/geospatial_service.py read KML / Shapefile, build features
├── services/measurement_service.py area / length / point / unsupported
├── utils/file_utils.py           safe ZIP extraction
├── utils/crs_utils.py            pick projected CRS, transform
└── exceptions.py
tests/                            pytest suite (fixtures are built in code)
sample-data/                      a KML and a Shapefile ZIP to try
uploads/                          stored uploads (git-ignored)
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional, values are read from the environment
```

Settings (environment variables): `UPLOAD_DIR` (default `uploads`), `MAX_UPLOAD_MB` (default `50`).

## Run locally

```bash
uvicorn app.main:app --reload
```

Docs: http://127.0.0.1:8000/docs. Tests: `pytest`. Lint: `ruff check . && ruff format .`.
Docker: `docker build -t geo-measure-api . && docker run -p 8000:8000 geo-measure-api`.

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/files/` | Upload a `.kml` or `.zip` (multipart field `file`). Processed during the request. |
| GET | `/api/files/{id}/` | File info: status, CRS and all features with measurements |
| GET | `/api/files/{id}/measurements/` | Only the per-feature measurements |

Errors are `{"detail": "..."}`: `400` unsupported/oversized file, `404` unknown id, `422` file could not be processed (the body also has the `id`; `GET /api/files/{id}/` then shows `status: "FAILED"` and the `error`).

### Example

```bash
curl -F file=@sample-data/sample.kml http://127.0.0.1:8000/api/files/
curl http://127.0.0.1:8000/api/files/<id>/measurements/
```

Measurements response:

```json
{
  "id": "fd5b758825054e5a878fdfc29e13d470",
  "measurements": [
    {"feature_id": 0, "geometry_type": "Polygon",
     "measurement": {"type": "area", "value": 123150885.84, "unit": "m2", "projected_crs": "EPSG:32643"},
     "note": null},
    {"feature_id": 1, "geometry_type": "LineString",
     "measurement": {"type": "length", "value": 11131.9, "unit": "m", "projected_crs": "EPSG:32643"},
     "note": null},
    {"feature_id": 2, "geometry_type": "Point", "measurement": null,
     "note": "Measurement not required for Point"}
  ]
}
```

A feature in the file response:

```json
{
  "id": 0, "geometry_type": "Polygon", "crs": "EPSG:4326",
  "geometry": {"type": "Polygon", "coordinates": [[[77.0, 0.0], [77.1, 0.0], [77.1, 0.1], [77.0, 0.1], [77.0, 0.0]]]},
  "properties": {"Name": "field"},
  "measurement": {"type": "area", "value": 123150885.84, "unit": "m2", "projected_crs": "EPSG:32643"},
  "measurement_note": null
}
```

## Architecture

Routes only deal with HTTP and call `file_service`. `file_service` validates and stores the upload, then asks `geospatial_service` for the features; that calls `measurement_service` per feature, which uses `crs_utils` for projection. Each upload lives in `uploads/<uuid>/` as `original.<ext>` and `result.json`. The id is a generated UUID, the user's filename is never used as a path.

## Processing flow

```text
POST /api/files/
 → check extension (.kml / .zip)
 → save to uploads/<id>/
 → .kml: read all layers   |   .zip: validate, safely extract, find .shp, read it
 → require a CRS
 → for each feature: geometry, GeoJSON, properties, measurement
 → store result.json (COMPLETED) or the error (FAILED)
```

ZIP safety: the archive must be a valid ZIP, every member must stay inside the extraction folder, the total uncompressed size is capped, and it must contain a `.shp`. Missing sidecar files (`.shx`/`.dbf`) make GDAL fail, which becomes a 422.

## Measurement flow

| Geometry | Result |
|---|---|
| Polygon / MultiPolygon | area |
| LineString / MultiLineString | length |
| Point | `null`, note says it is not required |
| Anything else, empty or missing geometry | `null`, note says why |

## CRS strategy

Latitude/longitude are angles, so `geometry.area` or `.length` on EPSG:4326 returns square or plain *degrees*, which are meaningless (a degree of longitude is about 111 km at the equator and shrinks to 0 at the poles). So geographic data is never measured directly:

```text
geometry + CRS
 → geographic?  yes → estimate the local UTM zone for that feature (GeoPandas estimate_utm_crs)
                     → transform → measure in metres
                no  → already projected, measure in its own units
```

A local UTM zone is accurate to well under 1% inside a zone and needs no hardcoded EPSG code, so a file from India and one from Chile each get a suitable CRS. The CRS used is returned as `projected_crs`. If the file already uses a projected CRS it is measured as is, and the unit is read from the CRS (a CRS in feet reports feet). A file with no CRS (Shapefile without `.prj`) is rejected, because guessing would silently produce wrong numbers. KML is always EPSG:4326 by specification.

## Design decisions

- Synchronous processing: files are small, so there is no queue or job system; status is just `COMPLETED` or `FAILED`.
- Local files plus one JSON per upload instead of a database: enough for the assignment, nothing to run.
- Measurements are computed once at upload and stored with the features.
- Multi-geometries are measured because Shapefile polygons are very often `MultiPolygon`.
- Geometry is returned as GeoJSON, properties go through GeoPandas' JSON writer so NaN and dates are API-safe.

### Alternatives considered

- **Django + DRF**: more setup (settings, migrations, serializers) than a database-less API needs; FastAPI gives typed models and docs for free.
- **Fixed CRS for everything (EPSG:3857 or one UTM zone)**: simplest, but Web Mercator inflates areas away from the equator and one UTM zone is wrong elsewhere. A per-feature UTM zone is nearly as simple and far more accurate.
- **Geodesic maths (`pyproj.Geod`)**: accurate everywhere, but the assignment asks for projected measurement and UTM is accurate enough inside a zone; listed under future scope.
- **Fiona / ogr2ogr directly**: GeoPandas wraps the same GDAL readers and adds CRS and GeoJSON handling.
- **Database / async job queue**: unnecessary for small synchronous uploads.

The file info endpoint returns the summary fields from the assignment (`id`, `filename`, `feature_count`, `crs`, `status`) plus the features, so one call is enough for a client.

## Learning

- Area/length in degrees is the classic geospatial bug; picking the CRS per feature is cheap with PyProj.
- KML folders become separate layers in GDAL, and a Shapefile can only hold one geometry type.
- ZIP uploads need path and size checks before extraction.

## Future scope

- A database and background processing for large files
- Geodesic measurement (`pyproj.Geod`) for features that span several UTM zones
- More formats (GeoJSON, GeoPackage), pagination of features, delete endpoint
- Authentication and per-user files
- A minimal upload page
