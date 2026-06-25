from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import unicodedata

from pypdf import PdfReader

from app.parsers.base import ParserError

MONEY_PATTERN = re.compile(r"-?\d{1,3}(?:[.,]\d{3})*[.,]\d{2}|-?\d+[.,]\d{2}")

MONTHS = {
    "jan": 1,
    "janeiro": 1,
    "fev": 2,
    "fevereiro": 2,
    "mar": 3,
    "marco": 3,
    "abr": 4,
    "abril": 4,
    "mai": 5,
    "maio": 5,
    "jun": 6,
    "junho": 6,
    "jul": 7,
    "julho": 7,
    "ago": 8,
    "agosto": 8,
    "set": 9,
    "setembro": 9,
    "out": 10,
    "outubro": 10,
    "nov": 11,
    "novembro": 11,
    "dez": 12,
    "dezembro": 12,
}


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii").lower()


def parse_decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))

    text = str(value).strip()
    cleaned = re.sub(r"[^0-9,.\-]", "", text)
    if cleaned in ("", "-"):
        raise ParserError("invalid_decimal", "Could not parse decimal value.")

    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")

    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ParserError("invalid_decimal", "Could not parse decimal value.") from exc


def parse_signed_money(value: str) -> Decimal:
    text = value.strip()
    normalized = normalize_text(text)
    multiplier = Decimal("-1") if normalized.endswith("d") else Decimal("1")
    amount = parse_decimal(text)
    if multiplier < 0 and amount > 0:
        return -amount
    return amount


def money_tokens(value: str) -> list[str]:
    return MONEY_PATTERN.findall(value)


def last_money(value: str) -> Decimal:
    tokens = money_tokens(value)
    if not tokens:
        raise ParserError("missing_money", "Could not find monetary value.")
    return parse_decimal(tokens[-1])


def parse_date(value: str, *, default_year: int | None = None) -> date:
    text = value.strip()
    for pattern in ("%d/%m/%Y", "%d-%m-%Y"):
        try:
            return date.fromisoformat(_to_iso_date(text, pattern))
        except ValueError:
            pass

    match = re.fullmatch(r"(\d{2})/(\d{2})/(\d{2})", text)
    if match:
        day, month, year = match.groups()
        return date(2000 + int(year), int(month), int(day))

    match = re.fullmatch(r"(\d{2})/(\d{2})", text)
    if match and default_year is not None:
        day, month = match.groups()
        return date(default_year, int(month), int(day))

    match = re.fullmatch(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", normalize_text(text))
    if match:
        day, month_name, year = match.groups()
        month = MONTHS.get(month_name)
        if month is None:
            raise ParserError("invalid_date", "Could not parse date value.")
        return date(int(year), month, int(day))

    raise ParserError("invalid_date", "Could not parse date value.")


def parse_month_year(value: str) -> str:
    match = re.fullmatch(r"(\d{2})/(\d{4})", value.strip())
    if not match:
        raise ParserError("invalid_month", "Could not parse month value.")
    month, year = match.groups()
    return f"{year}-{month}"


def read_pdf_text(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def non_empty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _to_iso_date(text: str, pattern: str) -> str:
    day_index = pattern.index("%d")
    month_index = pattern.index("%m")
    year_index = pattern.index("%Y")
    day = text[day_index : day_index + 2]
    month = text[month_index : month_index + 2]
    year = text[year_index : year_index + 4]
    return f"{year}-{month}-{day}"
