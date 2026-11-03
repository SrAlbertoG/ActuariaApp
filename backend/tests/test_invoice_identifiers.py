"""Pruebas de identificadores opacos de facturas."""

import pytest

from app.core.errors import AppError
from app.services.invoice_identifiers import decode_invoice_id, encode_invoice_id


def test_invoice_id_round_trip():
    original = {
        "source": "base_fixed",
        "invoice": "FVA-00123",
        "nit_provider": "900123456",
        "contract": "CNT-2026-9",
    }

    invoice_id = encode_invoice_id(**{
        "source": original["source"],
        "invoice": original["invoice"],
        "provider_nit": original["nit_provider"],
        "contract": original["contract"],
    })

    assert decode_invoice_id(invoice_id) == original


def test_invoice_id_rejects_unknown_source():
    with pytest.raises(ValueError):
        encode_invoice_id("unsupported", "F-1", "900", "CNT-1")


def test_invoice_id_rejects_malformed_value():
    with pytest.raises(AppError) as error:
        decode_invoice_id("not-a-valid-id")

    assert error.value.code == "invalid_invoice_id"
