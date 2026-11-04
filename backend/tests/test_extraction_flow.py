import threading
from contextlib import contextmanager
from datetime import date, datetime, timezone

import pytest
from openpyxl import load_workbook

from app.core.errors import AppError
from app.models.extraction import ExtractionStatus, ResultDataset, RipsCategory
from app.schemas.extractions import ExtractionCreateRequest
from app.schemas.invoices import ExtractionPreparationRead
from app.services.export_service import ExportService
from app.services.extraction_service import ExtractionQueryService, ExtractionService
from app.services.invoice_identifiers import encode_invoice_id
from app.storage.execution_store import ExecutionStore


class FakeAuth:
    @contextmanager
    def connection(self):
        yield object()


class InlineTasks:
    """Ejecuta la tarea de inmediato y de forma síncrona."""
    def __init__(self):
        self.event = threading.Event()

    def submit(self, task_id, fn):
        fn(self.event)

    def cancel(self, task_id):
        self.event.set()
        return True


def tx(i, invoice, contract):
    return {"id": str(i), "invoice": invoice, "contract": contract, "nit_provider": "900",
            "provider_code": "12", "rips_date": date(2026, 8, 1), "filing_date": None}


class FakePrep:
    def __init__(self, ids):
        self.ids = ids

    def prepare(self, invoice_ids, transaction_ids, **kw):
        return ExtractionPreparationRead(
            prepared_at=datetime.now(timezone.utc), invoice_ids=invoice_ids,
            transaction_ids=transaction_ids, invoice_count=len(invoice_ids),
            transaction_count=len(transaction_ids), contracts=["CNT-1"], providers=["900"])


class FakeRips:
    def validate_schema(self, c): pass

    def fetch_transactions(self, c, ids, size):
        return [tx(1, "F1", "CNT-1"), tx(2, "F2", "CNT-9"), tx(3, "F3", "CNT-7")]

    def fetch_details(self, c, spec, ids):
        def d(i, tx_id, code):
            return {"Id": str(i), "CodigoTransaccion": tx_id, "CodigoUsuario": "U",
                    "CodigoTecnologia": code, "Descripcion": None, "Valor": "100.00",
                    "TipoTecnologia": None, "NumeroUnidad": None, "FechaServicio": None}
        if spec.category is RipsCategory.CONSULTA:
            return [d(i, t, "890201") for i, t in enumerate(ids, 1)]
        if spec.category is RipsCategory.MEDICAMENTO:
            return [d(10, "1", "CUM-1")] if "1" in ids else []
        return []


class FakeContracts:
    def find_contracts(self, c, units, size):
        return {("F2", "900"): {"CNT-1"}, ("F3", "900"): {"CNT-7"}}


@pytest.fixture
def env(tmp_path):
    store = ExecutionStore(tmp_path / "t.sqlite")
    tasks = InlineTasks()
    svc = ExtractionService(FakeAuth(), store, tasks, preparation=FakePrep(None),
                            rips_repository=FakeRips(), contract_repository=FakeContracts(), chunk_size=100)
    ids = [encode_invoice_id("base_fixed", f"F{i}", "900", "CNT-1") for i in (1, 2, 3)]
    return store, tasks, svc, ids, tmp_path


def create(svc, ids):
    return svc.create(ExtractionCreateRequest(invoice_ids=ids, transaction_ids=["1", "2", "3"]))


def test_full_flow_metrics_and_excel_matches_ui(env):
    store, tasks, svc, ids, tmp = env
    created = create(svc, ids)
    query = ExtractionQueryService(store, tasks)
    run = query.get(created.execution_id)

    assert run.status is ExtractionStatus.COMPLETED_WITH_WARNINGS
    m = run.metrics
    assert (m.invoices_consulted, m.invoices_valid, m.invoices_corrected, m.invoices_discarded) == (3, 1, 1, 1)
    assert m.transactions_processed == 2
    assert m.records_by_category == {"consulta": 2, "procedimiento": 0, "medicamento": 1, "insumo": 0}

    corrected = store.page(ResultDataset.FACTURAS, created.execution_id, 1, 10)[0]
    assert {r["Factura"]: r["EstadoValidacion"] for r in corrected} == {
        "F1": "valida", "F2": "corregida", "F3": "descartada"}
    consulta = query.results(created.execution_id, ResultDataset.CONSULTA, 1, 50, None)
    assert consulta.total == 2 and {r["Contrato"] for r in consulta.items} == {"CNT-1"}

    export = ExportService(store, tmp / "exports").export(created.execution_id)
    wb = load_workbook(export.path, read_only=True)
    assert wb.sheetnames == ["Facturas", "Transacciones", "Consultas", "Procedimientos",
                             "Medicamentos", "Insumos", "Resumen"]
    assert wb["Consultas"].max_row - 1 == consulta.total
    assert wb["Medicamentos"].max_row - 1 == 1
    codes = {r[5] for r in wb["Consultas"].iter_rows(min_row=2, values_only=True)}
    assert codes == {"890201"}  # códigos originales intactos


def test_cancel_before_start_discards_results(env):
    store, tasks, svc, ids, _ = env
    tasks.event.set()
    created = create(svc, ids)
    got = ExtractionQueryService(store, tasks).get(created.execution_id)
    assert got.status is ExtractionStatus.CANCELLED
    assert store.count(ResultDataset.CONSULTA, created.execution_id) == 0


def test_cannot_cancel_or_export_unfinished_runs(env):
    store, tasks, svc, ids, tmp = env
    created = create(svc, ids)
    with pytest.raises(AppError) as err:
        ExtractionQueryService(store, tasks).cancel(created.execution_id)
    assert err.value.status_code == 409
    store.update(created.execution_id, status=ExtractionStatus.FAILED)
    with pytest.raises(AppError):
        ExportService(store, tmp / "x").export(created.execution_id)


def test_homologate_true_is_rejected():
    with pytest.raises(ValueError):
        ExtractionCreateRequest(invoice_ids=["a"], transaction_ids=["1"], homologate=True)