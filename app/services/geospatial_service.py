import json
import tempfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio
from pyproj import CRS

from app.api.schemas.file import Feature
from app.config.settings import MAX_UPLOAD_BYTES
from app.exceptions import ProcessingError
from app.services.measurement_service import measure
from app.utils.file_utils import safe_extract_zip


def read_geodataframe(path: Path) -> gpd.GeoDataFrame:
    """Read a .kml or a .zip (containing a Shapefile) into a GeoDataFrame."""
    try:
        if path.suffix == ".kml":
            return _read_kml(path)
        with tempfile.TemporaryDirectory() as tmp:
            shp = safe_extract_zip(path, Path(tmp), MAX_UPLOAD_BYTES)
            return gpd.read_file(shp)
    except ProcessingError:
        raise
    except Exception:  # noqa: BLE001 - any reader failure means bad input
        raise ProcessingError(
            "Could not read geospatial data; the file may be malformed or incomplete"
        )


def _read_kml(path: Path) -> gpd.GeoDataFrame:
    # a KML folder becomes a layer, so read every layer
    layers = [name for name, _ in pyogrio.list_layers(path)]
    frames = [gpd.read_file(path, driver="KML", layer=name) for name in layers]
    return pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]


def extract_features(gdf: gpd.GeoDataFrame) -> tuple[str, list[Feature]]:
    """Return (crs, features) with geometry, properties and measurements."""
    if gdf.crs is None:
        raise ProcessingError("File has no CRS (a Shapefile needs its .prj file)")
    crs: CRS = gdf.crs
    crs_name = crs.to_string()

    # to_json handles NaN/timestamps so properties are API-safe
    geojson_features = json.loads(gdf.to_json(drop_id=True))["features"]

    features = []
    for index, (geometry, item) in enumerate(zip(gdf.geometry, geojson_features)):
        measurement, note = measure(geometry, crs)
        features.append(
            Feature(
                id=index,
                geometry_type=None if geometry is None else geometry.geom_type,
                geometry=item["geometry"],
                crs=crs_name,
                properties=item["properties"],
                measurement=measurement,
                measurement_note=note,
            )
        )
    return crs_name, features
