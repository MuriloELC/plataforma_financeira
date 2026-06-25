# Feature 006 — Dashboard

## Objetivo
Exibir KPIs Gold.

## Ordem
1. Renda passiva.
2. Progresso R$ 100 mil.
3. Reserva.
4. Alocação.
5. Gastos/compromissos.

## Requisitos
- Cards.
- BRL.
- Data atualização.
- Loading/error/empty.

## Regras
- Não calcular regra crítica no frontend.
- Consumir endpoints Gold.

## Endpoints
- `GET /dashboard/summary`
- `GET /dashboard/passive-income`
- `GET /dashboard/goal-100k`
- `GET /dashboard/reserve`
- `GET /dashboard/allocation`

## Testes
- Renderização.
- Formatação BRL.
- Estados vazios.

## Critérios de aceite
- Ordem correta e dados claros.

## Prompt para Codex
```text
Implemente dashboard inicial consumindo endpoints Gold.
```
