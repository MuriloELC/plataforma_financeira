from __future__ import annotations

from app.parsers.b3 import B3AnnualConsolidatedXlsxParser, B3MonthlyConsolidatedXlsxParser
from app.parsers.base import ParserProtocol
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

PARSER_BY_SOURCE_TYPE: dict[str, type[ParserProtocol]] = {
    "mercado_livre_account_statement_csv": MercadoLivreAccountStatementCsvParser,
    "mercado_livre_manual_cdb_csv": MercadoLivreManualCdbCsvParser,
    "manual_investment_csv": MercadoLivreManualCdbCsvParser,
    "b3_monthly_consolidated_xlsx": B3MonthlyConsolidatedXlsxParser,
    "b3_annual_consolidated_xlsx": B3AnnualConsolidatedXlsxParser,
    "sicoob_payroll_pdf": SicoobPayrollPdfParser,
    "sicoob_checking_statement_pdf": SicoobCheckingStatementPdfParser,
    "sicoob_card_invoice_pdf": SicoobCardInvoicePdfParser,
    "sicoob_investments_pdf": SicoobInvestmentsPdfParser,
}


def parser_for_source_type(source_type: str) -> ParserProtocol | None:
    parser_class = PARSER_BY_SOURCE_TYPE.get(source_type)
    return parser_class() if parser_class is not None else None
