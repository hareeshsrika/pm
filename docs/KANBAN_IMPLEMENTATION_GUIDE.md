
# Project Management MVP: Beginner-Friendly Implementation Guide

## 1. What this project is

This project is a small Project Management web application built around a Kanban board.

A Kanban board represents work as cards that move through stages:

1. Backlog
2. Discovery
3. In Progress
4. Review
5. Done

The current MVP allows a user to:

- Sign in with the demo account user / password.
- View one personal Kanban board.
- Rename the five columns.
- Add, edit, and delete cards.
- Drag cards between columns.
- Keep changes after the application restarts.
- Log out.

The application runs locally inside Docker. The frontend is what users see. The backend handles authentication, database access, and board changes.

The backend OpenRouter connectivity foundation, structured board-operation route, and browser chat sidebar are implemented.

## 2. The big picture

The application has three main parts:

~~~text
Your browser
    |
    | HTTP requests
    v
FastAPI backend inside the Docker container
    |
    | Reads and writes
    v
SQLite database stored in a Docker volume
~~~

The frontend is built with Next.js and React. It is compiled into static browser files before the Docker image is created. FastAPI then serves those files and provides the API routes.

The running application uses one address:

~~~text
http://localhost:8000
~~~

The browser loads the frontend from that address. When the frontend needs data, it calls an API route on the same address, such as /api/board.

## 3. What each technology does

### Docker

Docker packages the application and its dependencies into a repeatable environment called a container.

Without Docker, a new developer would need to install and configure Node.js, Python, FastAPI, uv, and several package versions separately. Docker puts the server environment in one image.

Docker is used for:

- Building the frontend.
- Installing backend dependencies.
- Starting the FastAPI server.
- Providing persistent storage for SQLite.
- Exposing the application on port 8000.

### Next.js and React

Next.js is the frontend framework. React is the user-interface library used inside Next.js.

The frontend is divided into components:

- LoginForm displays the sign-in form.
- AuthGate decides whether to show the login form or board.
- KanbanBoard manages the board screen.
- KanbanColumn displays one column.
- KanbanCard displays one card.

Next.js is configured for a static export. During the Docker build, the frontend becomes browser files in frontend/out. Those files are copied into the backend image.

### FastAPI

FastAPI is the Python web server and API framework.

It has two responsibilities:

1. Serve the compiled frontend at the root address.
2. Provide backend API routes under /api/.

FastAPI also checks the login session before allowing access to board routes.

### uv

uv is the Python package and environment manager used in the container. The backend dependency list is in backend/pyproject.toml.

It installs FastAPI, Uvicorn, itsdangerous, pytest, and the other Python dependencies required by the application and tests.

### SQLite

SQLite is a database stored in a file. It is a good fit for this local MVP because it does not require a separate database server.

The application creates the database automatically if it does not exist. In Docker, the database is stored at:

~~~text
/data/project-management.db
~~~

The /data folder is backed by a named Docker volume, so rebuilding or restarting the container does not normally erase the board.

### Markdown files

Markdown is a simple text format used for documentation. Files ending in .md can be read as plain text or displayed with headings, lists, links, and code blocks in VS Code and other tools.

Markdown is used for:

- PLAN.md, the development plan and approval gates.
- DATABASE.md, the database design.
- AGENTS.md files, project instructions for development work.
- This implementation guide.

Markdown explains the project; it does not run the application.

## 4. Project folders and files

~~~text
pm/
├── Dockerfile                 Builds the complete application image
├── docker-compose.yml         Starts the application and database volume
├── .env                       Local environment values; never commit secrets
├── AGENTS.md                  Overall project instructions
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI application and API routes
│   │   ├── board.py           Board operations and validation
│   │   ├── database.py        SQLite schema, initialization, seed data
│   │   └── config.py          Environment configuration
│   ├── pyproject.toml         Python dependencies and pytest settings
│   └── tests/test_main.py     Backend tests
├── frontend/
│   ├── src/app/               Next.js page and global styles
│   ├── src/components/        React UI components
│   ├── src/lib/               API clients and board helpers
│   ├── tests/kanban.spec.ts   Playwright browser tests
│   ├── package.json            Frontend scripts and dependencies
│   └── next.config.ts         Static export configuration
├── scripts/
│   ├── start.ps1              Windows start script
│   ├── stop.ps1               Windows stop script
│   ├── start.sh               macOS/Linux start script
│   └── stop.sh                macOS/Linux stop script
└── docs/                      Planning, schema, and implementation documents
~~~

Generated folders such as frontend/node_modules, frontend/.next, and frontend/out contain dependencies or build output. They are not the main source code.

## 5. How Docker builds the application

The Dockerfile uses two build stages.

### Stage 1: build the frontend

The first stage:

1. Starts from a Node.js Alpine image.
2. Copies the frontend package files.
3. Runs npm ci to install the locked dependencies.
4. Copies the frontend source code.
5. Runs npm run build.

The result is a static export in frontend/out.

### Stage 2: run the backend

The second stage:

1. Starts from a Python 3.12 image.
2. Copies uv into the image.
3. Installs backend dependencies.
4. Copies the FastAPI application into /app/app.
5. Copies the frontend build into /app/frontend-static.
6. Creates /data for the database.
7. Starts Uvicorn on port 8000.

The final image contains the production frontend and backend together. A separate Next.js server is not required after the image is built.

## 6. How Docker Compose runs the application

The docker-compose.yml file defines one service named app.

It:

- Builds the image using the Dockerfile.
- Loads optional values from .env.
- Sets DATABASE_PATH to /data/project-management.db.
- Maps host port 8000 to container port 8000.
- Mounts the named volume project_management_data at /data.
- Checks /health to determine whether the server is healthy.

The port mapping is:

~~~text
Your computer: localhost:8000
Container:     port 8000
~~~

## 7. Starting and stopping the application

### Windows PowerShell

Run from the project root, which is the folder containing Dockerfile and docker-compose.yml:

~~~powershell
.\scripts\start.ps1
~~~

The script builds the image, starts the container, and prints the application address.

To stop the application:

~~~powershell
.\scripts\stop.ps1
~~~

If PowerShell blocks scripts with an execution-policy error, allow scripts for the current PowerShell window:

~~~powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
~~~

Then run the start script again.

You can also run Docker Compose directly:

~~~powershell
docker compose up -d --build
~~~

### macOS or Linux

From the project root:

~~~bash
./scripts/start.sh
~~~

Stop it with:

~~~bash
./scripts/stop.sh
~~~

If the shell says the script is not executable:

~~~bash
chmod +x scripts/start.sh scripts/stop.sh
~~~

## 8. Checking whether the container is running

Run:

~~~powershell
docker compose ps
~~~

The status should say Up and preferably include healthy.

The application should be available at:

~~~text
http://localhost:8000
~~~

The health endpoint is:

~~~text
http://localhost:8000/health
~~~

It should return:

~~~json
{"status":"ok"}
~~~

## 9. How the frontend works

### Application entry point

The frontend starts at frontend/src/app/page.tsx. It renders AuthGate.

AuthGate calls /api/auth/me when the page loads:

- If the user is not signed in, it displays LoginForm.
- If the user is signed in, it displays KanbanBoard.
- While waiting, it displays a session-checking message.

### Board loading

After sign-in, KanbanBoard calls getBoard from frontend/src/lib/boardApi.ts.

The backend returns the board as JSON. The frontend stores that response in React state and renders the columns and cards.

### Board changes

Each user action calls a backend route:

- Rename a column: PATCH /api/board/columns/{column_id}
- Add a card: POST /api/board/cards
- Edit a card: PATCH /api/board/cards/{card_id}
- Delete a card: DELETE /api/board/cards/{card_id}
- Move a card: POST /api/board/cards/{card_id}/move

The backend returns the updated board after each successful change. The frontend replaces its current state with that response. This keeps the browser synchronized with the database instead of treating the browser as the permanent source of truth.

### Drag and drop

The board uses the dnd-kit libraries.

- DndContext manages the drag operation.
- useSortable makes cards draggable.
- useDroppable makes columns valid drop targets.
- DragOverlay shows a card preview while it is dragged.
- The collision strategy first checks the area directly below the pointer. This matters when a column is empty; otherwise a nearby column could be selected accidentally.

The frontend calculates the intended target position, sends it to the backend, and displays the returned board.

## 10. How sign-in works

This is intentionally a simple MVP login.

~~~text
Username: user
Password: password
~~~

When login succeeds:

1. The browser sends credentials to POST /api/auth/login.
2. FastAPI validates the hardcoded values.
3. FastAPI stores the signed-in user in a session.
4. Starlette sends a signed pm_session cookie to the browser.
5. The browser includes that cookie in later API requests.

The session cookie is HttpOnly, so frontend JavaScript cannot read it directly. The browser still sends it automatically with requests to the same application.

Logout calls POST /api/auth/logout and clears the session.

Board routes require a valid session. Requests without one receive a 401 Not authenticated response.

This is not production authentication yet. The login is hardcoded for the MVP. The database already has a users table and nullable password_hash field so a future version can use real user accounts.

## 11. How the database works

The schema is documented in docs/DATABASE.md and docs/database-schema.json.

The database has four main tables:

### users

Stores user identity. The current MVP creates one user with username user.

### boards

Stores one board per user. A unique constraint on user_id supports the MVP rule of one board per user.

### columns

Stores the five board columns, their titles, and their order. Titles can be renamed, but the MVP does not allow adding, deleting, or reordering columns.

### cards

Stores each card's title, details, column, and position within that column.

Card positions begin at zero. When a card moves, the backend rewrites the affected positions so the order remains consistent.

The database is initialized when FastAPI starts. If the database does not exist, the tables, user, board, columns, and sample cards are created.

## 12. Backend API summary

| Route | Purpose | Requires sign-in |
| --- | --- | --- |
| GET /health | Container health check | No |
| GET /api/hello | Basic example API route | No |
| POST /api/auth/login | Sign in | No |
| GET /api/auth/me | Check current session | No |
| POST /api/auth/logout | Sign out | No |
| GET /api/board | Load the current user's board | Yes |
| PATCH /api/board/columns/{id} | Rename a column | Yes |
| POST /api/board/cards | Create a card | Yes |
| PATCH /api/board/cards/{id} | Edit a card | Yes |
| DELETE /api/board/cards/{id} | Delete a card | Yes |
| POST /api/board/cards/{id}/move | Move a card | Yes |
| POST /api/ai/chat | Ask the backend assistant and apply validated operations | Yes |

The backend checks that requested boards, columns, and cards belong to the signed-in user before changing anything.

## 13. Testing and verification

The project has three main testing layers.

### Backend tests

Backend tests are in backend/tests/test_main.py. They cover:

- Health and example routes.
- Valid and invalid login.
- Session creation and logout.
- Protected board access.
- Initial board creation.
- Column rename.
- Card creation, editing, deletion, and moving.
- Moving Backlog cards to every other column.
- Moving into an empty column.
- Invalid resources.
- Persistence across application restarts.

The latest verified result was:

~~~text
24 passed, 1 warning
~~~

The warning is a Starlette/httpx deprecation warning from the test client. It does not indicate a failed test.

To run the backend tests in Docker from Windows PowerShell:

~~~powershell
$testsPath = (Resolve-Path .\backend\tests).Path
docker compose run --rm -v "${testsPath}:/app/tests:ro" app sh -c "uv sync --group dev --no-install-project && uv run --no-sync pytest"
~~~

If copying multiple commands causes problems, paste the first line, wait for it to finish, then paste the second line.

### Frontend unit tests

Unit and component tests use Vitest and Testing Library. They cover:

- Pure Kanban movement calculations.
- Login and authentication states.
- Board component operations with mocked API responses.

Run from the frontend folder:

~~~powershell
npm.cmd run test:unit
~~~

Latest verified result:

~~~text
10 passed
~~~

### Browser tests

Playwright tests exercise the visible user experience. They cover:

- Signed-out users seeing the login screen.
- Signing in and logging out.
- Loading the board.
- Adding a card.
- Moving cards between columns.
- Moving Backlog cards to other columns.
- Moving a card into an empty column.

Run from the frontend folder:

~~~powershell
npx.cmd playwright test
~~~

Latest verified result:

~~~text
9 passed
~~~

These browser tests mock API responses so they are repeatable and do not alter the real Docker database.

To test the production frontend and real FastAPI API together through Docker, first start the container and then run:

~~~powershell
npm.cmd run test:e2e:docker
~~~

This dedicated smoke test loads the Docker-served login page, signs in through the real session API, confirms that all five columns load, and logs out. The latest result was 1 passed.

### Build and lint checks

Run from the frontend folder:

~~~powershell
npm.cmd run lint
npm.cmd run build
~~~

Lint checks code style and common mistakes. The build confirms that the frontend can be statically exported. The Docker build repeats this frontend build inside the image.

## 14. Environment variables and secrets

The root .env file can contain values used by Docker Compose. The project is prepared for:

~~~text
OPENROUTER_API_KEY=your-key-here
~~~

The key is used by the backend OpenRouter assistant. It must remain server-side and must not be placed in frontend code or variables beginning with NEXT_PUBLIC_.

The backend also supports:

- DATABASE_PATH: SQLite file location. Docker sets this to /data/project-management.db.
- SESSION_SECRET: secret used to sign the session cookie. The default is for development only.

Do not commit .env or real API keys to source control. The .gitignore file excludes .env.

## 15. Common beginner problems

### start.ps1 is not recognized

PowerShell is probably running from the wrong directory. The command must be run from the project root, the folder containing Dockerfile and docker-compose.yml.

Check the current folder:

~~~powershell
Get-Location
~~~

Move to the project folder if necessary:

~~~powershell
Set-Location "C:\path\to\projects\pm"
~~~

Then run:

~~~powershell
.\scripts\start.ps1
~~~

### PowerShell says script execution is disabled

Run:

~~~powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
~~~

Then run the start script again in the same PowerShell window.

### localhost:8000 refuses to connect

Check the container:

~~~powershell
docker compose ps
~~~

If it is stopped, start it:

~~~powershell
docker compose up -d --build
~~~

If it is restarting or unhealthy, inspect the logs:

~~~powershell
docker compose logs --tail=200 app
~~~

### The page says Board request failed

This usually means the frontend loaded but its API request failed. Check that:

1. The container is healthy.
2. You are using http://localhost:8000.
3. You are signed in.
4. The container was rebuilt after source changes.

Then rebuild and hard-refresh the browser with Ctrl+F5.

### Tests collect zero items

Run backend tests with the tests directory mounted into the container as shown in the backend testing section. The project configuration expects tests in /app/tests.

### The browser shows old behavior

The browser may have cached an older static build, or Docker may still be running an older image. Rebuild and restart:

~~~powershell
docker compose up -d --build
~~~

Then use Ctrl+F5 in the browser.

## 16. What is complete and what is next

### Complete in the current MVP

- Project plan and documentation structure.
- Docker packaging.
- Static Next.js frontend served by FastAPI.
- Demo sign-in and logout.
- SQLite schema and automatic initialization.
- Authenticated board API.
- Persistent board changes.
- Column renaming.
- Card creation, editing, deleting, and moving.
- Drag-and-drop handling for normal and empty columns.
- Frontend and backend automated tests.

### Future work outside the current MVP

The next planned area is:

1. Future multi-user authentication and cross-user board isolation.

The backend chat route accepts a user message and conversation history, includes the current board JSON in the provider request, validates the structured response, and applies valid card or column operations in one database transaction. The frontend sidebar displays the conversation and replaces its board state with the returned board.

The backend connectivity smoke check is optional because it makes a real external request:

~~~powershell
docker compose run --rm app sh -c "python -m app.openrouter_check"
~~~

Normal tests use mocked provider responses and do not spend API credits. The live check has been run successfully and returned 4.

The current AI flow looks like this:

~~~text
User asks a question in the chat sidebar
    |
    v
Frontend sends the question to FastAPI
    |
    v
FastAPI sends the current board and question to OpenRouter
    |
    v
FastAPI validates the AI response
    |
    +--> Displays the AI reply
    |
    +--> Applies safe card/column operations to SQLite
          |
          v
        Frontend refreshes the board
~~~

The AI must remain behind the backend so the OpenRouter key is never exposed to the browser.

## 17. A simple developer workflow

For a normal change:

1. Read AGENTS.md and docs/PLAN.md.
2. Identify whether the change belongs to the frontend, backend, Docker setup, or documentation.
3. Make the smallest change that satisfies the requirement.
4. Add or update a test for the behavior.
5. Run the relevant frontend tests.
6. Run the backend tests in Docker when backend behavior changed.
7. Rebuild the Docker image.
8. Check the application at http://localhost:8000.
9. Update documentation if setup or behavior changed.

A useful beginner rule is:

- If a change affects saved board data or an API route, test it in the backend.
- If it affects what a user sees or clicks, test it in the frontend or browser tests.
- If it affects how the app starts, test it through Docker.

## 18. Glossary

| Term | Plain-language meaning |
| --- | --- |
| API | URLs that software uses to communicate with other software. |
| Backend | The server-side part that applies rules and accesses data. |
| Build | Converting source code into runnable output. |
| Container | An isolated package containing an application and its runtime. |
| Docker image | The packaged template used to create a container. |
| Docker volume | Persistent storage managed by Docker. |
| Endpoint | One API URL, such as /api/board. |
| Frontend | The part of the application shown in the browser. |
| HTTP | The request and response language used by browsers and servers. |
| JSON | A text format used to send structured data. |
| Kanban | A workflow board where cards move through stages. |
| React component | A reusable piece of a React user interface. |
| Session cookie | A browser cookie that tells the backend a user is signed in. |
| SQLite | A database stored in a local file. |
| Static export | Frontend files served directly without a Next.js server. |
| Uvicorn | The server process that runs FastAPI. |

## 19. Final summary

The project started as a frontend-only Kanban demo. It was expanded into a locally runnable application by:

1. Adding a FastAPI backend.
2. Adding SQLite persistence.
3. Adding session-based sign-in and logout.
4. Connecting the frontend to authenticated board APIs.
5. Packaging the frontend and backend together with Docker.
6. Adding scripts for Windows, macOS, and Linux.
7. Adding unit, browser, and backend tests.

The main command for a Windows developer is:

~~~powershell
docker compose up -d --build
~~~

Then open:

~~~text
http://localhost:8000
~~~

The current application is a functional board MVP with backend AI connectivity, structured board operations, and a frontend assistant sidebar. Future work is multi-user authentication and cross-user board isolation.
