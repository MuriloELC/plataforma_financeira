from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, default=str)


class SilverRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def delete_for_import(self, import_batch_id: UUID) -> None:
        self.session.execute(
            text(
                """
                delete from silver.payroll_deductions
                where payroll_statement_id in (
                    select id from silver.payroll_statements where import_batch_id = :import_batch_id
                )
                """
            ),
            {"import_batch_id": import_batch_id},
        )
        self.session.execute(
            text(
                """
                delete from silver.payroll_earnings
                where payroll_statement_id in (
                    select id from silver.payroll_statements where import_batch_id = :import_batch_id
                )
                """
            ),
            {"import_batch_id": import_batch_id},
        )
        self.session.execute(
            text(
                """
                delete from silver.payroll_items
                where payroll_statement_id in (
                    select id from silver.payroll_statements where import_batch_id = :import_batch_id
                )
                """
            ),
            {"import_batch_id": import_batch_id},
        )
        self.session.execute(
            text(
                """
                delete from silver.installments
                where card_transaction_id in (
                    select id from silver.card_transactions where import_batch_id = :import_batch_id
                )
                """
            ),
            {"import_batch_id": import_batch_id},
        )
        for table_name in (
            "payroll_statements",
            "card_transactions",
            "card_invoices",
            "investment_income",
            "investment_transactions",
            "investment_trades",
            "investment_positions",
            "cash_transactions",
        ):
            self.session.execute(
                text(f"delete from silver.{table_name} where import_batch_id = :import_batch_id"),
                {"import_batch_id": import_batch_id},
            )

    def find_or_create_account(self, *, institution: str, account_name: str, account_type: str) -> UUID:
        existing = self.session.execute(
            text(
                """
                select id from silver.accounts
                where institution = :institution
                  and account_name = :account_name
                  and account_type = :account_type
                limit 1
                """
            ),
            {
                "institution": institution,
                "account_name": account_name,
                "account_type": account_type,
            },
        ).scalar_one_or_none()
        if existing is not None:
            return existing

        return self.session.execute(
            text(
                """
                insert into silver.accounts (institution, account_name, account_type)
                values (:institution, :account_name, :account_type)
                returning id
                """
            ),
            {
                "institution": institution,
                "account_name": account_name,
                "account_type": account_type,
            },
        ).scalar_one()

    def find_or_create_card(self, *, institution: str, card_name: str) -> UUID:
        existing = self.session.execute(
            text(
                """
                select id from silver.cards
                where institution = :institution and card_name = :card_name
                limit 1
                """
            ),
            {"institution": institution, "card_name": card_name},
        ).scalar_one_or_none()
        if existing is not None:
            return existing

        return self.session.execute(
            text(
                """
                insert into silver.cards (institution, card_name, brand)
                values (:institution, :card_name, :brand)
                returning id
                """
            ),
            {"institution": institution, "card_name": card_name, "brand": "Visa"},
        ).scalar_one()

    def find_or_create_asset(
        self,
        *,
        asset_code: str,
        asset_name: str,
        asset_class: str,
        institution: str | None,
        counts_as_reserve: bool = False,
    ) -> UUID:
        existing = self.session.execute(
            text(
                """
                select id from silver.investment_assets
                where asset_code = :asset_code
                  and institution is not distinct from :institution
                limit 1
                """
            ),
            {"asset_code": asset_code, "institution": institution},
        ).scalar_one_or_none()
        if existing is not None:
            return existing

        return self.session.execute(
            text(
                """
                insert into silver.investment_assets (
                    asset_code,
                    asset_name,
                    asset_class,
                    institution,
                    default_counts_as_reserve
                )
                values (
                    :asset_code,
                    :asset_name,
                    :asset_class,
                    :institution,
                    :default_counts_as_reserve
                )
                returning id
                """
            ),
            {
                "asset_code": asset_code,
                "asset_name": asset_name,
                "asset_class": asset_class,
                "institution": institution,
                "default_counts_as_reserve": counts_as_reserve,
            },
        ).scalar_one()

    def insert_cash_transaction(
        self,
        *,
        account_id: UUID,
        transaction_date: date,
        description_raw: str,
        amount: Decimal,
        direction: str,
        transaction_type: str,
        is_transfer: bool,
        source_file_id: UUID | None,
        import_batch_id: UUID,
        raw_reference: Mapping[str, Any],
    ) -> None:
        self.session.execute(
            text(
                """
                insert into silver.cash_transactions (
                    account_id,
                    transaction_date,
                    description_raw,
                    amount,
                    direction,
                    transaction_type,
                    is_transfer,
                    source_file_id,
                    import_batch_id,
                    raw_reference,
                    confidence_score,
                    needs_review
                )
                values (
                    :account_id,
                    :transaction_date,
                    :description_raw,
                    :amount,
                    :direction,
                    :transaction_type,
                    :is_transfer,
                    :source_file_id,
                    :import_batch_id,
                    cast(:raw_reference as jsonb),
                    1.0000,
                    false
                )
                """
            ),
            {
                "account_id": account_id,
                "transaction_date": transaction_date,
                "description_raw": description_raw,
                "amount": amount,
                "direction": direction,
                "transaction_type": transaction_type,
                "is_transfer": is_transfer,
                "source_file_id": source_file_id,
                "import_batch_id": import_batch_id,
                "raw_reference": _json(raw_reference),
            },
        )

    def insert_card_invoice(
        self,
        *,
        card_id: UUID,
        reference_month: date,
        due_date: date,
        total_amount: Decimal,
        minimum_payment: Decimal,
        credit_limit: Decimal,
        used_limit: Decimal,
        available_limit: Decimal,
        future_debt_total: Decimal,
        source_file_id: UUID | None,
        import_batch_id: UUID,
    ) -> UUID:
        return self.session.execute(
            text(
                """
                insert into silver.card_invoices (
                    card_id,
                    reference_month,
                    due_date,
                    total_amount,
                    minimum_payment,
                    credit_limit,
                    used_limit,
                    available_limit,
                    future_debt_total,
                    source_file_id,
                    import_batch_id
                )
                values (
                    :card_id,
                    :reference_month,
                    :due_date,
                    :total_amount,
                    :minimum_payment,
                    :credit_limit,
                    :used_limit,
                    :available_limit,
                    :future_debt_total,
                    :source_file_id,
                    :import_batch_id
                )
                returning id
                """
            ),
            {
                "card_id": card_id,
                "reference_month": reference_month,
                "due_date": due_date,
                "total_amount": total_amount,
                "minimum_payment": minimum_payment,
                "credit_limit": credit_limit,
                "used_limit": used_limit,
                "available_limit": available_limit,
                "future_debt_total": future_debt_total,
                "source_file_id": source_file_id,
                "import_batch_id": import_batch_id,
            },
        ).scalar_one()

    def insert_card_transaction(
        self,
        *,
        invoice_id: UUID,
        card_id: UUID,
        purchase_date: date,
        description_raw: str,
        amount: Decimal,
        installment_number: int | None,
        installment_total: int | None,
        source_file_id: UUID | None,
        import_batch_id: UUID,
        raw_reference: Mapping[str, Any],
    ) -> UUID:
        return self.session.execute(
            text(
                """
                insert into silver.card_transactions (
                    invoice_id,
                    card_id,
                    purchase_date,
                    description_raw,
                    amount,
                    installment_number,
                    installment_total,
                    is_installment,
                    source_file_id,
                    import_batch_id,
                    raw_reference,
                    confidence_score,
                    needs_review
                )
                values (
                    :invoice_id,
                    :card_id,
                    :purchase_date,
                    :description_raw,
                    :amount,
                    :installment_number,
                    :installment_total,
                    :is_installment,
                    :source_file_id,
                    :import_batch_id,
                    cast(:raw_reference as jsonb),
                    1.0000,
                    false
                )
                returning id
                """
            ),
            {
                "invoice_id": invoice_id,
                "card_id": card_id,
                "purchase_date": purchase_date,
                "description_raw": description_raw,
                "amount": amount,
                "installment_number": installment_number,
                "installment_total": installment_total,
                "is_installment": installment_total is not None and installment_total > 1,
                "source_file_id": source_file_id,
                "import_batch_id": import_batch_id,
                "raw_reference": _json(raw_reference),
            },
        ).scalar_one()

    def insert_installment(
        self,
        *,
        card_transaction_id: UUID,
        installment_number: int,
        installment_total: int,
        installment_amount: Decimal,
        due_month: date,
    ) -> None:
        self.session.execute(
            text(
                """
                insert into silver.installments (
                    card_transaction_id,
                    installment_number,
                    installment_total,
                    installment_amount,
                    due_month
                )
                values (
                    :card_transaction_id,
                    :installment_number,
                    :installment_total,
                    :installment_amount,
                    :due_month
                )
                """
            ),
            {
                "card_transaction_id": card_transaction_id,
                "installment_number": installment_number,
                "installment_total": installment_total,
                "installment_amount": installment_amount,
                "due_month": due_month,
            },
        )

    def insert_investment_position(
        self,
        *,
        asset_id: UUID,
        institution: str,
        source_type: str,
        reference_date: date,
        gross_value: Decimal | None,
        net_value: Decimal | None,
        market_value: Decimal | None,
        counts_as_reserve: bool,
        source_file_id: UUID | None,
        import_batch_id: UUID,
    ) -> None:
        self.session.execute(
            text(
                """
                insert into silver.investment_positions (
                    asset_id,
                    institution,
                    source_type,
                    reference_date,
                    gross_value,
                    net_value,
                    market_value,
                    counts_as_reserve,
                    source_file_id,
                    import_batch_id
                )
                values (
                    :asset_id,
                    :institution,
                    :source_type,
                    :reference_date,
                    :gross_value,
                    :net_value,
                    :market_value,
                    :counts_as_reserve,
                    :source_file_id,
                    :import_batch_id
                )
                """
            ),
            {
                "asset_id": asset_id,
                "institution": institution,
                "source_type": source_type,
                "reference_date": reference_date,
                "gross_value": gross_value,
                "net_value": net_value,
                "market_value": market_value,
                "counts_as_reserve": counts_as_reserve,
                "source_file_id": source_file_id,
                "import_batch_id": import_batch_id,
            },
        )

    def insert_manual_investment_position(
        self,
        *,
        asset_id: UUID,
        institution: str,
        product_name: str,
        asset_class: str,
        reference_date: date,
        gross_value: Decimal,
        net_value: Decimal | None,
        liquidity: str | None,
        maturity_date: date | None,
        rate_description: str | None,
        counts_as_reserve: bool,
    ) -> None:
        self.session.execute(
            text(
                """
                delete from silver.manual_investment_positions
                where institution = :institution
                  and product_name = :product_name
                  and reference_date = :reference_date
                """
            ),
            {
                "institution": institution,
                "product_name": product_name,
                "reference_date": reference_date,
            },
        )
        self.session.execute(
            text(
                """
                insert into silver.manual_investment_positions (
                    asset_id,
                    institution,
                    product_name,
                    asset_class,
                    reference_date,
                    gross_value,
                    net_value,
                    liquidity,
                    maturity_date,
                    rate_description,
                    counts_as_reserve
                )
                values (
                    :asset_id,
                    :institution,
                    :product_name,
                    :asset_class,
                    :reference_date,
                    :gross_value,
                    :net_value,
                    :liquidity,
                    :maturity_date,
                    :rate_description,
                    :counts_as_reserve
                )
                """
            ),
            {
                "asset_id": asset_id,
                "institution": institution,
                "product_name": product_name,
                "asset_class": asset_class,
                "reference_date": reference_date,
                "gross_value": gross_value,
                "net_value": net_value,
                "liquidity": liquidity,
                "maturity_date": maturity_date,
                "rate_description": rate_description,
                "counts_as_reserve": counts_as_reserve,
            },
        )

    def insert_investment_income(
        self,
        *,
        asset_id: UUID,
        payment_date: date | None,
        reference_date: date,
        income_type: str,
        net_amount: Decimal | None,
        source_type: str,
        source_file_id: UUID | None,
        import_batch_id: UUID,
    ) -> None:
        self.session.execute(
            text(
                """
                insert into silver.investment_income (
                    asset_id,
                    payment_date,
                    reference_date,
                    income_type,
                    net_amount,
                    source_type,
                    source_file_id,
                    import_batch_id
                )
                values (
                    :asset_id,
                    :payment_date,
                    :reference_date,
                    :income_type,
                    :net_amount,
                    :source_type,
                    :source_file_id,
                    :import_batch_id
                )
                """
            ),
            {
                "asset_id": asset_id,
                "payment_date": payment_date,
                "reference_date": reference_date,
                "income_type": income_type,
                "net_amount": net_amount,
                "source_type": source_type,
                "source_file_id": source_file_id,
                "import_batch_id": import_batch_id,
            },
        )

    def insert_investment_trade(
        self,
        *,
        asset_id: UUID,
        trade_date: date,
        side: str,
        quantity: Decimal,
        institution: str | None,
        source_file_id: UUID | None,
        import_batch_id: UUID,
    ) -> None:
        self.session.execute(
            text(
                """
                insert into silver.investment_trades (
                    asset_id,
                    trade_date,
                    side,
                    quantity,
                    institution,
                    source_file_id,
                    import_batch_id
                )
                values (
                    :asset_id,
                    :trade_date,
                    :side,
                    :quantity,
                    :institution,
                    :source_file_id,
                    :import_batch_id
                )
                """
            ),
            {
                "asset_id": asset_id,
                "trade_date": trade_date,
                "side": side,
                "quantity": quantity,
                "institution": institution,
                "source_file_id": source_file_id,
                "import_batch_id": import_batch_id,
            },
        )

    def insert_payroll_statement(
        self,
        *,
        employer: str,
        competence_month: date,
        payment_date: date,
        gross_income: Decimal,
        total_deductions: Decimal,
        net_income: Decimal,
        fgts_amount: Decimal,
        source_file_id: UUID | None,
        import_batch_id: UUID,
    ) -> UUID:
        return self.session.execute(
            text(
                """
                insert into silver.payroll_statements (
                    employer,
                    competence_month,
                    payment_date,
                    gross_income,
                    total_deductions,
                    net_income,
                    fgts_amount,
                    source_file_id,
                    import_batch_id
                )
                values (
                    :employer,
                    :competence_month,
                    :payment_date,
                    :gross_income,
                    :total_deductions,
                    :net_income,
                    :fgts_amount,
                    :source_file_id,
                    :import_batch_id
                )
                returning id
                """
            ),
            {
                "employer": employer,
                "competence_month": competence_month,
                "payment_date": payment_date,
                "gross_income": gross_income,
                "total_deductions": total_deductions,
                "net_income": net_income,
                "fgts_amount": fgts_amount,
                "source_file_id": source_file_id,
                "import_batch_id": import_batch_id,
            },
        ).scalar_one()

    def insert_payroll_item(
        self,
        *,
        table_name: str,
        payroll_statement_id: UUID,
        description: str,
        amount: Decimal,
    ) -> None:
        if table_name not in {"payroll_earnings", "payroll_deductions"}:
            raise ValueError("Invalid payroll table.")
        self.session.execute(
            text(
                f"""
                insert into silver.{table_name} (
                    payroll_statement_id,
                    description,
                    amount
                )
                values (
                    :payroll_statement_id,
                    :description,
                    :amount
                )
                """
            ),
            {
                "payroll_statement_id": payroll_statement_id,
                "description": description,
                "amount": amount,
            },
        )
