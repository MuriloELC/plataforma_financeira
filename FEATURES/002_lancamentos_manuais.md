# Feature 002 — Lançamentos Manuais

## Objetivo
Permitir cadastrar transações, investimentos, renda passiva e ajustes manualmente.

## Contexto
CDB Mercado Livre, Fundo DI Sicoob, INCO e Sicoob Previ entram por cadastro manual no MVP.

## Requisitos
- CRUD de transações manuais.
- CRUD de investimentos manuais.
- Cadastro de renda recebida e rendimento acumulado.
- Auditoria.

## Regras
- `source_type = manual`.
- Ajustes relevantes exigem justificativa.
- Investimento pode ter `counts_as_reserve`.

## Modelagem
- `silver.cash_transactions`
- `silver.investment_positions`
- `silver.investment_income`
- `silver.pension_positions`
- `audit.audit_log`

## Endpoints
- `POST /manual/transactions`
- `POST /manual/investments`
- `POST /manual/income`

## Telas
- Lançamento manual.
- Investimento manual.
- Histórico.

## Testes
- Criar, editar, excluir lógico.
- Auditoria.
- Validação monetária.

## Critérios de aceite
- Dados entram no Silver.
- Auditoria salva.

## Prompt para Codex
```text
Implemente lançamentos manuais com validação Pydantic e auditoria.
```
