"""Pruebas del servicio de preparación de extracción."""

from contextlib import contextmanager

import pytest

from app.core.errors import AppError
from app.services.extraction_preparation_service import (
    ExtractionPreparationService,
)
from app.services.invoice_identifiers import encode_invoice_id


class FakeAuthService:
    @contextmanager
    def connection(self):
        yield object()


class FakeTransactionRepository:
    def __init__(self, records):
        self.records = records
        self.received_invoice_keys = None
        self.received_transaction_ids = None
        self.received_filters = None

    def validate_selection(
        self,
        connection,
        invoice_keys,
        transaction_ids,
        **filters,
    ):
        self.received_invoice_keys = invoice_keys
        self.received_transaction_ids = transaction_ids
        self.received_filters = filters
        return self.records


def make_invoice_id():
    return encode_invoice_id(
        source="base_fixed",
        invoice="FE001",
        provider_nit="900123456",
        contract="CNT-2026-9",
    )


def test_prepare_returns_server_validated_selection():
    service = ExtractionPreparationService(FakeAuthService())
    repository = FakeTransactionRepository(
        [
            {
                "id": "501",
                "invoice": "FE001",
                "contract": "CNT-2026-9",
                "nit_provider": "900123456",
            },
            {
                "id": "502",
                "invoice": "FE001",
                "contract": "CNT-2026-9",
                "nit_provider": "900123456",
            },
        ]
    )
    service.transaction_repository = repository

    invoice_id = make_invoice_id()
    result = service.prepare(
        [invoice_id, invoice_id],
        ["501", "502", "501"],
    )

    assert result.status == "prepared"
    assert result.invoice_count == 1
    assert result.transaction_count == 2
    assert result.invoice_ids == [invoice_id]
    assert result.transaction_ids == ["501", "502"]
    assert result.contracts == ["CNT-2026-9"]
    assert result.providers == ["900123456"]
    assert repository.received_invoice_keys[0]["invoice"] == "FE001"


def test_prepare_rejects_inactive_or_unrelated_transactions():
    service = ExtractionPreparationService(FakeAuthService())
    service.transaction_repository = FakeTransactionRepository(
        [
            {
                "id": "501",
                "invoice": "FE001",
                "contract": "CNT-2026-9",
                "nit_provider": "900123456",
            }
        ]
    )

    with pytest.raises(AppError) as error:
        service.prepare([make_invoice_id()], ["501", "999"])

    assert error.value.code == "invalid_transaction_selection"
    assert error.value.status_code == 409


def test_prepare_revalidates_only_the_filters_used_for_invoice_search():
    service = ExtractionPreparationService(FakeAuthService())
    repository = FakeTransactionRepository(
        [
            {
                "id": "501",
                "invoice": "FE001",
                "contract": "CNT-2026-9",
                "nit_provider": "900123456",
            }
        ]
    )
    service.transaction_repository = repository

    service.prepare(
        [make_invoice_id()],
        ["501"],
        provider_nit="900123456",
    )

    assert repository.received_filters == {"provider_nit": "900123456"}
