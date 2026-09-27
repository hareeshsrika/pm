# Frontend Instructions

## Current application

This directory contains the existing frontend-only Kanban demo for the Project Management MVP. It is a Next.js application using React and TypeScript.

## Structure

- `src/app/page.tsx` is the root page and renders `AuthGate`, which checks the backend session before showing the board.
- `src/app/layout.tsx` defines the root layout and metadata. Typography uses local system-font fallbacks in `src/app/globals.css` so production builds do not require network access.
- `src/app/globals.css` contains Tailwind CSS setup and the project color variables.
- `src/lib/kanban.ts` defines `Card`, `Column`, and `BoardData`, provides the in-memory `initialData`, and contains card movement and ID-generation helpers.
- `src/lib/auth.ts` contains the frontend client for session lookup, login, and logout.
- `src/lib/boardApi.ts` contains the frontend client for loading and mutating the authenticated board.
- `src/components/AuthGate.tsx` handles the session check and switches between login and the board.
- `src/components/LoginForm.tsx` renders the sign-in form and credential errors.
- `src/components/KanbanBoard.tsx` is the client-side board container. It loads server state and persists drag, rename, add, edit, and delete actions through the API.
- `src/components/KanbanColumn.tsx` renders a column, its sortable cards, rename input, and new-card form.
- `src/components/KanbanCard.tsx` renders a sortable card with edit and remove actions.
- `src/components/KanbanCardPreview.tsx` renders the drag overlay.
- `src/components/NewCardForm.tsx` manages the add-card form state.
- `src/components/*.test.tsx` and `src/lib/*.test.ts` contain Vitest and Testing Library coverage for board behavior and pure movement logic.
- `tests/kanban.spec.ts` contains Playwright browser tests for loading, adding, and moving cards.

## Current behavior and limitations

- Board state is loaded from the backend and mutations are persisted through the API.
- The demo starts with five columns: Backlog, Discovery, In Progress, Review, and Done.
- Columns can be renamed in place.
- Cards can be added, removed, reordered, and moved between columns.
- Card editing is implemented through an inline edit form.
- AI chat is not implemented yet.
- `page.tsx` is a server component by default; `KanbanBoard.tsx` is the client component because it uses state and drag-and-drop hooks.

## Tooling and commands

Run commands from this directory:

```bash
npm install
npm run dev
npm run build
npm run lint
npm run test:unit
npm run test:e2e
npm run test:all
```

- Next.js and React provide the application runtime.
- Tailwind CSS 4 is loaded from `src/app/globals.css`.
- `@dnd-kit/core` and `@dnd-kit/sortable` provide drag-and-drop behavior.
- Vitest runs unit and component tests in `jsdom` through `vitest.config.ts`.
- Playwright runs Chromium tests through `playwright.config.ts`; it starts the Next.js development server at `http://127.0.0.1:3000` when needed.

## Project conventions

- Preserve the color variables and visual language in `src/app/globals.css` unless a requirement calls for a change.
- Keep board state transitions in small, testable functions. Prefer extending `src/lib/kanban.ts` for pure operations rather than embedding complex transformations in JSX.
- Use accessible labels and roles for interactive controls so the existing Testing Library and Playwright approach remains reliable.
- Keep frontend API calls separate from presentational components when backend integration is added.
- Add or update unit tests for pure logic and component behavior, and add Playwright coverage for user-visible flows.
- Do not put the OpenRouter API key or other secrets in frontend code or `NEXT_PUBLIC_*` variables.
- Keep README and code comments concise. Do not add emojis.
