"""Casos de uso para consultar transacciones de facturas seleccionadas."""

from app.core.errors import AppError
from app.repositories.sql_server_transaction_repository import SqlServerTransactionRepository
from app.schemas.invoices import TransactionPage, TransactionRead
from app.services.invoice_identifiers import decode_invoice_id


class TransactionService:
    """Recupera exclusivamente transacciones activas de las facturas seleccionadas."""

    def __init__(self, auth_service) -> None:
        self.auth_service = auth_service
        self.repository = SqlServerTransactionRepository()

    def search(
        self,
        invoice_ids: list[str],
        *,
        contract: str | None = None,
        provider_nit: str | None = None,
        invoice: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> TransactionPage:
        if not invoice_ids:
            raise AppError(
                "invoice_selection_required",
                "Selecciona al menos una factura para consultar sus transacciones.",
                400,
            )

        keys_by_natural_id: dict[tuple[str, str, str], dict[str, str]] = {}
        for invoice_id in invoice_ids:
            key = decode_invoice_id(invoice_id)
            natural_id = (
                key["invoice"],
                key["nit_provider"],
                key["contract"],
            )
            keys_by_natural_id[natural_id] = key

        invoice_keys = list(keys_by_natural_id.values())
        offset = (page - 1) * page_size

        with self.auth_service.connection() as connection:
            active_filters = {
                key: value
                for key, value in {
                    "contract": contract,
                    "provider_nit": provider_nit,
                    "invoice": invoice,
                }.items()
                if value and value.strip()
            }
            total = self.repository.count(
                connection,
                invoice_keys,
                **active_filters,
            )
            records = self.repository.search(
                connection,
                invoice_keys,
                offset,
                page_size,
                **active_filters,
            )

        items = [
            TransactionRead(
                id=str(record["id"]).strip(),
                invoice=str(record["invoice"]).strip(),
                contract=str(record["contract"]).strip(),
                nit_provider=str(record["nit_provider"]).strip(),
                provider_code=(
                    str(record["provider_code"]).strip()
                    if record.get("provider_code") is not None
                    else None
                ),
                rips_date=record.get("rips_date"),
                filing_date=record.get("filing_date"),
            )
            for record in records
        ]

        return TransactionPage(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )


    def search_dataset(
        self,
        invoice_ids: list[str],
        *,
        contract: str | None = None,
        provider_nit: str | None = None,
        invoice: str | None = None,
        max_records: int = 1000,
    ):
        """Recupera hasta 1001 filas en una sola consulta para validar el límite."""
        if not invoice_ids:
            raise AppError(
                "invoice_selection_required",
                "Selecciona al menos una factura para consultar sus transacciones.",
                400,
            )

        # Decodifica y deduplica claves antes de construir parámetros SQL.
        keys_by_natural_id: dict[tuple[str, str, str], dict[str, str]] = {}
        for invoice_id in invoice_ids:
            key = decode_invoice_id(invoice_id)
            natural_id = (key["invoice"], key["nit_provider"], key["contract"])
            keys_by_natural_id[natural_id] = key
        invoice_keys = list(keys_by_natural_id.values())
        active_filters = {
            key: value
            for key, value in {
                "contract": contract,
                "provider_nit": provider_nit,
                "invoice": invoice,
            }.items()
            if value and value.strip()
        }

        # No se ejecuta COUNT + SELECT: se recupera un registro centinela
        # adicional. Así una búsqueda de transacciones necesita un solo SELECT.
        with self.auth_service.connection() as connection:
            records = self.repository.search(
                connection,
                invoice_keys,
                0,
                max_records + 1,
                **active_filters,
            )

        if len(records) > max_records:
            raise AppError(
                "transaction_result_limit_exceeded",
                f"La selección genera más de {max_records} transacciones. Reduce las facturas o filtros para continuar.",
                413,
            )

        items = [
            TransactionRead(
                id=str(record["id"]).strip(),
                invoice=str(record["invoice"]).strip(),
                contract=str(record["contract"]).strip(),
                nit_provider=str(record["nit_provider"]).strip(),
                provider_code=(
                    str(record["provider_code"]).strip()
                    if record.get("provider_code") is not None
                    else None
                ),
                rips_date=record.get("rips_date"),
                filing_date=record.get("filing_date"),
            )
            for record in records
        ]
        return {"items": items, "total": len(items)}
