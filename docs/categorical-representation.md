# Representações categóricas e embeddings de gênero v0.1

Este documento transforma a especificação da issue #47 em um protocolo pequeno e reproduzível. O objetivo não é declarar que gênero causa `popularity`; é testar se diferentes representações adicionam informação held-out de forma estável e interpretável.

## Escada de representações

1. **Sem gênero**: baseline com áudio e categóricas auditadas.
2. **Multi-hot**: uma coluna por gênero conhecido no treino; gêneros ausentes no treino recebem zeros (OOV explícito).
3. **Embedding PPMI + TruncatedSVD**: matriz de coocorrência de gêneros por faixa, PPMI e SVD. A versão primária tem 8 dimensões; 4 e 16 são sensibilidades.

PPMI é ajustado somente nas faixas do treino. Uma faixa multigênero recebe a média dos vetores de seus gêneros conhecidos. Em validação, o vocabulário, a matriz de coocorrência e o SVD também são fold-local; nunca ajustamos o embedding no conjunto de teste.

## Categóricas restantes

- `explicit` e `mode`: binárias.
- `key`: `sin`/`cos` é a codificação primária porque a escala é circular; one-hot é sensibilidade.
- `time_signature`: nominal one-hot, com auditoria dos valores 0/1 que aparecem no snapshot apesar da descrição esperada 3–7.
- `artists`, `album_name`, `track_name` e `track_id`: identificadores/contexto. Não entram como preditores diretos. Agregados de artista só aparecem em ablations fold-local com fallback OOV.

## Perfis de áudio por gênero

A visão EDA complementar usa todas as memberships. Para cada gênero, calcula os quantis 10/25/50/75/90 de dez features contínuas, totalizando 50 dimensões; aplica RobustScaler e PCA. Sensibilidades são gênero único e peso fracionário `1/k` para uma faixa com `k` gêneros.

## Gate de decisão

PPMI só é promovido a evidência preditiva se superar o multi-hot no mesmo modelo, split e repetições, com redução de pelo menos 0,5 ponto de MAE e intervalo pareado por bootstrap agrupado excluindo zero. Se falhar, o resultado é um piloto bounded de relações gênero–artista e um scorecard de viabilidade; não iniciamos graph database, GNN, Node2Vec ou modelagem de artista nesta entrega.

## Uso nos notebooks

- `notebooks/data_contract_audit.py` documenta o contrato e não aprende representações.
- `notebooks/explorations/genre_representations.py` mostra o ladder e os perfis de áudio para EDA.
- `notebooks/explorations/popularity_validation.py` é a validação preditiva; deve ajustar as transformações em cada fold.
- `notebooks/spotify_analysis.py` recebe apenas resultados revisados e bounded.
