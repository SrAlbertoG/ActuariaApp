"""Endpoints de contratos, prestadores, facturas y detalle de factura."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_sql_connection
from app.schemas.invoices import CatalogItem, InvoicePage, InvoiceRead
from app.services.auth_service import AuthService
from app.services.contract_service import ContractService
from app.services.invoice_service import InvoiceService
from app.services.provider_service import ProviderService


router = APIRouter(tags=["facturación"])


def get_contract_service(
    auth_service: AuthService = Depends(require_sql_connection),
) -> ContractService:
    """Construye el servicio de catálogo de contratos."""
    return ContractService(auth_service)


def get_provider_service(
    auth_service: AuthService = Depends(require_sql_connection),
) -> ProviderService:
    """Construye el servicio de catálogo de prestadores."""
    return ProviderService(auth_service)


def get_invoice_service(
    auth_service: AuthService = Depends(require_sql_connection),
) -> InvoiceService:
    """Construye el servicio de búsqueda y detalle de facturas."""
    return InvoiceService(auth_service)


@router.get("/contracts", response_model=list[CatalogItem])
def list_contracts(
    search: str | None = Query(default=None, max_length=100),
    service: ContractService = Depends(get_contract_service),
):
    """Lista contratos disponibles en las fuentes de facturación."""
    return service.list(search)


@router.get("/providers", response_model=list[CatalogItem])
def list_providers(
    contract: str | None = Query(default=None, max_length=100),
    search: str | None = Query(default=None, max_length=100),
    service: ProviderService = Depends(get_provider_service),
):
    """Lista prestadores, opcionalmente filtrados por contrato."""
    return service.list(contract, search)


@router.get("/invoices", response_model=InvoicePage)
def search_invoices(
    contract: str | None = Query(default=None, max_length=100),
    provider_nit: str | None = Query(default=None, max_length=50),
    invoice: str | None = Query(default=None, max_length=100),
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    service: InvoiceService = Depends(get_invoice_service),
):
    """Busca y pagina facturas de Base Montos Fijos y FPR."""
    return service.search(
        contract=contract,
        provider_nit=provider_nit,
        invoice=invoice,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceRead)
def get_invoice(
    invoice_id: str,
    service: InvoiceService = Depends(get_invoice_service),
):
    """Obtiene el detalle normalizado de una factura."""
    return service.get_invoice(invoice_id)
