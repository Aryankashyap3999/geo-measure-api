from typing import Any, Literal

from pydantic import BaseModel


class Measurement(BaseModel):
    type: Literal["area", "length"]
    value: float
    unit: str
    projected_crs: str


class Feature(BaseModel):
    id: int
    geometry_type: str | None
    geometry: dict[str, Any] | None
    crs: str
    properties: dict[str, Any]
    measurement: Measurement | None = None
    measurement_note: str | None = None


class FileInfo(BaseModel):
    id: str
    filename: str
    status: Literal["COMPLETED", "FAILED"]
    error: str | None = None
    crs: str | None = None
    feature_count: int = 0
    features: list[Feature] = []


class FeatureMeasurement(BaseModel):
    feature_id: int
    geometry_type: str | None
    measurement: Measurement | None
    note: str | None


class FileMeasurements(BaseModel):
    id: str
    measurements: list[FeatureMeasurement]
