"""Pruebas del endpoint de dataset acotado de transacciones."""

from contextlib import contextmanager

import pytest

from app.core.errors import AppError
from app.services.invoice_identifiers import encode_invoice_id
from app.services.transaction_service import TransactionService


class FakeAuthService:
    @contextmanager
    def connection(self):
        yield object()


class FakeTransactionRepository:
    def __init__(self, rows):
        self.rows = rows
        self.requested_limit = None

    def search(self, connection, invoice_keys, offset, limit, **filters):
        self.requested_limit = limit
        return self.rows[:limit]


def invoice_id():
    return encode_invoice_id("base_fixed", "FE001", "900123456", "CNT-1")


def transaction_row(index=1):
    return {
        "id": str(index),
        "invoice": "FE001",
        "contract": "CNT-1",
        "nit_provider": "900123456",
        "provider_code": "12345",
        "rips_date": None,
        "filing_date": None,
    }


def test_dataset_fetches_records_once_and_returns_total_from_result_size():
    service = TransactionService(FakeAuthService())
    repository = FakeTransactionRepository([transaction_row()])
    service.repository = repository

    result = service.search_dataset([invoice_id()], provider_nit="900123456")

    assert result["total"] == 1
    assert result["items"][0].id == "1"
    assert repository.requested_limit == 1001


def test_dataset_rejects_more_than_one_thousand_without_truncating():
    service = TransactionService(FakeAuthService())
    repository = FakeTransactionRepository(
        [transaction_row(index) for index in range(1001)]
    )
    service.repository = repository

    with pytest.raises(AppError) as error:
        service.search_dataset([invoice_id()])

    assert error.value.code == "transaction_result_limit_exceeded"
    assert repository.requested_limit == 1001
