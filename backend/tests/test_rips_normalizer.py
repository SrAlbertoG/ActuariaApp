from datetime import date

from app.models.extraction import NORMALIZED_COLUMNS, RipsCategory
from app.processors.rips_normalizer import normalize

TX = {"1": {"invoice": "F1", "contract": "CNT-1", "nit_provider": "900", "provider_code": "12"}}


def detail(**kw):
    base = {"Id": "7", "CodigoTransaccion": "1", "CodigoUsuario": "U", "CodigoTecnologia": "890201",
            "Descripcion": None, "Valor": "15000.50", "TipoTecnologia": None,
            "NumeroUnidad": None, "FechaServicio": date(2026, 8, 1)}
    return {**base, **kw}


def test_preserves_codes_and_nulls_without_inventing_data():
    result = normalize(RipsCategory.CONSULTA, [detail()], TX)
    row = result.rows[0]
    assert tuple(row)[:13] == NORMALIZED_COLUMNS
    assert row["CodigoTecnologia"] == "890201"
    assert row["Descripcion"] is None and row["FechaFactura"] is None
    assert row["Valor"] == "15000.50" and row["FechaServicio"] == "2026-08-01"
    assert row["Tipo"] == "consulta" and row["Factura"] == "F1"


def test_orphans_and_invalid_numbers_are_counted():
    result = normalize(RipsCategory.INSUMO, [detail(CodigoTransaccion="99"), detail(Valor="abc")], TX)
    assert result.orphans == 1 and result.invalid_numbers == 1
    assert result.rows[0]["Valor"] is None