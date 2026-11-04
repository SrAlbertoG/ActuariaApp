"""Pruebas para filtros parametrizados de facturación FPR."""

from datetime import date

import pytest

from app.repositories.sql_server_invoice_repository import (
    SqlServerInvoiceRepository,
)


def test_invoice_filters_are_parameterized():
    repository = SqlServerInvoiceRepository("FechaFactura", date(2026, 9, 1))

    where, params = repository._where(
        contract="CNT-2026-9",
        provider_nit="900123456",
        invoice="FE001' OR 1=1 --",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
    )

    assert "FE001' OR 1=1 --" not in where
    assert "A.NumeroFactura LIKE ?" in where
    assert params == (
        date(2026, 9, 1),
        "Finalizada",
        "Para respuesta prestador",
        "CNT-2026-9",
        "900123456",
        "%FE001' OR 1=1 --%",
        date(2026, 9, 1),
        date(2026, 9, 30),
    )
    assert "A.ValorPagar IS NOT NULL" in where
    assert "TRY_CONVERT(decimal(38, 4), A.ValorPagar) <> 0" in where


def test_invoice_repository_only_accepts_whitelisted_period_fields():
    with pytest.raises(ValueError):
        SqlServerInvoiceRepository("FechaRadicacion; DROP TABLE X", date(2026, 9, 1))


def test_invoice_detail_uses_exact_invoice_match():
    repository = SqlServerInvoiceRepository("FechaFactura", date(2026, 9, 1))

    where, params = repository._where(
        invoice="FE001",
        invoice_exact=True,
    )

    assert "A.NumeroFactura = ?" in where
    assert "LIKE" not in where
    assert params == (
        date(2026, 9, 1),
        "Finalizada",
        "Para respuesta prestador",
        "FE001",
    )


def test_fixed_cost_exclusion_uses_nit_contract_and_full_invoice_key():
    repository = SqlServerInvoiceRepository("FechaFactura", date(2026, 9, 1))
    clause = repository._fixed_cost_exclusion_clause()

    assert "NOT EXISTS" in clause
    assert "FC.nit_provider" in clause
    assert "FC.contract" in clause
    assert "FC.invoice" in clause
    assert "A.NumeroFactura" in clause

def test_invoice_status_rule_only_requires_nonzero_amount_for_provider_response():
    repository = SqlServerInvoiceRepository("FechaFactura", date(2026, 9, 1))
    where, params = repository._where()
    assert "LTRIM(RTRIM(CONVERT(nvarchar(100), A.NombreEstadoFactura))) = ? OR (" in where
    assert "ValorPagar IS NOT NULL" in where
    assert "TRY_CONVERT(decimal(38, 4), A.ValorPagar) <> 0" in where
    assert params[:3] == (date(2026, 9, 1), "Finalizada", "Para respuesta prestador")
