# Luna → Sol handoff and delivery audit

This contract organizes the agent review described in issue #68. Luna executes a bounded unit; Sol audits it independently. No agent promotes a prototype, resolves a discussion, or closes an issue silently.

## Luna work package

Each run starts with an issue/Task, specification, fixed point, branch, authorized files, non-goals, acceptance criteria, and tests. The Luna coordinator may split work but owns scope and consolidates the handoff.

## Required delivery index

At completion, Luna must publish an index in the MR containing:

- parent issue and Task;
- fixed point, branch, and commit(s);
- changed files, functions, and notebook sections;
- satisfied contract and decisions;
- HTML, manifest, and other artifacts;
- executed commands and results;
- CI/pipeline and environment;
- risks, limitations, deviations, and deferred items;
- points Sol must verify.

Use addressable links to files, commits, jobs, issues, and artifacts. An index must let Sol locate every claim without repeatedly ingesting context.

## Sol audit

Sol receives the MR, index, diff, related specifications, standards documentation, manifest, HTML, and pipeline. The audit checks four independent axes:

1. **Spec:** adherence to decisions, invariants, and criteria.
2. **Code:** bugs, interfaces, duplication, tests, and conventions.
3. **Analysis:** grain, leakage, denominators, formulas, seeds, uncertainty, and reproducibility.
4. **Communication:** question, reading guidance, result, caveats, status, and claim ceiling.

Sol may run tests, create fixtures, and suggest missing checks. It does not silently change the delivery. Findings must state location, evidence, severity, impact, and recommended correction:

- **P0/P1:** blocks merge;
- **P2:** fix or record an accepted follow-up;
- **P3:** non-blocking recommendation.

After correction, Luna answers the finding and Sol revalidates affected axes. The merge decision is human.

## Routing and safety

Changes to schema/grain, statistics, modeling, claims, graphs, CI, or the integrator require a specification and Sol audit. Small isolated changes may use the delivery directly if the narrative contract is completed. The index must never contain tokens, secrets, or personal data.

The final report must distinguish “passed”, “failed”, “not run”, and “inconclusive”; HTTP 200 from a Molab preview does not prove execution.
