"""Servicio de catálogo de contratos."""

from app.core.config import get_settings
from app.core.errors import AppError
from app.repositories.fixed_cost_repository import FixedCostRepository
from app.repositories.sql_server_invoice_repository import SqlServerInvoiceRepository
from app.schemas.invoices import CatalogItem


class ContractService:
    """Consolida los contratos disponibles en las fuentes histórica y FPR."""

    def __init__(self, auth_service) -> None:
        self.auth_service = auth_service
        settings = get_settings()
        self.fixed_repository = FixedCostRepository(settings.fixed_costs_file)
        self.sql_repository = SqlServerInvoiceRepository(
            settings.fpr_period_field,
            settings.invoice_source_cutoff,
        )

    def list(self, search: str | None = None) -> list[CatalogItem]:
        """Devuelve contratos únicos ordenados alfabéticamente."""
        with self.auth_service.connection() as connection:
            values = set(self.sql_repository.list_contracts(connection, search))

        try:
            values.update(self.fixed_repository.list_contracts(search))
        except AppError as exc:
            if exc.code != "fixed_cost_file_missing":
                raise

        return [
            CatalogItem(value=value, label=value)
            for value in sorted(values, key=str.casefold)
        ]
