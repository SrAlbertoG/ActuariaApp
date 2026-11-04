"""Consultas parametrizadas a las tablas RIPS (solo lectura).

IMPORTANTE: los nombres de columna de CATEGORY_SPECS son SUPUESTOS y deben
validarse contra el esquema real. `validate_schema` falla al inicio de la
ejecución indicando exactamente qué columnas no existen.
None => la categoría no posee ese campo: se devuelve NULL (no se inventa).
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Iterator, Sequence

import pyodbc

from app.core.errors import AppError
from app.models.extraction import RipsCategory

log = logging.getLogger(__name__)
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class CategorySpec:
    category: RipsCategory
    table: str
    # campo normalizado -> columna SQL (None = no disponible en la categoría)
    fields: dict[str, str | None] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Defensa: estos identificadores se interpolan en el SQL.
        for name in (self.table, *(c for c in self.fields.values() if c)):
            if not _IDENT.fullmatch(name):
                raise ValueError(f"Identificador SQL no permitido: {name}")

    @property
    def columns(self) -> set[str]:
        return {c for c in self.fields.values() if c} | {"rat_Id"}


CATEGORY_SPECS: dict[RipsCategory, CategorySpec] = {
    RipsCategory.CONSULTA: CategorySpec(RipsCategory.CONSULTA, "RIPSArchivoConsulta", {
        "Id": "rao_Id",
        "CodigoUsuario": "rao_NumeroIdentificacion",   
        "CodigoTecnologia": "rao_CodigoConsulta",       
        "Descripcion": "rao_FinalidadConsulta",                             
        "Valor": "rao_ValorConsulta",                   
        "TipoTecnologia": None,
        "NumeroUnidad": None,
        "FechaServicio": "rao_FechaConsulta",            
    }),
    RipsCategory.PROCEDIMIENTO: CategorySpec(RipsCategory.PROCEDIMIENTO, "RIPSArchivoProcedimiento", {
        "Id": "rar_Id",
        "CodigoUsuario": "rar_NumeroIdentificacion",  
        "CodigoTecnologia": "rar_CodigoProcedimiento",   
        "Descripcion": "rar_Finalidad",                             
        "Valor": "rar_ValorProcedimiento",               
        "TipoTecnologia": None,
        "NumeroUnidad": None,
        "FechaServicio": "rar_FechaProcedimiento",      
    }),
    RipsCategory.MEDICAMENTO: CategorySpec(RipsCategory.MEDICAMENTO, "RIPSArchivoMedicamento", {
        "Id": "ram_Id",
        "CodigoUsuario": "ram_NumeroIdentificacion",  
        "CodigoTecnologia": "ram_CodigoMedicamento",     
        "Descripcion": None,          # HOMOLOGAR
        "Valor": "ram_ValorUnitario",                       
        "TipoTecnologia": "ram_TipoMedicamento",         
        "NumeroUnidad": "ram_NumeroUnidad",            
        "FechaServicio": "ram_FechaDispensAdmon",
    }),
    RipsCategory.INSUMO: CategorySpec(RipsCategory.INSUMO, "RIPSArchivoOtroServicio", {
        "Id": "ras_Id",
        "CodigoUsuario": "ras_NumeroIdentificacion",   
        "CodigoTecnologia": "ras_CodigoServicio",       
        "Descripcion": "ras_NombreServicio",            
        "Valor": "ras_ValorUnitario",                      
        "TipoTecnologia": "ras_Tiposervicio",            
        "NumeroUnidad": "ras_Cantidad",                  
        "FechaServicio": "ras_FechaSuministroTecnologia",
    }),
}

NORMALIZED_FROM_SQL = (
    "Id", "CodigoTransaccion", "CodigoUsuario", "CodigoTecnologia",
    "Descripcion", "Valor", "TipoTecnologia", "NumeroUnidad", "FechaServicio",
)


def chunked(values: Sequence, size: int) -> Iterator[list]:
    for start in range(0, len(values), size):
        yield list(values[start : start + size])


def _expression(field_name: str, column: str | None) -> str:
    if column is None:
        return "CAST(NULL AS nvarchar(1))"
    if field_name == "FechaServicio":
        return f"CAST(d.{column} AS date)"
    size = 500 if field_name == "Descripcion" else 100
    return f"LTRIM(RTRIM(CONVERT(nvarchar({size}), d.{column})))"


class RipsExtractionRepository:
    TRANSACTION_TABLE = "dbo.RIPSArchivoTransaccion"

    @staticmethod
    def _fetch(connection, query: str, params: tuple) -> list[dict]:
        cursor = connection.cursor()
        try:
            cursor.execute(query, params)
            columns = [c[0] for c in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except pyodbc.Error:
            log.exception("Error SQL Server en la extracción RIPS.")
            raise AppError(
                "rips_query_failed",
                "No fue posible consultar las tablas RIPS en SQL Server. Verifica los permisos de lectura.",
                503,
            ) from None
        finally:
            cursor.close()

    def validate_schema(self, connection) -> None:
        expected = {s.table: s.columns for s in CATEGORY_SPECS.values()}
        tables = list(expected)
        placeholders = ", ".join("?" for _ in tables)
        rows = self._fetch(
            connection,
            "SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            f"WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME IN ({placeholders})",
            tuple(tables),
        )
        present: dict[str, set[str]] = {}
        for row in rows:
            present.setdefault(row["TABLE_NAME"], set()).add(row["COLUMN_NAME"])
        missing = [
            f"{table}.{column}"
            for table, columns in expected.items()
            for column in sorted(columns - present.get(table, set()))
        ]
        if missing:
            raise AppError(
                "rips_schema_mismatch",
                "El esquema RIPS no coincide con la configuración. Columnas no encontradas: "
                + ", ".join(missing),
                500,
            )

    def fetch_transactions(self, connection, transaction_ids: Sequence[str], chunk_size: int) -> list[dict]:
        records: list[dict] = []
        for chunk in chunked(list(dict.fromkeys(transaction_ids)), chunk_size):
            placeholders = ", ".join("?" for _ in chunk)
            records.extend(self._fetch(
                connection,
                f"""
                SELECT
                    CONVERT(varchar(100), rat_Id) AS id,
                    LTRIM(RTRIM(CONVERT(varchar(100), rat_NumeroFactura))) AS invoice,
                    LTRIM(RTRIM(CONVERT(varchar(100), rat_NumeroContrato))) AS contract,
                    LTRIM(RTRIM(CONVERT(varchar(50), rat_NumeroIdentificacion))) AS nit_provider,
                    LTRIM(RTRIM(CONVERT(varchar(50), rat_CodigoPrestador))) AS provider_code,
                    CAST(FechaCargueRips AS date) AS rips_date,
                    CAST(FechaRadicacionFactura AS date) AS filing_date
                FROM {self.TRANSACTION_TABLE}
                WHERE rat_Activo = 'Activo' AND rat_Id IN ({placeholders})
                """,
                tuple(chunk),
            ))
        return records

    def fetch_details(self, connection, spec: CategorySpec, transaction_ids: Sequence[str]) -> list[dict]:
        select = ", ".join(
            f"{_expression(name, None if name == 'CodigoTransaccion' else spec.fields.get(name))} AS {name}"
            if name != "CodigoTransaccion"
            else "CONVERT(varchar(100), d.rat_Id) AS CodigoTransaccion"
            for name in NORMALIZED_FROM_SQL
        )
        placeholders = ", ".join("?" for _ in transaction_ids)
        return self._fetch(
            connection,
            f"SELECT {select} FROM dbo.{spec.table} AS d WHERE d.rat_Id IN ({placeholders})",
            tuple(transaction_ids),
        )