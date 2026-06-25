# TASKS — Plano de Execução para Codex

## Regras

- Uma tarefa pequena por vez.
- Sempre ler BLUEPRINT.md antes de implementar.
- Criar testes.
- Atualizar TASKS.md e CHANGELOG.md.
- Não inventar requisitos.

## Fases do MVP continuado

### Fase 2 - Modelo de dados inicial
Status: concluida

Entregaveis:
- migration Alembic `20260625_0002_create_initial_data_model`;
- tabelas iniciais em `bronze`, `silver`, `gold` e `app`;
- preservacao do schema `audit`;
- contrato de schema em `backend/app/db/schema_contract.py`;
- script `backend/scripts/check_schema.py`;
- teste `backend/tests/test_schema_contract.py`.

Validacao:
- migrations rodam do zero via Docker Compose;
- `python scripts/check_schema.py` retorna `Database schema OK`;
- `RUN_DB_TESTS=1 pytest` passa no container.

### Fase 3 - Ingestao Bronze
Status: concluida

Entregaveis:
- endpoint `POST /files/upload` para CSV, XLSX e PDF;
- endpoint `GET /files` para listar arquivos Bronze;
- endpoint `GET /import-batches/{id}` para consultar lote de importacao;
- calculo de hash SHA-256;
- deteccao inicial de fonte provavel alinhada aos parsers do MVP;
- deteccao de duplicidade por hash;
- armazenamento local seguro em `FILE_STORAGE_PATH`;
- persistencia em `bronze.raw_files`, `bronze.import_batches` e `bronze.raw_file_metadata`;
- extracao bruta em `bronze.raw_csv_rows`, `bronze.raw_sheet_data`, `bronze.raw_xlsx_rows`, `bronze.raw_pdf_text` e `bronze.raw_pdf_pages`;
- registro de erro controlado em `bronze.parser_errors` quando a extracao bruta falhar;
- testes de integracao em `backend/tests/test_bronze_ingestion.py`.

Validacao:
- `docker compose up --build -d` sobe Postgres e backend;
- `alembic current` retorna `20260625_0002 (head)`;
- `python scripts/check_schema.py` retorna `Database schema OK`;
- `GET /health` retorna `{"status":"ok","service":"finance-decision-backend"}`;
- `RUN_DB_TESTS=1 pytest` passa no container com 8 testes;
- testes usam apenas `fixtures/anonymized`.

### Fase 4 - Parsers
Status: concluida

Entregaveis:
- protocolo comum `ParserProtocol`;
- modelos Pydantic `ParsedDocument`, `ParsedRecord` e `ParserErrorDetail`;
- erro controlado `ParserError`;
- parser `MercadoLivreAccountStatementCsvParser`;
- parser `MercadoLivreManualCdbCsvParser`;
- parser `B3MonthlyConsolidatedXlsxParser`;
- parser `B3AnnualConsolidatedXlsxParser`;
- parser `SicoobPayrollPdfParser`;
- parser `SicoobCheckingStatementPdfParser`;
- parser `SicoobCardInvoicePdfParser`;
- parser `SicoobInvestmentsPdfParser`;
- testes comparando saida com `fixtures/expected`;
- preservacao de `import_batch_id`, `source_file_id`, `confidence_score`, `needs_review` e `raw_reference` nos registros parseados.

Validacao:
- `pytest backend/tests/test_parsers.py` passa localmente;
- `pytest` local passa com 19 testes ativos e 12 integracoes puladas;
- `RUN_DB_TESTS=1 pytest` passa no container com 31 testes;
- nenhum parser salva direto em Silver ou Gold;
- nenhum parser usa dados financeiros reais versionados.

### Fase 5 - Silver
Status: concluida

Entregaveis:
- registry de parsers por `source_type`;
- endpoint `GET /import-batches/{id}/preview`;
- endpoint `POST /import-batches/{id}/approve`;
- normalizacao idempotente para Silver a partir de importacoes aprovadas;
- persistencia em `silver.cash_transactions`;
- persistencia em `silver.card_invoices`, `silver.card_transactions` e `silver.installments`;
- persistencia em `silver.investment_assets`, `silver.investment_positions`, `silver.investment_income` e `silver.investment_trades`;
- persistencia em `silver.manual_investment_positions` para CDB manual importado por CSV;
- persistencia em `silver.payroll_statements`, `silver.payroll_earnings` e `silver.payroll_deductions`;
- status `approved_to_silver` e `parser_name` registrados em `bronze.import_batches`;
- testes de idempotencia e regras criticas em `backend/tests/test_silver_normalization.py`.

Validacao:
- `pytest` local passa com 19 testes ativos e 19 integracoes puladas;
- `RUN_DB_TESTS=1 pytest` passa no container com 38 testes;
- reaprovar o mesmo `import_batch` nao duplica registros Silver;
- pagamento de fatura e transferencia propria nao entram como gasto comum;
- renda fixa B3 importada nao entra como reserva;
- parcelas de cartao geram registros futuros em `silver.installments`;
- nenhum dado e gravado em Gold nesta fase.

### Fase 6 - Cadastro manual
Status: concluida

Entregaveis:
- endpoint `GET/POST/PATCH/DELETE /manual/accounts`;
- endpoint `GET/POST/PATCH/DELETE /categories`;
- endpoint `GET/POST/PATCH/DELETE /manual/goals`;
- endpoint `GET/POST/PATCH/DELETE /manual/transactions`;
- endpoint `GET/POST/PATCH/DELETE /manual/investments`;
- schemas Pydantic para cadastros manuais;
- repositorio manual com auditoria em `app.audit_logs`;
- lancamentos manuais em `silver.cash_transactions`;
- investimentos manuais em `silver.manual_investment_positions`;
- suporte a CDB, fundos, INCO, previdencia e outros via `asset_class`;
- `counts_as_reserve` persistido explicitamente para separar patrimonio e reserva.

Validacao:
- `pytest` local passa com 19 testes ativos e 23 integracoes puladas;
- `RUN_DB_TESTS=1 pytest` passa no container com 42 testes;
- criar, listar, editar e remover funciona para contas, categorias, metas, lancamentos e investimentos;
- create/update/delete gera `app.audit_logs`;
- investimentos manuais ficam em Silver para patrimonio;
- somente itens com `counts_as_reserve = true` ficam marcados como reserva.

### Fase 7 - Gold e indicadores
Status: concluida

Entregaveis:
- endpoint `POST /gold/refresh`;
- endpoint `GET /gold/passive-income`;
- endpoint `GET /gold/goal-100k`;
- endpoint `GET /gold/reserve`;
- endpoint `GET /gold/allocation`;
- endpoint `GET /gold/future-commitments`;
- endpoint `GET /gold/decision-context`;
- endpoint `GET /gold/alerts`;
- calculo de renda passiva recebida, media 3M, media 12M e progresso ate R$ 5.000/mes;
- calculo de progresso ate R$ 100 mil considerando investimentos;
- calculo de reserva alvo por media de gastos 3M x 6;
- calculo de alocacao por classe de ativo;
- calculo de compromissos futuros a partir de parcelas;
- contexto Gold para decisao de compra;
- alerta de aporte minimo mensal de R$ 300.

Validacao:
- `pytest` local passa com 19 testes ativos e 25 integracoes puladas;
- `RUN_DB_TESTS=1 pytest` passa no container com 44 testes;
- testes validam renda passiva, meta R$ 100 mil, reserva, alocacao, compromissos futuros e alerta de aporte;
- Gold usa apenas dados Silver.

### Fase 8 - Simulador Posso Comprar
Status: aberta

## Épico 0 — Bootstrap

### 0.1 Criar estrutura base
Status: concluida

Entregáveis:
- backend FastAPI;
- frontend React/Next;
- docker-compose com Postgres;
- healthcheck;
- `.env.example`;
- `.gitignore`.

Prompt:
```text
Leia todos os docs principais. Crie a estrutura inicial do projeto com FastAPI, frontend e PostgreSQL via Docker Compose. Não implemente regras financeiras ainda. Crie healthcheck e testes mínimos.
```

### 0.2 Configurar SQLAlchemy/Alembic
Status: concluida

Critérios:
- conexão com Postgres;
- migration inicial;
- schemas bronze, silver, gold, app, audit.

Prompt:
```text
Configure SQLAlchemy 2 e Alembic. Crie migration inicial com os schemas do DATA_MODEL.md e teste de conexão.
```

## Épico 1 — Bronze e upload

### 1.1 Criar raw_files e import_batches
Status: concluida
Depende de: 0.2

Resultado:
- tabelas criadas por Alembic na Fase 2;
- repositorio Bronze implementado em `backend/app/repositories/bronze_repository.py`;
- schemas de resposta implementados em `backend/app/schemas/ingestion.py`;
- cobertura de integracao adicionada em `backend/tests/test_bronze_ingestion.py`.

Prompt:
```text
Implemente bronze.raw_files e bronze.import_batches com migrations, models, schemas, repositories e testes.
```

### 1.2 Upload com hash
Status: concluida
Depende de: 1.1

Resultado:
- `POST /files/upload` implementado;
- storage local via `FILE_STORAGE_PATH`;
- SHA-256 calculado;
- duplicidade por hash implementada;
- `import_batch` criado para upload novo e upload duplicado.

Prompt:
```text
Implemente POST /files/upload com storage local, SHA-256, detecção de duplicidade e criação de import_batch.
```

### 1.3 Bronze bruto CSV/XLSX/PDF
Status: concluida
Depende de: 1.2

Resultado:
- CSV bruto salvo em `bronze.raw_csv_rows`;
- XLSX bruto salvo em `bronze.raw_sheet_data` e `bronze.raw_xlsx_rows`;
- PDF bruto salvo em `bronze.raw_pdf_text` e `bronze.raw_pdf_pages`;
- parser semantico e Silver/Gold continuam fora desta fase.

Prompt:
```text
Implemente extração bruta para CSV, XLSX e PDF salvando em bronze.raw_csv_rows, raw_xlsx_rows e raw_pdf_pages.
```

## Épico 2 — Mercado Livre

### 2.1 Parser CSV Mercado Livre
Status: concluida
Depende de: 1.3

Resultado:
- `MercadoLivreAccountStatementCsvParser` implementado;
- `MercadoLivreManualCdbCsvParser` implementado;
- saidas comparadas com golden files de Mercado Livre.

Prompt:
```text
Implemente MercadoLivreCsvParser. Ele deve identificar bloco de resumo e movimentações, retornar objetos Pydantic e erros estruturados. Não salvar direto no banco.
```

### 2.2 Persistir cash_transactions
Status: concluida
Depende de: 2.1

Resultado:
- `silver.cash_transactions` recebe transacoes aprovadas de Mercado Livre e Sicoob conta;
- registros mantem `source_file_id`, `import_batch_id` e `raw_reference`;
- pagamento de fatura recebe `transaction_type = card_payment`;
- transferencia para investimento recebe `is_transfer = true`.

Prompt:
```text
Crie silver.cash_transactions e grave transações validadas mantendo source_file_id, import_batch_id e raw_reference.
```

## Épico 3 — Investimentos

### 3.1 Modelos de investimentos
Status: concluida

Resultado:
- modelos/tabelas criados por migration na Fase 2;
- normalizacao Silver cria ativos, posicoes, proventos e negociacoes na Fase 5;
- renda fixa B3 fica com `counts_as_reserve = false`.

Prompt:
```text
Implemente investment_assets, investment_positions, investment_transactions, investment_income e pension_positions conforme DATA_MODEL.md.
```

### 3.2 Parser B3 XLSX
Status: concluida
Depende de: 3.1

Resultado:
- `B3MonthlyConsolidatedXlsxParser` implementado;
- `B3AnnualConsolidatedXlsxParser` implementado;
- saidas comparadas com golden files B3 mensal e anual.

Prompt:
```text
Implemente parser para relatórios B3 XLSX mensal/anual, extraindo posições, proventos e negociações com testes e fixtures anonimizadas.
```

### 3.3 Cadastro manual de investimentos
Status: concluida
Depende de: 3.1

Resultado:
- CRUD manual de investimentos implementado em `/manual/investments`;
- CDB, fundos, INCO, previdencia e outros sao suportados por `asset_class`;
- `counts_as_reserve` e auditoria implementados.

Prompt:
```text
Implemente CRUD de investimentos manuais para CDB, Fundo DI, INCO e Previdência. Incluir counts_as_reserve e auditoria.
```

## Épico 4 — Categorias e manual

### 4.1 Categorias iniciais
Status: aberta

Prompt:
```text
Crie app.categories com seed idempotente das categorias iniciais e endpoint GET /categories.
```

### 4.2 Lançamentos manuais
Status: concluida
Depende de: 4.1

Resultado:
- CRUD de lancamentos manuais implementado em `/manual/transactions`;
- registros entram em `silver.cash_transactions` com `transaction_type = manual`;
- mutacoes geram `app.audit_logs`.

Prompt:
```text
Implemente lançamentos manuais em silver.cash_transactions com auditoria.
```

### 4.3 Regras de categorização
Status: aberta
Depende de: 4.1

Prompt:
```text
Implemente app.categorization_rules e serviço de sugestão por padrão textual, priority e confidence.
```

## Épico 5 — Cartões

### 5.1 Modelar cartões/faturas/parcelas
Status: concluida

Resultado:
- tabelas criadas por migration na Fase 2;
- normalizacao Silver grava fatura, compras de cartao e parcelas futuras a partir da fatura Sicoob.

Prompt:
```text
Implemente silver.cards, card_invoices, card_transactions e installments com migrations e testes.
```

### 5.2 Cadastro manual de fatura
Status: aberta
Depende de: 5.1

Prompt:
```text
Implemente cadastro manual de fatura, compras e parcelas. Parcelas devem alimentar compromissos futuros.
```

## Épico 6 — Gold

### 6.1 Renda passiva
Status: concluida
Depende de: 3.1

Resultado:
- `gold.passive_income_monthly` calculado via `/gold/refresh`;
- separa `received_amount` de `accrued_amount`;
- calcula media 3M, media 12M e progresso ate R$ 5.000/mes.

Prompt:
```text
Implemente gold.monthly_passive_income separando received_amount e accrued_amount, com médias de 3 e 12 meses.
```

### 6.2 Progresso R$ 100 mil
Status: concluida
Depende de: 3.1

Resultado:
- `gold.goal_100k_progress` calculado via `/gold/refresh`;
- considera posicoes de investimento Silver e investimentos manuais;
- calcula percentual, restante, aporte medio e estimativa de meses.

Prompt:
```text
Implemente gold.goal_100k_progress considerando apenas investimentos.
```

### 6.3 Reserva dinâmica
Status: concluida
Depende de: 2.2 e 3.3

Resultado:
- `gold.reserve_status` calculado via `/gold/refresh`;
- alvo = media de gastos dos ultimos 3 meses x 6;
- usa somente ativos marcados com `counts_as_reserve = true`.

Prompt:
```text
Implemente gold.reserve_status: média de gastos dos últimos 3 meses × 6, usando apenas ativos elegíveis como reserva.
```

### 6.4 Dashboard inicial
Status: aberta
Depende de: 6.1, 6.2, 6.3

Prompt:
```text
Implemente dashboard com ordem: renda passiva, R$100 mil, reserva, alocação e gastos/compromissos.
```

## Épico 7 — Simulador

### 7.1 Contexto Gold
Status: concluida
Depende de: 6.1, 6.2, 6.3

Resultado:
- `gold.purchase_decision_context` calculado via `/gold/refresh`;
- inclui aporte minimo, reserva, investimentos, restante ate R$ 100 mil e compromissos futuros.

Prompt:
```text
Implemente gold.purchase_decision_context com renda líquida, aporte mínimo, reserva, investimentos e compromissos futuros.
```

### 7.2 Motor de decisão
Status: aberta
Depende de: 7.1

Prompt:
```text
Implemente motor determinístico do “Posso Comprar?”. Tecnologia acima de R$300 exige justificativa. Retorne veredito e impactos.
```

### 7.3 Tela do simulador
Status: aberta
Depende de: 7.2

Prompt:
```text
Implemente tela do simulador com formulário, resultado, justificativa e histórico.
```

## Épico 8 — Futuro

### 8.1 Relatório mensal
Status: futura

### 8.2 IA consultora Gold-only
Status: futura

## Definition of Done

- Código implementado.
- Testes criados.
- Testes passando.
- Migration criada se necessário.
- TASKS e CHANGELOG atualizados.

## Épico 0 - Fixtures e contratos de parser

### Tarefa 0.1 - Validar fixtures anônimas
- Ler `FIXTURES.md`.
- Confirmar existência de `fixtures/anonymized/` e `fixtures/expected/`.
- Critério de pronto: fixtures abrem localmente e não contêm CPF, conta, endereço ou nome completo real.

### Tarefa 0.2 - Criar interface base de parsers
Status: concluida

- Ler `PARSER_CONTRACTS.md`.
- Implementar `ParserProtocol` e modelos Pydantic.
- Critério de pronto: testes unitários validam contratos mínimos.

### Tarefa 0.3 - Parser Mercado Livre CSV
Status: concluida

- Usar `fixtures/anonymized/mercado_livre/account_statement_sample.csv`.
- Comparar com `fixtures/expected/mercado_livre_account_statement_expected.json`.
- Critério de pronto: separa resumo e movimentações, trata vírgula decimal e classifica rendimentos.

### Tarefa 0.4 - Parser B3 XLSX mensal
Status: concluida

- Usar `fixtures/anonymized/b3/relatorio-consolidado-mensal-sample.xlsx`.
- Comparar com `fixtures/expected/b3_monthly_expected.json`.
- Critério de pronto: extrai ações, ETF, renda fixa, proventos e negociações.

### Tarefa 0.5 - Parsers Sicoob PDF
Status: concluida

- Usar PDFs sintéticos em `fixtures/anonymized/sicoob/`.
- Comparar com arquivos de `fixtures/expected/`.
- Critério de pronto: extrai fatura, conta, investimentos e contracheque sem imprimir dados sensíveis.
