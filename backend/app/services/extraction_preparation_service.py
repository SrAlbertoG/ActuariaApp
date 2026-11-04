"""Validación y preparación de la selección para la extracción futura."""

from datetime import datetime, timezone

from app.core.errors import AppError
from app.repositories.sql_server_transaction_repository import (
    SqlServerTransactionRepository,
)
from app.schemas.invoices import ExtractionPreparationRead
from app.services.invoice_identifiers import decode_invoice_id


class ExtractionPreparationService:
    """Verifica la selección sin ejecutar todavía las consultas de extracción RIPS."""

    def __init__(self, auth_service) -> None:
        self.auth_service = auth_service
        self.transaction_repository = SqlServerTransactionRepository()

    def prepare(
        self,
        invoice_ids: list[str],
        transaction_ids: list[str],
        *,
        contract: str | None = None,
        provider_nit: str | None = None,
        invoice: str | None = None,
    ) -> ExtractionPreparationRead:
        """Valida la selección contra los registros activos de SQL Server."""
        # Se eliminan duplicados conservando el orden recibido desde la interfaz.
        unique_invoice_ids = list(dict.fromkeys(invoice_ids))
        unique_transaction_ids = list(dict.fromkeys(transaction_ids))

        if not unique_invoice_ids:
            raise AppError(
                "invoice_selection_required",
                "Selecciona al menos una factura.",
                400,
            )
        if not unique_transaction_ids:
            raise AppError(
                "transaction_selection_required",
                "Selecciona al menos una transacción.",
                400,
            )
        if len(unique_invoice_ids) > 1000:
            raise AppError(
                "too_many_invoices",
                "Selecciona máximo 1000 facturas por preparación.",
                400,
            )
        if len(unique_transaction_ids) > 1000:
            raise AppError(
                "too_many_transactions",
                "Selecciona máximo 1000 transacciones por preparación.",
                400,
            )

        invoice_keys = [
            decode_invoice_id(invoice_id)
            for invoice_id in unique_invoice_ids
        ]

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
            records = self.transaction_repository.validate_selection(
                connection,
                invoice_keys,
                unique_transaction_ids,
                **active_filters,
            )

        found_ids = {
            str(record["id"]).strip()
            for record in records
            if record.get("id") is not None
        }
        missing_ids = [
            transaction_id
            for transaction_id in unique_transaction_ids
            if transaction_id not in found_ids
        ]

        if missing_ids:
            raise AppError(
                "invalid_transaction_selection",
                (
                    "Una o varias transacciones ya no están activas o no "
                    "pertenecen a las facturas seleccionadas. Actualiza la "
                    "consulta y vuelve a seleccionar."
                ),
                409,
            )

        contracts = {
            str(record["contract"]).strip()
            for record in records
            if record.get("contract") is not None
            and str(record["contract"]).strip()
        }
        providers = {
            str(record["nit_provider"]).strip()
            for record in records
            if record.get("nit_provider") is not None
            and str(record["nit_provider"]).strip()
        }

        return ExtractionPreparationRead(
            status="prepared",
            prepared_at=datetime.now(timezone.utc),
            invoice_ids=unique_invoice_ids,
            transaction_ids=unique_transaction_ids,
            invoice_count=len(unique_invoice_ids),
            transaction_count=len(unique_transaction_ids),
            contracts=sorted(contracts, key=str.casefold),
            providers=sorted(providers, key=str.casefold),
        )
