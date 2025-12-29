# Change: Improve inline CLI documentation in main.py

## Why
Maintainers lack concise guidance in `src/bare/main.py` about how command parsing, session resolution, dependency checks, and shortcut handling fit together, making it harder to safely extend the CLI.

## What Changes
- Add clear module/function docstrings (numpydoc style) that describe responsibilities, inputs/outputs, and side effects for the CLI entrypoint and helpers.
- Document how shortcuts, session resolution, confirmation/dry-run guards, and dependency preflights work to reduce contributor guesswork, with inline notes kept concise and purposeful.
- Keep help/usage text aligned with the clarified docstrings where gaps are found.

## Impact
- Affected specs: cli-usage
- Affected code: src/bare/main.py
