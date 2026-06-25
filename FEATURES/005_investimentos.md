# Feature 005 — Investimentos

## Objetivo
Consolidar investimentos B3 e manuais, separando patrimônio, reserva, renda recebida e rendimento acumulado.

## Requisitos
- Parser B3 XLSX.
- Cadastro manual.
- Previdência.
- Renda passiva.
- Alocação.
- R$ 100 mil.

## Regras
- B3 é fonte oficial de ações/ETFs/FIIs/renda fixa registrada.
- Renda fixa B3 com liquidez desconhecida = patrimônio apenas.
- Previdência não conta como reserva.
- CDB manual pode contar como reserva se marcado.

## Modelagem
- `silver.investment_assets`
- `silver.investment_positions`
- `silver.investment_transactions`
- `silver.investment_income`
- `silver.pension_positions`
- `gold.monthly_passive_income`
- `gold.goal_100k_progress`
- `gold.portfolio_allocation`

## Endpoints
- `POST /investments/manual`
- `GET /investments/positions`
- `GET /investments/passive-income`
- `GET /goals/100k`

## Telas
- Carteira.
- Renda passiva.
- R$100 mil.
- Cadastro manual.

## Testes
- B3 fixture.
- CDB manual.
- Renda recebida vs acumulada.

## Critérios de aceite
- Gold de investimento calcula corretamente.

## Prompt para Codex
```text
Implemente investimentos com B3 XLSX e cadastro manual. Separe patrimônio, reserva, renda recebida e rendimento acumulado.
```
