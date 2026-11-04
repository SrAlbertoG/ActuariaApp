"""Exportación a Excel (OpenPyXL, modo streaming) desde los resultados persistidos."""

import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

from app.core.errors import AppError
from app.models.extraction import DATASETS, NUMERIC_COLUMNS, ResultDataset
from app.schemas.extractions import ExportRead
from app.storage.execution_store import ExecutionStore

EXCEL_MAX_ROWS = 1_048_575  # menos la fila de encabezado
_ORDER = (
    ResultDataset.FACTURAS, ResultDataset.TRANSACCIONES, ResultDataset.CONSULTA,
    ResultDataset.PROCEDIMIENTO, ResultDataset.MEDICAMENTO, ResultDataset.INSUMO,
)


class ExportService:
    def __init__(self, store: ExecutionStore, exports_dir: Path) -> None:
        self.store = store
        self.exports_dir = exports_dir

    def export(self, execution_id: str) -> ExportRead:
        execution = self.store.get(execution_id)
        if execution is None:
            raise AppError("extraction_not_found", "No se encontró la ejecución solicitada.", 404)
        if not execution["status"].has_results:
            raise AppError("export_not_available",
                           "Solo se pueden exportar ejecuciones finalizadas correctamente.", 409)
        for dataset in _ORDER:
            if self.store.count(dataset, execution_id) > EXCEL_MAX_ROWS:
                raise AppError("export_row_limit",
                               f"La hoja {DATASETS[dataset].sheet} supera el límite de filas de Excel.", 413)

        self.exports_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        target = self.exports_dir / f"RIPS_{execution_id[:8]}_{stamp}.xlsx"
        tmp = target.with_suffix(".tmp")

        workbook = Workbook(write_only=True)
        for dataset in _ORDER:
            spec = DATASETS[dataset]
            sheet = workbook.create_sheet(spec.sheet)
            sheet.append(list(spec.columns))
            numeric_idx = {i for i, c in enumerate(spec.columns) if c in NUMERIC_COLUMNS}
            for batch in self.store.iter_rows(dataset, execution_id):
                for row in batch:
                    sheet.append([self._cell(sheet, v, i in numeric_idx) for i, v in enumerate(row)])
        summary = workbook.create_sheet("Resumen")
        for line in self._summary(execution):
            summary.append([self._cell(summary, v, False) for v in line])
        workbook.save(tmp)
        os.replace(tmp, target)

        self.store.update(execution_id, export_path=str(target))
        return ExportRead(
            execution_id=execution_id, filename=target.name, path=str(target),
            size_bytes=target.stat().st_size, generated_at=datetime.now(timezone.utc),
        )

    def file_path(self, execution_id: str) -> Path:
        execution = self.store.get(execution_id)
        if execution is None or not execution["export_path"]:
            raise AppError("export_not_found", "Aún no se ha generado la exportación.", 404)
        path = Path(execution["export_path"]).resolve()
        if self.exports_dir.resolve() not in path.parents or not path.is_file():
            raise AppError("export_not_found", "El archivo exportado ya no está disponible.", 404)
        return path

    @staticmethod
    def _cell(sheet, value, numeric: bool):
        if value is None:
            return None
        if numeric:
            try:
                return Decimal(value)
            except (InvalidOperation, TypeError):
                return value
        if isinstance(value, str):
            value = ILLEGAL_CHARACTERS_RE.sub("", value)
            if value.startswith("="):  # evita que Excel lo interprete como fórmula
                cell = WriteOnlyCell(sheet, value=value)
                cell.data_type = "s"
                return cell
        return value

    @staticmethod
    def _summary(execution: dict) -> list[list]:
        p, m = execution["parameters"] or {}, execution["metrics"] or {}
        rows: list[list] = [
            ["Concepto", "Valor"],
            ["ID de ejecución", execution["id"]],
            ["Estado", execution["status"].value],
            ["Inicio", execution["started_at"]],
            ["Fin", execution["finished_at"]],
            ["Contratos", ", ".join(p.get("contracts", []))],
            ["Prestadores", ", ".join(p.get("providers", []))],
            ["Periodo desde", p.get("start_date")],
            ["Periodo hasta", p.get("end_date")],
            ["Categorías", ", ".join(p.get("categories", []))],
            ["Homologación aplicada", "No"],
            ["Facturas consultadas", m.get("invoices_consulted")],
            ["Facturas válidas", m.get("invoices_valid")],
            ["Facturas corregidas", m.get("invoices_corrected")],
            ["Facturas descartadas", m.get("invoices_discarded")],
            ["Transacciones seleccionadas", m.get("transactions_selected")],
            ["Transacciones procesadas", m.get("transactions_processed")],
        ]
        rows += [[f"Registros {k}", v] for k, v in (m.get("records_by_category") or {}).items()]
        rows += [["Advertencia", w] for w in (execution["warnings"] or [])]
        rows += [["Error", e] for e in (execution["errors"] or [])]
        return rows