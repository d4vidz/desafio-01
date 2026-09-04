# Branches, commits, and merge requests

This project uses a lightweight GitLab Flow: `main` represents the reviewed, integrated state; work happens on short-lived branches and enters through merge requests. We do not keep a permanent `develop` branch because it would add a second integration point without a current need.

## Branches

- `feature/<iid>-<summary>` for new functionality and analyses;
- `fix/<iid>-<summary>` for corrections;
- `docs/<iid>-<summary>` for documentation;
- `chore/<iid>-<summary>` for configuration, governance, and maintenance;
- `experiment/<iid>-<summary>` for experiments that do not yet support a final claim.

Use the primary issue IID. A branch may reference related issues in its merge request, but it should retain one integrable objective. Update it with `main` before merge and avoid long-lived branches that combine independent decisions.

## Commits

Prefer atomic commits and Conventional Commit messages, for example `feat(data): validate canonical grain`. In the body, use `Refs #29 #44` to create traceability without completing issues. Do not use `Closes`, `Fixes`, or equivalents until acceptance criteria and review are complete.

## Merge requests

Keep the merge request as Draft while decisions, validations, or outputs remain pending. Its description should identify the primary issue, related issues, milestone, grain, changed evidence, validation commands, and limitations. Before merge:

1. the pipeline must pass;
2. the reviewer must check the contract, results, and output sizes;
3. conflicts and blocking comments must be resolved;
4. documentation and notebooks must run from a clean clone.

Preserve atomic commits when they help the audit trail; squash when the history is only iteration noise. Closing an issue is separate from merging and depends on its definition of done.

## Protecting `main`

The versioned intent is: no direct pushes, merge requests only, and a required pipeline. Effective branch protection, merge permissions, and minimum approvals are GitLab server settings and cannot be enforced by repository files alone. A Maintainer should configure them under **Settings → Repository → Protected branches** and **Settings → Merge requests**, using this document as the team's source of truth.
