# Backend Instructions

The backend is a Python FastAPI application managed with `uv`.

## Current structure

- `pyproject.toml` declares runtime and development dependencies and pytest settings.
- `app/main.py` creates the FastAPI application, serves the frontend, exposes `/health` and `/api/hello`, provides the hardcoded-session auth routes under `/api/auth/`, and exposes the authenticated board routes under `/api/board`.
- `app/config.py` reads `DATABASE_PATH`, `OPENROUTER_API_KEY`, and `SESSION_SECRET` from the environment. Database initialization and models are intentionally deferred to the database phase.
- `app/database.py` creates the SQLite schema, seeds the MVP user and initial board, and provides database connections with foreign keys enabled.
- `app/board.py` contains board serialization and mutations for renaming columns, creating/editing/deleting cards, and moving cards.
- `app/static/index.html` is the temporary Part 2 page. It calls `/api/hello` in the browser and displays the response.
- `tests/test_main.py` covers the example page, API routes, login, session lookup, invalid credentials, logout, board reads, board mutations, persistence, and invalid resources.

## Commands

Run from `backend/`:

```bash
uv sync
uv run pytest
uv run uvicorn app.main:app --reload
```

The container test workflow mounts `backend/tests` into the image because the production image intentionally contains runtime code only:

```bash
docker compose run --rm -v "$(pwd)/backend/tests:/app/tests:ro" app sh -c "uv sync --group dev --no-install-project && uv run --no-sync pytest"
```

The Docker workflow runs Uvicorn on port `8000` and stores the future SQLite database at `/data/project-management.db`.

The MVP auth flow accepts `user` / `password` and stores the signed session in an HttpOnly `pm_session` cookie. The default session secret is intended only for local development; set `SESSION_SECRET` for other environments.

## Conventions

- Keep provider credentials and other secrets in environment variables. Never put them in source or static frontend files.
- Keep route handlers small and move pure business logic into testable modules as the backend grows.
- Add backend tests for every route and meaningful validation or error path.
- Keep the API response shapes explicit and JSON-serializable.
