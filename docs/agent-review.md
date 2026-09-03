# Handoff Luna → Sol e auditoria de entregas

Este contrato organiza a revisão agêntica descrita na issue #68. Luna executa uma unidade delimitada; Sol audita de forma independente. Nenhum agente promove protótipo, resolve discussão ou fecha issue silenciosamente.

## Pacote de trabalho Luna

Cada execução começa com issue/Task, especificação, fixed point, branch, arquivos autorizados, não objetivos, critérios de aceite e testes. O coordenador Luna pode dividir o trabalho, mas mantém o escopo e consolida o handoff.

## Índice de entrega obrigatório

Ao terminar, Luna deve publicar no MR um índice com:

- issue-pai e Task;
- fixed point, branch e commit(s);
- arquivos, funções e seções de notebook alterados;
- contrato atendido e decisões tomadas;
- HTML, manifest e demais artefatos;
- comandos executados e resultados;
- CI/pipeline e ambiente;
- riscos, limitações, desvios e itens adiados;
- pontos que Sol deve verificar.

Use links endereçáveis para arquivos, commits, jobs, issues e artefatos. Um índice deve permitir que Sol localize cada afirmação sem ingerir contexto repetido.

## Auditoria Sol

Sol recebe o MR, o índice, o diff, as specifications relacionadas, documentação de padrões, manifest, HTML e pipeline. A auditoria verifica quatro eixos independentes:

1. **Spec:** aderência a decisões, invariantes e critérios.
2. **Código:** bugs, interfaces, duplicação, testes e convenções.
3. **Análise:** grain, leakage, denominadores, fórmulas, seeds, incerteza e reprodutibilidade.
4. **Comunicação:** pergunta, leitura, resultado, caveats, status e claim ceiling.

Sol pode executar testes, criar fixtures e sugerir checks ausentes. Não altera silenciosamente a entrega. Findings devem indicar localização, evidência, severidade, impacto e correção recomendada:

- **P0/P1:** bloqueia merge;
- **P2:** corrigir ou registrar follow-up aceito;
- **P3:** recomendação não bloqueante.

Depois da correção, Luna responde ao finding e Sol revalida os eixos afetados. A decisão de merge é humana.

## Roteamento e segurança

Mudanças em schema/grain, estatística, modelagem, claims, grafos, CI ou integrador exigem specification e auditoria Sol. Mudanças pequenas e isoladas podem usar a entrega diretamente, desde que o contrato narrativo seja preenchido. O índice nunca deve conter tokens, segredos ou dados pessoais.

O relatório final deve distinguir “passou”, “falhou”, “não executado” e “inconclusivo”; HTTP 200 de um preview Molab não prova execução.
