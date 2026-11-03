"""Endpoints para consultar transacciones asociadas a facturas."""

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_sql_connection
from app.schemas.invoices import TransactionPage
from app.services.auth_service import AuthService
from app.services.transaction_service import TransactionService


router = APIRouter(tags=["transacciones"])


def get_transaction_service(
    auth_service: AuthService = Depends(require_sql_connection),
) -> TransactionService:
    """Construye el servicio usando la sesión SQL Server activa."""
    return TransactionService(auth_service)


@router.get("/transactions", response_model=TransactionPage)
def list_transactions(
    invoice_ids: list[str] = Query(default=[]),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    service: TransactionService = Depends(get_transaction_service),
):
    """Consulta transacciones activas de una selección de facturas."""
    return service.search(invoice_ids, page=page, page_size=page_size)


@router.get("/invoices/{invoice_id}/transactions", response_model=TransactionPage)
def list_invoice_transactions(
    invoice_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    service: TransactionService = Depends(get_transaction_service),
):
    """Atajo para consultar las transacciones de una sola factura."""
    return service.search([invoice_id], page=page, page_size=page_size)
