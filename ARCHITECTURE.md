# ARCHITECTURE — Arquitetura Detalhada

## 1. Visão

```text
Frontend React/Next.js
  ↓ HTTP
Backend FastAPI
  ↓ Services / Domain
Pydantic + Parsers
  ↓
PostgreSQL + Storage local
```

## 2. Frontend

Stack:

- React ou Next.js;
- TypeScript;
- Tailwind;
- shadcn/ui;
- TanStack Query;
- React Hook Form.

Telas MVP:

1. Dashboard.
2. Upload de arquivos.
3. Revisão de importação.
4. Lançamentos manuais.
5. Investimentos.
6. Cartões/faturas.
7. Simulador “Posso Comprar?”.
8. Configurações.

Regra: frontend não calcula regra financeira crítica. Ele exibe resultado do backend.

## 3. Backend

Stack:

- FastAPI;
- Pydantic v2;
- SQLAlchemy 2;
- Alembic;
- Pandas/Polars;
- Pytest.

Estrutura sugerida:

```text
backend/app/
├── api/routes
├── core
├── db
├── domain
├── parsers
├── repositories
├── schemas
├── services
└── tests
```

## 4. Banco

Schemas:

- `bronze`: bruto;
- `silver`: normalizado;
- `gold`: analítico;
- `app`: usuário, categorias e configurações;
- `audit`: auditoria.

## 5. Bronze

Responsável por preservar:

- arquivo original;
- hash;
- linhas de CSV/XLSX;
- texto de PDF;
- erros de parsing;
- lote de importação.

## 6. Silver

Responsável por:

- limpeza;
- normalização;
- revisão;
- categorias;
- investimentos;
- cartões;
- transações;
- payroll.

## 7. Gold

Responsável por:

- KPIs;
- dashboard;
- contexto do simulador;
- alertas;
- relatórios.

## 8. Orquestração

MVP:

- API executa upload/parse/refresh.
- Jobs manuais via scripts.

Futuro:

- Prefect flows:
  - ingest_file;
  - parse_bronze;
  - validate_silver;
  - refresh_gold;
  - monthly_close;
  - generate_alerts.

## 9. Observabilidade

Logs para:

- upload;
- parsing;
- validação;
- refresh Gold;
- simulação;
- erros.

Métricas:

- arquivos importados;
- registros válidos;
- registros pendentes;
- erros por parser;
- tempo de processamento.

## 10. Segurança

- Local-first.
- Storage local fora do Git.
- Dados sensíveis mascarados na UI.
- Autenticação simples no MVP.
- Nenhuma senha bancária.

## 11. Deploy

MVP com Docker Compose:

- postgres;
- backend;
- frontend.

Futuro:

- homelab ou VPS;
- backup de banco;
- backup de storage;
- criptografia se exposto externamente.
