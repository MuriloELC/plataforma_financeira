# Uso local do MVP

## Requisitos

- Docker Desktop com Docker Compose.
- Node.js e npm para rodar o frontend fora do container.
- Arquivo `.env` local baseado em `.env.example`.

## Subir backend e banco

```bash
cp .env.example .env
docker compose up --build -d
```

O backend fica em `http://localhost:8000` e o PostgreSQL em `localhost:5432`.

Validacoes rapidas:

```bash
curl http://localhost:8000/health
docker compose exec backend alembic current
docker compose exec backend python scripts/check_schema.py
```

## Rodar frontend

```bash
cd frontend
npm install
npm run dev -- -p 3000
```

O frontend fica em `http://localhost:3000` e consome `NEXT_PUBLIC_API_BASE_URL`.

## Rodar testes

Backend com banco:

```bash
docker compose exec -e RUN_DB_TESTS=1 backend pytest
```

Fluxo principal contra banco ja migrado:

```bash
docker compose exec backend python scripts/validate_mvp_flow.py
```

Frontend:

```bash
cd frontend
npm audit --omit=dev
npm run build
```

## Importar fixtures anonimizadas

Use apenas `fixtures/anonymized/` para testes versionados.

Exemplo:

```bash
curl -F "file=@fixtures/anonymized/mercado_livre/account_statement_sample.csv" http://localhost:8000/files/upload
```

Depois, use o `import_batch.id` retornado:

```bash
curl http://localhost:8000/import-batches/ID_DO_LOTE/preview
curl -X POST http://localhost:8000/import-batches/ID_DO_LOTE/approve
curl -X POST http://localhost:8000/gold/refresh
```

## Usar fixtures privadas

Arquivos reais devem ficar somente em `fixtures/private/`, que esta ignorada no Git.

Estrutura sugerida:

```text
fixtures/private/sicoob/
fixtures/private/b3/
fixtures/private/mercado_livre/
```

Validacao local sem expor nomes ou conteudo:

```bash
python scripts/validate_private_fixtures.py --source fixtures/private
```

Nao versionar PDFs, CSVs, XLSX, dumps, `.env`, storage local ou logs com dados reais.

## Fluxo principal do MVP

1. Subir banco e backend com Docker Compose.
2. Rodar frontend em `http://localhost:3000`.
3. Conferir categorias iniciais e criar regra de categorizacao, se necessario.
4. Fazer upload de fixture anonima.
5. Revisar preview do lote.
6. Aprovar importacao para Silver.
7. Cadastrar investimento manual, se necessario.
8. Cadastrar cartao, fatura e compra parcelada, se necessario.
9. Executar refresh Gold.
10. Conferir dashboard e indicadores.
11. Simular compra no "Posso Comprar?".
12. Consultar historico de decisoes.

## Endpoints principais

- `GET /health`
- `POST /files/upload`
- `GET /files`
- `GET /import-batches/{id}`
- `GET /import-batches/{id}/preview`
- `POST /import-batches/{id}/approve`
- `GET/POST/PATCH/DELETE /manual/accounts`
- `GET/POST/PATCH/DELETE /categories`
- `GET/POST/PATCH/DELETE /categorization-rules`
- `POST /categorize/preview`
- `GET/POST/PATCH/DELETE /manual/goals`
- `GET/POST/PATCH/DELETE /manual/transactions`
- `GET/POST/PATCH/DELETE /manual/investments`
- `GET/POST/PATCH/DELETE /cards`
- `GET/POST/PATCH/DELETE /card-invoices`
- `POST /card-invoices/{id}/transactions`
- `POST /gold/refresh`
- `GET /gold/passive-income`
- `GET /gold/goal-100k`
- `GET /gold/reserve`
- `GET /gold/allocation`
- `GET /gold/future-commitments`
- `GET /gold/decision-context`
- `GET /gold/alerts`
- `POST /purchase-decisions/simulate`
- `GET /purchase-decisions`

## Telas principais

- Dashboard financeiro.
- Importacao de arquivos.
- Revisao de importacoes.
- Lancamentos manuais.
- Investimentos manuais.
- Cartoes e faturas.
- Indicadores Gold.
- Simulador "Posso Comprar?".
- Historico de decisoes.

## Limitacoes conhecidas

- Autenticacao ainda nao foi implementada; o MVP e local-first.
- Categorizacao e deterministica por regras, sem IA.
- Frontend e operacional, sem design system externo.
- Imports reais devem ser validados localmente em `fixtures/private/`; nenhuma integracao bancaria direta existe.
- Faturas manuais cobrem cadastro de cartao, fatura e compras; conciliacao automatica com pagamento de fatura ainda depende do fluxo Silver.

## Proximas melhorias

- Autenticacao local simples.
- Tela dedicada para manutencao completa de regras de categorizacao.
- Relatorio mensal automatizado.
- Backups de banco e storage.
- IA consultora usando apenas Gold/Silver revisado, depois de maturar a base.
