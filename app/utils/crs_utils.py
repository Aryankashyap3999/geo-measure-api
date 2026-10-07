from geopandas import GeoSeries
from pyproj import CRS
from shapely.geometry.base import BaseGeometry


def projected_crs_for(geometry: BaseGeometry, crs: CRS) -> CRS:
    """CRS to measure in. Geographic CRS -> local UTM zone, projected CRS -> unchanged."""
    if not crs.is_geographic:
        return crs
    # ponytail: one UTM zone per feature; features spanning zones lose some accuracy
    return GeoSeries([geometry], crs=crs).estimate_utm_crs()


def to_projected(geometry: BaseGeometry, crs: CRS) -> tuple[BaseGeometry, CRS]:
    target = projected_crs_for(geometry, crs)
    if target == crs:
        return geometry, crs
    projected = GeoSeries([geometry], crs=crs).to_crs(target).iloc[0]
    return projected, target


def unit_labels(crs: CRS) -> tuple[str, str]:
    """(length unit, area unit) of a projected CRS."""
    name = crs.axis_info[0].unit_name
    if name == "metre":
        return "m", "m2"
    return name, f"{name}^2"
