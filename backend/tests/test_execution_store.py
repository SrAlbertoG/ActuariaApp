import json
from datetime import datetime, timedelta, timezone

import pytest

from app.models.extraction import ExtractionStatus, ResultDataset
from app.storage.execution_store import ExecutionStore


@pytest.fixture
def store(tmp_path):
    return ExecutionStore(tmp_path / "t.sqlite")


def row(i, **kw):
    base = {c: None for c in ("Id", "CodigoTransaccion", "Factura", "CodigoTecnologia", "Tipo")}
    return {**base, "Id": str(i), "CodigoTecnologia": f"C{i}", "Factura": "F1", **kw}


def test_pagination_search_and_category_isolation(store):
    store.create("e1", {})
    store.insert_rows(ResultDataset.CONSULTA, "e1", [row(i) for i in range(5)])
    store.insert_rows(ResultDataset.INSUMO, "e1", [row(9)])
    rows, total = store.page(ResultDataset.CONSULTA, "e1", 2, 2)
    assert total == 5 and [r["Id"] for r in rows] == ["2", "3"]
    assert store.count(ResultDataset.CONSULTA, "e1", "C3") == 1
    assert store.count(ResultDataset.CONSULTA, "e1", "%") == 0  # comodines escapados
    assert store.count(ResultDataset.INSUMO, "e1") == 1


def test_update_rejects_unknown_fields_and_serializes_json(store):
    store.create("e1", {"a": 1})
    with pytest.raises(ValueError):
        store.update("e1", id="x")
    store.update("e1", status=ExtractionStatus.RUNNING, warnings=["w"])
    got = store.get("e1")
    assert got["status"] is ExtractionStatus.RUNNING and got["warnings"] == ["w"]


def test_recovers_interrupted_runs_on_startup(tmp_path):
    first = ExecutionStore(tmp_path / "t.sqlite")
    first.create("e1", {})
    second = ExecutionStore(tmp_path / "t.sqlite")
    assert second.get("e1")["status"] is ExtractionStatus.FAILED


def test_retention_purges_old_results(store):
    store.create("e1", {})
    store.insert_rows(ResultDataset.CONSULTA, "e1", [row(1)])
    old = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    store.update("e1", status=ExtractionStatus.COMPLETED, finished_at=old)
    store.purge_older_than(30)
    assert store.count(ResultDataset.CONSULTA, "e1") == 0