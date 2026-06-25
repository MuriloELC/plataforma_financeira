# DATA_MODEL — Modelo de Dados Inicial

## Convenções

- IDs: `uuid`.
- Dinheiro: `numeric(14,2)` no banco e `Decimal` no Python.
- Quantidade de ativos: `numeric(20,8)`.
- Datas: `date`.
- Timestamps: `timestamptz`.
- Payload flexível: `jsonb`.

## Schemas

```sql
bronze
silver
gold
app
audit
```

## Bronze

### bronze.raw_files

| Campo | Tipo |
|---|---|
| id | uuid |
| original_filename | text |
| stored_path | text |
| mime_type | text |
| file_extension | text |
| file_size_bytes | bigint |
| sha256_hash | text unique |
| source_type | text |
| detected_institution | text |
| uploaded_at | timestamptz |
| status | text |
| metadata | jsonb |

### bronze.import_batches

| Campo | Tipo |
|---|---|
| id | uuid |
| raw_file_id | uuid |
| source_type | text |
| status | text |
| parser_name | text |
| started_at | timestamptz |
| finished_at | timestamptz |
| total_records | integer |
| valid_records | integer |
| invalid_records | integer |
| error_message | text |

### bronze.raw_csv_rows

| Campo | Tipo |
|---|---|
| id | uuid |
| import_batch_id | uuid |
| row_number | integer |
| raw_text | text |
| raw_payload | jsonb |

### bronze.raw_xlsx_rows

| Campo | Tipo |
|---|---|
| id | uuid |
| import_batch_id | uuid |
| sheet_name | text |
| row_number | integer |
| raw_payload | jsonb |

### bronze.raw_pdf_pages

| Campo | Tipo |
|---|---|
| id | uuid |
| import_batch_id | uuid |
| page_number | integer |
| extracted_text | text |
| extraction_metadata | jsonb |

### bronze.parser_errors

| Campo | Tipo |
|---|---|
| id | uuid |
| import_batch_id | uuid |
| raw_reference | jsonb |
| error_type | text |
| error_message | text |
| payload | jsonb |

## App

### app.categories

| Campo | Tipo |
|---|---|
| id | uuid |
| name | text |
| parent_id | uuid null |
| type | text |
| is_system | boolean |

Categorias iniciais:

- Moradia
- Alimentação
- Delivery
- Transporte
- Tecnologia
- Educação
- Saúde
- Lazer
- Assinaturas
- Investimentos
- Transferências
- Dívidas
- Impostos/Taxas
- Previdência
- Renda
- Renda passiva
- Outros
- Não classificado

### app.settings

| Campo | Tipo |
|---|---|
| key | text primary key |
| value | jsonb |

Configuração inicial:

```json
{
  "purchase_simulation_threshold": 300,
  "minimum_monthly_contribution": 300,
  "reserve_months": 6,
  "passive_income_target_monthly": 5000,
  "investment_goal": 100000
}
```

## Silver — Transações

### silver.accounts

| Campo | Tipo |
|---|---|
| id | uuid |
| institution | text |
| account_name | text |
| account_type | text |
| currency | text |
| is_active | boolean |

### silver.cash_transactions

| Campo | Tipo |
|---|---|
| id | uuid |
| account_id | uuid |
| transaction_date | date |
| posted_date | date |
| description_raw | text |
| description_clean | text |
| amount | numeric(14,2) |
| direction | text |
| category_id | uuid |
| transaction_type | text |
| is_transfer | boolean |
| is_recurring | boolean |
| source_file_id | uuid |
| import_batch_id | uuid |
| raw_reference | jsonb |
| confidence_score | numeric(5,4) |
| needs_review | boolean |
| review_status | text |

## Silver — Cartões

### silver.cards

| Campo | Tipo |
|---|---|
| id | uuid |
| institution | text |
| card_name | text |
| brand | text |
| last_four_digits | text |
| credit_limit | numeric(14,2) |
| is_active | boolean |

### silver.card_invoices

| Campo | Tipo |
|---|---|
| id | uuid |
| card_id | uuid |
| reference_month | date |
| closing_date | date |
| due_date | date |
| total_amount | numeric(14,2) |
| minimum_payment | numeric(14,2) |
| credit_limit | numeric(14,2) |
| used_limit | numeric(14,2) |
| available_limit | numeric(14,2) |
| next_invoice_committed_amount | numeric(14,2) |
| future_debt_total | numeric(14,2) |
| status | text |
| source_file_id | uuid |
| import_batch_id | uuid |

### silver.card_transactions

| Campo | Tipo |
|---|---|
| id | uuid |
| invoice_id | uuid |
| card_id | uuid |
| purchase_date | date |
| description_raw | text |
| description_clean | text |
| amount | numeric(14,2) |
| category_id | uuid |
| installment_number | integer |
| installment_total | integer |
| is_installment | boolean |
| confidence_score | numeric(5,4) |
| needs_review | boolean |

### silver.installments

| Campo | Tipo |
|---|---|
| id | uuid |
| card_transaction_id | uuid |
| installment_number | integer |
| installment_total | integer |
| installment_amount | numeric(14,2) |
| due_month | date |
| status | text |

## Silver — Investimentos

### silver.investment_assets

| Campo | Tipo |
|---|---|
| id | uuid |
| asset_code | text |
| asset_name | text |
| asset_class | text |
| institution | text |
| ticker | text |
| cnpj | text |
| currency | text |
| risk_level | text |
| default_counts_as_reserve | boolean |

### silver.investment_positions

| Campo | Tipo |
|---|---|
| id | uuid |
| asset_id | uuid |
| institution | text |
| source_type | text |
| reference_date | date |
| quantity | numeric(20,8) |
| gross_value | numeric(14,2) |
| net_value | numeric(14,2) |
| market_value | numeric(14,2) |
| liquidity | text |
| maturity_date | date |
| rate_description | text |
| counts_as_reserve | boolean |
| is_manual | boolean |
| source_file_id | uuid |
| import_batch_id | uuid |
| notes | text |

### silver.investment_transactions

| Campo | Tipo |
|---|---|
| id | uuid |
| asset_id | uuid |
| trade_date | date |
| side | text |
| quantity | numeric(20,8) |
| unit_price | numeric(14,6) |
| gross_amount | numeric(14,2) |
| fees | numeric(14,2) |
| net_amount | numeric(14,2) |
| institution | text |
| source_file_id | uuid |
| import_batch_id | uuid |

### silver.investment_income

| Campo | Tipo |
|---|---|
| id | uuid |
| asset_id | uuid |
| payment_date | date |
| reference_date | date |
| income_type | text |
| gross_amount | numeric(14,2) |
| tax_amount | numeric(14,2) |
| net_amount | numeric(14,2) |
| is_received | boolean |
| is_accrued | boolean |
| source_type | text |
| source_file_id | uuid |
| import_batch_id | uuid |

### silver.pension_positions

| Campo | Tipo |
|---|---|
| id | uuid |
| institution | text |
| plan_name | text |
| reference_date | date |
| employee_contribution | numeric(14,2) |
| employer_contribution | numeric(14,2) |
| total_balance | numeric(14,2) |
| vested_balance | numeric(14,2) |
| vesting_rule | text |
| notes | text |

## Silver — Payroll

### silver.payroll_statements

| Campo | Tipo |
|---|---|
| id | uuid |
| employer | text |
| role | text |
| competence_month | date |
| payment_date | date |
| base_salary | numeric(14,2) |
| gross_income | numeric(14,2) |
| total_deductions | numeric(14,2) |
| net_income | numeric(14,2) |
| fgts_amount | numeric(14,2) |
| source_file_id | uuid |
| import_batch_id | uuid |

### silver.payroll_items

| Campo | Tipo |
|---|---|
| id | uuid |
| payroll_statement_id | uuid |
| item_code | text |
| description | text |
| item_type | text |
| reference | numeric(14,4) |
| amount | numeric(14,2) |
| classification | text |

## Silver — Decisões

### silver.purchase_decisions

| Campo | Tipo |
|---|---|
| id | uuid |
| decision_date | date |
| item_name | text |
| amount | numeric(14,2) |
| category_id | uuid |
| is_planned | boolean |
| is_technology | boolean |
| payment_method | text |
| installments | integer |
| monthly_installment | numeric(14,2) |
| urgency | text |
| justification | text |
| verdict | text |
| reserve_impact_amount | numeric(14,2) |
| contribution_impact_amount | numeric(14,2) |
| goal_100k_delay_days | integer |
| future_commitment_impact | numeric(14,2) |
| explanation | text |

## Gold

### gold.monthly_passive_income

- month
- received_amount
- accrued_amount
- avg_3m_received
- avg_12m_received
- target_amount
- progress_pct

### gold.goal_100k_progress

- reference_date
- invested_amount
- target_amount
- remaining_amount
- progress_pct
- avg_monthly_contribution
- estimated_months_to_goal

### gold.reserve_status

- reference_date
- avg_monthly_expenses_3m
- reserve_months
- reserve_target
- eligible_reserve_amount
- gap_amount
- status

### gold.portfolio_allocation

- reference_date
- asset_class
- amount
- allocation_pct
- counts_as_reserve

### gold.future_commitments

- due_month
- source
- description
- amount
- commitment_type

### gold.purchase_decision_context

- reference_date
- net_income
- minimum_monthly_contribution
- reserve_target
- eligible_reserve_amount
- invested_amount
- goal_100k_remaining
- future_commitments_next_month
- available_after_commitments
