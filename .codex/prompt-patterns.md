# Prompt Patterns

## Implementar tarefa

```text
Leia CODEX_INSTRUCTIONS.md, BLUEPRINT.md, SPEC.md, ARCHITECTURE.md, DATA_MODEL.md e TASKS.md.
Implemente somente a tarefa [ID].
Crie testes.
Atualize TASKS.md e CHANGELOG.md.
```

## Criar migration

```text
Atue como Database Architect. Crie migration Alembic para [tabela] conforme DATA_MODEL.md, com constraints e teste.
```

## Criar parser

```text
Atue como Data Engineer. Implemente parser para [fonte] retornando objetos Pydantic e erros estruturados. Não salve direto no banco.
```

## Criar endpoint

```text
Atue como Backend Engineer. Implemente endpoint [rota], com service, repository, schemas e testes.
```

## Criar tela

```text
Atue como Frontend Engineer. Implemente tela [nome] consumindo endpoints existentes. Não calcule regra financeira crítica no frontend.
```

## Revisar

```text
Atue como QA/Test Engineer e Security Reviewer. Revise a implementação contra .codex/review-checklist.md.
```
