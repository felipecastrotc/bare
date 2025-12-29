## Context
We need PR-visible coverage gating and local coverage ergonomics. Pyproject already includes pytest-cov and coverage config but points to `your_package` in the Pixi task and lacks CI surfacing beyond XML.

## Goals / Non-Goals
- Goals: align coverage config on `src/bare`, enforce threshold, add local coverage task/docs, and surface PR coverage artifacts.
- Non-Goals: enforcing mutation testing or adding new test suites.

## Decisions
- Use pytest-cov with `--cov=src/bare` and term-missing summary; emit XML+HTML for PR artifacts and local drill-down.
- Set `fail_under=80` initially; adjust later if needed.
- Use actions/upload-artifact for XML; PR summary can be added by future step (e.g., coverage-commenter) if desired.

## Risks / Trade-offs
- Threshold might be tuned later; start conservative to avoid blocking PRs unnecessarily.
- Artifact upload adds CI time but provides drill-down.

## Open Questions
- Whether to add a coverage comment bot; for now we surface via status + artifact.
