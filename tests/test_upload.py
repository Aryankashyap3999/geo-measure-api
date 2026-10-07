import io
import zipfile

from tests.conftest import KML, SQUARE, make_shapefile_zip, upload


def test_kml_upload(client):
    response = upload(client, "a.kml", KML)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["crs"] == "EPSG:4326"
    assert [f["geometry_type"] for f in body["features"]] == [
        "Polygon",
        "LineString",
        "Point",
    ]
    assert body["features"][0]["properties"]["Name"] == "field"
    assert body["features"][0]["geometry"]["type"] == "Polygon"


def test_shapefile_zip_upload(client, tmp_path):
    response = upload(client, "a.zip", make_shapefile_zip(tmp_path, [SQUARE, SQUARE]))
    assert response.status_code == 201
    assert response.json()["feature_count"] == 2


def test_invalid_extension(client):
    response = upload(client, "a.txt", "hello")
    assert response.status_code == 400


def test_invalid_zip(client):
    assert upload(client, "a.zip", b"not a zip").status_code == 422


def test_zip_without_shapefile(client):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("readme.txt", "hi")
    response = upload(client, "a.zip", buffer.getvalue())
    assert response.status_code == 422
    assert "Shapefile" in response.json()["detail"]


def test_zip_path_traversal(client):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("../evil.shp", "x")
    assert upload(client, "a.zip", buffer.getvalue()).status_code == 422


def test_malformed_kml(client):
    assert upload(client, "a.kml", "<kml><broken").status_code == 422


def test_failed_upload_is_recorded(client):
    file_id = upload(client, "a.kml", "<kml><broken").json()["id"]
    info = client.get(f"/api/files/{file_id}/").json()
    assert info["status"] == "FAILED"
    assert info["error"]


def test_get_file_info(client):
    file_id = upload(client, "a.kml", KML).json()["id"]
    response = client.get(f"/api/files/{file_id}/")
    assert response.status_code == 200
    assert response.json()["feature_count"] == 3


def test_missing_file_id(client):
    assert client.get("/api/files/nope/").status_code == 404
    assert client.get("/api/files/nope/measurements/").status_code == 404
