import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.api.schemas.file import FeatureMeasurement, FileInfo, FileMeasurements
from app.config.settings import ALLOWED_EXTENSIONS, MAX_UPLOAD_BYTES, UPLOAD_DIR
from app.exceptions import FileIdNotFoundError, ProcessingError, UnsupportedFileError
from app.services.geospatial_service import extract_features, read_geodataframe


def upload_file(upload: UploadFile) -> FileInfo:
    filename = Path(upload.filename or "").name
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileError(
            "Unsupported file type; upload a .kml or a .zip containing a Shapefile"
        )

    file_id = uuid.uuid4().hex
    folder = UPLOAD_DIR / file_id
    folder.mkdir(parents=True)
    stored = folder / f"original{extension}"
    _save(upload, stored)

    try:
        gdf = read_geodataframe(stored)
        crs, features = extract_features(gdf)
        info = FileInfo(
            id=file_id,
            filename=filename,
            status="COMPLETED",
            crs=crs,
            feature_count=len(features),
            features=features,
        )
    except ProcessingError as error:
        info = FileInfo(
            id=file_id, filename=filename, status="FAILED", error=error.message
        )
        _save_info(info)
        raise ProcessingError(error.message, file_id)

    _save_info(info)
    return info


def get_file(file_id: str) -> FileInfo:
    path = UPLOAD_DIR / file_id / "result.json"
    # file_id is only ever a hex uuid, anything else cannot exist (and may be a path trick)
    if not file_id.isalnum() or not path.exists():
        raise FileIdNotFoundError("File not found")
    return FileInfo.model_validate_json(path.read_text())


def get_measurements(file_id: str) -> FileMeasurements:
    info = get_file(file_id)
    return FileMeasurements(
        id=info.id,
        measurements=[
            FeatureMeasurement(
                feature_id=f.id,
                geometry_type=f.geometry_type,
                measurement=f.measurement,
                note=f.measurement_note,
            )
            for f in info.features
        ],
    )


def _save(upload: UploadFile, dest: Path) -> None:
    with dest.open("wb") as out:
        shutil.copyfileobj(upload.file, out)
    if dest.stat().st_size > MAX_UPLOAD_BYTES:
        shutil.rmtree(dest.parent)
        raise UnsupportedFileError("File is too large")


def _save_info(info: FileInfo) -> None:
    (UPLOAD_DIR / info.id / "result.json").write_text(info.model_dump_json())
