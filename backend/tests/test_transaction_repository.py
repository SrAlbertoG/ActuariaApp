"""Pruebas de seguridad y límites del repositorio de transacciones."""

import pytest

from app.core.errors import AppError
from app.repositories.sql_server_transaction_repository import (
    SqlServerTransactionRepository,
)


def test_build_filter_uses_invoice_placeholders_and_parameters():
    keys = [
        {
            "invoice": "FE001' OR 1=1 --",
            "nit_provider": "900123456",
            "contract": "CNT-2026-9",
        },
        {
            "invoice": "FE002",
            "nit_provider": "900123456",
            "contract": "CNT-2026-9",
        },
    ]

    where, params = SqlServerTransactionRepository._build_filter(keys)

    assert where.count("?") == 2
    assert "FE001' OR 1=1 --" not in where
    assert params == ("FE001' OR 1=1 --", "FE002")


def test_build_filter_deduplicates_invoice_numbers():
    keys = [
        {"invoice": "FE001", "nit_provider": "900", "contract": "CNT-1"},
        {"invoice": "FE001", "nit_provider": "901", "contract": "CNT-2"},
    ]

    where, params = SqlServerTransactionRepository._build_filter(keys)

    assert where == "(rat_NumeroFactura = ?)"
    assert params == ("FE001",)


def test_build_filter_rejects_empty_selection():
    with pytest.raises(AppError) as error:
        SqlServerTransactionRepository._build_filter([])

    assert error.value.code == "invoice_selection_required"


def test_build_filter_rejects_more_than_1000_invoices():
    keys = [
        {
            "invoice": f"FE{index}",
            "nit_provider": "900123456",
            "contract": "CNT-2026-9",
        }
        for index in range(1001)
    ]

    with pytest.raises(AppError) as error:
        SqlServerTransactionRepository._build_filter(keys)

    assert error.value.code == "too_many_invoices"


def test_build_filter_applies_only_the_search_criteria_used_by_analyst():
    keys = [
        {
            "invoice": "FE001",
            "nit_provider": "900123456",
            "contract": "CNT-2026-9",
        }
    ]

    where, params = SqlServerTransactionRepository._build_filter(
        keys,
        provider_nit="900123456",
    )

    assert "rat_NumeroIdentificacion" in where
    assert "rat_NumeroContrato" not in where
    assert "rat_NumeroFactura LIKE ?" not in where
    assert params == ("FE001", "900123456")


def test_build_filter_combines_contract_provider_and_invoice_filters():
    keys = [
        {
            "invoice": "FE001",
            "nit_provider": "900123456",
            "contract": "CNT-2026-9",
        }
    ]

    where, params = SqlServerTransactionRepository._build_filter(
        keys,
        contract="CNT-2026-9",
        provider_nit="900123456",
        invoice="FE00",
    )

    assert "rat_NumeroContrato" in where
    assert "rat_NumeroIdentificacion" in where
    assert "rat_NumeroFactura LIKE ?" in where
    assert params == ("FE001", "CNT-2026-9", "900123456", "%FE00%")

def test_validate_selection_reapplies_only_original_search_filters():
    from app.repositories.sql_server_transaction_repository import SqlServerTransactionRepository

    class Cursor:
        description = [("id",), ("invoice",), ("contract",), ("nit_provider",)]
        query = ""
        params = ()
        def execute(self, query, params):
            self.query = query
            self.params = params
        def fetchall(self):
            return [("501", "FE001", "CNT-1", "900123456")]
        def close(self):
            pass

    class Connection:
        def __init__(self):
            self.cursor_instance = Cursor()
        def cursor(self):
            return self.cursor_instance

    connection = Connection()
    repository = SqlServerTransactionRepository()
    repository.validate_selection(
        connection,
        [{"invoice": "FE001", "nit_provider": "900123456", "contract": "CNT-1"}],
        ["501"],
        provider_nit="900123456",
    )

    query = connection.cursor_instance.query
    params = connection.cursor_instance.params
    assert "rat_NumeroIdentificacion" in query
    assert "rat_NumeroContrato" not in query
    assert params == ("FE001", "900123456", "501")
