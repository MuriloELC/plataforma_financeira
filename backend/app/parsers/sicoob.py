from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import re
from typing import Any
from uuid import UUID

from app.parsers.base import ParsedDocument, ParserError, make_record
from app.parsers.utils import (
    last_money,
    money_tokens,
    non_empty_lines,
    normalize_text,
    parse_date,
    parse_decimal,
    parse_month_year,
    parse_signed_money,
    read_pdf_text,
)


class _SicoobPdfParser:
    supported_extensions = {".pdf"}

    def detect(self, file_path: Path, metadata: dict[str, Any] | None = None) -> bool:
        del metadata
        return file_path.suffix.lower() == ".pdf"

    def _lines(self, file_path: Path) -> list[str]:
        return non_empty_lines(read_pdf_text(file_path))

    def _line_containing(self, lines: list[str], label: str) -> str:
        normalized_label = normalize_text(label)
        for line in lines:
            if normalized_label in normalize_text(line):
                return line
        raise ParserError("missing_pdf_line", f"Could not find PDF line for {label}.")


class SicoobPayrollPdfParser(_SicoobPdfParser):
    source_type = "sicoob_payroll_pdf"

    def parse(
        self,
        file_path: Path,
        import_batch_id: UUID,
        source_file_id: UUID | None = None,
    ) -> ParsedDocument:
        lines = self._lines(file_path)
        competence_month = self._competence_month(lines)
        payment_date = self._payment_date(lines)
        earnings, deductions, records = self._items(lines, import_batch_id, source_file_id)

        payload = {
            "competence_month": competence_month,
            "payment_date": payment_date,
            "gross_income": self._summary_amount(lines, "Total de Vencimentos"),
            "net_income": self._summary_amount(lines, "Liquido a Receber"),
            "total_deductions": self._summary_amount(lines, "Total de Descontos"),
            "fgts_amount": self._summary_amount(lines, "FGTS do Mes"),
            "earnings": earnings,
            "deductions": deductions,
        }
        return ParsedDocument(
            source_type=self.source_type,
            import_batch_id=import_batch_id,
            source_file_id=source_file_id,
            payload=payload,
            records=records,
            raw_reference={"file_path": str(file_path)},
        )

    def _competence_month(self, lines: list[str]) -> str:
        for index, line in enumerate(lines):
            if normalize_text(line) == "mes/ano" and index + 1 < len(lines):
                return parse_month_year(lines[index + 1])
        raise ParserError("missing_payroll_competence", "Payroll competence month was not found.")

    def _payment_date(self, lines: list[str]) -> str:
        for line in lines:
            match = re.search(r"\d{2}/\d{2}/\d{4}", line)
            if match and "conta" not in normalize_text(line):
                return parse_date(match.group(0)).isoformat()
            if match and "data pagamento" not in normalize_text(line):
                return parse_date(match.group(0)).isoformat()
        raise ParserError("missing_payroll_payment_date", "Payroll payment date was not found.")

    def _items(
        self,
        lines: list[str],
        import_batch_id: UUID,
        source_file_id: UUID | None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Any]]:
        earnings = []
        deductions = []
        records = []
        pattern = re.compile(r"^\d{4} - (?P<description>.+?) (?P<reference>\d+,\d{2}) (?P<amount>[\d.]+,\d{2})(?P<kind>[CD])$")
        for index, line in enumerate(lines, start=1):
            match = pattern.match(line)
            if not match:
                continue
            data = {
                "description": match.group("description").strip(),
                "amount": parse_decimal(match.group("amount")),
            }
            item_type = "earning" if match.group("kind") == "C" else "deduction"
            if item_type == "earning":
                earnings.append(data)
            else:
                deductions.append(data)
            records.append(
                make_record(
                    source_type=self.source_type,
                    import_batch_id=import_batch_id,
                    source_file_id=source_file_id,
                    data={**data, "item_type": item_type, "reference": parse_decimal(match.group("reference"))},
                    raw_reference={"raw_line": index, "raw_text": line},
                )
            )
        if not records:
            raise ParserError("empty_payroll_items", "Payroll PDF has no earning or deduction items.")
        return earnings, deductions, records

    def _summary_amount(self, lines: list[str], label: str) -> Decimal:
        line = self._line_containing(lines, label)
        return last_money(line)


class SicoobCheckingStatementPdfParser(_SicoobPdfParser):
    source_type = "sicoob_checking_statement_pdf"

    def parse(
        self,
        file_path: Path,
        import_batch_id: UUID,
        source_file_id: UUID | None = None,
    ) -> ParsedDocument:
        lines = self._lines(file_path)
        period_start, period_end = self._period(lines)
        transactions, future_transactions, records = self._transactions(
            lines,
            period_year=period_start.year,
            import_batch_id=import_batch_id,
            source_file_id=source_file_id,
        )
        payload = {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "final_balance": self._final_balance(lines),
            "transactions_count_min": len(transactions),
            "future_transactions_count": len(future_transactions),
            "reconciliation_hint": self._reconciliation_hint(transactions),
        }
        return ParsedDocument(
            source_type=self.source_type,
            import_batch_id=import_batch_id,
            source_file_id=source_file_id,
            payload=payload,
            records=records,
            raw_reference={"file_path": str(file_path)},
        )

    def _period(self, lines: list[str]) -> tuple[Any, Any]:
        line = self._line_containing(lines, "PERIODO:")
        match = re.search(r"(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})", line)
        if not match:
            raise ParserError("missing_checking_period", "Checking statement period was not found.")
        return parse_date(match.group(1)), parse_date(match.group(2))

    def _transactions(
        self,
        lines: list[str],
        *,
        period_year: int,
        import_batch_id: UUID,
        source_file_id: UUID | None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Any]]:
        transactions = []
        future_transactions = []
        records = []
        in_history = False
        in_future = False
        history_pattern = re.compile(r"^(?P<date>\d{2}/\d{2})\s+(?P<description>.+?)\s+(?P<amount>[\d.]+,\d{2}\s*[CD])$")
        future_pattern = re.compile(r"^(?P<date>\d{2}/\d{2}/\d{2})\s+(?P<description>.+?)\s+(?P<amount>[\d.]+,\d{2}\s*[CD])$")

        for index, line in enumerate(lines, start=1):
            normalized = normalize_text(line)
            if normalized == "data historico valor":
                in_history = True
                continue
            if normalized == "resumo":
                in_history = False
                continue
            if normalized == "lancamentos futuros":
                in_future = True
                continue

            if in_history:
                match = history_pattern.match(line)
                if not match:
                    continue
                data = {
                    "date": parse_date(match.group("date"), default_year=period_year).isoformat(),
                    "description": match.group("description").strip(),
                    "amount": parse_signed_money(match.group("amount")),
                }
                transactions.append(data)
                records.append(
                    make_record(
                        source_type=self.source_type,
                        import_batch_id=import_batch_id,
                        source_file_id=source_file_id,
                        data={**data, "record_type": "posted_transaction"},
                        raw_reference={"raw_line": index, "raw_text": line},
                    )
                )

            if in_future:
                match = future_pattern.match(line)
                if not match:
                    continue
                data = {
                    "date": parse_date(match.group("date")).isoformat(),
                    "description": match.group("description").strip(),
                    "amount": parse_signed_money(match.group("amount")),
                }
                future_transactions.append(data)
                records.append(
                    make_record(
                        source_type=self.source_type,
                        import_batch_id=import_batch_id,
                        source_file_id=source_file_id,
                        data={**data, "record_type": "future_transaction"},
                        raw_reference={"raw_line": index, "raw_text": line},
                    )
                )

        if not transactions:
            raise ParserError("empty_checking_transactions", "Checking statement has no transactions.")
        return transactions, future_transactions, records

    def _final_balance(self, lines: list[str]) -> Decimal:
        return parse_signed_money(self._line_containing(lines, "SALDO EM CONTA"))

    def _reconciliation_hint(self, transactions: list[dict[str, Any]]) -> dict[str, Decimal]:
        hint: dict[str, Decimal] = {}
        for transaction in transactions:
            description = normalize_text(transaction["description"])
            if "folha" in description:
                hint["payroll_credit"] = transaction["amount"]
            if "boleto" in description:
                hint["card_payment"] = transaction["amount"]
            if "conta invest" in description:
                hint["investment_transfer"] = transaction["amount"]
        return hint


class SicoobCardInvoicePdfParser(_SicoobPdfParser):
    source_type = "sicoob_card_invoice_pdf"

    def parse(
        self,
        file_path: Path,
        import_batch_id: UUID,
        source_file_id: UUID | None = None,
    ) -> ParsedDocument:
        lines = self._lines(file_path)
        due_date = self._due_date(lines)
        purchases, records = self._purchases(lines, import_batch_id, source_file_id)
        payload = {
            "reference_month": f"{due_date.year:04d}-{due_date.month:02d}",
            "due_date": due_date.isoformat(),
            "total_amount": self._amount_for_label(lines, "TOTAL R$"),
            "minimum_payment": self._amount_for_label(lines, "PAGAMENTO MINIMO"),
            "credit_limit": self._amount_for_label(lines, "COMPRAS:"),
            "used_limit": self._amount_for_label(lines, "Utilizado:"),
            "available_limit": self._amount_for_label(lines, "Disponivel:"),
            "future_debt_total": self._amount_for_label(lines, "TOTAL DA DIVIDA A VENCER"),
            "next_invoice_installments": self._amount_for_label(lines, "PARCELAS PARA A PROXIMA FATURA"),
            "purchases_count": len(purchases),
            "installment_examples": self._installment_examples(purchases),
        }
        return ParsedDocument(
            source_type=self.source_type,
            import_batch_id=import_batch_id,
            source_file_id=source_file_id,
            payload=payload,
            records=records,
            raw_reference={"file_path": str(file_path)},
        )

    def _due_date(self, lines: list[str]) -> Any:
        for index, line in enumerate(lines):
            if "vencimento" not in normalize_text(line):
                continue
            due_date = self._date_from_text(line)
            if due_date is not None:
                return due_date
            for nearby in lines[index + 1 : index + 4]:
                due_date = self._date_from_text(nearby)
                if due_date is not None:
                    return due_date
        raise ParserError("missing_card_due_date", "Card invoice due date was not found.")

    def _date_from_text(self, line: str) -> Any | None:
        normalized = normalize_text(line)
        for pattern in (r"\d{1,2}\s+[a-z]{3,}\s+\d{4}", r"\d{2}/\d{2}/\d{4}"):
            match = re.search(pattern, normalized)
            if match:
                return parse_date(match.group(0))
        return None

    def _amount_for_label(self, lines: list[str], label: str) -> Decimal:
        normalized_label = normalize_text(label)
        for index, line in enumerate(lines):
            if normalized_label not in normalize_text(line):
                continue
            tokens = money_tokens(line)
            if tokens:
                return parse_decimal(tokens[0] if normalized_label in {"total r$", "compras:"} else tokens[-1])

            nearby_tokens: list[str] = []
            for nearby in lines[index + 1 : index + 6]:
                nearby_tokens.extend(money_tokens(nearby))
            if not nearby_tokens:
                continue
            if normalized_label == "utilizado:" and len(nearby_tokens) > 1:
                return parse_decimal(nearby_tokens[1])
            return parse_decimal(nearby_tokens[0])

        raise ParserError("missing_card_amount", f"Card invoice amount was not found for {label}.")

    def _purchases(
        self,
        lines: list[str],
        import_batch_id: UUID,
        source_file_id: UUID | None,
    ) -> tuple[list[dict[str, Any]], list[Any]]:
        purchases = []
        records = []
        pattern = re.compile(r"^\d{2}\s+[A-Z]{3}\s+(?P<body>.+)$")
        installment_pattern = re.compile(r"\b(?P<number>\d{2})/(?P<total>\d{2})\b")

        for index, line in enumerate(lines, start=1):
            if not pattern.match(normalize_text(line).upper()):
                continue
            body = line[7:]
            tokens = money_tokens(body)
            if not tokens:
                continue
            amount = parse_decimal(tokens[-1])
            due_date = self._due_date(lines)
            purchase_day = int(line[:2])
            purchase_month_token = normalize_text(line[3:6])
            purchase_month = {
                "jan": 1,
                "fev": 2,
                "mar": 3,
                "abr": 4,
                "mai": 5,
                "jun": 6,
                "jul": 7,
                "ago": 8,
                "set": 9,
                "out": 10,
                "nov": 11,
                "dez": 12,
            }[purchase_month_token]
            money_match = list(re.finditer(r"R\$\s*[\d.,]+", body))
            body_before_amount = body[: money_match[-1].start()].strip() if money_match else body
            installment_match = installment_pattern.search(body_before_amount)
            description = body_before_amount
            installment_number = None
            installment_total = None
            if installment_match:
                description = body_before_amount[: installment_match.start()].strip()
                installment_number = int(installment_match.group("number"))
                installment_total = int(installment_match.group("total"))

            data = {
                "purchase_date": f"{due_date.year:04d}-{purchase_month:02d}-{purchase_day:02d}",
                "description": description,
                "amount": amount,
                "installment_number": installment_number,
                "installment_total": installment_total,
            }
            purchases.append(data)
            records.append(
                make_record(
                    source_type=self.source_type,
                    import_batch_id=import_batch_id,
                    source_file_id=source_file_id,
                    data=data,
                    raw_reference={"raw_line": index, "raw_text": line},
                )
            )

        if not purchases:
            raise ParserError("empty_card_invoice_purchases", "Card invoice has no purchases.")
        return purchases, records

    def _installment_examples(self, purchases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        wanted = {"CENTAURO CE46", "MERCADOLIVRE*MERCADO"}
        examples = []
        for purchase in purchases:
            if purchase["description"] not in wanted or purchase["installment_number"] is None:
                continue
            examples.append(
                {
                    "description": purchase["description"],
                    "installment_number": purchase["installment_number"],
                    "installment_total": purchase["installment_total"],
                    "amount": purchase["amount"],
                }
            )
        return examples


class SicoobInvestmentsPdfParser(_SicoobPdfParser):
    source_type = "sicoob_investments_pdf"

    def parse(
        self,
        file_path: Path,
        import_batch_id: UUID,
        source_file_id: UUID | None = None,
    ) -> ParsedDocument:
        lines = self._lines(file_path)
        period_start, period_end = self._period(lines)
        positions, records = self._positions(lines, import_batch_id, source_file_id)
        return ParsedDocument(
            source_type=self.source_type,
            import_batch_id=import_batch_id,
            source_file_id=source_file_id,
            payload={
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "positions": positions,
            },
            records=records,
            raw_reference={"file_path": str(file_path)},
        )

    def _period(self, lines: list[str]) -> tuple[Any, Any]:
        line = self._line_containing(lines, "Periodo:")
        match = re.search(r"(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})", line)
        if not match:
            raise ParserError("missing_investment_period", "Investment statement period was not found.")
        return parse_date(match.group(1)), parse_date(match.group(2))

    def _positions(
        self,
        lines: list[str],
        import_batch_id: UUID,
        source_file_id: UUID | None,
    ) -> tuple[list[dict[str, Any]], list[Any]]:
        section_positions = self._positions_from_movement_sections(lines, import_batch_id, source_file_id)
        if section_positions is not None:
            return section_positions

        positions = []
        records = []
        for index, line in enumerate(lines):
            if index + 1 >= len(lines) or "saldo final" not in normalize_text(lines[index + 1]):
                continue

            product = line
            section = lines[index + 2 : index + 10]
            data = {
                "product": product,
                "gross_value": self._section_amount(section, "Valor Bruto:"),
                "net_value": self._section_amount(section, "Valor Liquido:"),
                "period_gross_yield": self._section_amount(section, "Rendimento Bruto"),
                "counts_as_reserve": "referenciado di" in normalize_text(product),
            }
            positions.append(data)
            records.append(
                make_record(
                    source_type=self.source_type,
                    import_batch_id=import_batch_id,
                    source_file_id=source_file_id,
                    data=data,
                    raw_reference={"raw_line": index + 1, "raw_text": product},
                )
            )

        if not positions:
            raise ParserError("empty_investment_positions", "Investment statement has no positions.")
        return positions, records

    def _positions_from_movement_sections(
        self,
        lines: list[str],
        import_batch_id: UUID,
        source_file_id: UUID | None,
    ) -> tuple[list[dict[str, Any]], list[Any]] | None:
        section_starts = [
            index
            for index, line in enumerate(lines)
            if index + 1 < len(lines) and normalize_text(lines[index + 1]) == "data historico"
        ]
        if not section_starts:
            return None

        positions = []
        records = []
        for offset, start in enumerate(section_starts):
            end = section_starts[offset + 1] if offset + 1 < len(section_starts) else len(lines)
            product = lines[start]
            section = lines[start:end]
            saldo_final_index = next(
                (index for index, item in enumerate(section) if "saldo final" in normalize_text(item)),
                None,
            )
            if saldo_final_index is None:
                continue
            final_section = section[saldo_final_index + 1 : saldo_final_index + 8]
            yield_section = section[saldo_final_index + 1 :]
            data = {
                "product": product,
                "gross_value": self._section_amount(final_section, "Valor Bruto"),
                "net_value": self._section_amount(final_section, "Valor Liquido"),
                "period_gross_yield": self._section_amount(yield_section, "Rendimento Bruto"),
                "counts_as_reserve": "referenciado di" in normalize_text(product),
            }
            positions.append(data)
            records.append(
                make_record(
                    source_type=self.source_type,
                    import_batch_id=import_batch_id,
                    source_file_id=source_file_id,
                    data=data,
                    raw_reference={"raw_line": start + 1, "raw_text": product},
                )
            )

        if not positions:
            raise ParserError("empty_investment_positions", "Investment statement has no positions.")
        return positions, records

    def _section_amount(self, section: list[str], label: str) -> Decimal:
        normalized_label = normalize_text(label)
        for index, line in enumerate(section):
            if normalized_label in normalize_text(line):
                tokens = money_tokens(line)
                if tokens:
                    return parse_decimal(tokens[-1])
                for nearby in section[index + 1 : index + 4]:
                    tokens = money_tokens(nearby)
                    if tokens:
                        return parse_decimal(tokens[-1])
        raise ParserError("missing_investment_amount", f"Missing investment amount for {label}.")
