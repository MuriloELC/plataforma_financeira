from __future__ import annotations

import csv
from pathlib import Path
from typing import Any
from uuid import UUID

from app.parsers.base import ParsedDocument, ParserError, make_record
from app.parsers.utils import normalize_text, parse_date, parse_decimal


class MercadoLivreAccountStatementCsvParser:
    source_type = "mercado_livre_account_statement_csv"
    supported_extensions = {".csv"}

    def detect(self, file_path: Path, metadata: dict[str, Any] | None = None) -> bool:
        del metadata
        name = normalize_text(file_path.name)
        return file_path.suffix.lower() == ".csv" and "cdb" not in name and "position" not in name

    def parse(
        self,
        file_path: Path,
        import_batch_id: UUID,
        source_file_id: UUID | None = None,
    ) -> ParsedDocument:
        rows = self._read_rows(file_path)
        if len(rows) < 5:
            raise ParserError("invalid_mercado_livre_csv", "Mercado Livre CSV has too few rows.")

        summary = self._parse_summary(rows)
        header_index = self._find_header(rows, "RELEASE_DATE")
        records = []
        canonical_rows: list[dict[str, Any]] = []

        for index, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
            if len(row) < 5 or not row[0].strip():
                continue
            amount = parse_decimal(row[3])
            description = row[1].strip()
            data = {
                "date": parse_date(row[0]).isoformat(),
                "type": self._classify_transaction(description, amount),
                "description": description,
                "amount": amount,
                "partial_balance": parse_decimal(row[4]),
            }
            canonical_rows.append(data)
            records.append(
                make_record(
                    source_type=self.source_type,
                    import_batch_id=import_batch_id,
                    source_file_id=source_file_id,
                    data=data,
                    raw_reference={"raw_row": index, "raw_text": ";".join(row)},
                )
            )

        if not canonical_rows:
            raise ParserError("empty_mercado_livre_csv", "Mercado Livre CSV has no transactions.")

        payload = {
            "summary": summary,
            "records_count": len(canonical_rows),
            "sample_records": self._sample_records(canonical_rows),
        }
        return ParsedDocument(
            source_type=self.source_type,
            import_batch_id=import_batch_id,
            source_file_id=source_file_id,
            payload=payload,
            records=records,
            raw_reference={"file_path": str(file_path)},
        )

    def _read_rows(self, file_path: Path) -> list[list[str]]:
        with file_path.open("r", encoding="utf-8-sig", newline="") as file_handle:
            return list(csv.reader(file_handle, delimiter=";"))

    def _parse_summary(self, rows: list[list[str]]) -> dict[str, Any]:
        if rows[0][:4] != ["INITIAL_BALANCE", "CREDITS", "DEBITS", "FINAL_BALANCE"]:
            raise ParserError("invalid_mercado_livre_summary", "Mercado Livre summary header is invalid.")
        values = rows[1]
        return {
            "initial_balance": parse_decimal(values[0]),
            "credits": parse_decimal(values[1]),
            "debits": parse_decimal(values[2]),
            "final_balance": parse_decimal(values[3]),
        }

    def _find_header(self, rows: list[list[str]], column_name: str) -> int:
        for index, row in enumerate(rows):
            if row and row[0] == column_name:
                return index
        raise ParserError("missing_mercado_livre_header", "Mercado Livre transaction header was not found.")

    def _classify_transaction(self, description: str, amount: object) -> str:
        normalized = normalize_text(description)
        if "rendimento" in normalized:
            return "financial_yield"
        if parse_decimal(amount) < 0:
            return "payment"
        return "credit"

    def _sample_records(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        payment = next(record for record in records if record["type"] == "payment")
        yield_record = next(record for record in records if record["type"] == "financial_yield")
        return [payment, yield_record]


class MercadoLivreManualCdbCsvParser:
    source_type = "manual_investment_csv"
    supported_extensions = {".csv"}

    def detect(self, file_path: Path, metadata: dict[str, Any] | None = None) -> bool:
        del metadata
        name = normalize_text(file_path.name)
        return file_path.suffix.lower() == ".csv" and ("cdb" in name or "position" in name)

    def parse(
        self,
        file_path: Path,
        import_batch_id: UUID,
        source_file_id: UUID | None = None,
    ) -> ParsedDocument:
        with file_path.open("r", encoding="utf-8-sig", newline="") as file_handle:
            rows = list(csv.DictReader(file_handle))

        if not rows:
            raise ParserError("empty_manual_investment_csv", "Manual investment CSV has no positions.")

        records = []
        positions = []
        for index, row in enumerate(rows, start=2):
            data = {
                "institution": "Mercado Livre",
                "product": row["produto"].strip(),
                "asset_class": normalize_text(row["tipo"]).strip(),
                "gross_value": parse_decimal(row["saldo"]),
                "accumulated_yield": parse_decimal(row["rendimento_acumulado"]),
                "rate": row["taxa"].strip(),
                "liquidity": self._parse_liquidity(row["resgate"]),
                "maturity_date": parse_date(row["vencimento"]).isoformat(),
                "counts_as_reserve": True,
            }
            positions.append(data)
            records.append(
                make_record(
                    source_type=self.source_type,
                    import_batch_id=import_batch_id,
                    source_file_id=source_file_id,
                    data=data,
                    raw_reference={"raw_row": index, "raw_row_payload": row},
                )
            )

        return ParsedDocument(
            source_type=self.source_type,
            import_batch_id=import_batch_id,
            source_file_id=source_file_id,
            payload={"positions": positions},
            records=records,
            raw_reference={"file_path": str(file_path)},
        )

    def _parse_liquidity(self, value: str) -> str:
        normalized = normalize_text(value)
        if "mesmo dia" in normalized or "same day" in normalized:
            return "same_day"
        return "unknown"
