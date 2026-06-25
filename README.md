# Sistema de Gestão Financeira Pessoal

Sistema pessoal de gestão financeira orientado a dados, construído para importar arquivos financeiros, permitir cadastro manual, organizar tudo em arquitetura medalhão e apoiar decisões financeiras antes que elas aconteçam.

O objetivo não é criar apenas um app de registro de gastos. O objetivo é criar um **sistema de decisão financeira** capaz de responder: “essa compra me aproxima ou me afasta da minha rota financeira?”.

## Visão rápida

O sistema deve consolidar:

- extratos e movimentações de contas;
- faturas de cartão;
- relatórios B3;
- investimentos cadastrados manualmente;
- contracheques;
- categorias e recorrências;
- metas financeiras;
- renda passiva;
- pré-decisões de compra.

## Stack sugerida

| Camada | Stack |
|---|---|
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Banco | PostgreSQL |
| Frontend | React/Next.js, TypeScript, Tailwind, shadcn/ui |
| Processamento | Pandas/Polars, OpenPyXL, PyMuPDF/pdfplumber |
| Testes | Pytest, testes frontend futuros |
| Orquestração futura | Prefect |
| BI futuro | Metabase/Superset ou dashboard próprio |
| Deploy | Docker Compose local |

## Como começar com Codex

1. Crie um repositório Git.
2. Extraia este ZIP na raiz do projeto.
3. Envie ao Codex a instrução:

```text
Leia CODEX_INSTRUCTIONS.md, BLUEPRINT.md, SPEC.md, ARCHITECTURE.md, DATA_MODEL.md e TASKS.md.
Implemente apenas a primeira tarefa aberta em TASKS.md.
Crie testes e atualize CHANGELOG.md.
```

## Estrutura

```text
.
├── README.md
├── BLUEPRINT.md
├── SPEC.md
├── ARCHITECTURE.md
├── DATA_MODEL.md
├── TASKS.md
├── AGENTS.md
├── SKILLS.md
├── CODEX_INSTRUCTIONS.md
├── CHANGELOG.md
├── FEATURES/
└── .codex/
```

## Decisões já travadas

- Arquitetura medalhão: `bronze`, `silver`, `gold`.
- B3 será fonte oficial para ações, ETFs, FIIs e renda fixa registrada.
- Relatório mensal da B3 será snapshot oficial da carteira no fim do mês.
- Renda fixa B3 com liquidez desconhecida conta como patrimônio, não reserva.
- CDB Mercado Livre, Fundo DI Sicoob, INCO e Sicoob Previ entram inicialmente por cadastro manual.
- Reserva dinâmica = média dos gastos dos últimos 3 meses × 6.
- Aporte mínimo protegido inicial = R$ 300/mês.
- Meta intermediária = R$ 100 mil investidos.
- Meta final = R$ 5 mil/mês de renda passiva.
- Compras não planejadas acima de R$ 300 passam pelo simulador.
- Compras de tecnologia acima de R$ 300 exigem justificativa.
- FGTS aparece apenas como informação trabalhista.
- Sicoob Previ entra como previdência/investimento ilíquido.

## Regra principal

Primeiro dado confiável. Depois IA. Se o Codex tentar implementar IA antes de Bronze/Silver/Gold confiável, está pulando etapa.

## Fixtures de desenvolvimento

O projeto inclui fixtures anônimas em `fixtures/anonymized/` e saídas esperadas em `fixtures/expected/`. Elas permitem que o Codex implemente parsers funcionais sem versionar documentos financeiros reais.

Para validar com arquivos reais, use `fixtures/private/`, que está no `.gitignore`. Consulte `FIXTURES.md` e `PARSER_CONTRACTS.md` antes de implementar qualquer parser.

Regra dura: nenhum PDF, CSV ou XLSX real com CPF, conta, endereço, salário, fatura ou patrimônio deve ser commitado.

## Estado atual do MVP

O MVP executavel inclui:

- backend FastAPI com SQLAlchemy, Alembic e PostgreSQL;
- schemas `bronze`, `silver`, `gold`, `app` e `audit`;
- ingestao Bronze com upload, hash SHA-256, duplicidade e extracao bruta de CSV/XLSX/PDF;
- parsers para Mercado Livre, B3, Sicoob e CSV manual de investimentos;
- revisao/aprovacao de importacoes para Silver;
- CRUD manual de contas, categorias, metas, lancamentos e investimentos;
- seed inicial de categorias e categorizacao deterministica por regras;
- cadastro manual de cartoes, faturas e compras parceladas;
- calculos Gold de renda passiva, meta R$ 100 mil, reserva, alocacao, compromissos e alertas;
- simulador deterministico "Posso Comprar?";
- frontend Next.js com dashboard, importacao, revisao, cadastros, indicadores, simulador e historico.

## Rodar localmente

Backend e banco:

```bash
cp .env.example .env
docker compose up --build -d
curl http://localhost:8000/health
```

Frontend:

```bash
cd frontend
npm install
npm run dev -- -p 3000
```

URLs:

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

## Testes e validacoes

```bash
docker compose exec backend alembic current
docker compose exec backend python scripts/check_schema.py
docker compose exec -e RUN_DB_TESTS=1 backend pytest
docker compose exec backend python scripts/validate_mvp_flow.py
cd frontend && npm audit --omit=dev
cd frontend && npm run build
```

## Documentacao operacional

- Uso local e fluxo principal: `docs/USAGE.md`
- Como adicionar novo parser: `docs/ADDING_PARSER.md`
- Checklist final de revisao: `docs/FINAL_REVIEW_CHECKLIST.md`
