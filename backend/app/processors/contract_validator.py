"""Validación de contratos (lógica pura, sin acceso a datos)."""

from dataclasses import dataclass
from typing import Iterable, Mapping

from app.models.extraction import ValidationStatus

Unit = tuple[str, str]  # (factura, NIT prestador)


def _norm(value: str | None) -> str:
    return (value or "").strip().casefold()


@dataclass(frozen=True)
class Resolution:
    status: ValidationStatus
    final_contract: str | None
    reason: str


def detect_inconsistent(transactions: Iterable[Mapping], valid_contracts: Iterable[str]) -> dict[Unit, set[str]]:
    """Unidades (factura, NIT) con al menos una transacción fuera de los contratos válidos."""
    valid = {_norm(c) for c in valid_contracts}
    observed: dict[Unit, set[str]] = {}
    inconsistent: set[Unit] = set()
    for tx in transactions:
        unit = (tx["invoice"], tx["nit_provider"])
        observed.setdefault(unit, set()).add(tx["contract"])
        if _norm(tx["contract"]) not in valid:
            inconsistent.add(unit)
    return {unit: observed[unit] for unit in inconsistent}


def resolve(
    observed: Mapping[Unit, set[str]],
    fpr_contracts: Mapping[Unit, set[str]],
    valid_contracts: Iterable[str],
) -> dict[Unit, Resolution]:
    """Corrige si BiPagosFPR indica exactamente un contrato válido; si no, descarta."""
    valid = {_norm(c) for c in valid_contracts}
    result: dict[Unit, Resolution] = {}
    for unit, seen in observed.items():
        seen_text = ", ".join(sorted(seen))
        in_fpr = fpr_contracts.get(unit, set())
        if not in_fpr:
            result[unit] = Resolution(
                ValidationStatus.DISCARDED, None,
                f"Contrato {seen_text} no coincide y la factura no existe en BiPagosFPR.",
            )
            continue
        candidates = sorted(c for c in in_fpr if _norm(c) in valid)
        if len(candidates) == 1:
            result[unit] = Resolution(
                ValidationStatus.CORRECTED, candidates[0],
                f"Contrato corregido de {seen_text} a {candidates[0]} según BiPagosFPR.",
            )
        elif not candidates:
            result[unit] = Resolution(
                ValidationStatus.DISCARDED, None,
                f"BiPagosFPR indica {', '.join(sorted(in_fpr))}, fuera de los contratos seleccionados.",
            )
        else:
            result[unit] = Resolution(
                ValidationStatus.DISCARDED, None,
                f"Contrato ambiguo en BiPagosFPR: {', '.join(candidates)}.",
            )
    return result