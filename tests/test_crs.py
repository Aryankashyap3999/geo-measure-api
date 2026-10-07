import pytest
from pyproj import CRS
from shapely.geometry import Polygon

from app.services.measurement_service import measure
from app.utils.crs_utils import projected_crs_for
from tests.conftest import SQUARE, make_shapefile_zip, upload


def test_geographic_crs_is_projected_before_measuring():
    m, _ = measure(SQUARE, CRS("EPSG:4326"))
    assert m.projected_crs == "EPSG:32643"  # UTM 43N
    assert m.value > 1e8  # square metres, not 0.01 square degrees


def test_zone_depends_on_location():
    south_america = Polygon([(-70, -33), (-69.9, -33), (-69.9, -32.9), (-70, -32.9)])
    assert (
        projected_crs_for(south_america, CRS("EPSG:4326")).to_string() == "EPSG:32719"
    )


def test_projected_crs_is_used_as_is():
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    m, _ = measure(square, CRS("EPSG:32643"))
    assert m.value == pytest.approx(10_000)
    assert m.projected_crs == "EPSG:32643"


def test_missing_crs_is_rejected(client, tmp_path):
    zip_bytes = make_shapefile_zip(tmp_path, [SQUARE], with_prj=False)
    response = upload(client, "a.zip", zip_bytes)
    assert response.status_code == 422
    assert "CRS" in response.json()["detail"]
