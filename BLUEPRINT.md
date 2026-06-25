# BLUEPRINT — Sistema de Gestão Financeira Pessoal

Este é o arquivo central do projeto. O Codex deve lê-lo antes de qualquer implementação.

## 1. Visão do produto

Criar um sistema financeiro pessoal que transforma arquivos, cadastros manuais e dados de investimento em uma base confiável para decisão. O sistema deve mostrar números, aconselhar com base em regras, proteger aportes e quantificar consequências antes de compras relevantes.

O produto deve funcionar como um **sistema de decisão financeira**, não apenas como gerenciador de gastos.

## 2. Objetivos

### Objetivos financeiros

- Consolidar renda, gastos, cartões, investimentos, reserva e metas.
- Medir renda passiva recebida e rendimento acumulado separadamente.
- Acompanhar progresso até R$ 100 mil investidos.
- Acompanhar rota futura para R$ 5 mil/mês de renda passiva.
- Proteger aporte mínimo mensal inicial de R$ 300.
- Calcular reserva alvo por média dos gastos dos últimos 3 meses × 6.

### Objetivos comportamentais

- Forçar pré-decisão para compras não planejadas acima de R$ 300.
- Exigir justificativa para compras de tecnologia acima de R$ 300.
- Mostrar impacto de compras no aporte, reserva, parcelas futuras e meta de R$ 100 mil.
- Evitar autoengano: o sistema não bloqueia, mas quantifica a consequência.

### Objetivos técnicos

- Arquitetura medalhão com Bronze/Silver/Gold.
- Ingestão auditável por arquivo.
- Cadastro manual quando integração for inviável.
- Parsers isolados por fonte.
- Validação com Pydantic.
- Banco PostgreSQL com SQLAlchemy + Alembic.
- Testes para parsers, regras e cálculos.
- Evolução incremental com Codex.

## 3. Escopo MVP

1. Estrutura base backend/frontend/banco.
2. Schemas PostgreSQL: `bronze`, `silver`, `gold`, `app`, `audit`.
3. Upload de arquivos com hash SHA-256.
4. Bronze para CSV, XLSX e PDF.
5. Parser CSV Mercado Livre/Mercado Pago.
6. Parser XLSX B3 mensal/anual.
7. Cadastro manual de investimentos.
8. Cadastro manual de transações.
9. Categorias e regras de categorização.
10. Modelagem de cartões, faturas e parcelas.
11. Gold inicial: renda passiva, R$ 100 mil, reserva, alocação e compromissos futuros.
12. Simulador “Posso Comprar?”.
13. Dashboard básico.
14. Testes automatizados.

## 4. Escopo futuro

- Parser PDF Sicoob conta.
- Parser PDF Sicoob fatura cartão.
- Parser PDF Sicoob investimentos.
- Parser PDF contracheque.
- Prefect para orquestração.
- dbt para Gold.
- IA consultora usando apenas Gold/Silver revisado.
- Relatórios mensais automáticos.
- Alertas e recomendações.
- Open Finance, apenas se fizer sentido.

## 5. Fontes previstas

| Fonte | Tipo | Tratamento |
|---|---|---|
| Mercado Livre/Mercado Pago | CSV | Parser MVP |
| B3 mensal/anual | XLSX | Fonte oficial de bolsa/renda fixa registrada |
| Sicoob conta | PDF | Futuro parser |
| Sicoob cartão | PDF | Futuro parser/manual no MVP |
| Sicoob investimentos | PDF | Futuro parser/manual no MVP |
| Contracheque Sicoob | PDF | Futuro parser/manual no MVP |
| CDB Mercado Livre | Manual | Cadastro manual |
| INCO | Manual | Cadastro manual |
| Sicoob Previ | Manual | Previdência ilíquida |

## 6. Regras de negócio

### Reserva

- Reserva alvo = média dos gastos mensais dos últimos 3 meses × 6.
- Só entram na reserva ativos líquidos e seguros marcados como `counts_as_reserve = true`.
- Renda fixa B3 com liquidez desconhecida conta como patrimônio apenas.
- Ações, ETFs, FIIs, INCO, previdência e fundos de ações não contam como reserva.
- FGTS aparece apenas como informação, não patrimônio operacional.

### Investimentos

- B3 é fonte oficial para ações, ETFs, FIIs e renda fixa registrada.
- Relatório mensal B3 é snapshot oficial do fim do mês.
- Progresso até R$ 100 mil considera apenas investimentos.
- Cadastro manual cobre produtos fora da B3.
- Sicoob Previ é previdência/investimento ilíquido: 3% funcionário + 3% empresa; parte patrocinada só resgatável conforme regra de carência/vesting de 5 anos.

### Renda passiva

Separar:

- renda recebida: dividendos, JCP, FIIs, juros pagos, rendimentos creditados;
- rendimento acumulado: valorização e rendimento ainda não recebido/resgatado.

A tela deve mostrar renda passiva primeiro, mas sem incentivar ilusão: renda passiva pequena é placar, o jogo é aporte e patrimônio.

### Cartões

- Para comportamento: compra conta no mês da compra.
- Para caixa: fatura conta no mês do pagamento.
- Pagamento de fatura no extrato não deve duplicar despesas já importadas da fatura.
- Parcelas futuras alimentam compromissos futuros.

### Pré-decisão

- Compra não planejada acima de R$ 300 exige simulação.
- Compra de tecnologia acima de R$ 300 exige justificativa.
- Vereditos: Comprar agora, Comprar com ajuste, Esperar, Evitar.
- Se reduzir aporte mínimo, pode aprovar somente com justificativa e atraso explícito.

## 7. Entidades principais

- Arquivo bruto
- Lote de importação
- Registro bruto
- Conta
- Transação
- Categoria
- Regra de categorização
- Cartão
- Fatura
- Compra de cartão
- Parcela
- Ativo financeiro
- Posição de investimento
- Movimento de investimento
- Renda passiva
- Contracheque
- Previdência
- Reserva
- Meta
- Decisão de compra
- Alerta
- Auditoria

## 8. Arquitetura de dados

```text
Arquivo/manual
→ Bronze: bruto e auditável
→ Silver: limpo, normalizado, revisado
→ Gold: indicadores, contexto de decisão e dashboard
```

## 9. Critérios de aceite globais

- Todo upload gera arquivo bruto e lote.
- Todo arquivo tem hash.
- Todo dado derivado mantém referência à origem.
- Nenhum parser salva direto no Gold.
- Todo cálculo crítico tem teste.
- Dados manuais têm auditoria.
- Dashboard separa reserva, investimentos, patrimônio e renda passiva.
- Simulador explica consequência, não apenas status.

## 10. Roadmap

### Fase 0 — Base
Backend, frontend, banco, Docker, migrations e healthcheck.

### Fase 1 — Bronze
Upload, hash, raw files, import batches e extração bruta.

### Fase 2 — Silver inicial
Mercado Livre CSV, lançamentos manuais, categorias.

### Fase 3 — Investimentos
B3 XLSX, cadastro manual, renda passiva e progresso R$ 100 mil.

### Fase 4 — Cartões
Cartões, faturas, compras, parcelas e compromissos futuros.

### Fase 5 — Gold/Dashboard
KPIs e telas principais.

### Fase 6 — Simulador
Motor de decisão, justificativa e histórico.

### Fase 7 — IA consultora
Somente após dados Gold confiáveis.
