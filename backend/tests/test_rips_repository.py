import pytest

from app.core.errors import AppError
from app.models.extraction import RipsCategory
from app.repositories.rips_extraction_repository import (
    CATEGORY_SPECS, CategorySpec, RipsExtractionRepository, chunked,
)


class Cursor:
    def __init__(self, rows=None, description=None):
        self.rows, self.description, self.calls = rows or [], description or [], []

    def execute(self, query, params=()):
        self.calls.append((query, params))

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class Conn:
    def __init__(self, cursor):
        self._c = cursor

    def cursor(self):
        return self._c


def test_chunked_splits_by_size():
    assert [len(c) for c in chunked(list(range(1050)), 500)] == [500, 500, 50]


def test_fetch_details_is_parameterized_and_returns_nulls_for_missing_fields():
    cur = Cursor()
    RipsExtractionRepository().fetch_details(Conn(cur), CATEGORY_SPECS[RipsCategory.CONSULTA], ["1", "2' OR 1=1 --"])
    query, params = cur.calls[0]
    assert query.count("?") == 2 and "OR 1=1" not in query
    assert params == ("1", "2' OR 1=1 --")
    assert "CAST(NULL AS nvarchar(1)) AS Descripcion" in query
    assert "d.rat_Id IN (?, ?)" in query


def test_fetch_transactions_only_active_and_chunked():
    cur = Cursor()
    RipsExtractionRepository().fetch_transactions(Conn(cur), [str(i) for i in range(5)], 2)
    assert len(cur.calls) == 3
    assert all("rat_Activo = 'Activo'" in q for q, _ in cur.calls)


def test_category_spec_rejects_unsafe_identifiers():
    with pytest.raises(ValueError):
        CategorySpec(RipsCategory.CONSULTA, "T; DROP TABLE X", {})


def test_validate_schema_reports_missing_columns():
    cur = Cursor(rows=[("RIPSArchivoConsulta", "rao_Id")], description=[("TABLE_NAME",), ("COLUMN_NAME",)])
    with pytest.raises(AppError) as err:
        RipsExtractionRepository().validate_schema(Conn(cur))
    assert err.value.code == "rips_schema_mismatch"
    assert "RIPSArchivoConsulta.rat_Id" in err.value.message