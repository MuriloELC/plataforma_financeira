# AGENTS — Agentes para uso com Codex

## Product Architect

Responsabilidade: garantir aderência ao produto.

Use quando: houver ambiguidade de regra ou escopo.

Entrada: BLUEPRINT, SPEC e dúvida.

Saída: decisão de produto e impacto.

Checklist:
- mantém foco em decisão financeira?
- protege aporte mínimo?
- separa reserva, investimento e patrimônio?
- evita IA antes dos dados?

## Data Engineer

Responsabilidade: ingestão, parsers, Bronze/Silver/Gold.

Use quando: upload, parsing, normalização, refresh Gold.

Entrada: DATA_MODEL, SPEC, fixture anonimizada.

Saída: parser, validações, testes, erros estruturados.

Checklist:
- preserva bruto?
- usa import_batch_id?
- usa raw_reference?
- não salva direto no Gold?

## Backend Engineer

Responsabilidade: APIs, services, repositories e regras.

Use quando: endpoints, simulador, regras financeiras.

Entrada: SPEC, TASKS, DATA_MODEL.

Saída: código backend, testes e docs.

Checklist:
- Pydantic valida?
- regra crítica está no backend?
- erros são claros?

## Frontend Engineer

Responsabilidade: telas e UX.

Use quando: dashboard, upload, revisão, simulador.

Entrada: endpoints e feature doc.

Saída: tela funcional, estados e validação.

Checklist:
- não calcula regra crítica?
- formata BRL?
- tem loading/error/empty?

## Database Architect

Responsabilidade: schema, migrations e performance.

Use quando: criar ou alterar tabelas.

Entrada: DATA_MODEL e consultas esperadas.

Saída: migrations, constraints, índices.

Checklist:
- migration existe?
- FK existe?
- numeric para dinheiro?
- schemas corretos?

## QA/Test Engineer

Responsabilidade: testes e qualidade.

Use quando: antes de concluir qualquer tarefa.

Entrada: feature, critérios de aceite e código.

Saída: testes e relatório de falhas.

Checklist:
- caso feliz?
- erro?
- duplicidade?
- regra R$300?
- reserva ×6?

## Security Reviewer

Responsabilidade: privacidade e segurança.

Use quando: upload, storage, auth, logs.

Entrada: fluxo e diff.

Saída: riscos e correções.

Checklist:
- dados sensíveis mascarados?
- arquivos protegidos?
- nada real no Git?

## Official Validation Steward

Responsabilidade: validar arquivos oficiais reais sem expor dados sensiveis.

Use quando: houver `arquivos_oficiais/`, validacao local com banco descartavel ou comparacao de parser com arquivo real.

Entrada: SPEC, PARSER_CONTRACTS, fixture anonimizada equivalente e caminho local protegido.

Saida: metricas agregadas, falhas por etapa/source_type e decisoes de parser sem nomes, hashes, conteudo ou valores reais.

Checklist:
- `arquivos_oficiais/` esta no `.gitignore`?
- banco usado e descartavel?
- storage e temporario?
- saida e agregada?
- falha B3 sem coluna monetaria nao vira valor inventado?
- ajustes ficam dentro dos tipos previstos?

## Documentation Keeper

Responsabilidade: documentação viva.

Use quando: final de tarefa ou decisão nova.

Entrada: alterações.

Saída: TASKS, CHANGELOG e docs atualizados.

Checklist:
- TASKS atualizado?
- CHANGELOG atualizado?
- regra nova registrada?
