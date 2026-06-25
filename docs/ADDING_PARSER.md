# Como adicionar um novo parser

## Regra principal

Parser nunca grava direto em Silver ou Gold. Ele converte arquivo bruto em objetos Pydantic com origem preservada. A persistencia acontece depois, no fluxo de revisao/aprovacao.

## Passos

1. Atualize `PARSER_CONTRACTS.md` se a fonte exigir contrato novo.
2. Adicione fixture anonima em `fixtures/anonymized/`.
3. Adicione saida esperada em `fixtures/expected/`.
4. Crie a classe em `backend/app/parsers/`.
5. Registre a classe em `backend/app/parsers/__init__.py` e `backend/app/parsers/registry.py`.
6. Atualize deteccao em `backend/app/services/source_detection.py`.
7. Garanta que cada registro tenha `import_batch_id`, `source_file_id`, `raw_reference`, `confidence_score` e `needs_review`.
8. Adicione teste em `backend/tests/test_parsers.py` comparando com golden file.
9. Se a fonte for aprovada para Silver, implemente normalizacao em `backend/app/services/import_review.py` e testes de integracao.
10. Atualize `TASKS.md` e `CHANGELOG.md`.

## Cuidados com privacidade

- Nunca usar arquivos reais fora de `fixtures/private/`.
- Nunca commitar PDFs, CSVs ou XLSX reais.
- Nao imprimir CPF, endereco, conta, salario, fatura ou patrimonio em logs.
- Use `mask_sensitive_text` ou `mask_sensitive_value` de `backend/app/core/privacy.py` para mensagens e erros estruturados.
- Preserve bruto no Bronze, mas exponha respostas de API com campos mascarados quando houver risco.

## Exemplo minimo de parser

```python
class MinhaFonteParser:
    source_type = "minha_fonte_csv"
    supported_extensions = {".csv"}

    def detect(self, file_path: Path, metadata: dict | None = None) -> bool:
        return file_path.suffix.lower() == ".csv"

    def parse(
        self,
        file_path: Path,
        import_batch_id: UUID,
        source_file_id: UUID | None = None,
    ) -> ParsedDocument:
        records = [
            make_record(
                source_type=self.source_type,
                import_batch_id=import_batch_id,
                source_file_id=source_file_id,
                data={"description": "Exemplo", "amount": Decimal("10.00")},
                raw_reference={"raw_line": 1},
            )
        ]
        return ParsedDocument(
            source_type=self.source_type,
            import_batch_id=import_batch_id,
            source_file_id=source_file_id,
            records=records,
        )
```

## Checklist antes de concluir

- [ ] Fixture anonima criada.
- [ ] Golden file criado.
- [ ] Parser retorna Pydantic.
- [ ] Erro de parsing e controlado.
- [ ] Dados sensiveis nao aparecem em erro/log.
- [ ] Parser nao grava no Gold.
- [ ] Testes passam.
- [ ] TASKS e CHANGELOG atualizados.
