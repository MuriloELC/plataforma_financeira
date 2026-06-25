# SPEC — Especificação Funcional e Técnica

## 1. Requisitos funcionais

### RF001 — Upload de arquivos

O sistema deve aceitar CSV, XLSX e PDF. Cada arquivo deve gerar:

- `raw_file`;
- hash SHA-256;
- caminho local;
- metadados;
- `import_batch`;
- status de processamento.

### RF002 — Bronze

Bronze deve armazenar:

- linhas de CSV;
- linhas/abas de XLSX;
- texto de páginas PDF;
- erros de parser;
- referência de lote.

### RF003 — Silver

Silver deve armazenar dados normalizados:

- transações;
- contas;
- cartões;
- faturas;
- compras;
- parcelas;
- investimentos;
- posições;
- renda passiva;
- contracheques;
- categorias.

### RF004 — Gold

Gold deve conter:

- renda passiva mensal;
- progresso até R$ 100 mil;
- status da reserva;
- alocação de carteira;
- fluxo mensal;
- gastos por categoria;
- compromissos futuros;
- contexto para simulador.

### RF005 — Cadastro manual

Permitir cadastro manual de:

- transações;
- investimentos;
- renda passiva;
- rendimento acumulado;
- faturas;
- parcelas;
- previdência.

Todo cadastro manual deve gerar auditoria.

### RF006 — B3

Importar relatórios XLSX B3 mensal/anual. Abas esperadas:

- Posição - Ações;
- Posição - ETF;
- Posição - FII;
- Posição - Renda Fixa;
- Proventos Recebidos;
- Negociações.

### RF007 — Mercado Livre

Importar CSV com blocos de saldo e movimentações. Rendimentos devem ser classificados como renda/rendimento financeiro, não renda de trabalho.

### RF008 — Cartão e fatura

Modelar:

- cartão;
- fatura;
- vencimento;
- pagamento mínimo;
- limite;
- compras;
- parcelas;
- compromissos futuros.

### RF009 — Contracheque

Modelar:

- competência;
- data de pagamento;
- salário base;
- vencimentos;
- descontos;
- líquido;
- FGTS como informação;
- Sicoob Previ como previdência ilíquida.

### RF010 — Simulador “Posso Comprar?”

Entrada:

- item;
- valor;
- categoria;
- forma de pagamento;
- parcelas;
- urgência;
- justificativa;
- planejado ou não;
- tecnologia ou não.

Saída:

- veredito;
- impacto no aporte;
- impacto na reserva;
- impacto em parcelas futuras;
- impacto no progresso R$ 100 mil;
- explicação;
- recomendação.

## 2. Requisitos não funcionais

### Segurança

- Não armazenar senhas bancárias.
- Não commitar arquivos reais.
- Mascarar dados sensíveis na UI.
- Proteger storage local.
- Logs sem CPF/endereço/conta completos.

### Qualidade

- Testes obrigatórios.
- Parsers determinísticos.
- Pydantic para validação.
- Decimal para dinheiro.
- Gold só usa dados aprovados/revisados.

### Auditabilidade

- Todo dado derivado referencia origem.
- Todo manual tem auditoria.
- Toda alteração relevante gera log.

## 3. Casos de uso

### UC001 — Importar Mercado Livre CSV

1. Upload.
2. Hash.
3. Bronze.
4. Parser.
5. Validação.
6. Revisão.
7. Silver.
8. Gold refresh.

### UC002 — Importar B3 XLSX

1. Upload.
2. Leitura de abas.
3. Bronze.
4. Parser de posições/proventos/negociações.
5. Silver.
6. Gold de investimentos.

### UC003 — Cadastro manual de CDB

1. Usuário informa produto, saldo, taxa, liquidez e vencimento.
2. Define se conta como reserva.
3. Sistema valida e audita.
4. Gold atualiza.

### UC004 — Simular compra

1. Usuário informa compra.
2. Backend busca contexto Gold.
3. Calcula impacto.
4. Retorna veredito.
5. Exige justificativa quando necessário.
6. Salva histórico.

## 4. Fluxos

### Ingestão

```text
upload → bronze → parser → pydantic → silver staging → revisão → silver oficial → gold
```

### Manual

```text
formulário → pydantic → silver → audit → gold
```

### Decisão

```text
input compra → contexto gold → regras → veredito → justificativa → histórico
```

## 5. Qualidade dos dados

Cada registro normalizado deve ter:

- `source_file_id`;
- `import_batch_id`;
- `raw_reference`;
- `confidence_score`;
- `needs_review`;
- `review_status`.

## 6. Definition of Done

Uma feature está pronta quando:

- tem migration se envolver banco;
- tem schema Pydantic;
- tem serviço/backend;
- tem testes;
- TASKS.md atualizado;
- CHANGELOG.md atualizado;
- não viola BLUEPRINT.
