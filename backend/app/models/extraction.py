"""Modelos de dominio de la extracción RIPS (sin dependencias de FastAPI)."""

from dataclasses import dataclass
from enum import Enum


class ExtractionStatus(str, Enum):
    """Estados idénticos en backend y frontend (runTypes.ts)."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self not in (ExtractionStatus.QUEUED, ExtractionStatus.RUNNING)

    @property
    def has_results(self) -> bool:
        return self in (
            ExtractionStatus.COMPLETED,
            ExtractionStatus.COMPLETED_WITH_WARNINGS,
        )


class RipsCategory(str, Enum):
    CONSULTA = "consulta"
    PROCEDIMIENTO = "procedimiento"
    MEDICAMENTO = "medicamento"
    INSUMO = "insumo"


class ValidationStatus(str, Enum):
    VALID = "valida"
    CORRECTED = "corregida"
    DISCARDED = "descartada"


class ResultDataset(str, Enum):
    FACTURAS = "facturas"
    TRANSACCIONES = "transacciones"
    CONSULTA = "consulta"
    PROCEDIMIENTO = "procedimiento"
    MEDICAMENTO = "medicamento"
    INSUMO = "insumo"


# Estructura normalizada obligatoria (orden fijo).
NORMALIZED_COLUMNS: tuple[str, ...] = (
    "Id",
    "CodigoTransaccion",
    "CodigoPrestador",
    "CodigoUsuario",
    "Factura",
    "CodigoTecnologia",
    "Descripcion",
    "Valor",
    "TipoTecnologia",
    "NumeroUnidad",
    "FechaServicio",
    "FechaFactura",
    "Tipo",
)
# Columnas de trazabilidad añadidas al final (contrato y prestador exigidos en la exportación).
RECORD_COLUMNS: tuple[str, ...] = NORMALIZED_COLUMNS + ("Contrato", "NitPrestador")

INVOICE_COLUMNS: tuple[str, ...] = (
    "Factura",
    "NitPrestador",
    "Contrato",
    "ContratoFinal",
    "Fuente",
    "EstadoValidacion",
    "Motivo",
    "Transacciones",
)
TRANSACTION_COLUMNS: tuple[str, ...] = (
    "CodigoTransaccion",
    "Factura",
    "Contrato",
    "ContratoOriginal",
    "NitPrestador",
    "CodigoPrestador",
    "FechaRips",
    "FechaRadicacion",
)
NUMERIC_COLUMNS = frozenset({"Valor", "NumeroUnidad"})


@dataclass(frozen=True)
class DatasetSpec:
    table: str
    columns: tuple[str, ...]
    sheet: str
    category: str | None = None


DATASETS: dict[ResultDataset, DatasetSpec] = {
    ResultDataset.FACTURAS: DatasetSpec("extraction_invoices", INVOICE_COLUMNS, "Facturas"),
    ResultDataset.TRANSACCIONES: DatasetSpec(
        "extraction_transactions", TRANSACTION_COLUMNS, "Transacciones"
    ),
    ResultDataset.CONSULTA: DatasetSpec("extraction_records", RECORD_COLUMNS, "Consultas", "consulta"),
    ResultDataset.PROCEDIMIENTO: DatasetSpec(
        "extraction_records", RECORD_COLUMNS, "Procedimientos", "procedimiento"
    ),
    ResultDataset.MEDICAMENTO: DatasetSpec(
        "extraction_records", RECORD_COLUMNS, "Medicamentos", "medicamento"
    ),
    ResultDataset.INSUMO: DatasetSpec("extraction_records", RECORD_COLUMNS, "Insumos", "insumo"),
}