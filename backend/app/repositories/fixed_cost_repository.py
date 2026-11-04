"""Acceso de lectura a la fuente histórica Base Montos Fijos.

El archivo se utiliza para periodos anteriores al corte configurado. La ruta
se recibe desde Settings para no depender de rutas absolutas de un analista.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
import re

import pandas as pd

from app.core.errors import AppError


_REQUIRED_COLUMNS = (
    "Nit",
    "Contrato",
    "Prefijo",
    "Factura",
    "MesdeServicio",
    "ValorFacturaRadicada",
)


def _clean_identifier(value: object) -> str:
    """Normaliza identificadores de Excel sin convertirlos a notación científica."""
    if value is None or pd.isna(value):
        return ""

    text = str(value).strip().replace("\u00a0", "")
    if text.lower() in {"nan", "none", "nat"}:
        return ""

    if re.fullmatch(r"\d+\.0", text):
        text = text[:-2]

    return text


def _parse_service_month(value: object) -> date | None:
    """Convierte fechas Excel y representaciones YYYY-MM / YYYYMM a una fecha."""
    if value is None or pd.isna(value):
        return None

    if isinstance(value, (datetime, date, pd.Timestamp)):
        return date(value.year, value.month, 1)

    text = str(value).strip()
    if not text:
        return None

    try:
        if re.fullmatch(r"\d{6}", text):
            parsed = datetime.strptime(text, "%Y%m")
        elif re.fullmatch(r"\d{4}-\d{2}", text):
            parsed = datetime.strptime(text, "%Y-%m")
        else:
            parsed = pd.to_datetime(text, errors="raise").to_pydatetime()
        return date(parsed.year, parsed.month, 1)
    except (ValueError, TypeError, OverflowError):
        return None


def _parse_amount(value: object) -> Decimal | None:
    """Interpreta importes numéricos y formatos habituales de Excel en español."""
    if value is None or pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    text = re.sub(r"[^0-9,.\-]", "", text)
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        if re.fullmatch(r"-?\d{1,3}(,\d{3})+", text):
            text = text.replace(",", "")
        else:
            text = text.replace(",", ".")
    elif text.count(".") > 1:
        # Varios puntos sin coma suelen representar separadores de miles.
        text = text.replace(".", "")
    elif "." in text:
        # Un único punto seguido de tres dígitos suele ser un separador de miles.
        integer, decimal = text.split(".", maxsplit=1)
        if len(decimal) == 3 and integer.lstrip("-").isdigit():
            text = integer + decimal

    try:
        return Decimal(text)
    except InvalidOperation:
        return None


@lru_cache(maxsize=4)
def _read_cached_file(path_text: str, modified_ns: int) -> pd.DataFrame:
    """Lee el Excel una vez por versión del archivo; la caché se invalida por mtime."""
    del modified_ns

    try:
        frame = pd.read_excel(
            Path(path_text),
            sheet_name=0,
            dtype=str,
            engine="openpyxl",
        )
    except Exception as exc:
        raise AppError(
            "fixed_cost_file_invalid",
            "No fue posible leer Base Montos Fijos. Verifica el archivo y su hoja inicial.",
            500,
        ) from exc

    frame.columns = frame.columns.astype(str).str.strip()
    missing = [column for column in _REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise AppError(
            "fixed_cost_columns_missing",
            "Base Montos Fijos no contiene todas las columnas requeridas.",
            500,
        )

    frame = frame.loc[:, list(_REQUIRED_COLUMNS)].copy()
    frame["nit_provider"] = frame["Nit"].map(_clean_identifier)
    frame["contract"] = frame["Contrato"].map(_clean_identifier)
    prefix = frame["Prefijo"].map(_clean_identifier)
    invoice_number = frame["Factura"].map(_clean_identifier)
    frame["invoice"] = prefix + invoice_number
    frame["service_month"] = pd.to_datetime(
        frame["MesdeServicio"].map(_parse_service_month),
        errors="coerce",
    )
    frame["billed_amount"] = frame["ValorFacturaRadicada"].map(_parse_amount)

    frame = frame.loc[
        (frame["nit_provider"] != "")
        & (frame["contract"] != "")
        & (frame["invoice"] != "")
        & frame["service_month"].notna()
    ]
    frame = frame.drop_duplicates(
        subset=["nit_provider", "contract", "invoice"],
        keep="first",
    )

    return frame.reset_index(drop=True)


class FixedCostRepository:
    """Repositorio para consultar la base histórica de costos fijos."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def _load(self) -> pd.DataFrame:
        if not self.file_path.is_file():
            raise AppError(
                "fixed_cost_file_missing",
                (
                    "No se encontró BaseMontosFijos2026.xlsx. "
                    "Ubícalo en resources/inputs o configura ACTUARIA_FIXED_COSTS_FILE."
                ),
                503,
            )

        try:
            modified_ns = self.file_path.stat().st_mtime_ns
        except OSError as exc:
            raise AppError(
                "fixed_cost_file_unavailable",
                "No fue posible acceder al archivo Base Montos Fijos.",
                503,
            ) from exc

        return _read_cached_file(str(self.file_path.resolve()), modified_ns).copy()

    @staticmethod
    def invoice_keys(self) -> set[tuple[str, str, str]]:
        """Devuelve las claves naturales de facturas incluidas en Montos Fijos.

        La tupla se ordena como (NIT, contrato, número de factura), igual que
        la clave que se utiliza para identificar una factura en la interfaz.
        """
        frame = self._load()
        return set(
            zip(
                frame["nit_provider"].astype(str),
                frame["contract"].astype(str),
                frame["invoice"].astype(str),
            )
        )

    def contains_invoice(
        self,
        invoice: str,
        provider_nit: str,
        contract: str,
    ) -> bool:
        """Indica si la factura ya existe en la fuente de costos fijos."""
        return (
            provider_nit.strip(),
            contract.strip(),
            invoice.strip(),
        ) in self.invoice_keys()

    @staticmethod
    def _filter(
        frame: pd.DataFrame,
        *,
        contract: str | None = None,
        provider_nit: str | None = None,
        invoice: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        if contract:
            frame = frame.loc[frame["contract"] == contract.strip()]
        if provider_nit:
            frame = frame.loc[frame["nit_provider"] == provider_nit.strip()]
        if invoice:
            frame = frame.loc[
                frame["invoice"].str.contains(
                    invoice.strip(), case=False, na=False, regex=False
                )
            ]
        if start_date:
            month_start = date(start_date.year, start_date.month, 1)
            frame = frame.loc[frame["service_month"] >= pd.Timestamp(month_start)]
        if end_date:
            month_end = date(end_date.year, end_date.month, 1)
            frame = frame.loc[frame["service_month"] <= pd.Timestamp(month_end)]

        return frame.sort_values(
            ["service_month", "invoice"],
            ascending=[False, True],
        )

    def count(self, **filters: object) -> int:
        """Retorna el total de facturas que cumplen los filtros."""
        return len(self._filter(self._load(), **filters))

    def search(self, offset: int, limit: int, **filters: object) -> list[dict]:
        """Obtiene una página de facturas históricas."""
        frame = self._filter(self._load(), **filters)
        selected = frame.iloc[offset : offset + limit]
        records: list[dict] = []

        for row in selected.itertuples(index=False):
            records.append(
                {
                    "invoice": row.invoice,
                    "nit_provider": row.nit_provider,
                    "provider_name": None,
                    "contract": row.contract,
                    "period_reference": row.service_month.date(),
                    "invoice_date": None,
                    "filing_date": None,
                    "billed_amount": row.billed_amount,
                    "source": "base_fixed",
                }
            )

        return records

    def find_one(
        self,
        invoice: str,
        provider_nit: str,
        contract: str,
    ) -> dict | None:
        """Busca una factura por su clave natural exacta."""
        frame = self._load()
        frame = frame.loc[
            (frame["invoice"] == invoice.strip())
            & (frame["nit_provider"] == provider_nit.strip())
            & (frame["contract"] == contract.strip())
        ]
        if frame.empty:
            return None

        row = frame.sort_values("service_month", ascending=False).iloc[0]
        return {
            "invoice": row["invoice"],
            "nit_provider": row["nit_provider"],
            "provider_name": None,
            "contract": row["contract"],
            "period_reference": row["service_month"].date(),
            "invoice_date": None,
            "filing_date": None,
            "billed_amount": row["billed_amount"],
            "source": "base_fixed",
        }

    def list_contracts(self, search: str | None = None) -> list[str]:
        frame = self._load()
        values = frame["contract"].dropna().unique().tolist()
        if search:
            needle = search.strip().casefold()
            values = [value for value in values if needle in value.casefold()]
        return sorted(values, key=str.casefold)

    def list_providers(self, contract: str | None = None) -> list[str]:
        frame = self._load()
        if contract:
            frame = frame.loc[frame["contract"] == contract.strip()]
        return sorted(frame["nit_provider"].dropna().unique().tolist(), key=str.casefold)
