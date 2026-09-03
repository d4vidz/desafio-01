# Contrato de comunicação dos notebooks Marimo

Este documento é o contrato preventivo para a comunicação dos notebooks do projeto. A narrativa deve nascer junto da implementação, não como revisão editorial posterior. Ele atende à issue #67 e à especificação #69; o handoff de agentes é definido em #68.

## Público e objetivo

Cada notebook deve ser legível por uma pessoa que não acompanhou a implementação. Comentários internos podem registrar detalhes técnicos, mas não substituem uma explicação no fluxo principal.

## Seção narrativa obrigatória

Cada resultado ou visualização principal deve registrar, de forma visível:

1. **Pergunta:** o que estamos tentando aprender?
2. **População e filtros:** quais linhas, faixas, gêneros ou artistas entram?
3. **Grain:** o que representa uma observação?
4. **Método:** qual foi o cálculo, explicado sem depender de conhecimento do código?
5. **Como ler:** significado de eixos, cor, tamanho, distância, ordem e controles.
6. **Denominador:** tamanho da amostra, top-*n*, agregação e tratamento de memberships.
7. **Resultado:** número ou padrão calculado nesta execução, derivado da mesma tabela do gráfico.
8. **Interpretação:** o que o snapshot permite dizer.
9. **Limite:** o que não pode ser concluído, incluindo seleção, incerteza e proveniência.
10. **Status:** infraestrutura, protótipo, experimento completo ou evidência validada.

Informação essencial deve estar disponível sem interação. Accordion pode conter SQL, detalhes de schema e diagnóstico; tooltip pode complementar, mas não pode ser a única explicação.

## Primitivas e reatividade

Use `NarrativeSection` e o renderer de `spotify_data.notebook_ui` quando a entrega já os disponibilizar. O texto deve receber métricas e tabelas da mesma célula ou pipeline que alimenta a figura. Evite números copiados manualmente.

Widgets devem declarar default, efeito no denominador e limites de renderização. Um filtro que produz uma população esparsa deve mostrar aviso. Outputs devem permanecer abaixo do limite definido pelo projeto.

## Linguagem de claims

- associação: variáveis se movem juntas no snapshot;
- comparação: grupos diferem sob o recorte declarado;
- previsão: desempenho em dados held-out;
- causalidade: só com desenho que a sustente.

`popularity` é o score observado, não uma promessa de sucesso futuro. Não use “causa” ou “impacta” quando o método só mostra associação. Resultados exploratórios devem dizer que geram hipóteses.

## Checklist de revisão

- [ ] Uma pessoa sem contexto consegue explicar a pergunta e a unidade.
- [ ] O gráfico e o texto usam a mesma população e agregação.
- [ ] A leitura dos encodings está explícita.
- [ ] O resultado muda corretamente quando o widget muda.
- [ ] O status e o claim ceiling aparecem no HTML estático.
- [ ] Filtros, amostras, esparsidade e limitações estão visíveis.
- [ ] Testes, HTML e manifest foram atualizados.

Consulte [glossary.md](glossary.md) para a terminologia. A versão em inglês é uma tradução de apoio; o português é canônico.
