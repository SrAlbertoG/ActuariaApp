"""Esquemas de entrada y salida para facturas y transacciones."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class CatalogItem(BaseModel):
    """Opción para los selectores de contratos y prestadores."""

    value: str
    label: str


class InvoiceRead(BaseModel):
    """Representación normalizada de una factura, independientemente de su origen."""

    id: str = Field(description="Identificador opaco y estable para la selección.")
    invoice: str
    nit_provider: str
    provider_name: str | None = None
    contract: str
    service_month: str | None = None
    invoice_date: date | None = None
    filing_date: date | None = None
    billed_amount: Decimal | None = None
    source: str


class InvoicePage(BaseModel):
    """Respuesta paginada de la búsqueda de facturas."""

    items: list[InvoiceRead]
    total: int
    page: int
    page_size: int
    warnings: list[str] = []


class TransactionRead(BaseModel):
    """Representación de una transacción RIPS activa."""

    id: str
    invoice: str
    contract: str
    nit_provider: str
    provider_code: str | None = None
    rips_date: date | None = None
    filing_date: date | None = None


class TransactionPage(BaseModel):
    """Respuesta paginada de transacciones."""

    items: list[TransactionRead]
    total: int
    page: int
    page_size: int
