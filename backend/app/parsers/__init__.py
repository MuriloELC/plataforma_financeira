"""Parser package reserved for later ingestion phases."""
from app.parsers.b3 import B3AnnualConsolidatedXlsxParser, B3MonthlyConsolidatedXlsxParser
from app.parsers.base import ParsedDocument, ParsedRecord, ParserError, ParserProtocol
from app.parsers.mercado_livre import (
    MercadoLivreAccountStatementCsvParser,
    MercadoLivreManualCdbCsvParser,
)
from app.parsers.sicoob import (
    SicoobCardInvoicePdfParser,
    SicoobCheckingStatementPdfParser,
    SicoobInvestmentsPdfParser,
    SicoobPayrollPdfParser,
)

__all__ = [
    "B3AnnualConsolidatedXlsxParser",
    "B3MonthlyConsolidatedXlsxParser",
    "MercadoLivreAccountStatementCsvParser",
    "MercadoLivreManualCdbCsvParser",
    "ParsedDocument",
    "ParsedRecord",
    "ParserError",
    "ParserProtocol",
    "SicoobCardInvoicePdfParser",
    "SicoobCheckingStatementPdfParser",
    "SicoobInvestmentsPdfParser",
    "SicoobPayrollPdfParser",
]
