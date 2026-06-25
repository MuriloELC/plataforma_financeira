# Checklist final de revisao do MVP

## Produto

- [x] Segue `BLUEPRINT.md`.
- [x] Mantem foco em decisao financeira, nao apenas registro de gastos.
- [x] Nao adiciona IA nem requisitos fora do MVP.
- [x] Protege o aporte minimo de R$ 300 no simulador.
- [x] Separa reserva, investimentos, patrimonio e renda passiva nos indicadores Gold.

## Dados

- [x] Respeita arquitetura Bronze/Silver/Gold/App.
- [x] Upload preserva bruto no Bronze.
- [x] Registros derivados preservam `import_batch_id` e `source_file_id`.
- [x] Parsers usam `raw_reference`.
- [x] Nenhum parser grava direto no Gold.

## Banco

- [x] Migrations Alembic existem e rodam do zero.
- [x] Schemas `bronze`, `silver`, `gold`, `app` e `audit` existem.
- [x] Dinheiro usa `numeric` no PostgreSQL e `Decimal` no Python.
- [x] Contrato de schema validado por `backend/scripts/check_schema.py`.

## Backend

- [x] FastAPI com schemas Pydantic.
- [x] Regras criticas ficam no backend.
- [x] Erros de upload, parser e validacao sao estruturados.
- [x] Categorizacao deterministica fica no backend.
- [x] Cartoes, faturas e parcelas manuais ficam no backend.
- [x] CORS local configuravel para o frontend.

## Seguranca

- [x] `.env` e `fixtures/private/` estao ignorados no Git.
- [x] Upload rejeita extensao nao suportada, arquivo vazio e arquivo acima do limite configurado.
- [x] Mensagens de erro de extracao bruta nao expõem conteudo do arquivo.
- [x] Erros estruturados de parser passam por mascaramento.
- [x] Respostas de arquivo nao expõem caminho local completo.
- [x] Fixtures versionadas sao anonimizadas.

## Testes

- [x] Testes de healthcheck.
- [x] Testes de conexao e schema PostgreSQL.
- [x] Testes de upload, duplicidade e validacao Bronze.
- [x] Testes de parsers com golden files.
- [x] Testes de normalizacao Silver e nao duplicidade.
- [x] Testes de CRUD manual e auditoria.
- [x] Testes de indicadores Gold.
- [x] Testes dos quatro vereditos do simulador.
- [x] Teste de CORS para frontend.
- [x] Testes de mascaramento e limite de upload.
- [x] Testes de seed/categorizacao deterministica.
- [x] Testes de fatura manual e parcelas.

## Frontend

- [x] Dashboard financeiro.
- [x] Importacao de arquivos.
- [x] Revisao de importacoes.
- [x] Lancamentos manuais.
- [x] Regras e preview de categorizacao.
- [x] Investimentos manuais.
- [x] Cartoes e faturas.
- [x] Indicadores Gold.
- [x] Simulador "Posso Comprar?".
- [x] Historico de decisoes.
- [x] Build Next.js validado.

## Docs

- [x] `README.md` atualizado.
- [x] `docs/USAGE.md` criado.
- [x] `docs/ADDING_PARSER.md` criado.
- [x] `docs/FINAL_REVIEW_CHECKLIST.md` criado e preenchido.
- [x] `TASKS.md` atualizado.
- [x] `CHANGELOG.md` atualizado.

## Evidencias

- `docker compose up --build --pull never -d`
- `docker compose exec backend alembic current` -> `20260625_0003 (head)`
- `docker compose exec backend python scripts/check_schema.py`
- `docker compose exec -e RUN_DB_TESTS=1 backend pytest` -> 57 testes
- `docker compose exec backend python scripts/validate_mvp_flow.py`
- `cd frontend && npm audit --omit=dev`
- `cd frontend && npm run build`
- Playwright validou carregamento do frontend, navegacao das abas principais e controles de categorizacao/cartoes.
