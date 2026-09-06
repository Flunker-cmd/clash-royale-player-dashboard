# Ponytail Project Instructions

Use the smallest correct change that solves the requested problem. Efficiency means
avoiding unnecessary code, not skipping validation or safety.

## Decision Ladder

Before writing code, check these options in order:

1. Does the change need to exist at all?
2. Can existing code or data be reused?
3. Can the Python standard library or a native GitHub feature solve it?
4. Can the minimum implementation solve it without a new dependency?

Read the affected code path before choosing an option. Prefer deletion or reuse over
new abstractions, boilerplate, and dependencies. Fix shared root causes rather than
patching only the reported caller.

## Engineering Rules

- Keep diffs small and local.
- Preserve existing public APIs and repository conventions.
- Validate trust-boundary input, authentication, error handling, and data-loss paths.
- For non-trivial logic, leave one focused runnable test or check.
- Before editing, form one local hypothesis and identify one check that could disprove it.
- After the first substantive edit, run the narrowest relevant validation.
- Do not modify unrelated user changes in the working tree.

## Project Checks

- Run Python tests with `python -m unittest discover -s tests -v`.
- Validate GitHub Actions changes against `.github/workflows/fetch.yml`.
- Never expose `CLASH_ROYALE_TOKEN` in source files, logs, committed JSON, or documentation.
