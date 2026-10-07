import pytest
from shapely.geometry import Point

from tests.conftest import KML, make_shapefile_zip, upload


def test_polygon_area_and_linestring_length(client):
    file_id = upload(client, "a.kml", KML).json()["id"]
    response = client.get(f"/api/files/{file_id}/measurements/")
    assert response.status_code == 200
    area, length, point = response.json()["measurements"]

    assert area["measurement"]["type"] == "area"
    assert area["measurement"]["unit"] == "m2"
    assert area["measurement"]["value"] == pytest.approx(123.9e6, rel=0.01)
    assert length["measurement"]["type"] == "length"
    assert length["measurement"]["value"] == pytest.approx(11_132, rel=0.01)
    assert point["measurement"] is None


def test_point_has_no_measurement(client, tmp_path):
    body = upload(client, "a.zip", make_shapefile_zip(tmp_path, [Point(77, 0)])).json()
    feature = body["features"][0]
    assert feature["measurement"] is None
    assert "Point" in feature["measurement_note"]


def test_unsupported_geometry_does_not_fail_file(client):
    kml = KML.replace(
        "</Document>",
        "<Placemark><MultiGeometry><Point><coordinates>77,0</coordinates></Point>"
        "<LineString><coordinates>77,0 77.1,0</coordinates></LineString></MultiGeometry></Placemark></Document>",
    )
    body = upload(client, "a.kml", kml).json()
    assert body["status"] == "COMPLETED"
    unsupported = body["features"][-1]
    assert unsupported["measurement"] is None
    assert "Unsupported" in unsupported["measurement_note"]
    assert body["features"][0]["measurement"]["type"] == "area"
