from __future__ import annotations

from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.parsers.base import ParsedDocument, ParserError
from app.parsers.registry import parser_for_source_type
from app.parsers.utils import normalize_text
from app.repositories.bronze_repository import BronzeRepository
from app.repositories.silver_repository import SilverRepository
from app.schemas.import_review import ImportApprovalResponse, ImportRejectResponse


class ImportReviewError(Exception):
    pass


class ImportReviewService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.bronze_repository = BronzeRepository(session)
        self.silver_repository = SilverRepository(session)

    def preview_import(self, batch_id: UUID) -> ParsedDocument:
        batch, raw_file = self._load_batch_and_raw_file(batch_id)
        parser = parser_for_source_type(batch["source_type"])
        if parser is None:
            raise ImportReviewError(f"No parser registered for source type {batch['source_type']}.")

        file_path = Path(raw_file["stored_path"])
        if not file_path.exists():
            raise ImportReviewError("Stored raw file was not found.")

        try:
            return parser.parse(file_path, import_batch_id=batch["id"], source_file_id=raw_file["id"])
        except ParserError as exc:
            self.bronze_repository.add_parser_error(
                import_batch_id=batch["id"],
                error_type=exc.code,
                error_message=exc.message,
                raw_reference=exc.raw_reference,
                payload={"source_type": batch["source_type"]},
            )
            self.session.commit()
            raise ImportReviewError(exc.message) from exc

    def approve_import(self, batch_id: UUID) -> ImportApprovalResponse:
        batch, raw_file = self._load_batch_and_raw_file(batch_id)
        document = self.preview_import(batch_id)

        self.silver_repository.delete_for_import(batch_id)
        counts = self._normalize_document(document)
        self.bronze_repository.finish_import_batch(
            batch_id=batch_id,
            status="approved_to_silver",
            total_records=len(document.records),
            valid_records=len(document.records),
            invalid_records=0,
            error_message=None,
        )
        parser_name = parser_for_source_type(batch["source_type"]).__class__.__name__  # type: ignore[union-attr]
        self.bronze_repository.mark_import_batch_parser(batch_id=batch_id, parser_name=parser_name)
        self.bronze_repository.update_raw_file_status(raw_file["id"], "approved_to_silver")
        self.session.commit()

        return ImportApprovalResponse(
            import_batch_id=batch["id"],
            raw_file_id=raw_file["id"],
            source_type=batch["source_type"],
            parser_name=parser_name,
            status="approved_to_silver",
            silver_counts=dict(counts),
        )

    def reject_import(self, batch_id: UUID, *, reason: str | None = None) -> ImportRejectResponse:
        batch, raw_file = self._load_batch_and_raw_file(batch_id)
        self.bronze_repository.finish_import_batch(
            batch_id=batch_id,
            status="rejected",
            total_records=batch["total_records"],
            valid_records=0,
            invalid_records=batch["total_records"],
            error_message=reason,
        )
        self.bronze_repository.update_raw_file_status(raw_file["id"], "rejected")
        self.session.commit()
        return ImportRejectResponse(
            import_batch_id=batch["id"],
            raw_file_id=raw_file["id"],
            source_type=batch["source_type"],
            status="rejected",
            reason=reason,
        )

    def _load_batch_and_raw_file(self, batch_id: UUID) -> tuple[dict[str, Any], dict[str, Any]]:
        batch = self.bronze_repository.get_import_batch(batch_id)
        if batch is None:
            raise ImportReviewError("Import batch not found.")
        raw_file = self.bronze_repository.get_raw_file(batch["raw_file_id"])
        if raw_file is None:
            raise ImportReviewError("Raw file not found.")
        return batch, raw_file

    def _normalize_document(self, document: ParsedDocument) -> Counter[str]:
        match document.source_type:
            case "mercado_livre_account_statement_csv":
                return self._normalize_mercado_livre_statement(document)
            case "manual_investment_csv" | "mercado_livre_manual_cdb_csv":
                return self._normalize_manual_investment(document)
            case "b3_monthly_consolidated_xlsx" | "b3_annual_consolidated_xlsx":
                return self._normalize_b3(document)
            case "sicoob_checking_statement_pdf":
                return self._normalize_sicoob_checking(document)
            case "sicoob_card_invoice_pdf":
                return self._normalize_sicoob_card_invoice(document)
            case "sicoob_investments_pdf":
                return self._normalize_sicoob_investments(document)
            case "sicoob_payroll_pdf":
                return self._normalize_sicoob_payroll(document)
            case _:
                raise ImportReviewError(f"Unsupported parsed document source type {document.source_type}.")

    def _normalize_mercado_livre_statement(self, document: ParsedDocument) -> Counter[str]:
        account_id = self.silver_repository.find_or_create_account(
            institution="Mercado Livre",
            account_name="Mercado Livre",
            account_type="wallet",
        )
        counts: Counter[str] = Counter()
        for record in document.records:
            data = record.data
            amount = data["amount"]
            self.silver_repository.insert_cash_transaction(
                account_id=account_id,
                transaction_date=date.fromisoformat(data["date"]),
                description_raw=data["description"],
                amount=amount,
                direction="inflow" if amount >= 0 else "outflow",
                transaction_type=data["type"],
                is_transfer=False,
                source_file_id=document.source_file_id,
                import_batch_id=document.import_batch_id,
                raw_reference=record.raw_reference,
            )
            counts["cash_transactions"] += 1
        return counts

    def _normalize_sicoob_checking(self, document: ParsedDocument) -> Counter[str]:
        account_id = self.silver_repository.find_or_create_account(
            institution="Sicoob",
            account_name="Conta Corrente",
            account_type="checking",
        )
        counts: Counter[str] = Counter()
        for record in document.records:
            data = record.data
            if data.get("record_type") != "posted_transaction":
                continue
            transaction_type, is_transfer = self._classify_cash_transaction(data["description"])
            amount = data["amount"]
            self.silver_repository.insert_cash_transaction(
                account_id=account_id,
                transaction_date=date.fromisoformat(data["date"]),
                description_raw=data["description"],
                amount=amount,
                direction="inflow" if amount >= 0 else "outflow",
                transaction_type=transaction_type,
                is_transfer=is_transfer,
                source_file_id=document.source_file_id,
                import_batch_id=document.import_batch_id,
                raw_reference=record.raw_reference,
            )
            counts["cash_transactions"] += 1
        return counts

    def _normalize_sicoob_card_invoice(self, document: ParsedDocument) -> Counter[str]:
        card_id = self.silver_repository.find_or_create_card(
            institution="Sicoob",
            card_name="Sicoob Visa Platinum",
        )
        payload = document.payload
        reference_month = _month_start(payload["reference_month"])
        invoice_id = self.silver_repository.insert_card_invoice(
            card_id=card_id,
            reference_month=reference_month,
            due_date=date.fromisoformat(payload["due_date"]),
            total_amount=payload["total_amount"],
            minimum_payment=payload["minimum_payment"],
            credit_limit=payload["credit_limit"],
            used_limit=payload["used_limit"],
            available_limit=payload["available_limit"],
            future_debt_total=payload["future_debt_total"],
            source_file_id=document.source_file_id,
            import_batch_id=document.import_batch_id,
        )
        counts: Counter[str] = Counter({"card_invoices": 1})

        for record in document.records:
            data = record.data
            transaction_id = self.silver_repository.insert_card_transaction(
                invoice_id=invoice_id,
                card_id=card_id,
                purchase_date=date.fromisoformat(data["purchase_date"]),
                description_raw=data["description"],
                amount=data["amount"],
                installment_number=data.get("installment_number"),
                installment_total=data.get("installment_total"),
                source_file_id=document.source_file_id,
                import_batch_id=document.import_batch_id,
                raw_reference=record.raw_reference,
            )
            counts["card_transactions"] += 1
            if data.get("installment_number") and data.get("installment_total"):
                for installment_number in range(data["installment_number"], data["installment_total"] + 1):
                    due_month = _add_months(reference_month, installment_number - data["installment_number"])
                    self.silver_repository.insert_installment(
                        card_transaction_id=transaction_id,
                        installment_number=installment_number,
                        installment_total=data["installment_total"],
                        installment_amount=data["amount"],
                        due_month=due_month,
                    )
                    counts["installments"] += 1
        return counts

    def _normalize_b3(self, document: ParsedDocument) -> Counter[str]:
        counts: Counter[str] = Counter()
        reference_date = (
            _month_end(document.payload["reference_month"])
            if "reference_month" in document.payload
            else date(int(document.payload["reference_year"]), 12, 31)
        )
        for record in document.records:
            data = record.data
            if data.get("record_type") == "income":
                asset_id = self.silver_repository.find_or_create_asset(
                    asset_code=_asset_code(data["product"]),
                    asset_name=data["product"],
                    asset_class="listed_income",
                    institution="B3",
                )
                payment_date = date.fromisoformat(data["payment_date"])
                self.silver_repository.insert_investment_income(
                    asset_id=asset_id,
                    payment_date=payment_date,
                    reference_date=payment_date,
                    income_type=data["income_type"],
                    net_amount=data["net_amount"],
                    source_type=document.source_type,
                    source_file_id=document.source_file_id,
                    import_batch_id=document.import_batch_id,
                )
                counts["investment_income"] += 1
                continue

            if data.get("record_type") == "trade":
                asset_id = self.silver_repository.find_or_create_asset(
                    asset_code=data["ticker"],
                    asset_name=data["ticker"],
                    asset_class="listed_asset",
                    institution="B3",
                )
                self.silver_repository.insert_investment_trade(
                    asset_id=asset_id,
                    trade_date=date.fromisoformat(data["trade_date"]),
                    side="buy" if data["buy_quantity"] > 0 else "sell",
                    quantity=abs(data["net_quantity"]),
                    institution=data["institution"],
                    source_file_id=document.source_file_id,
                    import_batch_id=document.import_batch_id,
                )
                counts["investment_trades"] += 1
                continue

            asset_id = self.silver_repository.find_or_create_asset(
                asset_code=_asset_code(data["product"]),
                asset_name=data["product"],
                asset_class=data["asset_class"],
                institution="B3",
                counts_as_reserve=False,
            )
            self.silver_repository.insert_investment_position(
                asset_id=asset_id,
                institution=data.get("institution") or "B3",
                source_type=document.source_type,
                reference_date=reference_date,
                gross_value=data["amount"],
                net_value=None,
                market_value=data["amount"],
                counts_as_reserve=False,
                source_file_id=document.source_file_id,
                import_batch_id=document.import_batch_id,
            )
            counts["investment_positions"] += 1
        return counts

    def _normalize_manual_investment(self, document: ParsedDocument) -> Counter[str]:
        counts: Counter[str] = Counter()
        reference_date = date.today()
        for record in document.records:
            data = record.data
            asset_id = self.silver_repository.find_or_create_asset(
                asset_code=_asset_code(data["product"]),
                asset_name=data["product"],
                asset_class=data["asset_class"],
                institution=data["institution"],
                counts_as_reserve=data["counts_as_reserve"],
            )
            self.silver_repository.insert_manual_investment_position(
                asset_id=asset_id,
                institution=data["institution"],
                product_name=data["product"],
                asset_class=data["asset_class"],
                reference_date=reference_date,
                gross_value=data["gross_value"],
                net_value=data["gross_value"],
                liquidity=data["liquidity"],
                maturity_date=date.fromisoformat(data["maturity_date"]),
                rate_description=data["rate"],
                counts_as_reserve=data["counts_as_reserve"],
            )
            counts["manual_investment_positions"] += 1
        return counts

    def _normalize_sicoob_investments(self, document: ParsedDocument) -> Counter[str]:
        counts: Counter[str] = Counter()
        reference_date = date.fromisoformat(document.payload["period_end"])
        for record in document.records:
            data = record.data
            asset_id = self.silver_repository.find_or_create_asset(
                asset_code=_asset_code(data["product"]),
                asset_name=data["product"],
                asset_class="fund",
                institution="Sicoob",
                counts_as_reserve=data["counts_as_reserve"],
            )
            self.silver_repository.insert_investment_position(
                asset_id=asset_id,
                institution="Sicoob",
                source_type=document.source_type,
                reference_date=reference_date,
                gross_value=data["gross_value"],
                net_value=data["net_value"],
                market_value=data["gross_value"],
                counts_as_reserve=data["counts_as_reserve"],
                source_file_id=document.source_file_id,
                import_batch_id=document.import_batch_id,
            )
            counts["investment_positions"] += 1
        return counts

    def _normalize_sicoob_payroll(self, document: ParsedDocument) -> Counter[str]:
        payload = document.payload
        statement_id = self.silver_repository.insert_payroll_statement(
            employer="EMPRESA EXEMPLO LTDA",
            competence_month=_month_start(payload["competence_month"]),
            payment_date=date.fromisoformat(payload["payment_date"]),
            gross_income=payload["gross_income"],
            total_deductions=payload["total_deductions"],
            net_income=payload["net_income"],
            fgts_amount=payload["fgts_amount"],
            source_file_id=document.source_file_id,
            import_batch_id=document.import_batch_id,
        )
        counts: Counter[str] = Counter({"payroll_statements": 1})
        for item in payload["earnings"]:
            self.silver_repository.insert_payroll_item(
                table_name="payroll_earnings",
                payroll_statement_id=statement_id,
                description=item["description"],
                amount=item["amount"],
            )
            counts["payroll_earnings"] += 1
        for item in payload["deductions"]:
            self.silver_repository.insert_payroll_item(
                table_name="payroll_deductions",
                payroll_statement_id=statement_id,
                description=item["description"],
                amount=item["amount"],
            )
            counts["payroll_deductions"] += 1
        return counts

    def _classify_cash_transaction(self, description: str) -> tuple[str, bool]:
        normalized = normalize_text(description)
        if "boleto" in normalized:
            return "card_payment", False
        if "folha" in normalized:
            return "payroll_income", False
        if "conta invest" in normalized:
            return "investment_transfer", True
        if "resgate rdc" in normalized:
            return "investment_redemption", True
        if "transf.contas" in normalized:
            return "own_account_transfer", True
        return "cash", False


def _month_start(value: str) -> date:
    year, month = value.split("-")
    return date(int(year), int(month), 1)


def _month_end(value: str) -> date:
    first = _month_start(value)
    next_month = _add_months(first, 1)
    return date.fromordinal(next_month.toordinal() - 1)


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def _asset_code(product: str) -> str:
    first_part = product.split(" - ", 1)[0].strip()
    code = normalize_text(first_part).replace(" ", "_").replace("/", "_")
    return code.upper()[:64]
