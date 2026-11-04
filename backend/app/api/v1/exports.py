"""Generación y descarga del Excel de resultados."""

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.api.extraction_deps import get_export_service
from app.schemas.extractions import ExportRead
from app.services.export_service import ExportService

router = APIRouter(tags=["exportaciones"])

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.post("/exports/{execution_id}", response_model=ExportRead)
def generate_export(execution_id: str, service: ExportService = Depends(get_export_service)):
    """Genera el Excel y devuelve su ubicación local."""
    return service.export(execution_id)


@router.get("/exports/{execution_id}")
def download_export(execution_id: str, service: ExportService = Depends(get_export_service)):
    path = service.file_path(execution_id)
    return FileResponse(path, media_type=XLSX, filename=path.name)