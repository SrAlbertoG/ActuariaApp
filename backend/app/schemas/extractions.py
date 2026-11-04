"""Contratos de datos de /extractions y /exports."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.extraction import ExtractionStatus, ResultDataset, RipsCategory


class ExtractionCreateRequest(BaseModel):
    invoice_ids: list[str] = Field(min_length=1, max_length=1000)
    transaction_ids: list[str] = Field(min_length=1, max_length=1000)
    contracts: list[str] = Field(default_factory=list, max_length=100)
    providers: list[str] = Field(default_factory=list, max_length=500)
    start_date: date | None = None
    end_date: date | None = None
    # Filtros originales de búsqueda: se revalidan en el backend.
    contract: str | None = Field(default=None, max_length=100)
    provider_nit: str | None = Field(default=None, max_length=50)
    invoice: str | None = Field(default=None, max_length=100)
    categories: list[RipsCategory] = Field(
        default_factory=lambda: list(RipsCategory), min_length=1
    )
    # Debe ser explícitamente false en esta versión.
    homologate: Literal[False] = False


class ExtractionCreated(BaseModel):
    execution_id: str
    status: ExtractionStatus
    message: str


class ExtractionMetrics(BaseModel):
    invoices_consulted: int = 0
    invoices_valid: int = 0
    invoices_corrected: int = 0
    invoices_discarded: int = 0
    transactions_selected: int = 0
    transactions_found: int = 0
    transactions_processed: int = 0
    records_by_category: dict[str, int] = Field(default_factory=dict)


class ExtractionRead(BaseModel):
    execution_id: str
    status: ExtractionStatus
    progress: int
    current_step: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    contracts: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    metrics: ExtractionMetrics = Field(default_factory=ExtractionMetrics)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    export_path: str | None = None


class ResultPage(BaseModel):
    dataset: ResultDataset
    columns: list[str]
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int


class ExportRead(BaseModel):
    execution_id: str
    filename: str
    path: str
    size_bytes: int
    generated_at: datetime