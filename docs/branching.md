# Branches, commits e merge requests

Este projeto usa um GitLab Flow leve: `main` representa o estado integrado e revisado; o trabalho acontece em branches curtas e entra por merge request. Não mantemos uma branch `develop` permanente, pois ela adicionaria um segundo ponto de integração sem necessidade para o ritmo atual do projeto.

## Branches

- `feature/<iid>-<resumo>` para funcionalidades e análises novas;
- `fix/<iid>-<resumo>` para correções;
- `docs/<iid>-<resumo>` para documentação;
- `chore/<iid>-<resumo>` para configuração, governança e manutenção;
- `experiment/<iid>-<resumo>` para experimentos que ainda não sustentam um claim final.

Use o IID da issue principal. Uma branch pode referenciar issues relacionadas no merge request, mas deve preservar um objetivo integrável. Atualize-a com `main` antes do merge e evite branches longas que misturem decisões independentes.

## Commits

Prefira commits atômicos e mensagens no formato Conventional Commits, por exemplo `feat(data): validar o grain canônico`. No corpo, use `Refs #29 #44` para criar rastreabilidade sem concluir as issues. Não use `Closes`, `Fixes` ou equivalentes enquanto os critérios de aceite e a revisão não estiverem completos.

## Merge requests

Abra o merge request como Draft enquanto houver decisões, validações ou outputs pendentes. A descrição deve indicar issue principal, issues relacionadas, milestone, grain, evidências alteradas, comandos de validação e limitações. Para merge:

1. o pipeline deve estar verde;
2. o reviewer deve verificar contrato, resultados e tamanho dos outputs;
3. conflitos e comentários bloqueadores devem estar resolvidos;
4. a documentação e o notebook devem executar a partir de um clone limpo.

Preserve commits atômicos quando eles forem úteis à auditoria; use squash quando o histórico for apenas ruído de iteração. Fechar uma issue é uma decisão separada do merge e depende de sua definition of done.

## Proteção de `main`

A intenção versionada é: sem push direto, merge apenas por merge request e pipeline obrigatório. A proteção efetiva da branch, permissões de merge e aprovações mínimas são configurações do GitLab e não podem ser impostas apenas pelos arquivos do repositório. Um Maintainer deve configurá-las em **Settings → Repository → Protected branches** e **Settings → Merge requests**, usando este documento como fonte de verdade da equipe.
