"""Esquemas de entrada y salida para facturas y transacciones."""

from datetime import date, datetime
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
    warnings: list[str] = Field(default_factory=list)


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


class TransactionSearchRequest(BaseModel):
    """Solicitud de búsqueda de transacciones para una selección de facturas."""

    invoice_ids: list[str] = Field(min_length=1, max_length=250)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)



class ExtractionPreparationRequest(BaseModel):
    """Facturas y transacciones que el analista desea dejar preparadas."""

    invoice_ids: list[str] = Field(min_length=1, max_length=250)
    transaction_ids: list[str] = Field(min_length=1, max_length=1000)


class ExtractionPreparationRead(BaseModel):
    """Resumen validado que consumirá el flujo de extracción del entregable 3."""

    status: str = "prepared"
    prepared_at: datetime
    invoice_ids: list[str]
    transaction_ids: list[str]
    invoice_count: int
    transaction_count: int
    contracts: list[str]
    providers: list[str]
