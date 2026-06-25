import pytest

from app.services.source_detection import detect_source


@pytest.mark.parametrize(
    ("filename", "source_type", "institution"),
    (
        ("account_statement_sample.csv", "mercado_livre_account_statement_csv", "mercado_livre"),
        ("cdb_position_sample.csv", "mercado_livre_manual_cdb_csv", "mercado_livre"),
        ("manual_investments.csv", "manual_investment_csv", None),
        ("relatorio-consolidado-mensal-sample.xlsx", "b3_monthly_consolidated_xlsx", "b3"),
        ("relatorio-consolidado-anual-sample.xlsx", "b3_annual_consolidated_xlsx", "b3"),
        ("contracheque_sample.pdf", "sicoob_payroll_pdf", "sicoob"),
        ("extrato_conta_sample.pdf", "sicoob_checking_statement_pdf", "sicoob"),
        ("fatura_cartao_sample.pdf", "sicoob_card_invoice_pdf", "sicoob"),
        ("investimentos_sicoob_sample.pdf", "sicoob_investments_pdf", "sicoob"),
    ),
)
def test_detect_source_for_mvp_fixtures(
    filename: str,
    source_type: str,
    institution: str | None,
) -> None:
    detection = detect_source(filename)

    assert detection.source_type == source_type
    assert detection.detected_institution == institution
