"""Endpoint para validar y preparar la selección de extracción."""

from fastapi import APIRouter, Depends

from app.api.deps import require_sql_connection
from app.schemas.invoices import (
    ExtractionPreparationRead,
    ExtractionPreparationRequest,
)
from app.services.auth_service import AuthService
from app.services.extraction_preparation_service import (
    ExtractionPreparationService,
)


router = APIRouter(tags=["preparación de extracción"])


def get_preparation_service(
    auth_service: AuthService = Depends(require_sql_connection),
) -> ExtractionPreparationService:
    """Construye el servicio de preparación con la sesión SQL activa."""
    return ExtractionPreparationService(auth_service)


@router.post(
    "/extraction/prepare",
    response_model=ExtractionPreparationRead,
)
def prepare_extraction(
    body: ExtractionPreparationRequest,
    service: ExtractionPreparationService = Depends(get_preparation_service),
):
    """Valida facturas y transacciones seleccionadas sin iniciar la extracción."""
    return service.prepare(
        body.invoice_ids,
        body.transaction_ids,
        contract=body.contract,
        provider_nit=body.provider_nit,
        invoice=body.invoice,
    )
