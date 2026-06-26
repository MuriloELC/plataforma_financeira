# Sistema de Decisao Financeira Pessoal

Aplicacao local para importar arquivos financeiros, revisar dados, consolidar
patrimonio e apoiar decisoes de compra antes que elas afetem a rota financeira.

O foco do projeto nao e apenas registrar gastos. O objetivo e manter um pipeline
confiavel de dados financeiros e responder perguntas praticas, como:

- quanto tenho investido;
- quanto da carteira conta como reserva;
- quais compromissos futuros ja estao assumidos;
- se uma compra preserva o aporte minimo e a reserva;
- como importacoes e cadastros manuais mudam os indicadores.

## Estado Atual

O MVP ja possui:

- backend FastAPI com SQLAlchemy, Alembic e PostgreSQL;
- frontend Next.js com dashboard, importacao, revisao, lancamentos, investimentos,
  cartoes, indicadores, simulador, historico e configuracoes;
- arquitetura medalhao com schemas `bronze`, `silver`, `gold`, `app` e `audit`;
- upload Bronze de CSV, XLSX e PDF com hash, duplicidade e extracao bruta;
- parsers para Mercado Livre, B3 mensal/anual, Sicoob e CSV manual de investimentos;
- fluxo de revisao com previa, aprovacao para Silver e recusa;
- cadastros manuais de contas, categorias, metas, lancamentos, investimentos,
  cartoes, faturas e compras;
- cadastro de configuracoes auxiliares, como instituicoes, bandeiras, produtos,
  classes, taxas, liquidez e tipos de arquivo;
- indicadores Gold para renda passiva, meta de R$ 100 mil, reserva, alocacao,
  compromissos futuros e alertas;
- simulador deterministico "Posso Comprar?";
- validacao local de arquivos oficiais com saida agregada e banco descartavel.

## Stack

| Camada | Tecnologia |
| --- | --- |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Banco | PostgreSQL |
| Frontend | Next.js, React, TypeScript |
| Arquivos | OpenPyXL, pypdf |
| Testes | pytest, TypeScript, Next build |
| Local | Docker Compose |

## Estrutura Principal

```text
.
|-- backend/
|   |-- app/
|   |-- migrations/
|   |-- scripts/
|   `-- tests/
|-- frontend/
|   `-- app/
|-- docs/
|-- fixtures/
|-- FEATURES/
|-- docker-compose.yml
|-- DATA_MODEL.md
|-- TASKS.md
|-- CHANGELOG.md
`-- README.md
```

## Requisitos

- Docker Desktop com Docker Compose;
- Node.js 20+;
- Python 3.12, apenas para scripts locais fora do container;
- Git e acesso ao repositorio GitHub.

## Configuracao Local

1. Copie o arquivo de ambiente:

```bash
cp .env.example .env
```

2. Suba banco e backend:

```bash
docker compose up --build -d
```

3. Confirme a API:

```bash
curl http://localhost:8000/health
```

4. Instale e rode o frontend:

```bash
cd frontend
npm install
npm run dev -- --hostname 127.0.0.1 --port 3000
```

URLs locais:

- Frontend: `http://127.0.0.1:3000`
- Backend: `http://localhost:8000`

## Fluxo de Uso

1. Abra o frontend.
2. Entre em `Config` e cadastre ou revise instituicoes, bandeiras, produtos,
   classes, liquidez, taxas e tipos de arquivo.
3. Va em `Importacao`, escolha o arquivo e, se necessario, selecione manualmente
   o tipo/fonte do arquivo.
4. Em `Revisao`, selecione o lote pendente, confira a previa dos registros e
   aprove ou recuse com motivo.
5. Use `Lancamentos`, `Investimentos` e `Cartoes` para completar dados que nao
   vieram de arquivos.
6. Veja o `Dashboard` e `Indicadores` para reserva, patrimonio, renda passiva,
   compromissos e alertas.
7. Use `Simulador` para testar compras antes de comprometer aporte minimo,
   reserva ou metas.
8. Consulte `Historico geral` para uploads, batches, aprovacoes, recusas e
   alteracoes manuais.

## Importacao e Revisao

O Bronze preserva o arquivo e os dados brutos. A aprovacao grava dados
normalizados no Silver. O Gold e atualizado a partir dos dados confiaveis.

Tipos suportados no MVP:

- Mercado Livre CSV;
- Mercado Livre CDB CSV;
- B3 consolidado mensal XLSX;
- B3 consolidado anual XLSX;
- Sicoob extrato PDF;
- Sicoob fatura PDF;
- Sicoob investimentos PDF;
- Sicoob contracheque PDF.

Arquivos podem ser visualizados e baixados pela aba `Importacao > Arquivos`.
O sistema mascara nomes sensiveis nas respostas e nao deve versionar arquivos
financeiros reais.

## Regras Financeiras Atuais

- Reserva dinamica = media dos gastos dos ultimos 3 meses x 6.
- Aporte minimo protegido = R$ 300 por mes.
- Meta intermediaria = R$ 100 mil investidos.
- Meta final = R$ 5 mil por mes de renda passiva.
- B3 e fonte oficial para ativos listados e renda fixa registrada.
- Renda fixa B3 com liquidez desconhecida entra como patrimonio, nao reserva.
- Reserva, investimentos e patrimonio sao tratados separadamente.
- Compras nao planejadas acima de R$ 300 passam pelo simulador.
- Compras de tecnologia acima de R$ 300 exigem justificativa.

## Testes e Validacoes

Backend e banco:

```bash
docker compose exec backend alembic current
docker compose exec backend python scripts/check_schema.py
docker compose exec -e RUN_DB_TESTS=1 backend pytest
docker compose exec backend python scripts/validate_mvp_flow.py
```

Frontend:

```powershell
cd frontend
.\node_modules\.bin\tsc.cmd --noEmit --incremental false
npm run build
```

Validacao oficial local:

```bash
python backend/scripts/validate_official_files_local.py --source arquivos_oficiais
```

Use a validacao oficial apenas com `DATABASE_URL` apontando para um banco
descartavel ja migrado. O script imprime apenas metricas agregadas.

## Banco Descartavel Para Validacao Oficial

Exemplo usando o Postgres do Docker Compose:

```powershell
docker compose exec postgres psql -U finance_user -d postgres -c "DROP DATABASE IF EXISTS finance_decision_official_validation WITH (FORCE)"
docker compose exec postgres psql -U finance_user -d postgres -c "CREATE DATABASE finance_decision_official_validation"
docker compose exec -e DATABASE_URL=postgresql+psycopg://finance_user:change_me@postgres:5432/finance_decision_official_validation backend alembic upgrade head
$env:DATABASE_URL="postgresql+psycopg://finance_user:change_me@localhost:5432/finance_decision_official_validation"
python backend/scripts/validate_official_files_local.py --source arquivos_oficiais
docker compose exec postgres psql -U finance_user -d postgres -c "DROP DATABASE IF EXISTS finance_decision_official_validation WITH (FORCE)"
```

## Dados Sensiveis

Nao commite arquivos reais contendo CPF, conta, endereco, salario, fatura,
patrimonio ou extratos. Use:

- `fixtures/anonymized/` para fixtures versionadas;
- `fixtures/private/` para testes locais privados;
- `arquivos_oficiais/` para validacao local, mantido fora do Git.

## Documentacao Complementar

- `docs/USAGE.md`: uso operacional e validacoes.
- `docs/ADDING_PARSER.md`: como adicionar novo parser.
- `docs/FINAL_REVIEW_CHECKLIST.md`: checklist de revisao.
- `DATA_MODEL.md`: modelo de dados.
- `TASKS.md`: historico/plano de execucao.
- `CHANGELOG.md`: mudancas por versao.

## Regra de Engenharia

Primeiro dado confiavel. Depois automacao inteligente. Bronze, Silver e Gold
precisam estar corretos antes de qualquer camada de IA ou recomendacao mais
sofisticada.
