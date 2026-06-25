# CODEX_INSTRUCTIONS — Instruções para Codex

## Ordem obrigatória de leitura

1. BLUEPRINT.md
2. SPEC.md
3. ARCHITECTURE.md
4. DATA_MODEL.md
5. TASKS.md
6. Feature correspondente em FEATURES/
7. .codex/project-rules.md

## Regras

- Nunca implemente sem ler BLUEPRINT.md.
- Nunca implemente requisito fora do escopo.
- Sempre atualize TASKS.md.
- Sempre atualize CHANGELOG.md.
- Sempre crie testes.
- Sempre valide antes de declarar concluído.
- Divida tarefas grandes.
- Peça revisão quando houver ambiguidade.
- Não invente requisitos fora do blueprint.

## Banco

- Toda alteração de schema exige migration Alembic.
- Não alterar migration antiga aplicada.
- Dinheiro usa Decimal/numeric.

## Medalhão

- Bronze: bruto.
- Silver: normalizado/revisado.
- Gold: indicadores/decisão.

Proibido salvar parser direto no Gold.

## Dados reais

Nunca commitar:

- extratos reais;
- faturas reais;
- contracheques reais;
- relatórios reais;
- `.env`;
- dumps;
- storage local.

## Simulador

- Não usar IA no MVP.
- Motor deve ser determinístico.
- Compra não planejada > R$ 300 exige simulação.
- Tecnologia > R$ 300 exige justificativa.
- Vereditos: Comprar agora, Comprar com ajuste, Esperar, Evitar.

## IA futura

IA só depois de Gold confiável.

Quando existir:

- usar Gold primeiro;
- Silver apenas para investigação;
- nunca inventar números;
- dizer quando faltar dado.

## Formato de conclusão de tarefa

Ao finalizar, responder:

- o que foi implementado;
- arquivos alterados;
- testes criados;
- comandos executados;
- resultado dos testes;
- pendências;
- riscos.
