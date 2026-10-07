import io
import zipfile

import geopandas as gpd
import pytest
from fastapi.testclient import TestClient
from shapely.geometry import LineString, Polygon

# ~11.1 km square / line on the equator, inside UTM zone 43N
SQUARE = Polygon([(77, 0), (77.1, 0), (77.1, 0.1), (77, 0.1)])
LINE = LineString([(77, 0), (77.1, 0)])

KML = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
<Placemark><name>field</name><Polygon><outerBoundaryIs><LinearRing><coordinates>
77,0,0 77.1,0,0 77.1,0.1,0 77,0.1,0 77,0,0</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>
<Placemark><name>road</name><LineString><coordinates>77,0,0 77.1,0,0</coordinates></LineString></Placemark>
<Placemark><name>well</name><Point><coordinates>77.05,0.05,0</coordinates></Point></Placemark>
</Document></kml>"""


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.file_service.UPLOAD_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


def make_shapefile_zip(tmp_path, geometries, crs="EPSG:4326", with_prj=True) -> bytes:
    folder = tmp_path / "shp"
    folder.mkdir(exist_ok=True)
    gdf = gpd.GeoDataFrame(
        {"name": [f"f{i}" for i in range(len(geometries))]},
        geometry=geometries,
        crs=crs,
    )
    gdf.to_file(folder / "data.shp")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for path in folder.iterdir():
            if with_prj or path.suffix != ".prj":
                zf.write(path, path.name)
    return buffer.getvalue()


def upload(client, name, content):
    return client.post("/api/files/", files={"file": (name, content)})
