"""Consulta del contrato correcto en BiPagosFPR (validación de contratos)."""

import logging
from typing import Sequence

import pyodbc

from app.core.errors import AppError
from app.repositories.rips_extraction_repository import chunked

log = logging.getLogger(__name__)
Unit = tuple[str, str]  # (factura, NIT prestador)


class SqlServerContractRepository:
    TABLE = "[BoxaludBI_Comfenalco].[dbo].[BiPagosFPR]"

    def find_contracts(self, connection, units: Sequence[Unit], chunk_size: int = 500) -> dict[Unit, set[str]]:
        wanted = set(units)
        found: dict[Unit, set[str]] = {}
        invoices = list(dict.fromkeys(invoice for invoice, _ in units))
        for chunk in chunked(invoices, chunk_size):
            placeholders = ", ".join("?" for _ in chunk)
            cursor = connection.cursor()
            try:
                cursor.execute(
                    f"""
                    SELECT DISTINCT
                        LTRIM(RTRIM(CONVERT(varchar(100), NumeroFactura))) AS invoice,
                        LTRIM(RTRIM(CONVERT(varchar(50), NITPrestador))) AS nit,
                        LTRIM(RTRIM(CONVERT(varchar(100), Con_Codigo))) AS contract
                    FROM {self.TABLE}
                    WHERE Con_Codigo IS NOT NULL AND NumeroFactura IN ({placeholders})
                    """,
                    tuple(chunk),
                )
                for invoice, nit, contract in cursor.fetchall():
                    if (invoice, nit) in wanted:
                        found.setdefault((invoice, nit), set()).add(contract)
            except pyodbc.Error:
                log.exception("Error SQL Server al validar contratos en BiPagosFPR.")
                raise AppError(
                    "contract_validation_failed",
                    "No fue posible validar los contratos en BiPagosFPR.",
                    503,
                ) from None
            finally:
                cursor.close()
        return found