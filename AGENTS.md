# Repository Guidelines

## Project Structure & Module Organization
- `ulauncher/` - main Python package and app logic.
- `tests/` - pytest test suite.
- `docs/` - Sphinx documentation.
- `data/` - runtime assets (e.g., preferences build output).
- `preferences-src/` - Preferences UI (yarn build produces `data/preferences`).
- `bin/` - entry scripts (e.g., `bin/ulauncher`).
- `scripts/`, `debian/`, `nix/` - helper tooling and packaging.

## Build, Test, and Development Commands
- `make help` - list available developer targets.
- `make python-venv` - create and populate `.venv` with dev deps.
- `make run` - run Ulauncher from source (stops systemd unit if active).
- `make prefs` - build Preferences UI (requires `yarn`).
- `make check` - run linters: typos, ruff (lint+format check), mypy.
- `make test` - run linters and pytest (uses `xvfb-run` if available).
- `make format` - auto-fix via ruff (lint --fix + format).

## Coding Style & Naming Conventions
- Python 3.8+, 4-space indentation, max line length 120.
- Type hints required; mypy runs in strict mode (see `pyproject.toml`).
- Use ruff for linting/formatting; do not add other formatters.
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_SNAKE` for constants, modules/packages in `snake_case`.
- Keep imports sorted (ruff `I` rule); prefer explicit over wildcard.

## Testing Guidelines
- Framework: pytest; place tests under `tests/` and name `test_*.py`.
- Write unit tests for new logic and regressions; avoid GUI in unit tests when possible.
- Run locally with `make test`; CI assumes the same.

## Commit & Pull Request Guidelines
- Use Conventional Commits (e.g., `feat: …`, `fix: …`, `chore: …`).
- Keep commits focused; include tests and docs updates when relevant.
- Before pushing: `make format && make test` must pass locally.

## Tips & Tooling
- Git hooks (via `lefthook.toml`) run fast checks; keep them green.
- Docs preview: `make docs` then serve `_build/html` (auto-served when interactive).
- Packaging: `make sdist` (tarball), `make deb` (Debian package) for maintainers.
