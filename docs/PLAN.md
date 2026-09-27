# Project Management MVP Plan

This plan turns the existing frontend demo into a locally runnable project-management MVP with a FastAPI backend and SQLite persistence. OpenRouter-powered assistance remains planned for Parts 8–10.

## Working decisions

- The MVP has one hardcoded login: `user` / `password`.
- Authentication uses a backend-managed, HttpOnly session cookie. The implementation should remain simple and make it possible to add database-backed users later.
- Each user has one board. The initial board has five fixed columns: `Backlog`, `Discovery`, `In Progress`, `Review`, and `Done`. The number and order of columns are fixed, but their titles can be renamed.
- SQLite is created automatically when it does not exist and is stored in a Docker volume so data survives container restarts.
- OpenRouter is called with model `openai/gpt-oss-120b`. The API key is read from the project-root `.env` and is never sent to the frontend.
- OpenRouter integration tests mock the provider. A separate live connectivity check may use the configured key and should not be required for the normal test suite.
- The AI response schema contains a user-facing reply and optional validated board operations. Board changes are persisted by the backend and the frontend refreshes after a successful update.
- Existing frontend tooling should be retained: Vitest and Testing Library for unit/component tests, and Playwright for browser tests.
- The frontend is exported as static files by Next.js and served by FastAPI from the same Docker container. The Dockerfile uses a Node build stage followed by a Python runtime stage.
- The frontend uses local system-font fallbacks so Docker builds do not depend on downloading Google Fonts.
- Drag-and-drop uses pointer-first collision detection, with a nearest-corner fallback, so empty columns remain valid drop targets.
- SQLite card positions are temporarily staged at distinct negative values before final positions are assigned, avoiding uniqueness conflicts during moves.
- All work pauses at the approval gates below. No later phase should begin until its required design or implementation review is approved.

## Current status

- Parts 1–7 implementation is complete.
- Docker build, startup, health, and frontend smoke checks have been verified.
- The latest backend suite has 24 passing tests.
- The latest frontend suite has 10 unit tests and 9 mocked-API Playwright browser tests passing.
- Part 7 production-container browser/API integration is now verified with a dedicated Docker Playwright smoke test.
- The only remaining unchecked item is multi-user authentication and cross-user isolation, which are outside the hardcoded-login MVP.
- Part 8 backend connectivity is implemented, covered by mocked tests, and the live 2+2 check returned `4`.
- Part 9 structured AI board operations are implemented and covered by backend tests.
- Part 10 frontend AI chat sidebar is implemented and covered by frontend tests. The isolated clean-volume smoke test also passes.

## Part 1: Plan and frontend documentation

### Checklist

- [x] Review the project requirements and existing frontend.
- [x] Record the implementation decisions and phase boundaries in this document.
- [x] Create `frontend/AGENTS.md` describing the current frontend architecture, state model, commands, and known limitations.
- [x] User reviews and approves this plan.

### Tests and verification

- Confirm that the plan covers authentication, board behavior, persistence, deployment, AI, testing, and approval points.
- Confirm that `frontend/AGENTS.md` matches the current files and scripts.

### Success criteria

- The user has approved the plan.
- Future implementation work can proceed phase by phase without making undocumented architectural decisions.

## Part 2: Docker and backend scaffolding

### Checklist

- [x] Add the FastAPI backend in `backend/` using `uv` for Python dependency and environment management.
- [x] Add a minimal backend application entry point and health/example route.
- [x] Configure FastAPI to serve a temporary example static HTML response at `/` until the frontend is integrated.
- [x] Add a Dockerfile that installs the backend dependencies and runs the example backend in the container.
- [x] Add a local SQLite path configuration and a writable data location suitable for a Docker volume.
- [x] Add start and stop scripts for macOS, Linux, and Windows in `scripts/`.
- [x] Add a minimal `.dockerignore` and document required environment variables without committing secrets.
- [x] Add backend tests for the health/example route.

### Tests and verification

- [x] Run the backend unit tests in the rebuilt Docker image.
- [x] Build the Docker image successfully.
- [x] Start the container and verify its health status.
- [x] Verify that `/` serves the integrated frontend and that the health and example API routes respond.
- [x] Stop the container and verify that it exits cleanly.

### Success criteria

- A new checkout can be built and started locally with the documented command or platform script.
- The container serves the example page and responds to the example API call.
- SQLite and application configuration do not depend on files outside the documented volume or environment variables.

## Part 3: Integrate the static frontend

### Checklist

- [x] Configure Next.js for a static production build compatible with FastAPI serving the generated site.
- [x] Define the build and copy steps for placing the static frontend output in the backend's static directory.
- [x] Serve the generated frontend at `/` from FastAPI, including static assets and client-side routes if any are added.
- [x] Preserve the current Kanban demo behavior while moving it into the Docker workflow.
- [x] Add or update backend and frontend configuration needed for local development and production serving.
- [x] Add browser integration coverage for the frontend served through the backend container with the real API.

### Tests and verification

- [x] Run frontend lint, unit tests, and Playwright tests against the supported local development mode.
- [x] Build the static frontend.
- [x] Build the Docker image.
- [x] Start the container and verify that the Kanban board renders at `/`.
- [x] Add a dedicated automated check that static assets load through FastAPI rather than only through the Next.js development server.

Frontend lint, static build, 10 unit tests, and 9 mocked-API Playwright tests pass. The Docker image is healthy, all generated JavaScript and CSS assets returned HTTP 200 through FastAPI, and the dedicated production-container Playwright smoke test passed.

### Success criteria

- The existing demo board is visible at `/` when the container is running.
- The production container does not require a separate Next.js server.
- The board's existing add, remove, rename, and drag-and-drop behavior remains covered by tests.

## Part 4: Fake user sign-in

### Checklist

- [x] Add a sign-in screen shown when there is no valid session.
- [x] Accept only the MVP credentials `user` / `password`.
- [x] Add a backend login route that establishes the HttpOnly session cookie.
- [x] Add a backend logout route that clears the session.
- [x] Protect the board UI behind the session and establish the backend auth boundary for future board routes.
- [x] Add clear invalid-credential and signed-out states.
- [x] Keep the authentication boundary compatible with replacing the hardcoded credential check with a users table later.

### Tests and verification

- [x] Test valid and invalid login requests in the rebuilt Docker image.
- [x] Test that protected routes reject requests without a session.
- [x] Test logout invalidates the session.
- [x] Test the browser flow: signed-out user sees login, valid login reveals the board, and logout returns to login.
- [x] Test that refreshing after login preserves the session.

Backend authentication tests pass in Docker. The production-container browser smoke test covers sign-in, board loading, refresh persistence, and logout.

### Success criteria

- Users cannot see or modify the board without signing in.
- `user` / `password` signs in successfully.
- Invalid credentials do not create a session.
- Logout and browser refresh behave predictably.

## Part 5: Database modeling and approval

### Checklist

- [x] Define the SQLite schema for users, boards, columns, cards, and the relationship between a user and their single board.
- [x] Decide which identifiers, timestamps, ordering fields, and ownership constraints are required.
- [x] Define how the initial board and its five columns are created for a user.
- [x] Define the JSON representation returned by the board API.
- [x] Save the proposed schema and representative records as a JSON document in `docs/`.
- [x] Document database initialization and migration assumptions in `docs/`.
- [x] User reviews and signs off on the schema before database-backed routes are implemented.

### Tests and verification

- [x] Validate the schema document as JSON.
- [x] Check that the schema can represent renamed columns, ordered cards, edited card details, and future users.
- [x] Check that a fresh database can create the required tables and initial board data.

### Success criteria

- The schema supports all MVP board operations without storing the entire board as an opaque frontend-only object.
- User ownership is explicit and prevents cross-user board access.
- The user has approved the schema before Part 6 begins.

## Part 6: Backend board API

### Checklist

- [x] Initialize the SQLite database automatically on application startup or first use.
- [x] Create the authenticated user's initial board when needed.
- [x] Add an authenticated route to read the current user's board.
- [x] Add routes for renaming columns, creating cards, editing cards, deleting cards, and moving cards.
- [x] Validate identifiers, ownership, required fields, ordering, and the fixed-column constraint at the API boundary.
- [x] Return consistent JSON errors for invalid requests and missing resources.
- [x] Keep database transactions small and explicit for each board change.

### Tests and verification

- [x] Test fresh database creation and initial board creation.
- [x] Test every board read and write operation with an authenticated user.
- [x] Test unauthenticated access, invalid IDs, invalid payloads, and board ownership checks available in the MVP.
- [x] Test that card order and column names survive application restarts.
- [ ] Test that a second user can be supported by the schema without accessing the first user's board.

The backend suite was run in the rebuilt Docker image with 24 tests passing. Multiple-user authentication remains pending because the MVP still uses one hardcoded login.

### Success criteria

- The database is created automatically when absent.
- All board changes are persisted and scoped to the authenticated user.
- Backend tests cover normal operations and meaningful failure cases.

## Part 7: Connect the frontend to the backend

### Checklist

- [x] Replace frontend-only `initialData` state with authenticated API loading.
- [x] Add a small frontend API client for board loading and board mutations.
- [x] Keep the current board interactions while persisting each mutation through the backend.
- [x] Add loading, empty, and error states without obscuring the core board UI.
- [x] Refresh or reconcile board state after successful mutations so the UI reflects the server.
- [x] Ensure browser requests include the session cookie when required.

### Tests and verification

- [x] Test API client success and error handling with mocked responses.
- [x] Test board loading after login.
- [x] Test rename, add, edit, delete, and move operations through the browser with mocked API responses.
- [x] Test logout removes access to the board.
- [x] Run the frontend browser suite against the production frontend and real backend served by Docker.

Frontend lint, static build, 10 unit tests, and 9 mocked-API Playwright tests pass. Backend tests pass in Docker. The dedicated production-container Playwright smoke test also passes.

### Success criteria

- The board is server-backed rather than browser-memory-only.
- A mutation followed by a refresh shows the saved result.
- Network and server errors produce understandable UI feedback.

## Part 8: OpenRouter connectivity

### Checklist

- [x] Add a backend OpenRouter client that reads `OPENROUTER_API_KEY` from environment configuration.
- [x] Use model `openai/gpt-oss-120b`.
- [x] Keep provider calls on the backend and never expose the key to the browser.
- [x] Add a small internal connectivity path and mocked test that asks the model to calculate `2+2`.
- [x] Add request timeout and concise provider error handling.
- [x] Keep the normal automated tests mocked and document the optional live check.

### Tests and verification

- [x] Unit test the client with a mocked successful provider response.
- [x] Unit test configuration failure when the API key is missing.
- [x] Unit test provider errors and timeouts.
- [x] Run the optional live `2+2` check when a valid key is available and approved.

The backend client and mocked tests are complete. The live check was run with `docker compose run --rm app sh -c "python -m app.openrouter_check"` and returned `4`.

### Success criteria

- The backend made a successful authenticated request to OpenRouter when configured.
- The normal test suite does not require network access or a live secret.
- Provider failures are reported without leaking the API key.

## Part 9: Structured AI board operations

### Checklist

- [x] Define the chat request containing the user's question and conversation history.
- [x] Include the authenticated user's current board JSON in every AI request.
- [x] Define a strict structured response containing a user-facing reply and optional board operations.
- [x] Support operations for creating, editing, moving, renaming, and deleting cards as required by the product behavior.
- [x] Validate every operation against the current authenticated board before applying it.
- [x] Apply valid operations transactionally and return the resulting board state with the assistant reply.
- [x] Reject malformed or unsafe structured output without partially applying changes.

### Tests and verification

- [x] Test prompt construction includes board JSON, the current question, and conversation history.
- [x] Test valid responses with no board change.
- [x] Test valid responses with one and multiple board operations.
- [x] Test invalid IDs, invalid columns, malformed output, request limits, and partial-failure rollback.
- Test that one user's board cannot be changed by data supplied in another user's conversation.
- [x] Test response size and history handling at the API boundary.

### Success criteria

- The AI receives enough board context to answer questions about the current board.
- Board changes occur only through validated structured operations.
- A failed AI response or invalid operation leaves the persisted board unchanged.

The structured AI route and transactional board operations are implemented. The multi-user conversation ownership test remains outside the hardcoded-login MVP.

## Part 10: AI chat sidebar

### Checklist

- [x] Add a responsive sidebar widget to the authenticated board UI.
- [x] Render conversation history, the current input, loading state, and errors.
- [x] Send the user's question and conversation history to the backend chat route.
- [x] Render the assistant's structured reply as normal chat text.
- [x] Refresh the board automatically when the response contains board changes.
- [x] Keep the sidebar usable on narrower screens without disrupting core board interactions.
- [x] Add accessible labels, keyboard submission, focus handling, and sensible disabled states.

### Tests and verification

- [x] Test rendering and using the sidebar.
- [x] Test sending a question and rendering the assistant reply.
- [x] Test loading and provider-error states.
- [x] Test that a board update returned with the assistant response is applied to the UI.
- [x] Run browser flows covering sign-in, board interaction, chat, and logout with the AI provider mocked.
- [x] Perform a final Docker build and smoke test from an isolated clean database volume.

### Success criteria

- A signed-in user can chat with the assistant from the board.
- The assistant can answer using the current board and can make validated board changes.
- The UI reflects AI changes without a manual page reload.
- The complete MVP works through the documented local Docker workflow.
