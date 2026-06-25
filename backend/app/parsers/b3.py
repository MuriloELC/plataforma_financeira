from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from openpyxl import load_workbook
from openpyxl.workbook.workbook import Workbook

from app.parsers.base import ParsedDocument, ParserError, make_record
from app.parsers.utils import normalize_text, parse_date, parse_decimal


class _B3BaseParser:
    supported_extensions = {".xlsx"}

    def detect(self, file_path: Path, metadata: dict[str, Any] | None = None) -> bool:
        del metadata
        return file_path.suffix.lower() == ".xlsx"

    def _load_workbook(self, file_path: Path) -> Workbook:
        return load_workbook(filename=file_path, read_only=True, data_only=True)

    def _parse_positions(
        self,
        *,
        workbook: Workbook,
        import_batch_id: UUID,
        source_file_id: UUID | None,
    ) -> tuple[dict[str, Decimal], list[Any]]:
        totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        records = []

        for worksheet in workbook.worksheets:
            asset_class = self._asset_class_for_sheet(worksheet.title)
            if asset_class is None:
                continue

            rows = list(worksheet.iter_rows(values_only=True))
            if not rows:
                continue
            header = [str(value) if value is not None else "" for value in rows[0]]
            value_index = self._value_index(header)

            for row_number, row in enumerate(rows[1:], start=2):
                product = row[0] if row else None
                if product in (None, ""):
                    continue
                amount = parse_decimal(row[value_index])
                totals[asset_class] += amount
                data = {
                    "asset_class": asset_class,
                    "product": str(product),
                    "institution": str(row[1]) if len(row) > 1 and row[1] is not None else None,
                    "amount": amount,
                }
                records.append(
                    make_record(
                        source_type=self.source_type,
                        import_batch_id=import_batch_id,
                        source_file_id=source_file_id,
                        data=data,
                        raw_reference={"sheet_name": worksheet.title, "raw_row": row_number},
                    )
                )

        return dict(totals), records

    def _parse_income(
        self,
        *,
        workbook: Workbook,
        import_batch_id: UUID,
        source_file_id: UUID | None,
    ) -> tuple[Decimal, list[Any], list[date]]:
        worksheet = workbook["Proventos Recebidos"] if "Proventos Recebidos" in workbook.sheetnames else None
        if worksheet is None:
            return Decimal("0"), [], []

        rows = list(worksheet.iter_rows(values_only=True))
        records = []
        dates = []
        total = Decimal("0")
        for row_number, row in enumerate(rows[1:], start=2):
            if not row or row[0] in (None, ""):
                continue
            payment_date = parse_date(str(row[1]))
            amount = parse_decimal(row[6])
            total += amount
            dates.append(payment_date)
            records.append(
                make_record(
                    source_type=self.source_type,
                    import_batch_id=import_batch_id,
                    source_file_id=source_file_id,
                    data={
                        "record_type": "income",
                        "product": str(row[0]),
                        "payment_date": payment_date.isoformat(),
                        "income_type": str(row[2]),
                        "net_amount": amount,
                    },
                    raw_reference={"sheet_name": worksheet.title, "raw_row": row_number},
                )
            )
        return total, records, dates

    def _parse_trades(
        self,
        *,
        workbook: Workbook,
        import_batch_id: UUID,
        source_file_id: UUID | None,
    ) -> tuple[int, list[Any], list[date]]:
        worksheet = workbook["Negociações"] if "Negociações" in workbook.sheetnames else None
        if worksheet is None:
            return 0, [], []

        rows = list(worksheet.iter_rows(values_only=True))
        records = []
        dates = []
        for row_number, row in enumerate(rows[1:], start=2):
            if not row or row[0] in (None, ""):
                continue
            trade_date = parse_date(str(row[1]))
            dates.append(trade_date)
            records.append(
                make_record(
                    source_type=self.source_type,
                    import_batch_id=import_batch_id,
                    source_file_id=source_file_id,
                    data={
                        "record_type": "trade",
                        "ticker": str(row[0]),
                        "trade_date": trade_date.isoformat(),
                        "institution": str(row[3]),
                        "buy_quantity": parse_decimal(row[4]),
                        "sell_quantity": parse_decimal(row[5]),
                        "net_quantity": parse_decimal(row[6]),
                    },
                    raw_reference={"sheet_name": worksheet.title, "raw_row": row_number},
                )
            )
        return len(records), records, dates

    def _asset_class_for_sheet(self, sheet_name: str) -> str | None:
        normalized = normalize_text(sheet_name)
        if "renda fixa" in normalized:
            return "renda_fixa"
        if "etf" in normalized:
            return "etf"
        if "posicao" in normalized and "acoes" in normalized:
            return "acao"
        return None

    def _value_index(self, header: list[str]) -> int:
        normalized = [normalize_text(value) for value in header]
        for candidate in ("valor atualizado curva", "valor atualizado mtm", "valor atualizado"):
            if candidate in normalized:
                return normalized.index(candidate)
        raise ParserError("missing_b3_value_column", "B3 value column was not found.")


class B3MonthlyConsolidatedXlsxParser(_B3BaseParser):
    source_type = "b3_monthly_consolidated_xlsx"

    def parse(
        self,
        file_path: Path,
        import_batch_id: UUID,
        source_file_id: UUID | None = None,
    ) -> ParsedDocument:
        workbook = self._load_workbook(file_path)
        try:
            positions_by_class, position_records = self._parse_positions(
                workbook=workbook,
                import_batch_id=import_batch_id,
                source_file_id=source_file_id,
            )
            income_total, income_records, income_dates = self._parse_income(
                workbook=workbook,
                import_batch_id=import_batch_id,
                source_file_id=source_file_id,
            )
            trades_count, trade_records, trade_dates = self._parse_trades(
                workbook=workbook,
                import_batch_id=import_batch_id,
                source_file_id=source_file_id,
            )
        finally:
            workbook.close()

        reference_date = max(income_dates + trade_dates) if income_dates or trade_dates else None
        if reference_date is None:
            raise ParserError("missing_b3_reference_month", "B3 monthly report has no date reference.")

        return ParsedDocument(
            source_type=self.source_type,
            import_batch_id=import_batch_id,
            source_file_id=source_file_id,
            payload={
                "reference_month": f"{reference_date.year:04d}-{reference_date.month:02d}",
                "positions_by_class": positions_by_class,
                "income_received_total": income_total,
                "trades_count": trades_count,
                "rules": {
                    "b3_is_official_for_listed_assets": True,
                    "b3_fixed_income_counts_as_reserve": False,
                },
            },
            records=[*position_records, *income_records, *trade_records],
            raw_reference={"file_path": str(file_path)},
        )


class B3AnnualConsolidatedXlsxParser(_B3BaseParser):
    source_type = "b3_annual_consolidated_xlsx"

    def parse(
        self,
        file_path: Path,
        import_batch_id: UUID,
        source_file_id: UUID | None = None,
    ) -> ParsedDocument:
        workbook = self._load_workbook(file_path)
        try:
            positions_by_class, position_records = self._parse_positions(
                workbook=workbook,
                import_batch_id=import_batch_id,
                source_file_id=source_file_id,
            )
            created = workbook.properties.created
        finally:
            workbook.close()

        reference_year = str((created.year - 1) if created else date.today().year - 1)
        return ParsedDocument(
            source_type=self.source_type,
            import_batch_id=import_batch_id,
            source_file_id=source_file_id,
            payload={
                "reference_year": reference_year,
                "positions_by_class": positions_by_class,
                "rules": {"annual_report_is_snapshot": True},
            },
            records=position_records,
            raw_reference={"file_path": str(file_path)},
        )
