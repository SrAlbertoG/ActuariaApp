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


def test_build_filter_rejects_more_than_250_invoices():
    keys = [
        {
            "invoice": f"FE{index}",
            "nit_provider": "900123456",
            "contract": "CNT-2026-9",
        }
        for index in range(251)
    ]

    with pytest.raises(AppError) as error:
        SqlServerTransactionRepository._build_filter(keys)

    assert error.value.code == "too_many_invoices"
