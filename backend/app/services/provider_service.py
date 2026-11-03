"""Servicio de catálogo de prestadores."""

from app.core.config import get_settings
from app.core.errors import AppError
from app.repositories.fixed_cost_repository import FixedCostRepository
from app.repositories.sql_server_invoice_repository import SqlServerInvoiceRepository
from app.schemas.invoices import CatalogItem


class ProviderService:
    """Consolida los prestadores de FPR y Base Montos Fijos."""

    def __init__(self, auth_service) -> None:
        self.auth_service = auth_service
        settings = get_settings()
        self.fixed_repository = FixedCostRepository(settings.fixed_costs_file)
        self.sql_repository = SqlServerInvoiceRepository(
            settings.fpr_period_field,
            settings.invoice_source_cutoff,
        )

    def list(
        self,
        contract: str | None = None,
        search: str | None = None,
    ) -> list[CatalogItem]:
        """Filtra por contrato y por NIT o nombre del prestador."""
        with self.auth_service.connection() as connection:
            records = self.sql_repository.list_providers(
                connection,
                contract=contract,
                search=search,
            )

        providers = {
            item["value"]: item.get("label") or item["value"]
            for item in records
            if item.get("value")
        }

        try:
            for nit in self.fixed_repository.list_providers(contract):
                if search and search.strip().casefold() not in nit.casefold():
                    continue
                providers.setdefault(nit, f"NIT {nit}")
        except AppError as exc:
            if exc.code != "fixed_cost_file_missing":
                raise

        return [
            CatalogItem(value=nit, label=providers[nit])
            for nit in sorted(providers, key=str.casefold)
        ]
