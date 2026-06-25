# Fixtures e Arquivos Reais

Este projeto **não deve versionar documentos financeiros reais**. Os relatórios reais contêm CPF, endereço, conta, salário, fatura e patrimônio. Para permitir que o Codex implemente parsers funcionais sem expor esses dados, o projeto usa:

1. `fixtures/anonymized/`: arquivos sintéticos/anônimos com estrutura compatível com os formatos reais.
2. `fixtures/expected/`: saídas esperadas em JSON para testes de parsing.
3. `fixtures/private/`: pasta local, ignorada pelo Git, onde o usuário pode colocar PDFs/XLSX/CSV reais para validação manual.

## Regra operacional
- Desenvolver primeiro contra `fixtures/anonymized` e `fixtures/expected`.
- Validar arquivos reais apenas em `fixtures/private`.
- Nenhum arquivo real deve ser commitado.
- Logs com dados reais devem ser mascarados.

## Fixtures cobertas
| Fonte | Arquivo anônimo | Expected output |
|---|---|---|
| Mercado Livre extrato CSV | `fixtures/anonymized/mercado_livre/account_statement_sample.csv` | `fixtures/expected/mercado_livre_account_statement_expected.json` |
| Mercado Livre CDB manual CSV | `fixtures/anonymized/mercado_livre/cdb_position_sample.csv` | `fixtures/expected/cdb_position_expected.json` |
| Sicoob contracheque PDF | `fixtures/anonymized/sicoob/contracheque_sample.pdf` | `fixtures/expected/sicoob_payroll_expected.json` |
| Sicoob conta corrente PDF | `fixtures/anonymized/sicoob/extrato_conta_sample.pdf` | `fixtures/expected/sicoob_checking_statement_expected.json` |
| Sicoob cartão PDF | `fixtures/anonymized/sicoob/fatura_cartao_sample.pdf` | `fixtures/expected/sicoob_card_invoice_expected.json` |
| Sicoob investimentos PDF | `fixtures/anonymized/sicoob/investimentos_sicoob_sample.pdf` | `fixtures/expected/sicoob_investments_expected.json` |
| B3 consolidado mensal XLSX | `fixtures/anonymized/b3/relatorio-consolidado-mensal-sample.xlsx` | `fixtures/expected/b3_monthly_expected.json` |
| B3 consolidado anual XLSX | `fixtures/anonymized/b3/relatorio-consolidado-anual-sample.xlsx` | `fixtures/expected/b3_annual_expected.json` |

## Validação local com arquivos reais
Coloque arquivos reais em:

```text
fixtures/private/sicoob/
fixtures/private/b3/
fixtures/private/mercado_livre/
```

Depois rode, quando implementado:

```bash
python scripts/validate_private_fixtures.py --source fixtures/private
```

A saída deve trazer apenas contagens, totais e erros estruturais. Nunca imprimir CPF, conta, endereço ou nome completo.
