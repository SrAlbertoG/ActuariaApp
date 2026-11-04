"""Endpoints de ejecución, seguimiento y resultados de la extracción."""

from fastapi import APIRouter, Depends, Query

from app.api.extraction_deps import get_extraction_service, get_query_service
from app.models.extraction import ResultDataset
from app.schemas.extractions import (
    ExtractionCreated, ExtractionCreateRequest, ExtractionRead, ResultPage,
)
from app.services.extraction_service import ExtractionQueryService, ExtractionService

router = APIRouter(tags=["extracciones"])


@router.post("/extractions", response_model=ExtractionCreated, status_code=202)
def create_extraction(
    body: ExtractionCreateRequest,
    service: ExtractionService = Depends(get_extraction_service),
):
    """Registra la ejecución y retorna de inmediato; el trabajo corre en segundo plano."""
    return service.create(body)


@router.get("/extractions/{execution_id}", response_model=ExtractionRead)
def get_extraction(execution_id: str, service: ExtractionQueryService = Depends(get_query_service)):
    return service.get(execution_id)


@router.get("/extractions/{execution_id}/results", response_model=ResultPage)
def get_results(
    execution_id: str,
    dataset: ResultDataset = ResultDataset.CONSULTA,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    search: str | None = Query(default=None, max_length=100),
    service: ExtractionQueryService = Depends(get_query_service),
):
    return service.results(execution_id, dataset, page, page_size, search)


@router.post("/extractions/{execution_id}/cancel", response_model=ExtractionRead)
def cancel_extraction(execution_id: str, service: ExtractionQueryService = Depends(get_query_service)):
    return service.cancel(execution_id)