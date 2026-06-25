# Feature 001 — Ingestão de Arquivos

## Objetivo
Permitir upload de CSV, XLSX e PDF, registrar tudo no Bronze e preparar para parsers.

## Requisitos
- Upload com hash SHA-256.
- Detecção de duplicidade.
- Criação de `raw_files` e `import_batches`.
- Extração bruta para CSV/XLSX/PDF.
- Registro de erros.

## Regras
- Preservar arquivo original.
- Nenhum dado vai direto para Gold.
- Mascarar sensíveis na exibição.

## Modelagem
- `bronze.raw_files`
- `bronze.import_batches`
- `bronze.raw_csv_rows`
- `bronze.raw_xlsx_rows`
- `bronze.raw_pdf_pages`
- `bronze.parser_errors`

## Endpoints
- `POST /files/upload`
- `GET /files`
- `GET /import-batches/{id}`
- `POST /import-batches/{id}/parse`

## Telas
- Upload.
- Lista de importações.
- Detalhe do lote.
- Erros.

## Testes
- Upload válido.
- Upload duplicado.
- CSV/XLSX/PDF bruto salvo.

## Critérios de aceite
- Hash calculado.
- Lote criado.
- Bruto persistido.
- Erros rastreáveis.

## Prompt para Codex
```text
Implemente a feature de ingestão de arquivos com Bronze. Não implemente parsers específicos além da extração bruta.
```
