# Glossário do projeto

Termos abaixo devem ser usados de forma consistente nos notebooks, issues, MRs e evidence briefs.

| Termo | Definição operacional |
| --- | --- |
| **linha física** | Uma linha presente no CSV de origem; pode repetir a mesma faixa. |
| **faixa canônica** | Uma observação por `track_id` na tabela `tracks`; usada em features, PCA e clustering. |
| **membership** | Uma aresta explícita faixa–gênero em `track_genres`; uma faixa pode ter várias. |
| **colaboração** | Faixa com mais de um artista conforme a regra de parsing declarada. |
| **popularity** | Score observado de 0 a 100 no snapshot; não é forecasting de sucesso futuro. |
| **feature** | Variável usada para descrever ou modelar uma observação. |
| **painel humano** | Conjunto provisório de features escolhido por hipótese e interpretação. |
| **pool automatizado** | Candidatos adicionais avaliados por métodos de seleção/modelagem, sem pré-remoção arbitrária. |
| **multi-hot** | Representação binária de memberships categóricas. |
| **PPMI** | Positive Pointwise Mutual Information, calculada com coocorrência e marginais declaradas. |
| **OOV** | Categoria fora do vocabulário ajustado no treino; deve ter fallback explícito. |
| **PCA** | Redução linear que projeta variáveis padronizadas em componentes e loadings. |
| **clustering** | Agrupamento exploratório; só é chamado robusto se passar o gate de estabilidade. |
| **split por artista** | Partição que impede artista visto no treino de aparecer no teste principal. |
| **leakage** | Informação do teste, futuro ou target que chega indevidamente ao treino. |
| **MAE** | Erro absoluto médio; métrica primária de previsão deste projeto. |
| **claim ceiling** | Maior afirmação permitida pela população, desenho, evidência e limitações. |
| **protótipo** | Exploração visual/metodológica ainda não validada para claim final. |
| **evidence brief** | Resumo reproduzível de pergunta, método, resultado, incerteza e limite. |
| **manifest** | Registro de hashes, ambiente, execução, artefatos e warnings de notebooks. |
| **Molab preview** | URL temporária para visualizar/executar notebook; não é fonte canônica. |

Quando um termo puder ter mais de uma interpretação, declare a regra no notebook e na issue. Veja também [data-contract.md](data-contract.md) e [feature-roles.md](feature-roles.md).
