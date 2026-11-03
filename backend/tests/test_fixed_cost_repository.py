"""Pruebas de normalización de Base Montos Fijos."""

from datetime import date
from pathlib import Path

import pandas as pd

from app.repositories.fixed_cost_repository import FixedCostRepository


def test_fixed_cost_repository_normalizes_invoice_and_filters_month(tmp_path: Path):
    file_path = tmp_path / "BaseMontosFijos2026.xlsx"
    pd.DataFrame(
        [
            {
                "Nit": "900123456",
                "Contrato": "CNT-2026-9",
                "Prefijo": "FE",
                "Factura": "001",
                "MesdeServicio": "2026-08",
                "ValorFacturaRadicada": "1250000",
            },
            {
                "Nit": "900123456",
                "Contrato": "CNT-2026-9",
                "Prefijo": "FE",
                "Factura": "002",
                "MesdeServicio": "2026-07",
                "ValorFacturaRadicada": "1.250.000",
            },
        ]
    ).to_excel(file_path, index=False)

    repository = FixedCostRepository(file_path)

    records = repository.search(
        0,
        20,
        contract="CNT-2026-9",
        provider_nit="900123456",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
    )

    assert len(records) == 1
    assert records[0]["invoice"] == "FE001"
    assert str(records[0]["billed_amount"]) == "1250000"
    assert repository.count(contract="CNT-2026-9") == 2
    assert repository.find_one("FE001", "900123456", "CNT-2026-9")["invoice"] == "FE001"
    assert repository.find_one("FE00", "900123456", "CNT-2026-9") is None
    assert str(
        repository.find_one("FE002", "900123456", "CNT-2026-9")["billed_amount"]
    ) == "1250000"
