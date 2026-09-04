# Governança do trabalho analítico

Este projeto separa três tipos de work item no GitLab:

1. **Pergunta**: o que queremos aprender.
2. **Especificação**: quais decisões, contratos e evidências a implementação deve respeitar.
3. **Entrega**: código, análise, visualização ou documentação revisável.

Use os templates em `.gitlab/issue_templates/` e o template de merge request em `.gitlab/merge_request_templates/`. Toda issue deve ter uma pergunta ou objetivo, grain, definições, evidência esperada, critérios de aceitação e caveats. Uma entrega também registra os comandos de validação e links para a pergunta e a especificação.

## Labels e prioridade

Use labels para representar dimensões diferentes, sem transformar o título em um inventário:

- `tipo::pergunta`, `tipo::especificação`, `tipo::entrega`, `tipo::mudança`;
- `evidência::descritiva`, `comparativa`, `relacional`, `contextual`, `exploratória`, `explicativa`, `preditiva`;
- `área::qualidade-de-dados`, `camada-de-dados`, `visualização`, `modelagem`, `documentação`, `revisão`;
- `fluxo::pronto`, `em-andamento`, `bloqueado`, `revisão`;
- `prioridade::1`, `prioridade::2`, `prioridade::3`.

`prioridade::1` bloqueia correção ou entrega final; `prioridade::2` é importante para a narrativa selecionada; `prioridade::3` é exploração ou follow-up. Labels históricas não devem ser renomeadas ou removidas sem aprovação. Issues antigas continuam válidas como banco de perguntas; sua migração para um template deve ser proposta ao autor antes de editar o texto.

Cada issue nova deve usar, no máximo, uma label `tipo::`, uma `fluxo::` e uma `prioridade::`; pode usar várias labels `evidência::` e `área::` quando necessário. Milestones representam resultados, não reuniões. Assignment representa responsabilidade, links representam dependências e checklists representam critérios de aceitação.

Labels de proveniência no formato `proposta::<origem-ou-rodada>` são temporárias: servem para localizar propostas durante a revisão, não substituem `tipo::`, `fluxo::` ou `área::`. Depois da decisão registrada, devem ser removidas das issues e aposentadas até uma nova rodada explícita. Uma nova namespace só deve ser criada quando houver uma necessidade recorrente de filtro, uma definição clara, ausência de duplicação e aprovação do time.

### Paleta e descrição das labels

As cores identificam a dimensão antes do valor: azul para tipo, turquesa para evidência, roxo para área, cores semânticas para fluxo e vermelho/laranja/amarelo para prioridade. A configuração no GitLab deve seguir esta fonte de verdade:

| Label | Cor | Descrição curta |
| --- | --- | --- |
| `tipo::pergunta` | `#1F75CB` | Pergunta analítica que orienta uma ou mais entregas. |
| `tipo::especificação` | `#0B5CAD` | Contrato de implementação e critérios de aceite. |
| `tipo::entrega` | `#428BCA` | Artefato revisável: código, análise, visualização ou documentação. |
| `tipo::mudança` | `#6F42C1` | Alteração de escopo, contrato ou correção registrada. |
| `evidência::descritiva` | `#008B8B` | Caracteriza distribuição, frequência, qualidade ou resumo do dataset. |
| `evidência::comparativa` | `#009A9A` | Compara grupos, recortes ou condições com denominadores explícitos. |
| `evidência::relacional` | `#00A6A6` | Examina associação ou estrutura entre variáveis ou entidades. |
| `evidência::contextual` | `#087F8C` | Interpreta resultados com contexto externo e caveats documentados. |
| `evidência::exploratória` | `#00B3B3` | Faz screening gerador de hipóteses, sem claim confirmatório. |
| `evidência::explicativa` | `#006D77` | Testa mecanismos ou explicações concorrentes sem alegar causalidade indevida. |
| `evidência::preditiva` | `#005F73` | Avalia previsão em dados held-out com baseline e incerteza. |
| `área::qualidade-de-dados` | `#7B2CBF` | Validade, completude, duplicatas, ranges e limpeza. |
| `área::camada-de-dados` | `#5A189A` | Schema, grains, DuckDB, Polars e transformações compartilhadas. |
| `área::visualização` | `#9D4EDD` | Charts, widgets, interações e narrativa visual. |
| `área::modelagem` | `#C77DFF` | Features, experimentos, modelos e avaliação held-out. |
| `área::documentação` | `#815AC0` | Guias, contratos, handoffs e material de apoio. |
| `área::revisão` | `#3C096C` | Auditoria independente, integração e gate de qualidade. |
| `fluxo::pronto` | `#108548` | Escopo suficiente para alguém iniciar o trabalho. |
| `fluxo::em-andamento` | `#1F75CB` | Há lead trabalhando ativamente na issue. |
| `fluxo::bloqueado` | `#C91C00` | Dependência ou decisão impede progresso material. |
| `fluxo::revisão` | `#D99530` | Implementação ou proposta aguarda revisão/aceite. |
| `prioridade::1` | `#C91C00` | Bloqueia correção, integração ou entrega final. |
| `prioridade::2` | `#D99530` | Importante para a narrativa ou escopo selecionado. |
| `prioridade::3` | `#EAC54F` | Exploração ou follow-up não bloqueador. |

Cada label deve ter descrição própria no GitLab, mesmo quando compartilha a cor de sua dimensão. `evidência::*` é abreviação documental; as sete labels mantêm seus nomes individuais e descrevem a classe correspondente.

## Especificações, escopo e mudanças

Uma especificação é um contrato de implementação: define decisões obrigatórias, interfaces, invariantes, casos-limite, não objetivos, validação e definição de pronto. A entrega pode escolher a implementação, mas deve registrar qualquer desvio.

O escopo passa por checkpoints. Depois de um lock, uma nova pergunta vira proposta/follow-up, salvo correção crítica de qualidade ou reprodutibilidade. Toda mudança registra solicitante, decisor, motivo, impacto, trabalho removido ou adiado, novo critério de aceitação e data. Correções críticas podem atravessar o lock quando evitam um resultado incorreto ou não reproduzível.

Especificações aprovadas são obrigatórias para contratos compartilhados ou de alto risco: schema/grain, validação, headline claims, features de grafo e estrutura do notebook final. Uma exploração pequena e isolada pode ir diretamente de `pergunta::` para `entrega::`. Toda entrega deve apontar para a pergunta e a especificação que a autorizam.

O lock de features v0.1 separa o painel humano de um pool de candidatos para modelagem. O painel humano usa `danceability`, `energy`, `valence`, `acousticness`, `instrumentalness` e `speechiness`; `loudness`, `liveness`, `tempo` e `duration_ms` ficam em sensibilidade/contexto. Nenhuma coluna é removida permanentemente por esse lock. Alterações posteriores exigem registro de decisão.

O modelo de ownership recomendado é lead + reviewer, com um integrador para artefatos que cruzam notebooks. Autoria anterior pode orientar uma oferta de continuidade, mas não determina atribuição automática.

## Evidência e revisão

Declare sempre se a análise mostra associação, comparação, previsão ou causalidade. Não use “impacta” ou “causa” quando o desenho só sustenta associação. A unidade, agregação, amostra, incerteza, seleção, missingness e limitações devem acompanhar cada claim.

O notebook Marimo final deve ser reproduzível, ter células pequenas e outputs bounded. O CSV é a fonte versionada; DuckDB é efêmero e reconstruído no runtime; Polars é preferido para transformações tipadas. Gráficos e redes precisam de pergunta, grain, encoding, agregação e limite de renderização explícitos.

O cronograma usa horários em `America/Sao_Paulo` nas issues de checkpoint. Janelas remotas flexíveis não recebem due date. Para este ciclo: triagem até 12:00 em 31/08; lock de features às 16:00; congelamento de perguntas candidatas, métodos e classes de claims às 18:00; seleção dos claims finais às 10:00 de 02/09; meta de entregáveis às 12:00; auditoria às 16:00; hard deadline às 18:00. Trabalho remoto entre os locks é permitido apenas dentro do escopo congelado e não cria nova obrigação de status.

## Documentação bilíngue

O português é a fonte canônica. Os pares definidos em `docs/translation-pairs.json` mantêm a tradução inglesa sincronizada por hash do arquivo canônico. Execute `python scripts/check_translation_pairs.py` antes de abrir um merge request. O checker não julga a qualidade da tradução; ele impede que a tradução fique silenciosamente desatualizada.
