# Contratos de Parser

Todo parser converte arquivo bruto em registros canônicos validáveis com Pydantic.

## Interface mínima
```python
class ParserProtocol(Protocol):
    source_type: str
    supported_extensions: set[str]

    def detect(self, file_path: Path, metadata: dict) -> bool: ...
    def parse(self, file_path: Path, import_batch_id: UUID) -> ParsedDocument: ...
```

## Regras gerais
1. Parser nunca salva direto no core financeiro.
2. Parser escreve primeiro em bronze/staging.
3. Todo valor monetário vira `Decimal`.
4. Toda data vira `date` ISO.
5. Campo bruto é preservado em `raw_text` ou `raw_row`.
6. Todo registro tem `confidence_score` e `needs_review`.
7. CPF, conta, endereço e nome completo são mascarados em logs.
8. PDF é parseado em duas etapas: extração de texto/tabelas e normalização.
9. Testes comparam saída com `fixtures/expected`.

## Parsers do MVP
- `MercadoLivreAccountStatementCsvParser`
- `MercadoLivreManualCdbCsvParser`
- `SicoobPayrollPdfParser`
- `SicoobCheckingStatementPdfParser`
- `SicoobCardInvoicePdfParser`
- `SicoobInvestmentsPdfParser`
- `B3MonthlyConsolidatedXlsxParser`
- `B3AnnualConsolidatedXlsxParser`

## Regra Sicoob Previ
A contribuição do funcionário é desconto de folha e posição de previdência ilíquida. A empresa aporta valor equivalente a 3% do salário, mas a parte patrocinada só deve ser considerada desbloqueável após cumprir a regra de elegibilidade inicial de 5 anos. Sem informe da previdência, registrar como `estimated_employer_match` com `valuation_confidence = low`.
