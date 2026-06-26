# 009 - Melhorias observadas em teste manual

## Implementacao

Status geral: implementada

- Criada migration `20260625_0004` com cadastros auxiliares, instituicao/bandeira no cartao e campos estruturados de investimento.
- Revisao agora lista lotes, mostra previa com registros, exige confirmacao de aprovacao e permite recusa com motivo.
- Importacao permite escolher tipo de arquivo, ver detalhe do arquivo e baixar o bruto por endpoint seguro.
- Dashboard/Gold atualizam automaticamente no carregamento, somam posicoes manuais distintas de reserva e ordenam compromissos por data crescente.
- UI passou a traduzir labels visiveis para portugues, mostrar historicos nas abas de cadastro, mover historico do simulador para dentro do modulo e usar Historico geral no menu lateral.
- Validado com `RUN_DB_TESTS=1 pytest` no container, `next build` e navegacao automatizada em Chrome sem erros de console.

## Revisao de importacoes

### 009.1 - Listar lotes pendentes na aba Revisao

Status: implementada

Problema:
- A tela de Revisao exige copiar manualmente o `import_batch_id` retornado no upload.
- Isso torna o fluxo menos ergonomico e aumenta chance de erro operacional.

Melhoria:
- A aba Revisao deve listar os lotes de importacao pendentes ou recentes.
- Cada lote deve mostrar fonte, status, data, arquivo mascarado e contagens agregadas.
- O usuario deve conseguir abrir a previa e aprovar o lote por clique, sem digitar UUID.

Criterios de aceite:
- Lotes `raw_extracted` aparecem como pendentes de revisao.
- Acoes de `Prever` e `Aprovar` ficam disponiveis na linha do lote.
- A tela mantem loading, erro e vazio.
- Nenhum caminho local, hash ou dado sensivel aparece na lista.

### 009.2 - Revisao com selecao, previa detalhada, aprovacao e recusa

Status: implementada

Problema:
- A previa joga o usuario para a aba Resultado, mas o resultado mostra resumo e nao mostra os registros interpretados.
- A aprovacao aprova direto, sem confirmacao.
- O fluxo fica confuso porque Previa e Aprovacao usam o mesmo destino visual.

Melhoria:
- A tela deve permitir selecionar um lote pendente.
- A previa deve mostrar os registros parseados em tabela compacta, com source type, totais e campos principais.
- Depois da previa, o usuario deve poder aprovar ou recusar o lote.
- A aprovacao deve pedir confirmacao antes de gravar em Silver.
- A recusa deve registrar status/motivo sem apagar o bruto.

Criterios de aceite:
- Selecionar lote pendente mostra detalhes do lote e registros parseados.
- Aprovar exige confirmacao explicita.
- Recusar exige motivo curto.
- Resultado final mostra contagens Silver ou motivo da recusa.
- Nenhum dado sensivel cru e exibido fora do necessario para revisao local.

## Dashboard

### 009.3 - Verificar soma da reserva no dashboard

Status: implementada

Problema:
- O card de Reserva parece mostrar apenas um CDB marcado como reserva, mesmo existindo mais de um investimento com `counts_as_reserve = true`.

Melhoria:
- Verificar se o card usa o endpoint Gold correto e se o Gold soma todos os ativos elegiveis para reserva.
- Conferir se investimentos manuais, posicoes importadas e duplicidades estao sendo agregados corretamente.

Criterios de aceite:
- O card de Reserva mostra a soma de todos os ativos elegiveis.
- A tabela/visao de alocacao permite identificar quais itens contam como reserva.
- Teste cobre dois ou mais ativos `counts_as_reserve = true`.

### 009.4 - Ordenar compromissos futuros por data crescente

Status: implementada

Problema:
- Compromissos futuros nao estao em ordem clara de vencimento.

Melhoria:
- Ordenar compromissos futuros por `due_month`/data em ordem crescente.

Criterios de aceite:
- Dashboard e modulo de Cartoes mostram compromissos futuros do mais antigo para o mais futuro.
- A ordenacao e consistente entre endpoint, dashboard e tabela.

## Importacao

### 009.5 - Permitir escolher o tipo de arquivo na importacao

Status: implementada

Problema:
- O upload depende somente da deteccao automatica do sistema para descobrir a fonte/tipo do arquivo.

Melhoria:
- Na tela de importacao, permitir selecionar o tipo/fonte do arquivo antes de enviar.
- A deteccao automatica pode continuar como sugestao, mas o usuario deve conseguir confirmar ou ajustar.

Criterios de aceite:
- Campo de tipo/fonte aparece no upload.
- Opcoes incluem os tipos suportados do MVP: Mercado Livre CSV, B3 XLSX mensal/anual, Sicoob extrato, Sicoob fatura, Sicoob investimentos e contracheque.
- Backend valida que a escolha e compativel com a extensao.
- Historico registra tipo escolhido e tipo detectado, sem expor conteudo sensivel.

### 009.6 - Melhorar tabela de arquivos importados

Status: implementada

Problema:
- A aba Arquivos nao mostra informacoes suficientes para auditar o upload rapidamente.

Melhoria:
- Mostrar data e hora da importacao.
- Adicionar acoes de visualizar detalhes e baixar arquivo, respeitando seguranca local.

Criterios de aceite:
- Lista mostra arquivo mascarado, source type, status, data/hora e contagens.
- Visualizar abre detalhe do raw/import batch sem caminho local completo nem hash.
- Baixar arquivo exige endpoint seguro e nao expoe caminhos do storage.

## Lancamentos

### 009.7 - Traduzir tipos, categorias e registros visiveis para portugues

Status: implementada

Problema:
- Alguns tipos aparecem em ingles, como `expense`, `income`, `investment`, `open`, `closed`, `paid` e similares.

Melhoria:
- Mostrar labels em portugues em todas as telas.
- Avaliar se valores persistidos no banco tambem devem ser migrados/traduzidos ou se basta uma camada de apresentacao com mapeamento.

Criterios de aceite:
- Usuario nao ve enums internos em ingles nas telas.
- Categorias, status, tipos de transacao, tipos de conta, status de fatura e similares aparecem em portugues.
- APIs continuam validando valores de forma consistente.

## Investimentos

### 009.8 - Tornar alocacao e origem dos investimentos mais claras

Status: implementada

Problema:
- A coluna `%` na alocacao fica vaga sem explicar percentual de que.
- A tela nao deixa claro origem, produto e classe de cada investimento.

Melhoria:
- Renomear `%` para algo como `% da carteira`.
- Mostrar origem do investimento: manual, B3, Sicoob, Mercado Livre ou outro source type.
- Mostrar produto e classe em colunas separadas quando houver detalhe suficiente.

Criterios de aceite:
- Percentual explicita que representa participacao na carteira/patrimonio.
- Cada linha mostra origem e produto quando disponivel.
- Reserva e patrimonio ficam visualmente diferenciados.

### 009.9 - Estruturar cadastro de produto, classe, taxa e liquidez

Status: implementada

Problema:
- Produto/classe poderiam ser configuraveis e selecionados, em vez de sempre digitados livremente.
- Taxa e liquidez como texto livre dificultam interpretacao futura.

Melhoria:
- Criar cadastros/configuracoes para classes e produtos de investimento.
- Taxa deve permitir tipo estruturado: prefixada, pos-fixada, indexada ou composta.
- Permitir indexador como CDI, Selic, IPCA ou outro.
- Permitir percentual, spread e periodicidade quando aplicavel.
- Liquidez deve ser selecionavel: diaria, D+1, D+30, vencimento, iliquido ou personalizada.

Criterios de aceite:
- Cadastro manual de investimento seleciona classe/produto de listas configuradas.
- Taxa consegue representar exemplos como `100% CDI`, `IPCA + 0,07%`, `Selic + spread` e taxa fixa anual/mensal.
- Liquidez fica estruturada e comparavel.

## Cartoes

### 009.10 - Cadastro global de instituicoes

Status: implementada

Problema:
- Varias telas pedem para digitar instituicao manualmente.

Melhoria:
- Criar cadastro de instituicoes reutilizavel no projeto inteiro.
- Telas de contas, investimentos, cartoes e importacoes devem selecionar instituicao cadastrada.

Criterios de aceite:
- Instituicoes podem ser cadastradas, editadas e inativadas.
- Telas usam selecao em vez de texto livre quando possivel.
- Registros antigos continuam funcionando.

### 009.11 - Melhorar cadastro de cartao

Status: implementada

Problema:
- Bandeira e digitada livremente.
- Campo `final` nao deixa claro que sao os ultimos 4 digitos.
- Nao existe indicacao se o cartao e virtual.

Melhoria:
- Criar cadastro/lista de bandeiras, pre-populada com principais opcoes.
- Alterar label para `Ultimos 4 digitos`.
- Adicionar campo `Cartao virtual`.

Criterios de aceite:
- Bandeiras principais aparecem como opcoes.
- Campo de final aceita apenas 4 digitos.
- Cartao virtual fica marcado no cadastro e na listagem.

### 009.12 - Mostrar historico de compras no modulo Cartoes

Status: implementada

Problema:
- A aba Compras hoje serve para cadastrar, mas nao mostra o historico de compras.

Melhoria:
- Exibir compras ja cadastradas/importadas, com filtro por cartao, fatura, categoria e periodo.

Criterios de aceite:
- Compras aparecem em tabela apos cadastro/importacao.
- Compra parcelada mostra parcela atual/total.
- Existe acao para ver detalhes da compra.

## Indicadores

### 009.13 - Automatizar refresh Gold

Status: implementada

Problema:
- Atualizacao de indicadores depende de acao manual explicita.

Melhoria:
- Avaliar refresh automatico apos aprovacao de importacao, cadastro manual relevante ou abertura da tela de Indicadores/Dashboard.

Criterios de aceite:
- Gold atualiza automaticamente apos eventos que mudam Silver/manual.
- UI mostra quando foi o ultimo refresh.
- Usuario ainda pode rodar refresh manual se quiser.

## Simulador e historico

### 009.14 - Mostrar resultado do simulador na mesma aba e mover historico para dentro do modulo

Status: implementada

Problema:
- A aba Resultado no simulador pode ser desnecessaria.
- Historico como item separado no menu lateral fica estranho para historico de decisoes do simulador.

Melhoria:
- Mostrar resultado da simulacao abaixo do formulario.
- Trocar a aba Resultado por Historico dentro do modulo Simulador.
- Transformar o item Historico do menu lateral em historico geral do sistema.

Criterios de aceite:
- Simulacao mostra veredito, explicacao e impactos abaixo do formulario.
- Historico de decisoes fica dentro de Simulador.
- Menu Historico vira trilha geral de uploads, aprovacoes, recusas, cadastros e alteracoes.

## Configuracoes

### 009.15 - Adicionar menu Config para cadastros auxiliares

Status: implementada

Problema:
- Cadastros auxiliares ficam misturados em telas operacionais ou aparecem como texto livre.

Melhoria:
- Criar menu Configuracoes para cadastrar, editar e inativar entidades auxiliares.
- Incluir instituicoes, bandeiras de cartao, classes/produtos de investimento, tipos de conta e outros cadastros reutilizaveis.

Criterios de aceite:
- Config permite cadastrar, editar e inativar itens auxiliares.
- Telas operacionais consomem esses cadastros.
- Itens inativos nao aparecem como opcao padrao, mas continuam preservando historico.

## Geral

### 009.16 - Mostrar historico/listagem em todas as abas de cadastro

Status: implementada

Problema:
- Algumas abas servem apenas para cadastrar e nao mostram o que ja existe.

Melhoria:
- Em telas de cadastro, mostrar tambem a lista/historico dos registros existentes.
- Usar botao `Novo` ou acao equivalente para abrir formulario de cadastro quando necessario.

Criterios de aceite:
- Cada modulo permite ver registros existentes sem sair da tela.
- Cadastro novo fica claro e separado da listagem.
- Estados vazio, loading e erro existem em todos os modulos.
