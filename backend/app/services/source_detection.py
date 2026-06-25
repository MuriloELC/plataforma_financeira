from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import unicodedata

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".pdf"}


@dataclass(frozen=True)
class SourceDetection:
    source_type: str
    detected_institution: str | None


def normalize_filename(filename: str) -> str:
    normalized = unicodedata.normalize("NFKD", filename)
    return normalized.encode("ascii", "ignore").decode("ascii").lower()


def detect_source(filename: str, mime_type: str | None = None) -> SourceDetection:
    del mime_type
    name = normalize_filename(filename)
    extension = Path(filename).suffix.lower()

    if extension == ".csv":
        if "cdb" in name or "position" in name:
            return SourceDetection(
                source_type="mercado_livre_manual_cdb_csv",
                detected_institution="mercado_livre",
            )
        if "manual" in name or "invest" in name:
            return SourceDetection(
                source_type="manual_investment_csv",
                detected_institution=None,
            )
        return SourceDetection(
            source_type="mercado_livre_account_statement_csv",
            detected_institution="mercado_livre",
        )

    if extension == ".xlsx":
        if "anual" in name or "annual" in name:
            return SourceDetection(
                source_type="b3_annual_consolidated_xlsx",
                detected_institution="b3",
            )
        return SourceDetection(
            source_type="b3_monthly_consolidated_xlsx",
            detected_institution="b3",
        )

    if extension == ".pdf":
        if "contracheque" in name or "payroll" in name:
            return SourceDetection(source_type="sicoob_payroll_pdf", detected_institution="sicoob")
        if "fatura" in name or "cartao" in name or "card" in name:
            return SourceDetection(
                source_type="sicoob_card_invoice_pdf",
                detected_institution="sicoob",
            )
        if "invest" in name:
            return SourceDetection(
                source_type="sicoob_investments_pdf",
                detected_institution="sicoob",
            )
        if "extrato" in name or "conta" in name or "checking" in name:
            return SourceDetection(
                source_type="sicoob_checking_statement_pdf",
                detected_institution="sicoob",
            )
        return SourceDetection(source_type="sicoob_pdf_unknown", detected_institution="sicoob")

    return SourceDetection(source_type="unsupported", detected_institution=None)
