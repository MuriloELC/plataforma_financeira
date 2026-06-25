# CHANGELOG

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
