# Geospatial File Measurement API - Development Guide

## Project Goal

Build a small, clean and maintainable FastAPI backend for processing geospatial files.

The application must:

- Accept `.kml` files.
- Accept `.zip` files containing a Shapefile.
- Extract geospatial features.
- Return feature information.
- Calculate Polygon area.
- Calculate LineString length.
- Handle Point features without measurement.
- Handle unsupported geometry types gracefully.
- Correctly handle geographic CRS such as EPSG:4326 before measurement.
- Expose the required REST APIs.
- Include tests and clear documentation.

The assignment requirements are the source of truth. Do not add functionality that is not useful for the assignment.

---

## Main Principles

Prefer:

- Simple code.
- Small functions.
- Clear names.
- Modular files.
- Easy-to-follow control flow.
- Standard Python/FastAPI patterns.
- Useful validation.
- Explicit error handling.
- Code that another developer can understand quickly.

Avoid:

- Over-engineering.
- Unnecessary abstractions.
- Large classes.
- Deep inheritance.
- Generic repositories when there is no database.
- Factory patterns unless actually useful.
- Excessive dependency injection.
- Unnecessary interfaces/protocols.
- Background queues for normal file processing.
- Redis/Celery/Kafka.
- Microservices.
- Premature optimization.
- Adding libraries without a clear reason.

The simplest design that satisfies the requirement is preferred.

---

## Technology

Use:

- Python
- FastAPI
- Uvicorn
- GeoPandas
- Shapely
- PyProj

Use Pydantic models for API response/request schemas where appropriate.

Do not introduce Django because FastAPI is the selected framework for this implementation.

---

## Project Structure

Use this structure unless there is a strong implementation reason to change it:

```text
app/
├── main.py
├── config/
│   └── settings.py
├── api/
│   ├── routes/
│   │   └── files.py
│   └── schemas/
│       └── file.py
├── services/
│   ├── file_service.py
│   ├── geospatial_service.py
│   └── measurement_service.py
├── utils/
│   ├── file_utils.py
│   └── crs_utils.py
└── exceptions.py
```

### Responsibility of each layer

### `main.py`

- Create the FastAPI application.
- Register routers.
- Configure application-level behavior.

Do not put business logic here.

### `api/routes/files.py`

Handle HTTP endpoints:

```text
POST /api/files/
GET /api/files/{id}/
GET /api/files/{id}/measurements/
```

Responsibilities:

- Receive request.
- Validate basic API input.
- Call services.
- Return response.
- Translate known application errors into HTTP responses.

Do not put geospatial processing logic directly inside routes.

### `api/schemas/file.py`

Define response models and simple API schemas.

Keep schemas focused on API contracts.

### `services/file_service.py`

Handle:

- Uploaded file validation.
- Supported extension validation.
- Temporary/storage path handling.
- File ID generation.
- File metadata.
- Processing orchestration.

### `services/geospatial_service.py`

Handle:

- Reading KML.
- Reading zipped Shapefile.
- Extracting features.
- Geometry information.
- CRS information.
- Feature properties.
- Unsupported geometry handling.

This service should hide GeoPandas-specific implementation details from the API layer.

### `services/measurement_service.py`

Handle:

- Polygon area.
- LineString length.
- Point handling.
- Unsupported geometry handling.

The measurement service should never calculate area/length directly from latitude/longitude coordinates in degrees.

### `utils/crs_utils.py`

Handle:

- CRS validation.
- Detecting geographic CRS.
- Selecting a suitable projected CRS.
- Transforming geometries before measurement.

Keep CRS-specific logic here as much as practical.

### `utils/file_utils.py`

Handle small file-related helpers:

- Extension detection.
- Safe file names.
- Temporary directory handling.
- Shapefile ZIP validation.

### `exceptions.py`

Define only useful application-specific exceptions.

Do not create an exception class for every possible error.

---

## Geospatial Processing Rules

For every feature capture at minimum:

- Feature ID/index.
- Geometry type.
- Geometry.
- CRS.
- Properties/attributes.

Supported measurements:

### Polygon

Return area.

### LineString

Return length.

### Point

Return no measurement.

### Unsupported geometry

Do not crash the complete request.

Return a clear representation indicating that measurement is not supported.

---

## CRS Rules

Never calculate:

```python
geometry.area
```

or:

```python
geometry.length
```

directly on geographic longitude/latitude coordinates such as EPSG:4326.

When the source CRS is geographic:

1. Detect that the CRS is geographic.
2. Select an appropriate projected CRS.
3. Transform the geometry.
4. Calculate area or length using the projected geometry.

When the source file already uses a suitable projected CRS, avoid unnecessary transformations.

Keep CRS selection understandable.

A reasonable strategy is preferred over building a complex CRS framework.

Document the chosen CRS strategy in `README.md`.

---

## File Handling

Supported uploads:

- `.kml`
- `.zip` containing a Shapefile.

For ZIP uploads:

- Validate that the archive actually contains the required Shapefile components.
- Extract to a temporary/safe location.
- Do not trust arbitrary archive paths.
- Avoid path traversal vulnerabilities.

Do not store uploaded files in Git.

Use a local `uploads/` directory for development unless the implementation has a clear reason to use another approach.

---

## API Contract

### Upload

```http
POST /api/files/
```

Accept a multipart file upload.

The endpoint should process the file and return a file identifier plus useful metadata/status.

### File Information

```http
GET /api/files/{id}/
```

Return information similar to:

```json
{
  "id": "abc123",
  "filename": "survey.kml",
  "feature_count": 120,
  "crs": "EPSG:4326",
  "status": "COMPLETED"
}
```

### Measurements

```http
GET /api/files/{id}/measurements/
```

Return measurement information for the features.

The exact response shape can be chosen if it remains clear and documented.

---

## Error Handling

Handle at least:

- Unsupported file extension.
- Invalid ZIP.
- ZIP without a Shapefile.
- Invalid KML.
- Missing/invalid CRS where measurement cannot be safely performed.
- Missing file ID.
- Invalid geospatial data.
- Unsupported geometry type.

Errors should return useful HTTP status codes and readable messages.

Do not expose raw stack traces in API responses.

---

## Testing

Add tests for important behavior rather than trying to test every line.

At minimum cover:

- KML upload.
- Shapefile ZIP upload.
- Invalid file type.
- Invalid ZIP.
- Polygon area calculation.
- LineString length calculation.
- Point handling.
- Unsupported geometry handling.
- Geographic CRS transformation.
- File information endpoint.
- Measurements endpoint.

Tests should be simple and readable.

Use small test fixtures.

---

## Code Style

Prefer functions over classes when a class does not add value.

Keep functions reasonably small.

Use type hints for public/service functions.

Use descriptive variable names.

Avoid clever one-liners when normal code is easier to understand.

Comments should explain why something is done, not restate obvious code.

Do not add comments just to increase documentation.

---

## Dependencies

Before adding a dependency, ask:

1. Is it required?
2. Does an existing dependency already solve the problem?
3. Does it make the code simpler?

Prefer the existing Python geospatial ecosystem.

---

## README Requirements

README must contain:

1. Project overview.
2. Requirements.
3. Local setup.
4. How to run the application.
5. API endpoints.
6. Example requests.
7. Example responses.
8. Architecture.
9. File-processing flow.
10. Measurement flow.
11. CRS handling.
12. Important design decisions.
13. Learning.
14. Future scope.

The assignment explicitly requires learning and future scope in the README.

Keep the README practical rather than overly long.

---

## Git Workflow

Always work on a feature branch.

Never develop the entire task directly on `main`.

Recommended branch naming:

```text
feature/geospatial-api
```

Use small human-readable commits.

Good:

```text
setup api
add file upload
process geospatial data
add measurements
handle crs
add tests
update readme
```

Avoid:

```text
feat: implement enterprise-grade geospatial processing architecture
refactor: improve everything
```

Do not mention AI assistants, Claude, generated code, or similar tools in commit messages, PR descriptions, comments, source code, or documentation.

Before merging:

1. Run tests.
2. Run lint/format checks if configured.
3. Review the diff.
4. Make sure secrets are not committed.
5. Update README.
6. Create a PR into `main`.
7. Use a clear PR description.
8. Merge only after the branch is complete.

---

## Pull Request Style

PR title:

```text
Add geospatial measurement API
```

PR description should briefly contain:

### What changed

- Added file upload endpoint.
- Added KML and Shapefile processing.
- Added feature measurements.
- Added CRS-aware measurement handling.
- Added tests and documentation.

### Validation

- Tests run.
- Example API calls verified.

### Notes

Mention only relevant implementation decisions.

Do not write exaggerated or promotional PR descriptions.

---

## Important Constraint

Build the required application first.

Do not add features simply because they are technically interesting.

A smaller, clear and correct implementation is better than a larger, complicated implementation.

Before introducing a new abstraction, check whether a simple function or existing service is enough.