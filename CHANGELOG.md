# CHANGELOG

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
