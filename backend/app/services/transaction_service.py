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
            total = self.repository.count(connection, invoice_keys)
            records = self.repository.search(
                connection,
                invoice_keys,
                offset,
                page_size,
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
