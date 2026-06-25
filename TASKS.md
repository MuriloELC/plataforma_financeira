# TASKS — Plano de Execução para Codex

## Regras

- Uma tarefa pequena por vez.
- Sempre ler BLUEPRINT.md antes de implementar.
- Criar testes.
- Atualizar TASKS.md e CHANGELOG.md.
- Não inventar requisitos.

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
Status: aberta
Depende de: 0.2

Prompt:
```text
Implemente bronze.raw_files e bronze.import_batches com migrations, models, schemas, repositories e testes.
```

### 1.2 Upload com hash
Status: aberta
Depende de: 1.1

Prompt:
```text
Implemente POST /files/upload com storage local, SHA-256, detecção de duplicidade e criação de import_batch.
```

### 1.3 Bronze bruto CSV/XLSX/PDF
Status: aberta
Depende de: 1.2

Prompt:
```text
Implemente extração bruta para CSV, XLSX e PDF salvando em bronze.raw_csv_rows, raw_xlsx_rows e raw_pdf_pages.
```

## Épico 2 — Mercado Livre

### 2.1 Parser CSV Mercado Livre
Status: aberta
Depende de: 1.3

Prompt:
```text
Implemente MercadoLivreCsvParser. Ele deve identificar bloco de resumo e movimentações, retornar objetos Pydantic e erros estruturados. Não salvar direto no banco.
```

### 2.2 Persistir cash_transactions
Status: aberta
Depende de: 2.1

Prompt:
```text
Crie silver.cash_transactions e grave transações validadas mantendo source_file_id, import_batch_id e raw_reference.
```

## Épico 3 — Investimentos

### 3.1 Modelos de investimentos
Status: aberta

Prompt:
```text
Implemente investment_assets, investment_positions, investment_transactions, investment_income e pension_positions conforme DATA_MODEL.md.
```

### 3.2 Parser B3 XLSX
Status: aberta
Depende de: 3.1

Prompt:
```text
Implemente parser para relatórios B3 XLSX mensal/anual, extraindo posições, proventos e negociações com testes e fixtures anonimizadas.
```

### 3.3 Cadastro manual de investimentos
Status: aberta
Depende de: 3.1

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
Status: aberta
Depende de: 4.1

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
Status: aberta

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
Status: aberta
Depende de: 3.1

Prompt:
```text
Implemente gold.monthly_passive_income separando received_amount e accrued_amount, com médias de 3 e 12 meses.
```

### 6.2 Progresso R$ 100 mil
Status: aberta
Depende de: 3.1

Prompt:
```text
Implemente gold.goal_100k_progress considerando apenas investimentos.
```

### 6.3 Reserva dinâmica
Status: aberta
Depende de: 2.2 e 3.3

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
Status: aberta
Depende de: 6.1, 6.2, 6.3

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
- Ler `PARSER_CONTRACTS.md`.
- Implementar `ParserProtocol` e modelos Pydantic.
- Critério de pronto: testes unitários validam contratos mínimos.

### Tarefa 0.3 - Parser Mercado Livre CSV
- Usar `fixtures/anonymized/mercado_livre/account_statement_sample.csv`.
- Comparar com `fixtures/expected/mercado_livre_account_statement_expected.json`.
- Critério de pronto: separa resumo e movimentações, trata vírgula decimal e classifica rendimentos.

### Tarefa 0.4 - Parser B3 XLSX mensal
- Usar `fixtures/anonymized/b3/relatorio-consolidado-mensal-sample.xlsx`.
- Comparar com `fixtures/expected/b3_monthly_expected.json`.
- Critério de pronto: extrai ações, ETF, renda fixa, proventos e negociações.

### Tarefa 0.5 - Parsers Sicoob PDF
- Usar PDFs sintéticos em `fixtures/anonymized/sicoob/`.
- Comparar com arquivos de `fixtures/expected/`.
- Critério de pronto: extrai fatura, conta, investimentos e contracheque sem imprimir dados sensíveis.
