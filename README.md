# Geo Measure API

A simple REST API for uploading geospatial files and calculating measurements from their features.

The API supports KML files and ZIP files containing Shapefiles. It extracts the features, their geometry and properties, and calculates measurements based on the geometry type.

## Features

- Upload `.kml` files
- Upload `.zip` files containing a Shapefile
- Extract feature information
- Support Point, LineString and Polygon geometries
- Calculate:
  - Polygon area
  - LineString length
- Handle Point geometries without measurement
- Handle unsupported geometry types gracefully
- Handle geographic CRS such as `EPSG:4326`
- Transform geographic coordinates to a suitable projected CRS before calculating measurements
- Store uploaded files locally
- Simple REST APIs
- Automated tests

## Tech Stack

- Python
- FastAPI
- GeoPandas
- Shapely
- PyProj
- Uvicorn
- Pytest

## Project Structure

```text
geo-measure-api/
│
├── app/
│   ├── main.py
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   └── files.py
│   │   └── schemas/
│   │       └── file.py
│   │
│   ├── services/
│   │   ├── file_service.py
│   │   ├── geospatial_service.py
│   │   └── measurement_service.py
│   │
│   ├── utils/
│   │   ├── file_utils.py
│   │   └── crs_utils.py
│   │
│   └── exceptions.py
│
├── tests/
│   ├── test_upload.py
│   ├── test_measurements.py
│   └── test_crs.py
│
├── uploads/
│   └── .gitkeep
│
├── sample-data/
│   └── README.md
│
├── .env.example
├── .gitignore
├── CLAUDE.md
├── Dockerfile
├── requirements.txt
└── README.md