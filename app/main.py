from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import files
from app.config.settings import UPLOAD_DIR
from app.exceptions import AppError, ProcessingError

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Geo Measure API")
app.include_router(files.router)


@app.exception_handler(AppError)
def handle_app_error(request: Request, error: AppError):
    body = {"detail": error.message}
    if isinstance(error, ProcessingError) and error.file_id:
        body["id"] = error.file_id
    return JSONResponse(status_code=error.status_code, content=body)
