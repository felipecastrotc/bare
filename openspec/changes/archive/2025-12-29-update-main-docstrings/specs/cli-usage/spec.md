## ADDED Requirements
### Requirement: CLI main module is self-documented for maintainers
The BARE CLI main entrypoint SHALL include module- and function-level documentation that explains command dispatch, session resolution, dependency checks, and shortcut handling so contributors can reason about CLI flows without external references, using numpydoc-style docstrings for functions.

#### Scenario: Core command handlers are documented
- **WHEN** a contributor reads `src/bare/main.py` to extend or debug CLI behavior
- **THEN** the module and key functions (parser construction, session resolution, config building, backup/restic/maintain/umount/list dispatch) include numpydoc-style docstrings describing purpose, inputs/outputs, and notable side effects such as confirmation/dry-run prompts.

#### Scenario: Inline notes cover safety checks and defaults
- **WHEN** a contributor reviews code paths for dependency preflight, default session resolution, and shortcut routing
- **THEN** inline comments or docstrings call out these safeguards and default behaviors so they are preserved during future changes, following concise numpydoc guidance (e.g., Parameters/Returns/Notes for side effects).
