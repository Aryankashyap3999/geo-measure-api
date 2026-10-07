class AppError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class UnsupportedFileError(AppError):
    status_code = 400


class FileIdNotFoundError(AppError):
    status_code = 404


class ProcessingError(AppError):
    """The file was stored but its contents could not be processed."""

    status_code = 422

    def __init__(self, message: str, file_id: str | None = None):
        super().__init__(message)
        self.file_id = file_id
