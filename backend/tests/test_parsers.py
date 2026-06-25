import json
import os
from pathlib import Path
from uuid import UUID

import pytest

from app.parsers import (
    B3AnnualConsolidatedXlsxParser,
    B3MonthlyConsolidatedXlsxParser,
    MercadoLivreAccountStatementCsvParser,
    MercadoLivreManualCdbCsvParser,
    ParserError,
    SicoobCardInvoicePdfParser,
    SicoobCheckingStatementPdfParser,
    SicoobInvestmentsPdfParser,
    SicoobPayrollPdfParser,
)

IMPORT_BATCH_ID = UUID("00000000-0000-0000-0000-000000000001")
SOURCE_FILE_ID = UUID("00000000-0000-0000-0000-000000000002")


def fixture_path(relative_path: str) -> Path:
    return Path(os.getenv("FIXTURES_PATH", "fixtures")) / relative_path


def expected_payload(relative_path: str) -> dict:
    with fixture_path(relative_path).open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


@pytest.mark.parametrize(
    ("parser", "fixture", "expected"),
    (
        (
            MercadoLivreAccountStatementCsvParser(),
            "anonymized/mercado_livre/account_statement_sample.csv",
            "expected/mercado_livre_account_statement_expected.json",
        ),
        (
            MercadoLivreManualCdbCsvParser(),
            "anonymized/mercado_livre/cdb_position_sample.csv",
            "expected/cdb_position_expected.json",
        ),
        (
            B3MonthlyConsolidatedXlsxParser(),
            "anonymized/b3/relatorio-consolidado-mensal-sample.xlsx",
            "expected/b3_monthly_expected.json",
        ),
        (
            B3AnnualConsolidatedXlsxParser(),
            "anonymized/b3/relatorio-consolidado-anual-sample.xlsx",
            "expected/b3_annual_expected.json",
        ),
        (
            SicoobPayrollPdfParser(),
            "anonymized/sicoob/contracheque_sample.pdf",
            "expected/sicoob_payroll_expected.json",
        ),
        (
            SicoobCheckingStatementPdfParser(),
            "anonymized/sicoob/extrato_conta_sample.pdf",
            "expected/sicoob_checking_statement_expected.json",
        ),
        (
            SicoobCardInvoicePdfParser(),
            "anonymized/sicoob/fatura_cartao_sample.pdf",
            "expected/sicoob_card_invoice_expected.json",
        ),
        (
            SicoobInvestmentsPdfParser(),
            "anonymized/sicoob/investimentos_sicoob_sample.pdf",
            "expected/sicoob_investments_expected.json",
        ),
    ),
)
def test_parser_matches_expected_golden_file(parser, fixture: str, expected: str) -> None:
    document = parser.parse(
        fixture_path(fixture),
        import_batch_id=IMPORT_BATCH_ID,
        source_file_id=SOURCE_FILE_ID,
    )

    assert document.to_expected_payload() == expected_payload(expected)
    assert document.import_batch_id == IMPORT_BATCH_ID
    assert document.source_file_id == SOURCE_FILE_ID
    assert document.records

    for record in document.records:
        assert record.source_type == document.source_type
        assert record.import_batch_id == IMPORT_BATCH_ID
        assert record.source_file_id == SOURCE_FILE_ID
        assert record.confidence_score > 0
        assert record.needs_review is False
        assert record.raw_reference


def test_parser_failure_is_controlled(tmp_path: Path) -> None:
    invalid_file = tmp_path / "account_statement_sample.csv"
    invalid_file.write_text("not;the;expected;format\n", encoding="utf-8")

    parser = MercadoLivreAccountStatementCsvParser()

    with pytest.raises(ParserError) as exc:
        parser.parse(invalid_file, import_batch_id=IMPORT_BATCH_ID)

    assert exc.value.code == "invalid_mercado_livre_csv"
    assert exc.value.to_dict()["message"]


def test_parser_error_masks_sensitive_raw_reference() -> None:
    error = ParserError(
        "invalid_pdf",
        "Falha ao ler CPF 123.456.789-09",
        raw_reference={
            "raw_text": "CPF 123.456.789-09 Conta 12345-6 Rua Exemplo, 100",
        },
    )

    payload = error.to_dict()

    assert "123.456.789-09" not in str(payload)
    assert "12345-6" not in str(payload)
    assert "Rua Exemplo" not in str(payload)
    assert "***.***.***-**" in str(payload)
    assert "<mascarado>" in str(payload)
    assert "<endereco mascarado>" in str(payload)
