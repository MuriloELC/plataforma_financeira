# Review Checklist

## Produto
- [ ] Segue BLUEPRINT?
- [ ] Ajuda decisão financeira?
- [ ] Não adiciona escopo solto?

## Dados
- [ ] Respeita Bronze/Silver/Gold?
- [ ] Preserva bruto?
- [ ] Usa import_batch_id?
- [ ] Tem raw_reference?

## Banco
- [ ] Migration?
- [ ] FK/constraints?
- [ ] numeric para dinheiro?

## Backend
- [ ] Pydantic?
- [ ] Regra crítica no backend?
- [ ] Erros claros?

## Segurança
- [ ] Sem dados reais no Git?
- [ ] Logs seguros?
- [ ] Arquivos protegidos?

## Testes
- [ ] Caso feliz?
- [ ] Erro?
- [ ] Edge case financeiro?
- [ ] Regra R$300/reserva ×6 quando aplicável?

## Docs
- [ ] TASKS atualizado?
- [ ] CHANGELOG atualizado?

## Revisao final do MVP - Fase 10

## Produto
- [x] Segue BLUEPRINT.
- [x] Ajuda decisao financeira.
- [x] Nao adiciona escopo solto.

## Dados
- [x] Respeita Bronze/Silver/Gold.
- [x] Preserva bruto.
- [x] Usa import_batch_id.
- [x] Tem raw_reference.

## Banco
- [x] Migrations rodam do zero ate `20260625_0003`.
- [x] FK/constraints revisadas.
- [x] Dinheiro usa numeric/Decimal.

## Backend
- [x] Pydantic.
- [x] Regra critica no backend.
- [x] Erros claros.

## Seguranca
- [x] Sem dados reais no Git.
- [x] Logs/erros seguros.
- [x] Arquivos protegidos por `.gitignore` e storage local fora do Git.

## Testes
- [x] Caso feliz.
- [x] Erro.
- [x] Edge case financeiro.
- [x] Regra R$300/reserva x6 quando aplicavel.

## Docs
- [x] TASKS atualizado.
- [x] CHANGELOG atualizado.
