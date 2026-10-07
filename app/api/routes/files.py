from fastapi import APIRouter, UploadFile

from app.api.schemas.file import FileInfo, FileMeasurements
from app.services import file_service

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/", response_model=FileInfo, status_code=201)
def upload_file(file: UploadFile):
    return file_service.upload_file(file)


@router.get("/{file_id}/", response_model=FileInfo)
def get_file(file_id: str):
    return file_service.get_file(file_id)


@router.get("/{file_id}/measurements/", response_model=FileMeasurements)
def get_measurements(file_id: str):
    return file_service.get_measurements(file_id)
