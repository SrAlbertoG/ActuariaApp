"""Pruebas de combinación y paginación del servicio de facturas."""

from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from app.services import invoice_service


class FakeAuthService:
    @contextmanager
    def connection(self):
        yield object()


class FakeFixedRepository:
    def count(self, **filters):
        return 3

    def search(self, offset, limit, **filters):
        records = [
            {
                "invoice": "FE-AUG-03",
                "nit_provider": "900123456",
                "provider_name": None,
                "contract": "CNT-1",
                "period_reference": date(2026, 8, 3),
                "invoice_date": None,
                "filing_date": None,
                "billed_amount": Decimal("300"),
                "source": "base_fixed",
            },
            {
                "invoice": "FE-AUG-02",
                "nit_provider": "900123456",
                "provider_name": None,
                "contract": "CNT-1",
                "period_reference": date(2026, 8, 2),
                "invoice_date": None,
                "filing_date": None,
                "billed_amount": Decimal("200"),
                "source": "base_fixed",
            },
            {
                "invoice": "FE-AUG-01",
                "nit_provider": "900123456",
                "provider_name": None,
                "contract": "CNT-1",
                "period_reference": date(2026, 8, 1),
                "invoice_date": None,
                "filing_date": None,
                "billed_amount": Decimal("100"),
                "source": "base_fixed",
            },
        ]
        return records[offset : offset + limit]


class FakeSqlRepository:
    def __init__(self, period_field, cutoff_date):
        self.period_field = period_field
        self.cutoff_date = cutoff_date

    def count(self, connection, **filters):
        return 2

    def search(self, connection, offset, limit, **filters):
        records = [
            {
                "invoice": "FPR-SEP-02",
                "nit_provider": "900123456",
                "provider_name": "Prestador",
                "contract": "CNT-1",
                "period_reference": date(2026, 9, 2),
                "invoice_date": date(2026, 9, 2),
                "filing_date": date(2026, 9, 4),
                "billed_amount": Decimal("500"),
                "source": "sql_server",
            },
            {
                "invoice": "FPR-SEP-01",
                "nit_provider": "900123456",
                "provider_name": "Prestador",
                "contract": "CNT-1",
                "period_reference": date(2026, 9, 1),
                "invoice_date": date(2026, 9, 1),
                "filing_date": date(2026, 9, 3),
                "billed_amount": Decimal("400"),
                "source": "sql_server",
            },
        ]
        return records[offset : offset + limit]


def test_search_combines_sources_and_paginates_across_cutoff(monkeypatch):
    settings = SimpleNamespace(
        invoice_source_cutoff=date(2026, 9, 1),
        fixed_costs_file=Path("unused.xlsx"),
        fpr_period_field="FechaFactura",
    )
    monkeypatch.setattr(invoice_service, "get_settings", lambda: settings)

    service = invoice_service.InvoiceService(FakeAuthService())
    service.fixed_repository = FakeFixedRepository()
    service.sql_repository = FakeSqlRepository(
        "FechaFactura",
        date(2026, 9, 1),
    )

    result = service.search(
        start_date=date(2026, 8, 1),
        end_date=date(2026, 9, 30),
        page=2,
        page_size=2,
    )

    assert result.total == 5
    assert result.page == 2
    assert [item.invoice for item in result.items] == [
        "FE-AUG-03",
        "FE-AUG-02",
    ]
    assert all(item.source == "base_fixed" for item in result.items)


def test_search_uses_only_sql_for_periods_after_cutoff(monkeypatch):
    settings = SimpleNamespace(
        invoice_source_cutoff=date(2026, 9, 1),
        fixed_costs_file=Path("unused.xlsx"),
        fpr_period_field="FechaFactura",
    )
    monkeypatch.setattr(invoice_service, "get_settings", lambda: settings)

    service = invoice_service.InvoiceService(FakeAuthService())
    service.fixed_repository = FakeFixedRepository()
    service.sql_repository = FakeSqlRepository(
        "FechaFactura",
        date(2026, 9, 1),
    )

    result = service.search(
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
        page=1,
        page_size=25,
    )

    assert result.total == 2
    assert len(result.items) == 2
    assert all(item.source == "sql_server" for item in result.items)
