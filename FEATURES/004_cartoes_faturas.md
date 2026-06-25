# Feature 004 — Cartões e Faturas

## Objetivo
Modelar cartões, faturas, compras e parcelas futuras.

## Requisitos
- Cartão.
- Fatura.
- Compras.
- Parcelas.
- Compromissos futuros.

## Regras
- Compra conta no mês da compra para comportamento.
- Fatura conta no pagamento para caixa.
- Pagamento de fatura não duplica gasto.
- Parcelas alimentam futuro.

## Modelagem
- `silver.cards`
- `silver.card_invoices`
- `silver.card_transactions`
- `silver.installments`
- `gold.future_commitments`

## Endpoints
- `POST /cards`
- `POST /card-invoices`
- `POST /card-invoices/{id}/transactions`
- `GET /future-commitments`

## Telas
- Cartões.
- Fatura.
- Parcelas.

## Testes
- Fatura.
- Compra à vista.
- Compra parcelada.
- Compromisso futuro.

## Critérios de aceite
- Parcelas geradas corretamente.

## Prompt para Codex
```text
Implemente cartões, faturas, compras e parcelas conforme DATA_MODEL.md.
```
