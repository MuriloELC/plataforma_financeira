# Feature 007 — Relatórios

## Objetivo
Gerar relatórios mensais, de importação e de decisão.

## Requisitos
- Relatório mensal Markdown.
- Relatório de importação.
- Relatório de compra simulada.

## Regras
- Usar apenas dados aprovados.
- Indicar dados ausentes.
- Não inventar informação.

## Endpoints
- `GET /reports/monthly?month=YYYY-MM`
- `GET /reports/import-batches/{id}`
- `GET /reports/purchase-decisions/{id}`

## Testes
- Relatório com dados fake.
- Dados ausentes.

## Critérios de aceite
- Relatório legível e rastreável.

## Prompt para Codex
```text
Implemente relatório mensal em Markdown usando Gold.
```
