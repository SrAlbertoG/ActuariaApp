"""Consultas parametrizadas de facturación FPR en SQL Server."""

from datetime import date

import logging

import pyodbc

from app.core.errors import AppError


logger = logging.getLogger(__name__)


class SqlServerInvoiceRepository:
    """Ejecuta consultas FPR sin concatenar valores recibidos desde la interfaz."""

    TABLE = "[BoxaludBI_Comfenalco].[dbo].[BiPagosFPR]"
    LIQUIDATION_TABLE = "[BoxaludBI_Comfenalco].[dbo].[BiPagosLiquidacion]"
    PERIOD_FIELDS = {
        "FechaFactura": "A.FechaFactura",
        "FechaRadicacion": "A.FechaRadicacion",
    }

    def __init__(self, period_field: str, cutoff_date: date) -> None:
        if period_field not in self.PERIOD_FIELDS:
            raise ValueError("El campo de periodo FPR no está permitido.")
        self.period_field = period_field
        self.period_expression = self.PERIOD_FIELDS[period_field]
        self.cutoff_date = cutoff_date

    @staticmethod
    def _fetch_all(connection, query: str, params: tuple = ()) -> list[dict]:
        cursor = connection.cursor()
        try:
            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except pyodbc.Error:
            # Conserva el detalle técnico en el log del backend sin exponerlo al cliente.
            logger.exception("Error SQL Server al consultar facturas FPR.")
            raise AppError(
                "invoice_query_failed",
                "No fue posible consultar las facturas en SQL Server. Verifica los permisos de lectura.",
                503,
            ) from None
        finally:
            cursor.close()

    @staticmethod
    def _fetch_all_excluding(
        connection,
        query: str,
        params: tuple,
        excluded_keys: set[tuple[str, str, str]],
    ) -> list[dict]:
        """Ejecuta una consulta excluyendo claves cargadas en una tabla temporal."""
        cursor = connection.cursor()
        try:
            cursor.execute(
                "IF OBJECT_ID('tempdb..#FixedCostInvoiceKeys') IS NOT NULL "
                "DROP TABLE #FixedCostInvoiceKeys"
            )
            cursor.execute(
                """
                CREATE TABLE #FixedCostInvoiceKeys (
                    nit_provider nvarchar(100) COLLATE DATABASE_DEFAULT NOT NULL,
                    contract nvarchar(100) COLLATE DATABASE_DEFAULT NOT NULL,
                    invoice nvarchar(100) COLLATE DATABASE_DEFAULT NOT NULL,
                    CONSTRAINT PK_FixedCostInvoiceKeys
                        PRIMARY KEY CLUSTERED (nit_provider, contract, invoice)
                )
                """
            )
            if excluded_keys:
                cursor.executemany(
                    """
                    INSERT INTO #FixedCostInvoiceKeys
                        (nit_provider, contract, invoice)
                    VALUES (?, ?, ?)
                    """,
                    list(excluded_keys),
                )
            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except pyodbc.Error:
            # Este bloque también cubre CREATE/INSERT/SELECT sobre la tabla temporal.
            logger.exception(
                "Error SQL Server al consultar facturas FPR con exclusión de Base Montos Fijos."
            )
            raise AppError(
                "invoice_query_failed",
                "No fue posible consultar las facturas en SQL Server. Verifica los permisos de lectura.",
                503,
            ) from None
        finally:
            try:
                cursor.execute(
                    "IF OBJECT_ID('tempdb..#FixedCostInvoiceKeys') IS NOT NULL "
                    "DROP TABLE #FixedCostInvoiceKeys"
                )
            except pyodbc.Error:
                pass
            cursor.close()

    @staticmethod
    def _fixed_cost_exclusion_clause() -> str:
        return """
            AND NOT EXISTS (
                SELECT 1
                FROM #FixedCostInvoiceKeys AS FC
                WHERE FC.nit_provider =
                    LTRIM(RTRIM(CONVERT(nvarchar(100), A.NITPrestador)))
                  AND FC.contract =
                    LTRIM(RTRIM(CONVERT(nvarchar(100), A.Con_Codigo)))
                  AND FC.invoice =
                    LTRIM(RTRIM(CONVERT(nvarchar(100), A.NumeroFactura)))
            )
        """

    def _where(
        self,
        *,
        contract: str | None = None,
        provider_nit: str | None = None,
        invoice: str | None = None,
        invoice_exact: bool = False,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> tuple[str, tuple]:
        clauses = [
            "A.Con_Codigo IS NOT NULL",
            "A.NITPrestador IS NOT NULL",
            "A.NumeroFactura IS NOT NULL",
            f"{self.period_expression} >= ?",
        ]
        params: list[object] = [self.cutoff_date]
        status_expression = (
            "LTRIM(RTRIM(CONVERT(nvarchar(100), A.NombreEstadoFactura)))"
        )
        clauses.append(
            f"({status_expression} = ? OR "
            f"({status_expression} = ? "
            "AND A.ValorPagar IS NOT NULL "
            "AND TRY_CONVERT(decimal(38, 4), A.ValorPagar) IS NOT NULL "
            "AND TRY_CONVERT(decimal(38, 4), A.ValorPagar) <> 0))"
        )
        params.extend(["Finalizada", "Para respuesta prestador"])

        if contract:
            clauses.append("A.Con_Codigo = ?")
            params.append(contract.strip())
        if provider_nit:
            clauses.append("A.NITPrestador = ?")
            params.append(provider_nit.strip())
        if invoice:
            if invoice_exact:
                clauses.append("A.NumeroFactura = ?")
                params.append(invoice.strip())
            else:
                clauses.append("A.NumeroFactura LIKE ?")
                params.append(f"%{invoice.strip()}%")
        if start_date:
            clauses.append(f"{self.period_expression} >= ?")
            params.append(start_date)
        if end_date:
            clauses.append(f"{self.period_expression} < DATEADD(day, 1, ?)")
            params.append(end_date)

        return " AND ".join(clauses), tuple(params)

    def count(
        self,
        connection,
        *,
        excluded_keys: set[tuple[str, str, str]] | None = None,
        **filters: object,
    ) -> int:
        where, params = self._where(**filters)
        exclusion = (
            self._fixed_cost_exclusion_clause()
            if excluded_keys
            else ""
        )
        query = (
            f"SELECT COUNT_BIG(1) AS total FROM {self.TABLE} AS A "
            f"WHERE {where}{exclusion}"
        )
        rows = (
            self._fetch_all_excluding(connection, query, params, excluded_keys)
            if excluded_keys
            else self._fetch_all(connection, query, params)
        )
        return int(rows[0]["total"]) if rows else 0

    def search(
        self,
        connection,
        offset: int,
        limit: int,
        *,
        excluded_keys: set[tuple[str, str, str]] | None = None,
        **filters: object,
    ) -> list[dict]:
        where, params = self._where(**filters)
        period_expression = self.period_expression
        exclusion = (
            self._fixed_cost_exclusion_clause()
            if excluded_keys
            else ""
        )
        query = f"""
            SELECT
                LTRIM(RTRIM(CONVERT(varchar(100), A.NumeroFactura))) AS invoice,
                LTRIM(RTRIM(CONVERT(varchar(50), A.NITPrestador))) AS nit_provider,
                LTRIM(RTRIM(CONVERT(nvarchar(250), A.NombrePrestador))) AS provider_name,
                LTRIM(RTRIM(CONVERT(varchar(100), A.Con_Codigo))) AS contract,
                CAST({period_expression} AS date) AS period_reference,
                CAST(A.FechaFactura AS date) AS invoice_date,
                CAST(A.FechaRadicacion AS date) AS filing_date,
                COALESCE(LIQ.ValorInicioFactura, A.ValorBruto) AS billed_amount,
                'sql_server' AS source
            FROM {self.TABLE} AS A
            OUTER APPLY (
                SELECT TOP (1)
                    B.ValorInicioFactura
                FROM {self.LIQUIDATION_TABLE} AS B
                WHERE B.NumRadicadoBoxalud = A.fpr_Id
                ORDER BY B.FechaLiquidacion DESC, B.IdLiquidacion DESC
            ) AS LIQ
            WHERE {where}{exclusion}
            ORDER BY period_reference DESC, invoice ASC, A.fpr_Id DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        query_params = (*params, offset, limit)
        return (
            self._fetch_all_excluding(
                connection, query, query_params, excluded_keys
            )
            if excluded_keys
            else self._fetch_all(connection, query, query_params)
        )

    def find_one(
        self,
        connection,
        invoice: str,
        provider_nit: str,
        contract: str,
        *,
        excluded_keys: set[tuple[str, str, str]] | None = None,
    ) -> dict | None:
        records = self.search(
            connection,
            0,
            1,
            excluded_keys=excluded_keys,
            contract=contract,
            provider_nit=provider_nit,
            invoice=invoice,
            invoice_exact=True,
        )
        return records[0] if records else None

    def list_contracts(self, connection, search: str | None = None) -> list[str]:
        query = f"""
            SELECT DISTINCT
                LTRIM(RTRIM(CONVERT(varchar(100), A.Con_Codigo))) AS value
            FROM {self.TABLE} AS A
            WHERE A.Con_Codigo IS NOT NULL
        """
        params: tuple = ()
        if search:
            query += " AND CONVERT(varchar(100), A.Con_Codigo) LIKE ?"
            params = (f"%{search.strip()}%",)
        query += " ORDER BY value"
        return [row["value"] for row in self._fetch_all(connection, query, params)]

    def list_providers(
        self,
        connection,
        contract: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, str]]:
        clauses = ["A.NITPrestador IS NOT NULL"]
        params: list[object] = []

        if contract:
            clauses.append("A.Con_Codigo = ?")
            params.append(contract.strip())
        if search:
            clauses.append(
                "(CONVERT(varchar(50), A.NITPrestador) LIKE ? "
                "OR A.NombrePrestador LIKE ?)"
            )
            params.extend([f"%{search.strip()}%", f"%{search.strip()}%"])

        query = f"""
            SELECT
                LTRIM(RTRIM(CONVERT(varchar(50), A.NITPrestador))) AS value,
                MAX(LTRIM(RTRIM(CONVERT(nvarchar(250), A.NombrePrestador)))) AS label
            FROM {self.TABLE} AS A
            WHERE {" AND ".join(clauses)}
            GROUP BY A.NITPrestador
            ORDER BY value
        """
        return self._fetch_all(connection, query, tuple(params))
