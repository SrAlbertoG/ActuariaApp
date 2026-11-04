"""Casos de uso de búsqueda, detalle y catálogos de facturación."""

from datetime import date, timedelta

from app.core.config import get_settings
from app.core.errors import AppError
from app.repositories.fixed_cost_repository import FixedCostRepository
from app.repositories.sql_server_invoice_repository import SqlServerInvoiceRepository
from app.schemas.invoices import InvoicePage, InvoiceRead
from app.services.invoice_identifiers import decode_invoice_id, encode_invoice_id


class InvoiceService:
    """Combina las fuentes históricas y FPR respetando la fecha de corte."""

    def __init__(self, auth_service) -> None:
        self.auth_service = auth_service
        settings = get_settings()
        self.cutoff_date = settings.invoice_source_cutoff
        self.fixed_repository = FixedCostRepository(settings.fixed_costs_file)
        self.sql_repository = SqlServerInvoiceRepository(
            settings.fpr_period_field,
            self.cutoff_date,
        )

    def search(
        self,
        *,
        contract: str | None = None,
        provider_nit: str | None = None,
        invoice: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> InvoicePage:
        if start_date and end_date and start_date > end_date:
            raise AppError(
                "invalid_date_range",
                "La fecha inicial no puede ser posterior a la fecha final.",
                422,
            )

        offset = (page - 1) * page_size
        warnings: list[str] = []
        base_count = 0
        sql_count = 0
        fixed_invoice_keys: set[tuple[str, str, str]] = set()
        fixed_file_missing = False
        base_filters = {
            "contract": contract,
            "provider_nit": provider_nit,
            "invoice": invoice,
            "start_date": start_date,
            "end_date": min(end_date, self.cutoff_date - timedelta(days=1))
            if end_date
            else self.cutoff_date - timedelta(days=1),
        }
        use_base = start_date is None or start_date < self.cutoff_date
        use_sql = end_date is None or end_date >= self.cutoff_date

        if start_date and start_date >= self.cutoff_date:
            use_base = False
        if end_date and end_date < self.cutoff_date:
            use_sql = False

        if use_base and base_filters["start_date"] and base_filters["start_date"] >= self.cutoff_date:
            use_base = False

        sql_start = max(start_date, self.cutoff_date) if start_date else self.cutoff_date
        sql_filters = {
            "contract": contract,
            "provider_nit": provider_nit,
            "invoice": invoice,
            "start_date": sql_start,
            "end_date": end_date,
        }

        try:
            fixed_invoice_keys = self.fixed_repository.invoice_keys()
        except AppError as exc:
            if exc.code != "fixed_cost_file_missing":
                raise
            fixed_file_missing = True
            warnings.append(
                "No se encontró Base Montos Fijos. No se pueden consultar sus "
                "periodos históricos ni excluir posibles duplicados de FPR."
            )

        with self.auth_service.connection() as connection:
            if use_sql:
                if fixed_invoice_keys:
                    sql_count = self.sql_repository.count(
                        connection,
                        excluded_keys=fixed_invoice_keys,
                        **sql_filters,
                    )
                else:
                    sql_count = self.sql_repository.count(
                        connection,
                        **sql_filters,
                    )

            if use_base and not fixed_file_missing:
                base_count = self.fixed_repository.count(**base_filters)

            # Las fuentes no se solapan por el corte temporal. Por eso se puede
            # paginar cada bloque en orden cronológico sin traer todos los registros.
            sources = []
            if use_sql:
                sources.append(("sql_server", sql_count))
            if use_base:
                sources.append(("base_fixed", base_count))

            total = sql_count + base_count
            items: list[InvoiceRead] = []
            consumed = 0

            for source, source_count in sources:
                local_offset = max(0, offset - consumed)
                remaining = page_size - len(items)
                local_limit = min(remaining, max(0, source_count - local_offset))

                if local_limit:
                    if source == "sql_server":
                        if fixed_invoice_keys:
                            records = self.sql_repository.search(
                                connection,
                                local_offset,
                                local_limit,
                                excluded_keys=fixed_invoice_keys,
                                **sql_filters,
                            )
                        else:
                            records = self.sql_repository.search(
                                connection,
                                local_offset,
                                local_limit,
                                **sql_filters,
                            )
                    else:
                        records = self.fixed_repository.search(
                            local_offset,
                            local_limit,
                            **base_filters,
                        )
                    items.extend(self._to_invoice(record) for record in records)

                consumed += source_count
                if len(items) >= page_size:
                    break

        return InvoicePage(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            warnings=warnings,
        )

    def get_invoice(self, invoice_id: str) -> InvoiceRead:
        key = decode_invoice_id(invoice_id)

        if key["source"] == "base_fixed":
            record = self.fixed_repository.find_one(
                key["invoice"],
                key["nit_provider"],
                key["contract"],
            )
        else:
            try:
                fixed_invoice_keys = self.fixed_repository.invoice_keys()
            except AppError as exc:
                if exc.code != "fixed_cost_file_missing":
                    raise
                fixed_invoice_keys = set()

            with self.auth_service.connection() as connection:
                record = self.sql_repository.find_one(
                    connection,
                    key["invoice"],
                    key["nit_provider"],
                    key["contract"],
                    **(
                        {"excluded_keys": fixed_invoice_keys}
                        if fixed_invoice_keys
                        else {}
                    ),
                )

        if record is None:
            raise AppError("invoice_not_found", "No se encontró la factura solicitada.", 404)

        return self._to_invoice(record)

    @staticmethod
    def _to_invoice(record: dict) -> InvoiceRead:
        period = record.get("period_reference")
        service_month = period.strftime("%Y-%m") if period else None

        return InvoiceRead(
            id=encode_invoice_id(
                record["source"],
                str(record["invoice"]).strip(),
                str(record["nit_provider"]).strip(),
                str(record["contract"]).strip(),
            ),
            invoice=str(record["invoice"]).strip(),
            nit_provider=str(record["nit_provider"]).strip(),
            provider_name=record.get("provider_name"),
            contract=str(record["contract"]).strip(),
            service_month=service_month,
            invoice_date=record.get("invoice_date"),
            filing_date=record.get("filing_date"),
            billed_amount=record.get("billed_amount"),
            source=record["source"],
        )
