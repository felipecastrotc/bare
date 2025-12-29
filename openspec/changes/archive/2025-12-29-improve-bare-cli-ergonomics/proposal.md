# Change: Improve BARE CLI ergonomics and user experience

## Why
Users struggle with the current CLI because help output is terse, error messages are not actionable, and safeguards like dry runs or confirmation flows are absent. Making the CLI self-explanatory and forgiving reduces support burden and prevents accidental or failed backups.

## What Changes
- Expand CLI help for every command with clear descriptions, common flows, and flag examples
- Add shortcuts for frequent restic/rsync operations (e.g., snapshots, stats/check) to reduce typing
- Add preflight validation for session discovery and external dependencies with actionable guidance
- Introduce ergonomic flags (e.g., dry-run/confirm) and defaults that make backups safer and easier to operate

## Impact
- Affected specs: cli-usage
- Affected code: src/bare/main.py, src/bare/__init__.py, docs/ and mkdocs navigation, CLI tests
