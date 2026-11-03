"""Codificación de identificadores de factura usados por la interfaz."""

import base64
import json

from app.core.errors import AppError


_ALLOWED_SOURCES = {"base_fixed", "sql_server"}


def encode_invoice_id(
    source: str,
    invoice: str,
    provider_nit: str,
    contract: str,
) -> str:
    """Genera un identificador URL-safe a partir de la clave natural de la factura."""
    if source not in _ALLOWED_SOURCES:
        raise ValueError("Origen de factura no permitido.")

    payload = json.dumps(
        [source, invoice, provider_nit, contract],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def decode_invoice_id(invoice_id: str) -> dict[str, str]:
    """Valida y recupera la clave natural sin confiar en valores del cliente."""
    try:
        padding = "=" * (-len(invoice_id) % 4)
        decoded = base64.urlsafe_b64decode(invoice_id + padding)
        values = json.loads(decoded.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        raise AppError(
            "invalid_invoice_id",
            "El identificador de factura no es válido.",
            400,
        ) from None

    if (
        not isinstance(values, list)
        or len(values) != 4
        or values[0] not in _ALLOWED_SOURCES
        or not all(isinstance(value, str) and value.strip() for value in values)
    ):
        raise AppError(
            "invalid_invoice_id",
            "El identificador de factura no es válido.",
            400,
        )

    source, invoice, provider_nit, contract = values
    return {
        "source": source,
        "invoice": invoice,
        "nit_provider": provider_nit,
        "contract": contract,
    }
