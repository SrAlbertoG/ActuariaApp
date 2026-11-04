"""Orquestación de la extracción RIPS (crear, ejecutar en segundo plano, consultar, cancelar)."""

import logging
import threading
import uuid
from typing import Any

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.task_manager import ExtractionCancelled, LocalTaskManager
from app.models.extraction import ExtractionStatus, ResultDataset, ValidationStatus
from app.processors.contract_validator import detect_inconsistent, resolve
from app.processors.rips_normalizer import normalize
from app.repositories.rips_extraction_repository import (
    CATEGORY_SPECS, RipsExtractionRepository, chunked,
)
from app.repositories.sql_server_contract_repository import SqlServerContractRepository
from app.schemas.extractions import (
    ExtractionCreated, ExtractionCreateRequest, ExtractionMetrics, ExtractionRead, ResultPage,
)
from app.models.extraction import DATASETS
from app.services.extraction_preparation_service import ExtractionPreparationService
from app.services.invoice_identifiers import decode_invoice_id
from app.storage.execution_store import ExecutionStore, utcnow

log = logging.getLogger(__name__)


class ExtractionService:
    """Crea y ejecuta extracciones. Requiere sesión SQL Server."""

    def __init__(
        self, auth_service, store: ExecutionStore, task_manager: LocalTaskManager, *,
        preparation=None, rips_repository=None, contract_repository=None,
        chunk_size: int | None = None,
    ) -> None:
        self.auth_service = auth_service
        self.store = store
        self.task_manager = task_manager
        self.preparation = preparation or ExtractionPreparationService(auth_service)
        self.rips_repo = rips_repository or RipsExtractionRepository()
        self.contract_repo = contract_repository or SqlServerContractRepository()
        self.chunk_size = chunk_size or get_settings().extraction_chunk_size

    # ---- Crear ------------------------------------------------------------
    def create(self, request: ExtractionCreateRequest) -> ExtractionCreated:
        if request.start_date and request.end_date and request.start_date > request.end_date:
            raise AppError("invalid_date_range",
                           "La fecha inicial no puede ser posterior a la fecha final.", 422)
        prepared = self.preparation.prepare(
            request.invoice_ids, request.transaction_ids,
            contract=request.contract, provider_nit=request.provider_nit, invoice=request.invoice,
        )
        keys = [decode_invoice_id(i) for i in prepared.invoice_ids]
        valid_contracts = request.contracts or sorted({k["contract"] for k in keys}, key=str.casefold)
        execution_id = str(uuid.uuid4())
        self.store.create(execution_id, {
            "contracts": valid_contracts,
            "providers": request.providers or prepared.providers,
            "start_date": request.start_date.isoformat() if request.start_date else None,
            "end_date": request.end_date.isoformat() if request.end_date else None,
            "categories": [c.value for c in request.categories],
            "filters": {"contract": request.contract, "provider_nit": request.provider_nit,
                        "invoice": request.invoice},
            "homologate": False,
            "invoice_count": prepared.invoice_count,
            "transaction_count": prepared.transaction_count,
        })
        transaction_ids = list(prepared.transaction_ids)
        categories = list(request.categories)
        self.task_manager.submit(
            execution_id,
            lambda cancel: self._run(execution_id, keys, transaction_ids, valid_contracts, categories, cancel),
        )
        return ExtractionCreated(
            execution_id=execution_id, status=ExtractionStatus.QUEUED,
            message="Extracción registrada correctamente",
        )

    # ---- Ejecución (hilo de fondo) ---------------------------------------
    @staticmethod
    def _check(cancel: threading.Event) -> None:
        if cancel.is_set():
            raise ExtractionCancelled()

    def _step(self, execution_id: str, progress: int, step: str) -> None:
        self.store.update(execution_id, progress=progress, current_step=step)

    def _run(self, execution_id, keys, transaction_ids, valid_contracts, categories, cancel) -> None:
        store = self.store
        try:
            self._check(cancel)
            store.update(execution_id, status=ExtractionStatus.RUNNING, started_at=utcnow(),
                         progress=2, current_step="Verificando esquema RIPS")
            warnings: list[str] = []
            metrics = ExtractionMetrics(
                invoices_consulted=len(keys), transactions_selected=len(transaction_ids),
                records_by_category={c.value: 0 for c in categories},
            )
            with self.auth_service.connection() as conn:
                self.rips_repo.validate_schema(conn)

                # 1. Transacciones seleccionadas (solo las de las facturas elegidas).
                self._step(execution_id, 8, "Consultando transacciones")
                fetched = self.rips_repo.fetch_transactions(conn, transaction_ids, self.chunk_size)
                self._check(cancel)
                selected_units = {(k["invoice"], k["nit_provider"]) for k in keys}
                transactions = [t for t in fetched if (t["invoice"], t["nit_provider"]) in selected_units]
                metrics.transactions_found = len(fetched)
                if len(fetched) < len(transaction_ids):
                    warnings.append(f"{len(transaction_ids) - len(fetched)} transacciones seleccionadas ya no están activas.")
                if len(transactions) < len(fetched):
                    warnings.append(f"{len(fetched) - len(transactions)} transacciones no pertenecen al NIT/factura seleccionados y se omitieron.")

                # 2. Validación de contratos.
                self._step(execution_id, 20, "Validando contratos")
                observed = detect_inconsistent(transactions, valid_contracts)
                fpr = self.contract_repo.find_contracts(conn, list(observed), self.chunk_size) if observed else {}
                resolutions = resolve(observed, fpr, valid_contracts)
                self._check(cancel)

                tx_index: dict[str, dict] = {}
                tx_rows: list[dict] = []
                tx_count: dict[tuple[str, str], int] = {}
                for tx in transactions:
                    unit = (tx["invoice"], tx["nit_provider"])
                    res = resolutions.get(unit)
                    if res and res.status is ValidationStatus.DISCARDED:
                        continue
                    final = res.final_contract if res else tx["contract"]
                    entry = {**tx, "contract": final}
                    tx_index[str(tx["id"])] = entry
                    tx_count[unit] = tx_count.get(unit, 0) + 1
                    tx_rows.append({
                        "CodigoTransaccion": tx["id"], "Factura": tx["invoice"], "Contrato": final,
                        "ContratoOriginal": tx["contract"], "NitPrestador": tx["nit_provider"],
                        "CodigoPrestador": tx["provider_code"],
                        "FechaRips": tx["rips_date"].isoformat() if tx["rips_date"] else None,
                        "FechaRadicacion": tx["filing_date"].isoformat() if tx["filing_date"] else None,
                    })
                metrics.transactions_processed = len(tx_index)

                invoice_rows: list[dict] = []
                for key in keys:
                    unit = (key["invoice"], key["nit_provider"])
                    res = resolutions.get(unit)
                    status = res.status if res else ValidationStatus.VALID
                    metrics.invoices_valid += status is ValidationStatus.VALID
                    metrics.invoices_corrected += status is ValidationStatus.CORRECTED
                    metrics.invoices_discarded += status is ValidationStatus.DISCARDED
                    invoice_rows.append({
                        "Factura": key["invoice"], "NitPrestador": key["nit_provider"],
                        "Contrato": key["contract"],
                        "ContratoFinal": res.final_contract if res and res.final_contract else (None if status is ValidationStatus.DISCARDED else key["contract"]),
                        "Fuente": key["source"], "EstadoValidacion": status.value,
                        "Motivo": res.reason if res else None,
                        "Transacciones": str(tx_count.get(unit, 0)),
                    })
                if metrics.invoices_corrected:
                    warnings.append(f"{metrics.invoices_corrected} facturas con contrato corregido (ver hoja Facturas).")
                if metrics.invoices_discarded:
                    warnings.append(f"{metrics.invoices_discarded} facturas descartadas por contrato no validable (ver hoja Facturas).")

                # 3. Extracción por categoría, por bloques, persistiendo de inmediato.
                tx_ids = list(tx_index)
                span = 60 // max(len(categories), 1)
                for index, category in enumerate(categories):
                    spec = CATEGORY_SPECS[category]
                    dataset = ResultDataset(category.value)
                    base = 30 + index * span
                    self._step(execution_id, base, f"Extrayendo {category.value}")
                    orphans = invalid = 0
                    for chunk in chunked(tx_ids, self.chunk_size):
                        self._check(cancel)
                        details = self.rips_repo.fetch_details(conn, spec, chunk)
                        result = normalize(category, details, tx_index)
                        store.insert_rows(dataset, execution_id, result.rows)
                        metrics.records_by_category[category.value] += len(result.rows)
                        orphans += result.orphans
                        invalid += result.invalid_numbers
                    if orphans:
                        warnings.append(f"{category.value}: {orphans} registros sin transacción válida se omitieron.")
                    if invalid:
                        warnings.append(f"{category.value}: {invalid} valores numéricos no interpretables quedaron en blanco.")

            if sum(metrics.records_by_category.values()) == 0:
                warnings.append("La extracción no devolvió registros RIPS.")

            self._check(cancel)
            self._step(execution_id, 95, "Consolidando resultados")
            store.insert_rows(ResultDataset.FACTURAS, execution_id, invoice_rows)
            store.insert_rows(ResultDataset.TRANSACCIONES, execution_id, tx_rows)
            final = ExtractionStatus.COMPLETED_WITH_WARNINGS if warnings else ExtractionStatus.COMPLETED
            store.update(execution_id, status=final, progress=100, current_step="Finalizada",
                         finished_at=utcnow(), metrics=metrics.model_dump(), warnings=warnings)
        except ExtractionCancelled:
            store.delete_results(execution_id)
            store.update(execution_id, status=ExtractionStatus.CANCELLED,
                         current_step="Cancelada", finished_at=utcnow())
        except AppError as exc:
            log.error("Extracción %s falló: %s", execution_id, exc.code)
            store.delete_results(execution_id)
            store.update(execution_id, status=ExtractionStatus.FAILED, finished_at=utcnow(),
                         errors=[exc.message])
        except Exception:
            log.exception("Extracción %s falló por un error inesperado", execution_id)
            store.delete_results(execution_id)
            store.update(execution_id, status=ExtractionStatus.FAILED, finished_at=utcnow(),
                         errors=["Ocurrió un error inesperado durante la extracción."])


class ExtractionQueryService:
    """Consulta y cancelación: solo usa SQLite, no requiere sesión SQL Server."""

    def __init__(self, store: ExecutionStore, task_manager: LocalTaskManager) -> None:
        self.store = store
        self.task_manager = task_manager

    def _require(self, execution_id: str) -> dict[str, Any]:
        data = self.store.get(execution_id)
        if data is None:
            raise AppError("extraction_not_found", "No se encontró la ejecución solicitada.", 404)
        return data

    def get(self, execution_id: str) -> ExtractionRead:
        d = self._require(execution_id)
        params = d["parameters"] or {}
        return ExtractionRead(
            execution_id=d["id"], status=d["status"], progress=d["progress"],
            current_step=d["current_step"], created_at=d["created_at"],
            started_at=d["started_at"], finished_at=d["finished_at"],
            contracts=params.get("contracts", []), parameters=params,
            metrics=ExtractionMetrics(**(d["metrics"] or {})),
            warnings=d["warnings"] or [], errors=d["errors"] or [], export_path=d["export_path"],
        )

    def results(self, execution_id: str, dataset: ResultDataset, page: int, page_size: int,
                search: str | None) -> ResultPage:
        self._require(execution_id)
        rows, total = self.store.page(dataset, execution_id, page, page_size, search)
        return ResultPage(dataset=dataset, columns=list(DATASETS[dataset].columns),
                          items=rows, total=total, page=page, page_size=page_size)

    def cancel(self, execution_id: str) -> ExtractionRead:
        d = self._require(execution_id)
        if d["status"].is_terminal:
            raise AppError("extraction_not_cancellable",
                           "La ejecución ya finalizó y no puede cancelarse.", 409)
        self.task_manager.cancel(execution_id)
        self.store.update(execution_id, current_step="Cancelando…")
        return self.get(execution_id)