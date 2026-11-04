"""Normalización de detalles RIPS a la estructura común (sin homologación)."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Mapping, Sequence

from app.models.extraction import RipsCategory


@dataclass
class NormalizationResult:
    rows: list[dict]
    orphans: int = 0
    invalid_numbers: int = 0


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _date(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()[:10]
    return _text(value)


def _number(value: object) -> tuple[str | None, bool]:
    """Devuelve (texto decimal exacto, es_inválido). No altera el valor original."""
    text = _text(value)
    if text is None:
        return None, False
    try:
        return format(Decimal(text), "f"), False
    except InvalidOperation:
        return None, True


def normalize(
    category: RipsCategory,
    details: Sequence[Mapping],
    tx_index: Mapping[str, Mapping],
) -> NormalizationResult:
    """`tx_index`: CodigoTransaccion -> transacción (con `contract` ya validado)."""
    result = NormalizationResult(rows=[])
    for detail in details:
        code = _text(detail.get("CodigoTransaccion"))
        tx = tx_index.get(code or "")
        if tx is None:
            result.orphans += 1
            continue
        valor, bad_valor = _number(detail.get("Valor"))
        unidad, bad_unidad = _number(detail.get("NumeroUnidad"))
        result.invalid_numbers += int(bad_valor) + int(bad_unidad)
        result.rows.append({
            "Id": _text(detail.get("Id")),
            "CodigoTransaccion": code,
            "CodigoPrestador": _text(tx.get("provider_code")),
            "CodigoUsuario": _text(detail.get("CodigoUsuario")),
            "Factura": tx["invoice"],
            "CodigoTecnologia": _text(detail.get("CodigoTecnologia")),
            "Descripcion": _text(detail.get("Descripcion")),
            "Valor": valor,
            "TipoTecnologia": _text(detail.get("TipoTecnologia")),
            "NumeroUnidad": unidad,
            "FechaServicio": _date(detail.get("FechaServicio")),
            "FechaFactura": None,  # sin fuente documentada: no se inventa
            "Tipo": category.value,
            "Contrato": tx["contract"],
            "NitPrestador": tx["nit_provider"],
        })
    return result