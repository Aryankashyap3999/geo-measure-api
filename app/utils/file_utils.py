import zipfile
from pathlib import Path

from app.exceptions import ProcessingError


def safe_extract_zip(zip_path: Path, dest: Path, max_bytes: int) -> Path:
    """Extract a zip and return the path of its .shp file."""
    try:
        with zipfile.ZipFile(zip_path) as zf:
            members = zf.infolist()
            if sum(m.file_size for m in members) > max_bytes:
                raise ProcessingError("ZIP is too large when extracted")
            root = dest.resolve()
            for member in members:
                if not (root / member.filename).resolve().is_relative_to(root):
                    raise ProcessingError("ZIP contains an unsafe path")
            zf.extractall(dest)
    except zipfile.BadZipFile:
        raise ProcessingError("File is not a valid ZIP archive")

    shapefiles = sorted(dest.rglob("*.shp"))
    if not shapefiles:
        raise ProcessingError("ZIP does not contain a Shapefile (.shp)")
    return shapefiles[0]
