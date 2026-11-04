"""Consultas parametrizadas para transacciones RIPS activas."""

import pyodbc

from app.core.errors import AppError


class SqlServerTransactionRepository:
    """Consulta RIPSArchivoTransaccion a partir de facturas seleccionadas."""

    TABLE = "dbo.RIPSArchivoTransaccion"

    @staticmethod
    def _build_filter(
        invoice_keys: list[dict],
        *,
        contract: str | None = None,
        provider_nit: str | None = None,
        invoice: str | None = None,
    ) -> tuple[str, tuple]:
        if not invoice_keys:
            raise AppError(
                "invoice_selection_required",
                "Selecciona al menos una factura para consultar sus transacciones.",
                400,
            )

        if len(invoice_keys) > 1000:
            raise AppError(
                "too_many_invoices",
                "Selecciona máximo 1000 facturas por consulta de transacciones.",
                400,
            )

        # La selección limita el conjunto de facturas. Además, se aplican
        # únicamente los criterios que el analista utilizó en la búsqueda de
        # facturas, para evitar asociar transacciones de otro NIT o contrato.
        invoice_numbers = list(dict.fromkeys(item["invoice"] for item in invoice_keys))
        placeholders = ", ".join("?" for _ in invoice_numbers)
        clauses = [f"rat_NumeroFactura IN ({placeholders})"]
        params: list[object] = list(invoice_numbers)

        if contract and contract.strip():
            clauses.append(
                "LTRIM(RTRIM(CONVERT(varchar(100), rat_NumeroContrato))) = ?"
            )
            params.append(contract.strip())
        if provider_nit and provider_nit.strip():
            clauses.append(
                "LTRIM(RTRIM(CONVERT(varchar(50), rat_NumeroIdentificacion))) = ?"
            )
            params.append(provider_nit.strip())
        if invoice and invoice.strip():
            clauses.append(
                "LTRIM(RTRIM(CONVERT(varchar(100), rat_NumeroFactura))) LIKE ?"
            )
            params.append(f"%{invoice.strip()}%")

        return " AND ".join(clauses), tuple(params)

    @staticmethod
    def _fetch_all(connection, query: str, params: tuple) -> list[dict]:
        cursor = connection.cursor()
        try:
            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except pyodbc.Error:
            raise AppError(
                "transaction_query_failed",
                "No fue posible consultar las transacciones RIPS en SQL Server. Verifica los permisos de lectura.",
                503,
            ) from None
        finally:
            cursor.close()

    def count(
        self,
        connection,
        invoice_keys: list[dict],
        *,
        contract: str | None = None,
        provider_nit: str | None = None,
        invoice: str | None = None,
    ) -> int:
        invoice_filter, params = self._build_filter(
            invoice_keys,
            contract=contract,
            provider_nit=provider_nit,
            invoice=invoice,
        )
        query = f"""
            SELECT COUNT(DISTINCT rat_Id) AS total
            FROM {self.TABLE}
            WHERE rat_Activo = 'Activo' AND {invoice_filter}
        """
        rows = self._fetch_all(connection, query, params)
        return int(rows[0]["total"]) if rows else 0

    def validate_selection(
        self,
        connection,
        invoice_keys: list[dict],
        transaction_ids: list[str],
        *,
        contract: str | None = None,
        provider_nit: str | None = None,
        invoice: str | None = None,
    ) -> list[dict]:
        """Valida que los IDs elegidos sigan activos y pertenezcan a las facturas."""
        if not transaction_ids:
            raise AppError(
                "transaction_selection_required",
                "Selecciona al menos una transacción para preparar la extracción.",
                400,
            )
        if len(transaction_ids) > 1000:
            raise AppError(
                "too_many_transactions",
                "Selecciona máximo 1000 transacciones por preparación.",
                400,
            )

        invoice_filter, invoice_params = self._build_filter(
            invoice_keys,
            contract=contract,
            provider_nit=provider_nit,
            invoice=invoice,
        )
        unique_ids = list(dict.fromkeys(transaction_ids))
        id_placeholders = ", ".join("?" for _ in unique_ids)
        query = f"""
            SELECT DISTINCT
                CONVERT(varchar(100), rat_Id) AS id,
                CONVERT(varchar(100), rat_NumeroFactura) AS invoice,
                CONVERT(varchar(100), rat_NumeroContrato) AS contract,
                CONVERT(varchar(50), rat_NumeroIdentificacion) AS nit_provider
            FROM {self.TABLE}
            WHERE rat_Activo = 'Activo'
                AND {invoice_filter}
                AND rat_Id IN ({id_placeholders})
            ORDER BY id
        """
        return self._fetch_all(
            connection,
            query,
            (*invoice_params, *unique_ids),
        )

    def search(
        self,
        connection,
        invoice_keys: list[dict],
        offset: int,
        limit: int,
        *,
        contract: str | None = None,
        provider_nit: str | None = None,
        invoice: str | None = None,
    ) -> list[dict]:
        invoice_filter, params = self._build_filter(
            invoice_keys,
            contract=contract,
            provider_nit=provider_nit,
            invoice=invoice,
        )
        query = f"""
            SELECT DISTINCT
                rat_Id AS id,
                CONVERT(varchar(100), rat_NumeroFactura) AS invoice,
                CONVERT(varchar(100), rat_NumeroContrato) AS contract,
                CONVERT(varchar(50), rat_NumeroIdentificacion) AS nit_provider,
                CONVERT(varchar(50), rat_CodigoPrestador) AS provider_code,
                CAST(FechaCargueRips AS date) AS rips_date,
                CAST(FechaRadicacionFactura AS date) AS filing_date
            FROM {self.TABLE}
            WHERE rat_Activo = 'Activo' AND {invoice_filter}
            ORDER BY id DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        return self._fetch_all(connection, query, (*params, offset, limit))
