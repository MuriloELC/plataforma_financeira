# CHANGELOG

## 0.12.0 - Qualidade final do MVP

- Adicionado mascaramento centralizado para CPF, conta e endereco em `backend/app/core/privacy.py`.
- Adicionada validacao de upload para arquivo vazio, extensao nao suportada e limite configuravel `MAX_UPLOAD_SIZE_BYTES`.
- Ajustadas respostas de arquivos para nao expor caminho local completo e mascarar CPF no nome exibido.
- Adicionada migration `20260625_0003_add_categorization_rules_and_seed_categories`.
- Seedadas categorias iniciais do DATA_MODEL de forma idempotente.
- Adicionados endpoints `/categorization-rules` e `/categorize/preview` para categorizacao deterministica.
- Adicionados endpoints `/cards`, `/card-invoices` e `/card-invoices/{id}/transactions`.
- Compras manuais de cartao parceladas passam a gerar `silver.installments`.
- Adicionados testes de upload seguro, mascaramento, categorizacao, faturas manuais e parcelas.
- Criado script `backend/scripts/validate_mvp_flow.py` para validar o fluxo principal do MVP.
- Tornado `scripts/validate_private_fixtures.py` seguro, exibindo apenas contagens e totais.
- Criadas documentacoes `docs/USAGE.md`, `docs/ADDING_PARSER.md` e `docs/FINAL_REVIEW_CHECKLIST.md`.
- Atualizado README com estado do MVP, comandos locais e comandos de validacao.
- Validado `RUN_DB_TESTS=1 pytest` com 57 testes, migrations do zero, audit/build frontend e navegacao Playwright.

## 0.11.0 - Frontend MVP

- Implementado frontend MVP em Next.js consumindo a API real.
- Adicionadas telas de dashboard financeiro, importacao, revisao, lancamentos, investimentos, cartoes/faturas, indicadores Gold, simulador e historico.
- Conectados formularios a upload Bronze, preview/aprovacao de importacao, cadastros manuais, refresh Gold e simulacao de compra.
- Adicionados estados de carregamento, erro, vazio e exibicao de mensagens de validacao da API.
- Configurado CORS no backend para liberar o frontend local de forma configuravel.
- Atualizado `NEXT_PUBLIC_API_BASE_URL` e `CORS_ALLOW_ORIGINS` no ambiente de exemplo.
- Atualizado Next.js para `16.2.9` e aplicado override de `postcss@8.5.10`.
- Adicionado teste automatizado de preflight CORS em `/health`.
- Validado build do frontend, audit npm, testes backend e navegacao das abas principais com Playwright.

## 0.10.0 - Simulador Posso Comprar

- Adicionado endpoint `POST /purchase-decisions/simulate`.
- Adicionado endpoint `GET /purchase-decisions` para historico.
- Implementado motor deterministico sem score numerico.
- Implementados vereditos `Comprar agora`, `Comprar com ajuste`, `Esperar` e `Evitar`.
- Calculados impactos no aporte minimo, reserva, parcelas futuras e atraso estimado na meta de R$ 100 mil.
- Exigida justificativa para tecnologia acima de R$ 300.
- Exigida justificativa quando a compra compromete o aporte minimo.
- Historico de decisoes salvo em `app.purchase_decisions`.
- Adicionados testes dos quatro vereditos, justificativa obrigatoria e persistencia de historico.

## 0.9.0 - Gold e indicadores

- Adicionado endpoint `POST /gold/refresh`.
- Adicionados endpoints de leitura para renda passiva, meta R$ 100 mil, reserva, alocacao, compromissos futuros, contexto de decisao e alertas.
- Implementado calculo de renda passiva recebida, medias 3M/12M e progresso ate R$ 5.000/mes.
- Implementado calculo de progresso ate R$ 100 mil considerando investimentos Silver.
- Implementado calculo de reserva alvo por media de gastos dos ultimos 3 meses multiplicada por 6.
- Implementado calculo de alocacao por classe de ativo.
- Implementado refresh de compromissos futuros a partir de parcelas.
- Implementado contexto Gold para decisao de compra.
- Implementado alerta de aporte minimo mensal de R$ 300.
- Adicionados testes com dados Silver conhecidos para validar os calculos Gold.

## 0.8.0 - Cadastro manual

- Adicionados endpoints CRUD para contas manuais em `/manual/accounts`.
- Adicionados endpoints CRUD para categorias em `/categories`.
- Adicionados endpoints CRUD para metas em `/manual/goals`.
- Adicionados endpoints CRUD para lancamentos manuais em `/manual/transactions`.
- Adicionados endpoints CRUD para investimentos manuais em `/manual/investments`.
- Adicionados schemas Pydantic para cadastros manuais.
- Adicionado repositorio manual com auditoria em `app.audit_logs`.
- Lancamentos manuais passam a ser gravados em `silver.cash_transactions`.
- Investimentos manuais passam a ser gravados em `silver.manual_investment_positions`.
- Persistido `counts_as_reserve` para diferenciar patrimonio de ativos elegiveis para reserva.
- Adicionados testes de CRUD manual, auditoria e regra de reserva.

## 0.7.0 - Normalizacao Silver

- Adicionado registry de parsers por `source_type`.
- Adicionado endpoint `GET /import-batches/{id}/preview`.
- Adicionado endpoint `POST /import-batches/{id}/approve`.
- Implementada normalizacao idempotente de importacoes Bronze aprovadas para Silver.
- Gravadas transacoes de caixa em `silver.cash_transactions` preservando origem.
- Gravadas faturas, compras de cartao e parcelas futuras em tabelas Silver.
- Gravadas posicoes, proventos e negociacoes de investimentos em tabelas Silver.
- Gravados contracheques em `silver.payroll_statements`, `silver.payroll_earnings` e `silver.payroll_deductions`.
- Registrado `approved_to_silver` e `parser_name` em `bronze.import_batches`.
- Adicionados testes de idempotencia e regras criticas Silver.
- Mantida a restricao de nao gravar em Gold nesta fase.

## 0.6.0 - Parsers do MVP

- Adicionada infraestrutura comum de parsers com `ParserProtocol`, `ParsedDocument`, `ParsedRecord` e `ParserError`.
- Implementado parser de extrato CSV Mercado Livre.
- Implementado parser de CDB manual Mercado Livre.
- Implementados parsers B3 XLSX mensal e anual.
- Implementados parsers PDF Sicoob para contracheque, conta corrente, fatura de cartao e investimentos.
- Adicionada comparacao automatizada com golden files em `fixtures/expected`.
- Garantido que registros parseados preservam `import_batch_id`, `source_file_id`, `confidence_score`, `needs_review` e `raw_reference`.
- Adicionado teste de falha controlada de parsing.
- Mantida a restricao de nao gravar dados parseados diretamente em Silver ou Gold.

## 0.5.0 - Ingestao Bronze

- Adicionado endpoint `POST /files/upload` para registrar CSV, XLSX e PDF no Bronze.
- Adicionados endpoints `GET /files` e `GET /import-batches/{id}`.
- Adicionado calculo de hash SHA-256 e deteccao de duplicidade por hash.
- Adicionada deteccao inicial de fonte provavel para Mercado Livre, B3, Sicoob e CSV manual.
- Adicionada persistencia de metadados e conteudo bruto em tabelas Bronze.
- Adicionada extracao bruta de CSV, XLSX e PDF sem gravar dados em Silver ou Gold.
- Adicionado registro controlado de erros de extracao em `bronze.parser_errors`.
- Adicionados testes de integracao para upload valido, duplicidade, CSV, XLSX, PDF e extensao invalida.
- Montadas fixtures anonimizadas no container backend somente para testes.

## 0.4.0 - Modelo de dados inicial

- Adicionada migration Alembic `20260625_0002_create_initial_data_model`.
- Criadas tabelas iniciais em `bronze`, `silver`, `gold` e `app`.
- Mantido o schema `audit` criado na fundacao.
- Adicionado contrato de schema em `backend/app/db/schema_contract.py`.
- Adicionado script `backend/scripts/check_schema.py` para validar estrutura do banco.
- Adicionado teste `backend/tests/test_schema_contract.py`.
- Validado `alembic upgrade head` em banco limpo via Docker Compose.

## 0.3.0 - Fundacao executavel

- Criada estrutura inicial do backend com FastAPI.
- Criado endpoint `GET /health`.
- Adicionada configuracao SQLAlchemy e Alembic.
- Adicionada migration inicial para schemas `bronze`, `silver`, `gold`, `app` e `audit`.
- Adicionado Docker Compose com PostgreSQL e backend.
- Criada estrutura inicial do frontend Next.js.
- Adicionados testes Pytest para `/health` e teste opt-in de conexao PostgreSQL.
- Adicionado script `backend/scripts/check_db_connection.py` para validar conexao com banco.
- Atualizado `.env.example` com `DATABASE_URL`, portas e URL publica da API.

## [0.1.0] — Bootstrap documental

### Adicionado

- README inicial.
- BLUEPRINT central.
- SPEC funcional/técnica.
- ARCHITECTURE.
- DATA_MODEL.
- TASKS.
- FEATURES.
- AGENTS.
- SKILLS.
- CODEX_INSTRUCTIONS.
- Regras auxiliares `.codex/`.

### Decisões

- Arquitetura medalhão.
- B3 como fonte oficial para bolsa e renda fixa registrada.
- B3 mensal como snapshot oficial.
- Renda fixa B3 com liquidez desconhecida como patrimônio apenas.
- Investimentos fora da B3 por cadastro manual.
- Reserva = média de gastos 3M × 6.
- Aporte mínimo inicial = R$ 300.
- Meta intermediária = R$ 100 mil investidos.
- Meta final = R$ 5 mil/mês de renda passiva.
- Compras não planejadas acima de R$ 300 passam por simulação.
- Tecnologia acima de R$ 300 exige justificativa.
- FGTS apenas informativo.
- Sicoob Previ como previdência ilíquida.

## 0.2.0 - Fixtures anônimas e contratos de parser

- Adicionada pasta `fixtures/anonymized` com amostras sintéticas de Mercado Livre, Sicoob e B3.
- Adicionada pasta `fixtures/expected` com saídas JSON esperadas.
- Adicionado `FIXTURES.md` para política de uso de arquivos reais.
- Adicionado `PARSER_CONTRACTS.md` para padronização dos parsers.
- Atualizado `.gitignore` para bloquear arquivos financeiros reais.
- Adicionada feature `000_fixtures_e_parsers.md`.
