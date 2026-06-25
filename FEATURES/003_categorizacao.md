# Feature 003 — Categorização

## Objetivo
Sugerir e revisar categorias de transações e compras.

## Requisitos
- Categorias iniciais.
- Regras por padrão textual.
- Prioridade e confiança.
- Revisão manual.

## Regras
- Transferência própria não é gasto.
- Pagamento de fatura não duplica gasto.
- Tecnologia é categoria crítica.

## Modelagem
- `app.categories`
- `app.categorization_rules`

## Endpoints
- `GET /categories`
- `POST /categorization-rules`
- `POST /categorize/preview`

## Telas
- Categorias.
- Regras.
- Revisão de não classificados.

## Testes
- Seed.
- Regra por contains.
- Prioridade.
- Baixa confiança.

## Critérios de aceite
- Sugestão e revisão funcionando.

## Prompt para Codex
```text
Implemente categorização determinística sem IA.
```
