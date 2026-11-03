"""Consultas parametrizadas para transacciones RIPS activas."""

import pyodbc

from app.core.errors import AppError


class SqlServerTransactionRepository:
    """Consulta RIPSArchivoTransaccion a partir de facturas seleccionadas."""

    TABLE = "dbo.RIPSArchivoTransaccion"

    @staticmethod
    def _build_filter(invoice_keys: list[dict]) -> tuple[str, tuple]:
        if not invoice_keys:
            raise AppError(
                "invoice_selection_required",
                "Selecciona al menos una factura para consultar sus transacciones.",
                400,
            )

        if len(invoice_keys) > 250:
            raise AppError(
                "too_many_invoices",
                "Selecciona máximo 250 facturas por consulta de transacciones.",
                400,
            )

        # Se conserva el criterio de la automatización anterior: el vínculo
        # inicial se realiza por número completo de factura. Contrato y NIT se
        # devuelven desde RIPSArchivoTransaccion como datos propios del registro;
        # no se usan como filtros para no descartar transacciones históricamente
        # asociadas a una factura cuyo contrato fue corregido posteriormente.
        invoice_numbers = list(dict.fromkeys(item["invoice"] for item in invoice_keys))
        expressions = ["rat_NumeroFactura = ?" for _ in invoice_numbers]
        return "(" + " OR ".join(expressions) + ")", tuple(invoice_numbers)

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

    def count(self, connection, invoice_keys: list[dict]) -> int:
        invoice_filter, params = self._build_filter(invoice_keys)
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

        invoice_filter, invoice_params = self._build_filter(invoice_keys)
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
    ) -> list[dict]:
        invoice_filter, params = self._build_filter(invoice_keys)
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
