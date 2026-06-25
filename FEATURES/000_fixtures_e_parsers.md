# Feature 000 - Fixtures e Contratos de Parsers

## Objetivo
Permitir extração funcional sem versionar documentos financeiros reais.

## Contexto
Os arquivos reais contêm dados sensíveis. O sistema usa fixtures anônimas para testes automatizados e uma pasta privada ignorada pelo Git para validação local.

## Requisitos
- Usar `fixtures/anonymized` como fonte de testes.
- Usar `fixtures/expected` como golden files.
- Ignorar `fixtures/private` no Git.
- Criar parsers com interface padronizada.
- Nunca salvar direto no core financeiro.
- Escrever em bronze/staging antes de silver/gold.

## Regras
- Todo parser deve ter `detect()` e `parse()`.
- Todo parser deve retornar modelos Pydantic.
- Todo registro extraído deve ter `source_type`, `import_batch_id`, `confidence_score` e `needs_review`.
- Dados sensíveis devem ser mascarados em logs e respostas.

## Endpoints
- `POST /imports/detect-source`
- `POST /imports/upload`
- `GET /imports/{id}/preview`
- `POST /imports/{id}/approve`

## Testes
- Testar cada parser com fixture anônima.
- Comparar saída com JSON esperado.
- Testar arquivo duplicado por hash.
- Testar PDF com linhas quebradas.
- Testar CSV com vírgula decimal.

## Critérios de aceite
- Parser Mercado Livre CSV funcionando.
- Parser B3 mensal XLSX funcionando.
- Parser Sicoob PDF inicial funcionando com PDFs sintéticos.
- Nenhum dado sensível impresso em logs.
- Documentos reais só aceitos em `fixtures/private`.

## Prompt para Codex
Leia `BLUEPRINT.md`, `FIXTURES.md` e `PARSER_CONTRACTS.md`. Implemente a infraestrutura de parsers com Pydantic, testes Pytest e golden files. Comece pelo Mercado Livre CSV, depois B3 XLSX mensal, depois Sicoob PDF. Não implemente interface visual nesta etapa. Atualize `TASKS.md` e `CHANGELOG.md`.
