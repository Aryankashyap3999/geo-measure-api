from pyproj import CRS
from shapely.geometry.base import BaseGeometry

from app.api.schemas.file import Measurement
from app.utils.crs_utils import to_projected, unit_labels

AREA_TYPES = {"Polygon", "MultiPolygon"}
LENGTH_TYPES = {"LineString", "MultiLineString"}


def measure(
    geometry: BaseGeometry | None, crs: CRS
) -> tuple[Measurement | None, str | None]:
    """Return (measurement, note). note explains why there is no measurement."""
    if geometry is None or geometry.is_empty:
        return None, "Feature has no geometry"

    kind = geometry.geom_type
    if kind == "Point":
        return None, "Measurement not required for Point"
    if kind not in AREA_TYPES | LENGTH_TYPES:
        return None, f"Unsupported geometry type: {kind}"

    projected, projected_crs = to_projected(geometry, crs)
    length_unit, area_unit = unit_labels(projected_crs)
    projected_name = projected_crs.to_string()
    if kind in AREA_TYPES:
        return Measurement(
            type="area",
            value=projected.area,
            unit=area_unit,
            projected_crs=projected_name,
        ), None
    return Measurement(
        type="length",
        value=projected.length,
        unit=length_unit,
        projected_crs=projected_name,
    ), None
